from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .store import Store


class DeployEngine:
    def __init__(self, *, workspace_root: str | Path, state_dir: str | Path):
        self.workspace_root = Path(workspace_root).expanduser().resolve()
        self.state_dir = Path(state_dir).expanduser().resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = self.state_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.store = Store(self.state_dir / "sol-deploy.sqlite3")
        self._processes: dict[str, subprocess.Popen[Any]] = {}
        self._log_handles: dict[str, Any] = {}

    def _inside_workspace(self, path: str | Path) -> Path:
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = self.workspace_root / target
        target = target.resolve()
        try:
            target.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ValueError(f"ROOT_OUTSIDE_WORKSPACE:{target}") from exc
        if not target.exists() or not target.is_dir():
            raise FileNotFoundError(f"ROOT_NOT_FOUND:{target}")
        return target

    def create_project(self, name: str, root: str) -> dict[str, Any]:
        target = self._inside_workspace(root)
        return self.store.create_project(name.strip() or target.name, str(target))

    def create_service(
        self,
        *,
        project_id: str,
        name: str,
        root: str,
        build_command: str,
        start_command: str,
        health_path: str = "/",
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        if not project:
            raise KeyError(f"PROJECT_NOT_FOUND:{project_id}")
        target = self._inside_workspace(root)
        hp = health_path if health_path.startswith("/") else "/" + health_path
        return self.store.create_service(
            project_id=project_id,
            name=name.strip() or target.name,
            root=str(target),
            build_command=build_command.strip(),
            start_command=start_command.strip(),
            health_path=hp,
            env=env or {},
        )

    def _service(self, service_id: str) -> dict[str, Any]:
        item = self.store.get_service(service_id)
        if not item:
            raise KeyError(f"SERVICE_NOT_FOUND:{service_id}")
        self._inside_workspace(item["root"])
        return item

    def _runtime_env(self, service: dict[str, Any], port: int | None = None) -> dict[str, str]:
        env = os.environ.copy()
        for key, value in (service.get("env") or {}).items():
            env[str(key)] = str(value)
        if port is not None:
            env["PORT"] = str(port)
        return env

    @staticmethod
    def _allocate_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def build(self, service_id: str, timeout: int = 900) -> dict[str, Any]:
        service = self._service(service_id)
        command = service["build_command"]
        if not command:
            self.store.update_service(service_id, status="BUILT")
            return {"ok": True, "skipped": True, "service": self.store.get_service(service_id)}

        log_path = self.logs_dir / f"{service_id}-build.log"
        run = self.store.create_run(service_id, "BUILD", log_path=str(log_path))
        self.store.update_service(service_id, status="BUILDING")
        try:
            proc = subprocess.run(
                command,
                cwd=service["root"],
                env=self._runtime_env(service),
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
            output = proc.stdout or ""
            log_path.write_text(output, encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                self.store.finish_run(run["id"], status="FAILED", exit_code=proc.returncode)
                self.store.update_service(service_id, status="BUILD_FAILED")
                return {"ok": False, "exit_code": proc.returncode, "log": output[-12000:]}
            self.store.finish_run(run["id"], status="SUCCEEDED", exit_code=0)
            service = self.store.update_service(service_id, status="BUILT")
            return {"ok": True, "exit_code": 0, "service": service, "log": output[-12000:]}
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            log_path.write_text(output, encoding="utf-8", errors="replace")
            self.store.finish_run(run["id"], status="TIMEOUT")
            self.store.update_service(service_id, status="BUILD_TIMEOUT")
            return {"ok": False, "error": "BUILD_TIMEOUT", "log": output[-12000:]}

    def _healthcheck(self, port: int, path: str, timeout: float) -> tuple[bool, int | None, str | None]:
        deadline = time.monotonic() + timeout
        url = f"http://127.0.0.1:{port}{path}"
        last_error: str | None = None
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=1.5) as res:
                    code = int(res.status)
                    if 200 <= code < 400:
                        return True, code, None
                    last_error = f"HTTP_{code}"
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = str(exc)
            time.sleep(0.2)
        return False, None, last_error

    def deploy(self, service_id: str, health_timeout: float = 15.0) -> dict[str, Any]:
        service = self._service(service_id)
        if service_id in self._processes and self._processes[service_id].poll() is None:
            raise RuntimeError("SERVICE_ALREADY_RUNNING")
        if not service["start_command"]:
            raise ValueError("START_COMMAND_REQUIRED")

        port = self._allocate_port()
        command = service["start_command"].replace("{port}", str(port))
        log_path = self.logs_dir / f"{service_id}-deploy.log"
        handle = open(log_path, "a", encoding="utf-8", buffering=1)
        kwargs: dict[str, Any] = {}
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            kwargs["start_new_session"] = True

        run = self.store.create_run(service_id, "DEPLOY", log_path=str(log_path), meta={"port": port})
        self.store.update_service(service_id, status="DEPLOYING", port=port, pid=None)
        proc = subprocess.Popen(
            command,
            cwd=service["root"],
            env=self._runtime_env(service, port),
            shell=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            **kwargs,
        )
        self._processes[service_id] = proc
        self._log_handles[service_id] = handle
        self.store.update_service(service_id, status="HEALTHCHECK", port=port, pid=proc.pid)

        ok, status_code, error = self._healthcheck(port, service["health_path"], health_timeout)
        if not ok:
            self._terminate(service_id)
            self.store.finish_run(run["id"], status="FAILED", exit_code=proc.poll(), meta={"health_error": error, "port": port})
            self.store.update_service(service_id, status="DEPLOY_FAILED", port=port, pid=None)
            return {"ok": False, "error": "HEALTHCHECK_FAILED", "health_error": error, "port": port}

        service = self.store.update_service(service_id, status="RUNNING", port=port, pid=proc.pid)
        self.store.finish_run(run["id"], status="SUCCEEDED", exit_code=None, meta={"health_status": status_code, "port": port, "pid": proc.pid})
        return {
            "ok": True,
            "service": service,
            "url": f"http://127.0.0.1:{port}",
            "health_status": status_code,
        }

    def _terminate(self, service_id: str) -> bool:
        proc = self._processes.get(service_id)
        if not proc:
            return False
        if proc.poll() is None:
            try:
                if os.name != "nt":
                    os.killpg(proc.pid, signal.SIGTERM)
                else:
                    proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                    proc.wait(timeout=3)
                except Exception:
                    pass
        handle = self._log_handles.pop(service_id, None)
        if handle:
            try:
                handle.close()
            except Exception:
                pass
        self._processes.pop(service_id, None)
        return True

    def stop(self, service_id: str) -> dict[str, Any]:
        self._service(service_id)
        stopped = self._terminate(service_id)
        service = self.store.update_service(service_id, status="STOPPED", pid=None, port=None)
        return {"ok": True, "stopped_current_runtime_process": stopped, "service": service}

    def redeploy(self, service_id: str) -> dict[str, Any]:
        self.stop(service_id)
        build = self.build(service_id)
        if not build.get("ok"):
            return {"ok": False, "stage": "BUILD", "build": build}
        deploy = self.deploy(service_id)
        return {"ok": bool(deploy.get("ok")), "stage": "DEPLOY", "build": build, "deploy": deploy}

    def logs(self, service_id: str, max_bytes: int = 65536) -> str:
        service = self._service(service_id)
        candidates = [
            self.logs_dir / f"{service_id}-deploy.log",
            self.logs_dir / f"{service_id}-build.log",
        ]
        for path in candidates:
            if path.exists():
                data = path.read_bytes()
                return data[-max_bytes:].decode("utf-8", errors="replace")
        return ""

    def services(self) -> list[dict[str, Any]]:
        items = self.store.list_services()
        for item in items:
            proc = self._processes.get(item["id"])
            if proc is not None and proc.poll() is not None and item["status"] == "RUNNING":
                item = self.store.update_service(item["id"], status="EXITED", pid=None)
        return items
