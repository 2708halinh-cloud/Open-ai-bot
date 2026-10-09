#!/usr/bin/env python3
"""SOL personal-access — GitHub REST from user's own OS and credential.
Never embeds tokens in source or prints secret values. Python stdlib; PyNaCl only for GitHub Secrets.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.parse import urlencode, quote

API_BASE = 'https://api.github.com'
VERSION = '2026-03-10'
CHUNK_BYTES = 35000  # under 48 KiB GitHub Actions secret limit, even after seal overhead
MAX_REPO_SECRETS = 100

class APIError(RuntimeError):
    pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def configured_token():
    for key in ('SOL_GITHUB_TOKEN','GH_TOKEN','GITHUB_TOKEN'):
        token = os.environ.get(key)
        if token:
            return token.strip()
    # Import only explicitly opted-in local credential file; never from repository or plugin.
    p = os.environ.get('SOL_GITHUB_TOKEN_FILE')
    if p:
        file = Path(p).expanduser()
        if file.exists():
            text = file.read_text(encoding='utf-8-sig').strip()
            if '\n' not in text and '=' not in text:
                return text
            for ln in text.splitlines():
                if re.match(r'^\s*(?:SOL_GITHUB_TOKEN|GH_TOKEN|GITHUB_TOKEN|personal_access_tokens)\s*=',ln):
                    return ln.split('=',1)[1].strip().strip('"\'')
    raise APIError('No token supplied via SOL_GITHUB_TOKEN, GH_TOKEN, GITHUB_TOKEN or SOL_GITHUB_TOKEN_FILE')

class Client:
    def __init__(self, token=None):
        self._token = token if token is not None else configured_token()
    def call(self, method, path, data=None, redirect=False):
        if not path.startswith('/') or path.startswith('//') or '://' in path:
            raise APIError('GitHub API path must start with one slash')
        headers = {'Accept':'application/vnd.github+json','X-GitHub-Api-Version':VERSION,
                   'User-Agent':'SOL-personal-access/0.1', 'Authorization':'Bearer '+self._token}
        body = None
        if data is not None:
            body = json.dumps(data,ensure_ascii=False).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        request = Request(API_BASE+path, data=body, headers=headers, method=method.upper())
        opener = build_opener(NoRedirect()) if not redirect else None
        try:
            with ((opener.open(request, timeout=25) if opener else urlopen(request,timeout=25))) as response:
                raw=response.read()
                return response.status, json.loads(raw.decode('utf-8')) if raw else None, dict(response.headers)
        except HTTPError as e:
            if e.code == 302:
                return 302,None,dict(e.headers)
            # Do not echo any returned tokens or secrets in API errors.
            raise APIError(f'GitHub HTTP {e.code} for {method} {path}') from None
        except URLError as e:
            raise APIError(f'Network error during {method} {path}: {type(e.reason).__name__}') from None
    def paginated(self, path, max_pages=30):
        ret=[]
        for page in range(1,max_pages+1):
            q=('&' if '?' in path else '?')+'per_page=100&page='+str(page)
            _,payload,_=self.call('GET',path+q)
            if not isinstance(payload,list):
                raise APIError('Expected array in paginated response')
            ret.extend(payload)
            if len(payload)<100:break
        return ret
    def list_artifacts(self,repo,run_id=None):
        path=f'/repos/{repo}/actions/' + (f'runs/{int(run_id)}/artifacts' if run_id else 'artifacts')
        return self.call('GET',path+'?per_page=100')[1]
    def get_artifact(self,repo,artifact_id):
        return self.call('GET',f'/repos/{repo}/actions/artifacts/{int(artifact_id)}')[1]
    def download_artifact(self,repo,artifact_id,target,max_bytes=300_000_000):
        art=self.get_artifact(repo,artifact_id)
        if art.get('expired'):
            raise APIError('Artifact is marked expired')
        status,_,hdr=self.call('GET',f'/repos/{repo}/actions/artifacts/{int(artifact_id)}/zip')
        if status != 302:raise APIError(f'Expected artifact redirect (302), got {status}')
        link=hdr.get('Location') or hdr.get('location')
        if not link or not link.startswith('https://'):
            raise APIError('Missing HTTPS signed artifact link')
        # Fresh request WITHOUT Authorization, so the PAT is not sent to the object-store host.
        dest=Path(target)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dig=hashlib.sha256(); size=0
        with tempfile.NamedTemporaryFile(dir=dest.parent,prefix='.sol-artifact-',delete=False) as f:
            temp=Path(f.name)
            try:
                with urlopen(Request(link,headers={'User-Agent':'SOL-personal-access/0.1'}),timeout=90) as r:
                    while True:
                        part=r.read(1024*1024)
                        if not part: break
                        size+=len(part)
                        if size>max_bytes: raise APIError('Artifact exceeds configured size limit')
                        f.write(part);dig.update(part)
                expected=str(art.get('digest') or '')
                if expected.startswith('sha256:') and expected[7:].lower()!=dig.hexdigest():
                    raise APIError('Downloaded artifact digest mismatch')
                os.replace(temp,dest)
            finally:
                temp.unlink(missing_ok=True)
        return {'path':str(dest),'sha256':dig.hexdigest(),'bytes':size,'artifact_id':int(artifact_id),'digest_recorded':bool(art.get('digest'))}
    def write_status(self,repo,sha,state,description,context='sol-personal-access/ci',target_url=None):
        if state not in ('error','failure','pending','success'):raise APIError('Bad state')
        data={'state':state,'description':description[:140],'context':context}
        if target_url:data['target_url']=target_url
        return self.call('POST',f'/repos/{repo}/statuses/{sha}',data)[1]
    def list_secret_metadata(self,repo):
        return self.call('GET',f'/repos/{repo}/actions/secrets?per_page=100')[1]
    def write_secret(self,repo,name,value):
        try:
            from nacl import encoding,public
        except ImportError:
            raise APIError('PyNaCl required for GitHub Actions Secrets. Install via pip install pynacl') from None
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name):raise APIError('Invalid secret name')
        _,key,_=self.call('GET',f'/repos/{repo}/actions/secrets/public-key')
        pub=public.PublicKey(key['key'].encode('ascii'),encoding.Base64Encoder())
        enc=base64.b64encode(public.SealedBox(pub).encrypt(value.encode('utf-8'))).decode('ascii')
        code,_,_=self.call('PUT',f'/repos/{repo}/actions/secrets/{name}',{'encrypted_value':enc,'key_id':key['key_id']})
        if code not in (201,204):raise APIError('Unexpected secret API status')
        return code

def ensure_repo(repo):
    if not re.fullmatch(r'[A-Za-z0-9-]+/[A-Za-z0-9_.-]+',repo) or '..' in repo or repo.split('/')[-1].startswith('.'):raise APIError('Expected owner/repo')
    return repo

def chunks_for_file(path,prefix):
    """Return opaque base64 chunks and minimal encrypted manifest. Never output contents in report."""
    raw=Path(path).read_bytes()
    packed=base64.b64encode(gzip.compress(raw,compresslevel=9,mtime=0)).decode('ascii')
    chunks=[packed[i:i+CHUNK_BYTES] for i in range(0,len(packed),CHUNK_BYTES)]
    if not chunks: chunks=['']
    manifest={'schema':'ggdv.secret-carrier/1','name':prefix,'encoding':'gzip+base64',
              'sha256':hashlib.sha256(raw).hexdigest(),'raw_bytes':len(raw),
              'part_count':len(chunks),'part_prefix':'GGDV_'+prefix+'_PART_'}
    return manifest,chunks

def decode_chunks(manifest,chunks):
    if len(chunks)!=manifest['part_count']:
        raise APIError('Incorrect chunk count')
    raw=gzip.decompress(base64.b64decode(''.join(chunks),validate=True))
    if len(raw)!=manifest['raw_bytes'] or hashlib.sha256(raw).hexdigest()!=manifest['sha256']:
        raise APIError('Source SHA-256 readback failed')
    return raw

SOURCE_NAMES=[('DOT_ENV','.ENV'),('TOKEN_JSON','TOKEN.JSON'),('SOL_TXT','SOL.txt'),('HALIN_TXT','Halin.txt')]

def source_plan(source_dir,overrides):
    planned=[]
    for pref,file in SOURCE_NAMES:
        path=Path(overrides.get(pref) or (Path(source_dir)/file))
        if not path.is_file():
            planned.append({'name':pref,'state':'OPEN_SOURCE_NOT_FOUND','path':str(path)})
            continue
        manifest,chunks=chunks_for_file(path,pref)
        if len(chunks)+1>MAX_REPO_SECRETS:
            raise APIError('File requires too many Actions Secrets; choose encrypted asset carrier')
        # Verify in memory before any GitHub modifications.
        assert decode_chunks(manifest,chunks)==path.read_bytes()
        planned.append({'name':pref,'state':'PREPARED_LOCAL_VERIFIED','path':str(path),
                        'sha256':manifest['sha256'],'raw_bytes':manifest['raw_bytes'],
                        'part_count':len(chunks),'manifest':manifest,'chunks':chunks})
    return planned

def source_sync(client,repo,plan,apply=False):
    # Do not disclose source bytes. Only names/hash/count included in audit.
    result=[]
    prepared=[p for p in plan if 'chunks' in p]
    required=sum(len(p['chunks'])+1 for p in prepared)
    if required>MAX_REPO_SECRETS:raise APIError('Secrets exceed GitHub repository limit')
    if apply:
        metadata=client.list_secret_metadata(repo)
        existing={x['name'] for x in metadata.get('secrets',[])}
        names={f'GGDV_{p["name"]}_META' for p in prepared}
        names.update(f'GGDV_{p["name"]}_PART_{i:03d}' for p in prepared for i in range(len(p['chunks'])))
        if len(existing | names)>MAX_REPO_SECRETS:
            raise APIError('Existing repository Secrets + planned names exceed 100; no writes performed')
    for p in plan:
        out={k:p[k] for k in ('name','state')}
        if 'manifest' in p:
            out.update({'sha256':p['sha256'],'raw_bytes':p['raw_bytes'],'part_count':p['part_count']})
            if apply:
                for i,part in enumerate(p['chunks']):
                    client.write_secret(repo,f'GGDV_{p["name"]}_PART_{i:03d}',part)
                client.write_secret(repo,f'GGDV_{p["name"]}_META',json.dumps(p['manifest'],separators=(',',':')))
                out['state']='WRITTEN_API_NOT_BYTE_READBACK'
        result.append(out)
    if apply:
        metadata=client.list_secret_metadata(repo)
        available={x['name'] for x in metadata.get('secrets',[])}
        for p in result:
            if p['state']=='WRITTEN_API_NOT_BYTE_READBACK':
                p['remote_name_receipt']=(f'GGDV_{p["name"]}_META' in available)
    return result

def cli(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',default='2708halinh-cloud/SOL-LONG-MACH')
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('whoami')
    sub.add_parser('repo')
    a=sub.add_parser('artifacts');a.add_argument('--run-id',type=int)
    a=sub.add_parser('artifact');a.add_argument('id',type=int)
    a=sub.add_parser('download-artifact');a.add_argument('id',type=int);a.add_argument('--output',required=True)
    a=sub.add_parser('secrets-list')
    a=sub.add_parser('status');a.add_argument('sha');a.add_argument('state',choices=['pending','success','error','failure']);a.add_argument('--description',required=True);a.add_argument('--context',default='sol-personal-access/ci')
    a=sub.add_parser('source-plan');a.add_argument('--source-dir',required=True);a.add_argument('--env-file');a.add_argument('--token-json');a.add_argument('--sol-txt');a.add_argument('--halin-txt')
    a=sub.add_parser('source-sync');a.add_argument('--source-dir',required=True);a.add_argument('--apply',action='store_true');a.add_argument('--env-file');a.add_argument('--token-json');a.add_argument('--sol-txt');a.add_argument('--halin-txt')
    a=sub.add_parser('api');a.add_argument('method',choices=['GET','POST','PUT','PATCH','DELETE']);a.add_argument('path');a.add_argument('--data-json-file')
    args=p.parse_args(argv)
    repo=ensure_repo(args.repo)
    if args.cmd in ('source-plan','source-sync'):
        overrides={k:v for k,v in [('DOT_ENV',args.env_file),('TOKEN_JSON',args.token_json),('SOL_TXT',args.sol_txt),('HALIN_TXT',args.halin_txt)] if v}
        plan=source_plan(args.source_dir,overrides)
        client=Client() if args.cmd=='source-sync' and args.apply else None
        value=source_sync(client,repo,plan,apply=bool(args.cmd=='source-sync' and args.apply))
        print(json.dumps(value,ensure_ascii=False,indent=2));return
    c=Client()
    if args.cmd=='whoami': obj=c.call('GET','/user')[1]; v={'login':obj.get('login'),'id':obj.get('id')}
    elif args.cmd=='repo': obj=c.call('GET','/repos/'+repo)[1];v={'full_name':obj['full_name'],'private':obj['private'],'permissions':obj.get('permissions',{})}
    elif args.cmd=='artifacts':v=c.list_artifacts(repo,args.run_id)
    elif args.cmd=='artifact':v=c.get_artifact(repo,args.id)
    elif args.cmd=='download-artifact':v=c.download_artifact(repo,args.id,args.output)
    elif args.cmd=='secrets-list':
        obj=c.list_secret_metadata(repo);v={'total_count':obj.get('total_count'),'secrets':[{'name':s['name'],'updated_at':s.get('updated_at')} for s in obj.get('secrets',[])]}
    elif args.cmd=='status': obj=c.write_status(repo,args.sha,args.state,args.description,args.context);v={'id':obj.get('id'),'state':obj.get('state'),'context':obj.get('context'),'sha':args.sha}
    elif args.cmd=='api':
        data=json.loads(Path(args.data_json_file).read_text()) if args.data_json_file else None
        status,obj,_=c.call(args.method,args.path,data);v={'status':status,'body':obj}
    else:raise APIError('Unsupported command')
    print(json.dumps(v,ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:cli()
    except (APIError,KeyError,ValueError) as e:
        print('SOL personal-access: '+str(e),file=sys.stderr);sys.exit(2)
