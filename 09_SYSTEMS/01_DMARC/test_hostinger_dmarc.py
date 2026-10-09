import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).with_name("hostinger_dmarc.py")
s=importlib.util.spec_from_file_location("dm",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestDmarc(unittest.TestCase):
    def test_domain(self):
        self.assertEqual(m.check_domain("EXAMPLE.COM."),"example.com")
        with self.assertRaises(ValueError):m.check_domain("../x")
    def test_rua(self):
        self.assertEqual(m.check_mail("DMARC@Example.COM","example.com"),"dmarc@example.com")
        with self.assertRaises(ValueError):m.check_mail("dmarc@other.com","example.com")
    def test_existing_preserved(self):
        z=[{"name":"_dmarc","type":"TXT","records":[{"content":"v=DMARC1; p=reject"}]}]
        ops=[]
        def mock(method,path,payload=None):ops.append(method);return z
        r=m.run("example.com","dmarc@example.com",apply=True,mailbox_ok=True,auth_ok=True,api_fn=mock)
        self.assertEqual(r["state"],"EXISTING_DMARC_PRESERVED");self.assertEqual(ops,["GET"])
    def test_missing_spf_and_dkim(self):
        self.assertEqual(m.run("example.com","dmarc@example.com",api_fn=lambda *args:[])["state"],"SPF_DKIM_NOT_VISIBLE")
    def test_plan_is_readonly(self):
        z=[{"name":"@","type":"TXT","records":[{"content":"v=spf1 ~all"}]}];ops=[]
        def mock(method,path,payload=None):ops.append(method);return z
        r=m.run("example.com","dmarc@example.com",api_fn=mock)
        self.assertEqual(ops,["GET"]);self.assertEqual(r["state"],"PLAN_ONLY")
        self.assertIn("p=none",r["proposed_txt"])
    def test_write_requires_confirmation(self):
        z=[{"name":"@","type":"TXT","records":[{"content":"v=spf1 ~all"}]}]
        with self.assertRaises(ValueError):m.run("example.com","dmarc@example.com",apply=True,api_fn=lambda *args:z)
    def test_apply_reads_back(self):
        z=[{"name":"@","type":"TXT","records":[{"content":"v=spf1 ~all"}]}]
        z2=z+[{"name":"_dmarc","type":"TXT","records":[{"content":"v=DMARC1; p=none; rua=mailto:dmarc@example.com; pct=100"}]}]
        i=iter([z,{}, {},z2]);ops=[]
        def mock(method,path,payload=None):ops.append(method);return next(i)
        r=m.run("example.com","dmarc@example.com",apply=True,mailbox_ok=True,auth_ok=True,api_fn=mock)
        self.assertEqual(ops,["GET","POST","PUT","GET"]);self.assertTrue(r["readback"])
if __name__=="__main__":unittest.main()
