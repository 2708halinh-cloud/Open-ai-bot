#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, pathlib, subprocess, sys
from typing import Any

FORBIDDEN_CANONICAL_PREFIXES = ("W:", "/mnt/w")

def _walk_strings(obj: Any):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)
    elif isinstance(obj, str):
        yield obj

def validate_config(cfg: dict[str, Any]) -> None:
    if cfg.get("gate_id") != "GGDV_MODUAL_PREACTION_GATE":
        raise ValueError("wrong gate_id")
    policy = cfg.get("policy", {})
    required_true = (
        "mandatory_before_target_mutation",
        "open_means_continue",
        "response_boundary_does_not_close_objective",
        "provider_failure_exhausts_only_that_carrier",
        "fallback_across_authorized_carriers",
        "offline_local_does_not_stop",
    )
    for key in required_true:
        if policy.get(key) is not True:
            raise ValueError(f"{key} must be true")
    gd = cfg.get("google_drive", {})
    if not gd.get("folder_id") or not gd.get("target_title"):
        raise ValueError("Google Drive folder/title binding is required")
    if policy.get("filesystem_mount_is_identity") is not False:
        raise ValueError("filesystem mount must not be canonical Drive identity")
    canonical = {
        "folder_id": gd.get("folder_id"),
        "folder_title": gd.get("folder_title"),
        "target_title": gd.get("target_title"),
        "provider_file_id": gd.get("provider_file_id"),
    }
    for s in _walk_strings(canonical):
        if s.startswith(FORBIDDEN_CANONICAL_PREFIXES):
            raise ValueError("filesystem mount path found in canonical Drive identity")
    required_plugins = {"modual_auto_log","runtime_gate","all_plugins","neurons_sensorimotor","infinity_stones"}
    if not required_plugins.issubset(set(cfg.get("plugins", {}))):
        raise ValueError("missing mandatory plugin binding")

def repo_root_from_config(cfg: dict[str, Any]) -> pathlib.Path:
    return pathlib.Path(cfg["surfaces"]["ubuntu"]["worktree"])

def local_surface_readback(cfg: dict[str, Any]) -> dict[str, Any]:
    root = repo_root_from_config(cfg)
    rels = {
        "ububu": cfg["surfaces"]["ububu"]["entrypoint"],
        "tesseract_os": cfg["surfaces"]["tesseract_os"]["pointer"],
        "tesseract_continuation": cfg["surfaces"]["tesseract_os"]["continuation_workflow"],
        "local_bridge": cfg["surfaces"]["local"]["bridge"],
    }
    out = {}
    for key, rel in rels.items():
        p = root / rel
        out[key] = {"path": str(p), "exists": p.exists()}
    return out

def git_state(root: pathlib.Path) -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            return subprocess.check_output(["git","-C",str(root),*args], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return None
    return {
        "repository": run("config","--get","remote.origin.url"),
        "branch": run("branch","--show-current"),
        "head": run("rev-parse","HEAD"),
    }

def build_gate_packet(cfg: dict[str, Any], task_id: str, route_surface: str, source_direct: str) -> dict[str, Any]:
    validate_config(cfg)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    gd = cfg["google_drive"]
    surfaces = local_surface_readback(cfg)
    blocked = [k for k,v in surfaces.items() if not v["exists"]]
    packet = {
        "schema":"GGDV_MODUAL_GATE_PACKET/1.1",
        "gate_id":cfg["gate_id"],
        "task_id":task_id,
        "observed_at":now,
        "source_direct":source_direct,
        "drive_binding":{
            "provider":gd["provider"],
            "folder_id":gd["folder_id"],
            "target_title":gd["target_title"],
            "provider_file_id":gd.get("provider_file_id"),
            "provider_file_state":gd.get("provider_file_state"),
        },
        "neurons_sensorimotor_binding":cfg["plugins"]["neurons_sensorimotor"],
        "route_surface":route_surface,
        "sequence":cfg["sequence"],
        "surface_readback":surfaces,
        "git":git_state(repo_root_from_config(cfg)),
        "blocked_local_surfaces":blocked,
        "state":"OPEN_CONTINUE",
        "next_rule":"SELECT_NEXT_CALLABLE_CARRIER; blocked/offline carrier never closes objective",
    }
    packet["surface_ready"] = not blocked
    return packet

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="CONFIG_SOL/MODUAL_PREACTION_GATE_CURRENT.json")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--route-surface", required=True)
    ap.add_argument("--source-direct", default="current_chat")
    ap.add_argument("--receipt")
    args = ap.parse_args()
    cfg_path = pathlib.Path(args.config)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    packet = build_gate_packet(cfg, args.task_id, args.route_surface, args.source_direct)
    text = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
    if args.receipt:
        out = pathlib.Path(args.receipt)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
