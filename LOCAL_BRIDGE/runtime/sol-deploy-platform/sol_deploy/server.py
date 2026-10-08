from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .engine import DeployEngine


DASHBOARD = r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SOL Deploy Platform</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#0d1117;color:#e6edf3}
main{max-width:1100px;margin:auto;padding:24px}
h1{margin:0 0 8px}.muted{color:#8b949e}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px}
input{width:100%;box-sizing:border-box;margin:5px 0 10px;padding:9px;border-radius:8px;border:1px solid #30363d;background:#0d1117;color:#e6edf3}
button{padding:8px 12px;border:0;border-radius:8px;margin:3px;cursor:pointer}
table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #30363d;text-align:left}
code{font-size:12px}.ok{color:#3fb950}.bad{color:#f85149}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body><main>
<h1>SOL DEPLOY</h1>
<p class="muted">Xây dựng (build) và triển khai (deploy) ứng dụng cục bộ.</p>
<div class="grid">
<section class="card"><h2>Tạo project</h2>
<input id="pn" placeholder="Tên project">
<input id="pr" placeholder="Thư mục project">
<button onclick="createProject()">Tạo project</button></section>
<section class="card"><h2>Tạo service</h2>
<input id="sp" placeholder="Project ID">
<input id="sn" placeholder="Tên service">
<input id="sr" placeholder="Thư mục service">
<input id="sb" placeholder="Lệnh build">
<input id="ss" placeholder="Lệnh start">
<input id="sh" value="/health" placeholder="Health path">
<button onclick="createService()">Tạo service</button></section>
</div>
<section class="card" style="margin-top:16px"><h2>Dịch vụ</h2><div id="services"></div></section>
<pre class="card" id="out" style="white-space:pre-wrap"></pre>
<script>
const out=x=>document.getElementById('out').textContent=typeof x==='string'?x:JSON.stringify(x,null,2);
async function api(path,opt={}){const r=await fetch(path,{headers:{'content-type':'application/json'},...opt});const t=await r.text();let v;try{v=JSON.parse(t)}catch{v=t}if(!r.ok)throw new Error(typeof v==='string'?v:JSON.stringify(v));return v}
async function load(){
 const s=await api('/api/services');
 document.getElementById('services').innerHTML='<table><tr><th>Tên</th><th>Trạng thái</th><th>Cổng</th><th>Hành động</th></tr>'+s.map(x=>'<tr><td>'+x.name+'<br><code>'+x.id+'</code></td><td>'+x.status+'</td><td>'+(x.port||'')+'</td><td><button onclick="act(\''+x.id+'\',\'build\')">Build</button><button onclick="act(\''+x.id+'\',\'deploy\')">Deploy</button><button onclick="act(\''+x.id+'\',\'stop\')">Stop</button><button onclick="act(\''+x.id+'\',\'redeploy\')">Redeploy</button><button onclick="logs(\''+x.id+'\')">Logs</button></td></tr>').join('')+'</table>';
}
async function createProject(){try{out(await api('/api/projects',{method:'POST',body:JSON.stringify({name:pn.value,root:pr.value})}));load()}catch(e){out(e.message)}}
async function createService(){try{out(await api('/api/services',{method:'POST',body:JSON.stringify({project_id:sp.value,name:sn.value,root:sr.value,build_command:sb.value,start_command:ss.value,health_path:sh.value})}));load()}catch(e){out(e.message)}}
async function act(id,a){try{out(await api('/api/services/'+id+'/'+a,{method:'POST',body:'{}'}));load()}catch(e){out(e.message);load()}}
async function logs(id){try{out(await api('/api/services/'+id+'/logs'))}catch(e){out(e.message)}}
load();setInterval(load,4000);
</script></main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    engine: DeployEngine

    def _json(self, status: int, payload):
        raw = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict:
        n = int(self.headers.get("content-length") or "0")
        if not n:
            return {}
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/":
                raw = DASHBOARD.encode("utf-8")
                self.send_response(200)
                self.send_header("content-type", "text/html; charset=utf-8")
                self.send_header("content-length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            if path == "/api/health":
                self._json(200, {"ok": True, "service": "sol-deploy-platform", "version": "0.1.0"})
                return
            if path == "/api/projects":
                self._json(200, self.engine.store.list_projects())
                return
            if path == "/api/services":
                self._json(200, self.engine.services())
                return
            parts = [x for x in path.split("/") if x]
            if len(parts) == 4 and parts[:2] == ["api", "services"] and parts[3] == "logs":
                self._json(200, {"service_id": parts[2], "log": self.engine.logs(parts[2])})
                return
            self._json(404, {"error": "NOT_FOUND"})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self._body()
            if path == "/api/projects":
                item = self.engine.create_project(body.get("name", ""), body["root"])
                self._json(201, item)
                return
            if path == "/api/services":
                item = self.engine.create_service(
                    project_id=body["project_id"],
                    name=body.get("name", ""),
                    root=body["root"],
                    build_command=body.get("build_command", ""),
                    start_command=body["start_command"],
                    health_path=body.get("health_path", "/"),
                    env=body.get("env") or {},
                )
                self._json(201, item)
                return
            parts = [x for x in path.split("/") if x]
            if len(parts) == 4 and parts[:2] == ["api", "services"]:
                sid, action = parts[2], parts[3]
                if action == "build":
                    self._json(200, self.engine.build(sid))
                    return
                if action == "deploy":
                    self._json(200, self.engine.deploy(sid))
                    return
                if action == "stop":
                    self._json(200, self.engine.stop(sid))
                    return
                if action == "redeploy":
                    self._json(200, self.engine.redeploy(sid))
                    return
            self._json(404, {"error": "NOT_FOUND"})
        except (KeyError, ValueError, FileNotFoundError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def log_message(self, fmt, *args):
        return


def serve(host: str | None = None, port: int | None = None) -> None:
    workspace = Path(os.environ.get("SOL_DEPLOY_WORKSPACE") or os.getcwd()).resolve()
    state_dir = Path(os.environ.get("SOL_DEPLOY_STATE_DIR") or (Path(__file__).resolve().parents[1] / ".runtime"))
    engine = DeployEngine(workspace_root=workspace, state_dir=state_dir)
    Handler.engine = engine
    host = host or os.environ.get("SOL_DEPLOY_HOST", "127.0.0.1")
    port = int(port or os.environ.get("SOL_DEPLOY_PORT", "8788"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(json.dumps({"status":"LISTENING","host":host,"port":port,"workspace":str(workspace)}, ensure_ascii=False), flush=True)
    server.serve_forever()
