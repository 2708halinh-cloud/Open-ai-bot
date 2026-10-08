from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sol_deploy.engine import DeployEngine
from sol_deploy.server import Handler


APP = r"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        raw = b"ok"
        self.send_response(200)
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def log_message(self, fmt, *args):
        return

ThreadingHTTPServer(("127.0.0.1", int(os.environ["PORT"])), H).serve_forever()
"""


def request(url: str, *, method: str = "GET", body: dict | None = None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        method=method,
        data=data,
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        raw = res.read().decode("utf-8")
        return res.status, json.loads(raw)


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name)
        self.app_root = self.workspace / "api-demo"
        self.app_root.mkdir()
        (self.app_root / "app.py").write_text(APP, encoding="utf-8")

        Handler.engine = DeployEngine(
            workspace_root=self.workspace,
            state_dir=self.workspace / ".state",
        )
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.httpd.server_address[:2]
        self.base = f"http://{host}:{port}"

    def tearDown(self):
        try:
            for service in Handler.engine.services():
                Handler.engine.stop(service["id"])
        finally:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.thread.join(timeout=3)
            self.tmp.cleanup()

    def test_http_control_plane_build_deploy_stop(self):
        status, health = request(self.base + "/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["ok"])

        _, project = request(
            self.base + "/api/projects",
            method="POST",
            body={"name": "api-demo", "root": str(self.app_root)},
        )
        _, service = request(
            self.base + "/api/services",
            method="POST",
            body={
                "project_id": project["id"],
                "name": "web",
                "root": str(self.app_root),
                "build_command": f'"{sys.executable}" -m compileall .',
                "start_command": f'"{sys.executable}" app.py',
                "health_path": "/health",
            },
        )

        _, built = request(self.base + f"/api/services/{service['id']}/build", method="POST", body={})
        self.assertTrue(built["ok"], built)

        _, deployed = request(self.base + f"/api/services/{service['id']}/deploy", method="POST", body={})
        self.assertTrue(deployed["ok"], deployed)
        with urllib.request.urlopen(deployed["url"] + "/health", timeout=3) as res:
            self.assertEqual(res.status, 200)

        _, listed = request(self.base + "/api/services")
        current = next(x for x in listed if x["id"] == service["id"])
        self.assertEqual(current["status"], "RUNNING")

        _, stopped = request(self.base + f"/api/services/{service['id']}/stop", method="POST", body={})
        self.assertTrue(stopped["ok"])
        self.assertEqual(stopped["service"]["status"], "STOPPED")


if __name__ == "__main__":
    unittest.main()
