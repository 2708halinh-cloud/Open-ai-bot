import hashlib, hmac, json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import personal_access as pa
import ci_server

class Fake:
    def __init__(self):self.names=set();self.calls=[]
    def list_secret_metadata(self,repo):return {'secrets':[{'name':n} for n in sorted(self.names)]}
    def write_secret(self,repo,name,value):
        self.names.add(name);self.calls.append(name)

class Tests(unittest.TestCase):
    def test_roundtrip_binary(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'data';p.write_bytes(b'\0A'+bytes(range(256))*200)
            m,parts=pa.chunks_for_file(p,'SOL_TXT')
            self.assertEqual(pa.decode_chunks(m,parts),p.read_bytes())
            self.assertTrue(all(len(s)<=pa.CHUNK_BYTES for s in parts))
    def test_modified_part_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'SOL.txt';p.write_bytes(b'test'*100)
            m,parts=pa.chunks_for_file(p,'SOL_TXT')
            with self.assertRaises(Exception):pa.decode_chunks(m,['A']+parts[1:])
    def test_missing_sources_remain_open(self):
        with tempfile.TemporaryDirectory() as temp:
            planned=pa.source_plan(temp,{})
            self.assertEqual(len(planned),4)
            self.assertTrue(all(p['state']=='OPEN_SOURCE_NOT_FOUND' for p in planned))
    def test_sync_uses_remote_names_only(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'SOL.txt';p.write_bytes(b'Top secret simulated content')
            planned=pa.source_plan(temp,{})
            fake=Fake(); out=pa.source_sync(fake,'A/B',planned,apply=True)
            self.assertIn('GGDV_SOL_TXT_META',fake.names)
            self.assertTrue(any(x['state']=='WRITTEN_API_NOT_BYTE_READBACK' for x in out))
            self.assertNotIn('Top secret simulated content',str(out))
    def test_client_path(self):
        c=pa.Client('dummy')
        with self.assertRaises(pa.APIError):c.call('GET','https://fake.example/secret')
    def test_filename_repo(self):
        self.assertEqual(pa.ensure_repo('owner/repo'),'owner/repo')
        with self.assertRaises(pa.APIError):pa.ensure_repo('../nope')
    def test_webhook_signature(self):
        payload=b'{"test":1}';key='localsecret'
        sig='sha256='+hmac.new(key.encode(),payload,hashlib.sha256).hexdigest()
        self.assertTrue(ci_server.verify_event(payload,sig,key))
        self.assertFalse(ci_server.verify_event(b'bad',sig,key))
    def test_real_ci_failure(self):
        result=ci_server.execute_real_tests([sys.executable,'-c','import sys;sys.exit(12)'],'.')
        self.assertEqual(result['exit_code'],12)
        self.assertFalse(result['passed'])
    def test_real_ci_success(self):
        result=ci_server.execute_real_tests([sys.executable,'-c','print("hello")'],'.')
        self.assertTrue(result['passed'])
    def test_missing_ci_cmd(self):
        with self.assertRaises(pa.APIError):ci_server.execute_real_tests('exit 0','.')

if __name__=='__main__':unittest.main()
