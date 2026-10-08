#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "GGDV_MEMORY_STEWARDSHIP/1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def sha256_file(path: str | os.PathLike[str], chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _default_registry() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "updated_at": None,
        "policy": {
            "THA": "Release current operational relation while preserving source/history.",
            "CAM_GIU": "Pin identity/provenance with a verified recovery copy.",
            "hard_delete_guard": "No hard delete before a verified recovery path exists.",
        },
        "items": [],
        "events": [],
    }


def load_registry(path: str | os.PathLike[str]) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return _default_registry()
    return json.loads(p.read_text(encoding="utf-8"))


def save_registry(path: str | os.PathLike[str], data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now_iso()
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _upsert_item(registry: dict[str, Any], item: dict[str, Any]) -> None:
    items = registry.setdefault("items", [])
    for i, current in enumerate(items):
        if current.get("item_id") == item["item_id"]:
            items[i] = item
            return
    items.append(item)


def retain(
    source_path: str | os.PathLike[str],
    registry_path: str | os.PathLike[str],
    recovery_dir: str | os.PathLike[str],
    *,
    item_id: str | None = None,
) -> dict[str, Any]:
    source = Path(source_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    registry = load_registry(registry_path)
    digest = sha256_file(source)
    size = source.stat().st_size

    recovery_root = Path(recovery_dir).resolve()
    recovery_root.mkdir(parents=True, exist_ok=True)
    safe_name = source.name.replace(os.sep, "_")
    recovery = recovery_root / f"{digest}__{safe_name}"

    if not recovery.exists():
        shutil.copy2(source, recovery)

    recovery_hash = sha256_file(recovery)
    verified = recovery_hash == digest and recovery.stat().st_size == size
    if not verified:
        raise RuntimeError("Recovery copy verification failed")

    iid = item_id or source.name
    item = {
        "item_id": iid,
        "source_path": str(source),
        "source_sha256": digest,
        "bytes": size,
        "current_participation": True,
        "preservation": {
            "mode": "CAM_GIU",
            "recovery_path": str(recovery),
            "recovery_sha256": recovery_hash,
            "verified": verified,
            "verified_at": now_iso(),
        },
    }
    _upsert_item(registry, item)
    registry.setdefault("events", []).append({
        "at": now_iso(),
        "item_id": iid,
        "action": "CAM_GIU",
        "consequence": "VERIFIED_RECOVERY_COPY_CREATED_OR_CONFIRMED",
        "receipt": {
            "source_sha256": digest,
            "recovery_path": str(recovery),
            "recovery_sha256": recovery_hash,
        },
        "readback": {"verified": verified},
    })
    save_registry(registry_path, registry)
    return item


def release_current_relation(
    item_id: str,
    registry_path: str | os.PathLike[str],
    *,
    reason: str,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    items = registry.setdefault("items", [])
    match = next((x for x in items if x.get("item_id") == item_id), None)
    if match is None:
        match = {
            "item_id": item_id,
            "source_path": None,
            "source_sha256": None,
            "bytes": None,
            "preservation": None,
        }
        items.append(match)

    match["current_participation"] = False
    match["release"] = {
        "mode": "THA",
        "reason": reason,
        "source_history_preserved": True,
        "released_at": now_iso(),
    }
    registry.setdefault("events", []).append({
        "at": now_iso(),
        "item_id": item_id,
        "action": "THA",
        "consequence": "CURRENT_RELATION_RELEASED",
        "receipt": {"source_history_preserved": True},
        "readback": {"current_participation": False},
    })
    save_registry(registry_path, registry)
    return match


def deletion_guard(
    source_path: str | os.PathLike[str],
    registry_path: str | os.PathLike[str],
) -> dict[str, Any]:
    source = Path(source_path).resolve()
    if not source.is_file():
        return {
            "allowed": False,
            "reason": "SOURCE_NOT_PRESENT_FOR_HASH_CHECK",
            "source_path": str(source),
        }

    digest = sha256_file(source)
    registry = load_registry(registry_path)
    for item in registry.get("items", []):
        p = (item.get("preservation") or {})
        recovery = p.get("recovery_path")
        if item.get("source_sha256") != digest or not recovery:
            continue
        recovery_path = Path(recovery)
        if recovery_path.is_file() and sha256_file(recovery_path) == digest:
            return {
                "allowed": True,
                "reason": "VERIFIED_RECOVERY_COPY_EXISTS",
                "source_path": str(source),
                "source_sha256": digest,
                "recovery_path": str(recovery_path),
            }

    return {
        "allowed": False,
        "reason": "NO_VERIFIED_RECOVERY_COPY",
        "source_path": str(source),
        "source_sha256": digest,
    }


def registry_readback(registry_path: str | os.PathLike[str]) -> dict[str, Any]:
    registry = load_registry(registry_path)
    results = []
    for item in registry.get("items", []):
        p = item.get("preservation") or {}
        recovery = p.get("recovery_path")
        source_hash = item.get("source_sha256")
        ok = False
        if recovery and source_hash and Path(recovery).is_file():
            ok = sha256_file(recovery) == source_hash
        results.append({
            "item_id": item.get("item_id"),
            "recovery_exists": bool(recovery and Path(recovery).is_file()),
            "hash_matches": ok,
            "current_participation": item.get("current_participation"),
        })
    return {
        "schema": "GGDV_MEMORY_STEWARDSHIP_READBACK/1.0",
        "observed_at": now_iso(),
        "registry": str(Path(registry_path).resolve()),
        "items": results,
        "all_pinned_items_verified": bool(results) and all(x["hash_matches"] for x in results if x["recovery_exists"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("retain")
    p.add_argument("source")
    p.add_argument("--registry", required=True)
    p.add_argument("--recovery-dir", required=True)
    p.add_argument("--item-id")

    p = sub.add_parser("release")
    p.add_argument("item_id")
    p.add_argument("--registry", required=True)
    p.add_argument("--reason", required=True)

    p = sub.add_parser("guard")
    p.add_argument("source")
    p.add_argument("--registry", required=True)

    p = sub.add_parser("readback")
    p.add_argument("--registry", required=True)

    args = parser.parse_args()
    if args.cmd == "retain":
        out = retain(args.source, args.registry, args.recovery_dir, item_id=args.item_id)
    elif args.cmd == "release":
        out = release_current_relation(args.item_id, args.registry, reason=args.reason)
    elif args.cmd == "guard":
        out = deletion_guard(args.source, args.registry)
    else:
        out = registry_readback(args.registry)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
