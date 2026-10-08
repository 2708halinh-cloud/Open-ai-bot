from __future__ import annotations

import os
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sol_deploy.engine import DeployEngine


APP = r'''
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            raw = b"ok"
            self.send_response(200)
        else:
            raw = json.dumps({"hello":"sol-deploy"}).encode()
            self.send_response(200)
        self.send_header("content-type","application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def log_message(self, fmt, *args):
        return

ThreadingHTTPServer(("127.0.0.1", int(os.environ["PORT"])), H).serve_forever()
'''


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name)
        self.project_root = self.workspace / "demo"
        self.project_root.mkdir()
        (self.project_root / "app.py").write_text(APP, encoding="utf-8")
        self.engine = DeployEngine(
            workspace_root=self.workspace,
            state_dir=self.workspace / ".state",
        )

    def tearDown(self):
        for service in self.engine.services():
            try:
                self.engine.stop(service["id"])
            except Exception:
                pass
        self.tmp.cleanup()

    def test_build_deploy_health_read_stop(self):
        project = self.engine.create_project("demo", str(self.project_root))
        service = self.engine.create_service(
            project_id=project["id"],
            name="web",
            root=str(self.project_root),
            build_command=f'"{sys.executable}" -c "from pathlib import Path; Path(\'built.txt\').write_text(\'ok\')"',
            start_command=f'"{sys.executable}" app.py',
            health_path="/health",
        )
        built = self.engine.build(service["id"])
        self.assertTrue(built["ok"], built)
        self.assertEqual((self.project_root / "built.txt").read_text(), "ok")

        deployed = self.engine.deploy(service["id"], health_timeout=10)
        self.assertTrue(deployed["ok"], deployed)
        with urllib.request.urlopen(deployed["url"] + "/", timeout=3) as res:
            self.assertEqual(res.status, 200)
            self.assertIn("sol-deploy", res.read().decode())

        current = self.engine.store.get_service(service["id"])
        self.assertEqual(current["status"], "RUNNING")
        stopped = self.engine.stop(service["id"])
        self.assertTrue(stopped["ok"])
        self.assertEqual(stopped["service"]["status"], "STOPPED")

    def test_reject_root_outside_workspace(self):
        outside = Path(tempfile.mkdtemp())
        try:
            with self.assertRaises(ValueError):
                self.engine.create_project("outside", str(outside))
        finally:
            try:
                outside.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
