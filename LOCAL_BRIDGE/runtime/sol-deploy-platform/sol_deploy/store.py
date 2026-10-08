from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    root TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS services (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    root TEXT NOT NULL,
                    build_command TEXT NOT NULL,
                    start_command TEXT NOT NULL,
                    health_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    port INTEGER,
                    pid INTEGER,
                    env_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    exit_code INTEGER,
                    log_path TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    meta_json TEXT NOT NULL,
                    FOREIGN KEY(service_id) REFERENCES services(id)
                );
                """
            )

    def _one(self, query: str, args: tuple[Any, ...]) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(query, args).fetchone()
            return dict(row) if row else None

    def create_project(self, name: str, root: str) -> dict[str, Any]:
        item = {"id": uuid.uuid4().hex, "name": name, "root": root, "created_at": utc_now()}
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO projects(id,name,root,created_at) VALUES(?,?,?,?)",
                (item["id"], item["name"], item["root"], item["created_at"]),
            )
        return item

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM projects WHERE id=?", (project_id,))

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM projects ORDER BY created_at DESC")]

    def create_service(
        self,
        *,
        project_id: str,
        name: str,
        root: str,
        build_command: str,
        start_command: str,
        health_path: str,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": uuid.uuid4().hex,
            "project_id": project_id,
            "name": name,
            "root": root,
            "build_command": build_command,
            "start_command": start_command,
            "health_path": health_path,
            "status": "CREATED",
            "port": None,
            "pid": None,
            "env_json": json.dumps(env or {}, ensure_ascii=False, sort_keys=True),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO services(
                    id,project_id,name,root,build_command,start_command,health_path,
                    status,port,pid,env_json,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                tuple(item[k] for k in (
                    "id","project_id","name","root","build_command","start_command","health_path",
                    "status","port","pid","env_json","created_at","updated_at"
                )),
            )
        return self.get_service(item["id"]) or item

    def _decode_service(self, item: dict[str, Any] | None) -> dict[str, Any] | None:
        if not item:
            return None
        item = dict(item)
        item["env"] = json.loads(item.pop("env_json") or "{}")
        return item

    def get_service(self, service_id: str) -> dict[str, Any] | None:
        return self._decode_service(self._one("SELECT * FROM services WHERE id=?", (service_id,)))

    def list_services(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [self._decode_service(dict(r)) for r in conn.execute("SELECT * FROM services ORDER BY created_at DESC")]

    def update_service(self, service_id: str, **changes: Any) -> dict[str, Any]:
        allowed = {"status", "port", "pid", "env_json", "build_command", "start_command", "health_path"}
        payload = {k: v for k, v in changes.items() if k in allowed}
        payload["updated_at"] = utc_now()
        sets = ", ".join(f"{k}=?" for k in payload)
        with self._lock, self._connect() as conn:
            conn.execute(f"UPDATE services SET {sets} WHERE id=?", (*payload.values(), service_id))
        item = self.get_service(service_id)
        if not item:
            raise KeyError(service_id)
        return item

    def create_run(self, service_id: str, kind: str, *, log_path: str | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        item = {
            "id": uuid.uuid4().hex,
            "service_id": service_id,
            "kind": kind,
            "status": "RUNNING",
            "exit_code": None,
            "log_path": log_path,
            "started_at": utc_now(),
            "finished_at": None,
            "meta_json": json.dumps(meta or {}, ensure_ascii=False, sort_keys=True),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO runs(id,service_id,kind,status,exit_code,log_path,started_at,finished_at,meta_json) VALUES(?,?,?,?,?,?,?,?,?)",
                tuple(item[k] for k in ("id","service_id","kind","status","exit_code","log_path","started_at","finished_at","meta_json")),
            )
        return item

    def finish_run(self, run_id: str, *, status: str, exit_code: int | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE runs SET status=?,exit_code=?,finished_at=?,meta_json=? WHERE id=?",
                (status, exit_code, utc_now(), json.dumps(meta or {}, ensure_ascii=False, sort_keys=True), run_id),
            )
        item = self._one("SELECT * FROM runs WHERE id=?", (run_id,))
        if not item:
            raise KeyError(run_id)
        item["meta"] = json.loads(item.pop("meta_json") or "{}")
        return item

    def list_runs(self, service_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM runs WHERE service_id=? ORDER BY started_at DESC LIMIT ?",
                (service_id, max(1, min(limit, 200))),
            ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["meta"] = json.loads(item.pop("meta_json") or "{}")
            out.append(item)
        return out
