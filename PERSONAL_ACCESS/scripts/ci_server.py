#!/usr/bin/env python3
"""SOL Personal Access CI receiver: verified webhook -> real tests -> commit status.
Run on the owned host, then forward GitHub webhooks to localhost; does not fabricate CI results.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib, hmac, json, os, subprocess, sys, time
from pathlib import Path
from personal_access import Client, APIError

MAX_EVENT = 1_000_000

def verify_event(body, signature, secret):
    if not secret or not signature or not signature.startswith('sha256='):return False
    expected='sha256='+hmac.new(secret.encode(),body,hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,signature)

def execute_real_tests(cmd,cwd,timeout=600):
    if not isinstance(cmd,list) or not cmd or not all(isinstance(s,str) and s for s in cmd):
        raise APIError('CI command must be a JSON array of non-empty argv strings')
    proc=subprocess.run(cmd,cwd=cwd,shell=False,text=True,encoding='utf-8',errors='replace',
                        capture_output=True,timeout=timeout,check=False)
    return {'exit_code':proc.returncode,'passed':proc.returncode==0,
            'stdout_sha256':hashlib.sha256(proc.stdout.encode()).hexdigest(),
            'stderr_sha256':hashlib.sha256(proc.stderr.encode()).hexdigest()}

def main():
    repo=os.environ.get('SOL_CI_REPO','2708halinh-cloud/SOL-LONG-MACH')
    secret=os.environ.get('SOL_CI_WEBHOOK_SECRET','')
    command=os.environ.get('SOL_CI_COMMAND_JSON','')
    if not secret or not command:
        raise APIError('Set SOL_CI_WEBHOOK_SECRET and SOL_CI_COMMAND_JSON before starting')
    try:argv=json.loads(command)
    except ValueError:raise APIError('SOL_CI_COMMAND_JSON is invalid JSON')
    cwd=Path(os.environ.get('SOL_CI_CWD','.')).resolve()
    if not cwd.is_dir():raise APIError('SOL_CI_CWD not found')
    host=os.environ.get('SOL_CI_BIND','127.0.0.1')
    port=int(os.environ.get('SOL_CI_PORT','8777'))
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path!='/event_handler':self.send_error(404);return
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>MAX_EVENT:self.send_error(413);return
            raw=self.rfile.read(n)
            if not verify_event(raw,self.headers.get('X-Hub-Signature-256'),secret):
                self.send_error(401);return
            event=self.headers.get('X-GitHub-Event','')
            try:payload=json.loads(raw.decode())
            except Exception:self.send_error(400);return
            pr=payload.get('pull_request') or {}
            if (event!='pull_request' or payload.get('action') not in ('opened','reopened','synchronize')):
                self.send_response(202);self.end_headers();return
            received_repo=(payload.get('repository') or {}).get('full_name')
            sha=(pr.get('head') or {}).get('sha')
            if received_repo!=repo or not isinstance(sha,str) or len(sha)!=40 or any(c not in '0123456789abcdefABCDEF' for c in sha):
                self.send_error(400);return
            try:
                client=Client()
                client.write_status(repo,sha,'pending','Host tests running')
                start=time.monotonic()
                try:
                    result=execute_real_tests(argv,str(cwd))
                    state='success' if result['passed'] else 'failure'
                except (subprocess.TimeoutExpired,Exception) as error:
                    result={'passed':False,'error_type':type(error).__name__};state='error'
                receipt={'repo':repo,'sha':sha,'state':state,'duration_seconds':round(time.monotonic()-start,2),
                         'test_command':argv,'result':result}
                # This receipt is local; it is never posted as an artifact without an actual producer.
                directory=Path(os.environ.get('SOL_CI_RECEIPTS',str(cwd/'ci-receipts')))
                directory.mkdir(parents=True,exist_ok=True)
                outfile=directory/(sha+'.json')
                outfile.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
                client.write_status(repo,sha,state,'Host test command '+state)
                self.send_response(200);self.end_headers();self.wfile.write(b'CI receipt written')
            except APIError:
                self.send_error(502)
        def log_message(self, fmt, *args):
            # Does not log webhook bodies or credentials.
            sys.stderr.write('SOL CI receiver: '+(fmt%args)+'\n')
    print(f'SOL personal-access CI listening on {host}:{port} repo={repo}')
    ThreadingHTTPServer((host,port),Handler).serve_forever()

if __name__=='__main__':
    try:main()
    except (APIError,ValueError) as e:print(str(e),file=sys.stderr);sys.exit(2)
