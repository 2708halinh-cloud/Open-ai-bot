from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _spec(raw: Any) -> dict:
    if isinstance(raw, str):
        return {"path": raw, "depth": 1, "max_entries": 2048, "label": raw}
    if not isinstance(raw, dict):
        return {"path": "", "depth": 1, "max_entries": 2048, "label": ""}
    path = str(raw.get("path") or "")
    return {
        "path": path,
        "label": str(raw.get("label") or path),
        "depth": max(0, int(raw.get("depth", 1))),
        "max_entries": max(1, int(raw.get("max_entries", 2048))),
    }


def _entry_kind(entry: os.DirEntry) -> str:
    try:
        if entry.is_symlink():
            return "symlink"
        if entry.is_dir(follow_symlinks=False):
            return "dir"
        if entry.is_file(follow_symlinks=False):
            return "file"
    except OSError:
        pass
    return "other"


def observe_path(raw_spec: Any) -> dict:
    spec = _spec(raw_spec)
    raw_path = spec["path"]
    result = {
        "label": spec["label"],
        "path": raw_path,
        "exists": False,
        "kind": "absent",
        "files": 0,
        "dirs": 0,
        "bytes": 0,
        "entries": {},
        "truncated": False,
        "errors": [],
    }
    if not raw_path:
        result["errors"].append("EMPTY_PATH")
        return result

    p = Path(raw_path)
    try:
        st = p.stat()
    except FileNotFoundError:
        return result
    except OSError as exc:
        result["errors"].append(f"ROOT_STAT:{type(exc).__name__}:{exc}")
        return result

    result["exists"] = True
    if p.is_file():
        result["kind"] = "file"
        result["files"] = 1
        result["bytes"] = int(st.st_size)
        result["entries"]["."] = {
            "kind": "file",
            "size": int(st.st_size),
            "mtime_ns": int(st.st_mtime_ns),
        }
        return result

    if not p.is_dir():
        result["kind"] = "other"
        result["entries"]["."] = {
            "kind": "other",
            "size": int(getattr(st, "st_size", 0)),
            "mtime_ns": int(st.st_mtime_ns),
        }
        return result

    result["kind"] = "dir"
    max_entries = spec["max_entries"]
    max_depth = spec["depth"]
    stack = [(p, "", 0)]
    seen = 0

    while stack:
        base, rel_base, depth = stack.pop()
        if depth >= max_depth:
            continue
        try:
            children = list(os.scandir(base))
        except OSError as exc:
            result["errors"].append(
                f"SCAN:{rel_base or '.'}:{type(exc).__name__}:{exc}"
            )
            continue

        children.sort(key=lambda e: e.name.casefold())
        for entry in children:
            if seen >= max_entries:
                result["truncated"] = True
                stack.clear()
                break

            rel = entry.name if not rel_base else rel_base + os.sep + entry.name
            kind = _entry_kind(entry)
            try:
                est = entry.stat(follow_symlinks=False)
                size = int(est.st_size) if kind == "file" else 0
                mtime_ns = int(est.st_mtime_ns)
            except OSError as exc:
                size = 0
                mtime_ns = 0
                result["errors"].append(
                    f"STAT:{rel}:{type(exc).__name__}:{exc}"
                )

            result["entries"][rel] = {
                "kind": kind,
                "size": size,
                "mtime_ns": mtime_ns,
            }
            seen += 1

            if kind == "file":
                result["files"] += 1
                result["bytes"] += size
            elif kind == "dir":
                result["dirs"] += 1
                if depth + 1 < max_depth:
                    stack.append((Path(entry.path), rel, depth + 1))

    return result


def observe_paths(specs: list[Any] | None) -> list[dict]:
    return [observe_path(spec) for spec in (specs or [])]


def _key(obs: dict) -> str:
    return str(obs.get("path") or obs.get("label") or "")


def diff_observations(previous: list[dict] | None, current: list[dict] | None) -> dict:
    prev_map = {_key(x): x for x in (previous or [])}
    cur_map = {_key(x): x for x in (current or [])}
    roots = []
    summary = {
        "roots_changed": 0,
        "added": 0,
        "removed": 0,
        "modified": 0,
        "files_delta": 0,
        "dirs_delta": 0,
        "bytes_delta": 0,
        "signals": [],
    }

    for path in sorted(set(prev_map) | set(cur_map), key=str.casefold):
        before = prev_map.get(path) or {
            "path": path, "label": path, "exists": False, "entries": {},
            "files": 0, "dirs": 0, "bytes": 0,
        }
        after = cur_map.get(path) or {
            "path": path, "label": before.get("label", path), "exists": False,
            "entries": {}, "files": 0, "dirs": 0, "bytes": 0,
        }

        b_entries = before.get("entries") or {}
        a_entries = after.get("entries") or {}
        added = sorted(set(a_entries) - set(b_entries), key=str.casefold)
        removed = sorted(set(b_entries) - set(a_entries), key=str.casefold)
        modified = sorted(
            (
                key for key in (set(a_entries) & set(b_entries))
                if a_entries.get(key) != b_entries.get(key)
            ),
            key=str.casefold,
        )

        root_transition = None
        if not before.get("exists") and after.get("exists"):
            root_transition = "ABSENT_TO_PRESENT"
        elif before.get("exists") and not after.get("exists"):
            root_transition = "PRESENT_TO_ABSENT"

        files_delta = int(after.get("files", 0)) - int(before.get("files", 0))
        dirs_delta = int(after.get("dirs", 0)) - int(before.get("dirs", 0))
        bytes_delta = int(after.get("bytes", 0)) - int(before.get("bytes", 0))

        changed = bool(
            root_transition or added or removed or modified
            or files_delta or dirs_delta or bytes_delta
            or before.get("truncated") != after.get("truncated")
            or before.get("errors") != after.get("errors")
        )
        if not changed:
            continue

        roots.append({
            "label": after.get("label") or before.get("label") or path,
            "path": path,
            "transition": root_transition,
            "added": added,
            "removed": removed,
            "modified": modified,
            "files_delta": files_delta,
            "dirs_delta": dirs_delta,
            "bytes_delta": bytes_delta,
            "before_exists": bool(before.get("exists")),
            "after_exists": bool(after.get("exists")),
            "before_truncated": bool(before.get("truncated")),
            "after_truncated": bool(after.get("truncated")),
        })
        summary["roots_changed"] += 1
        summary["added"] += len(added)
        summary["removed"] += len(removed)
        summary["modified"] += len(modified)
        summary["files_delta"] += files_delta
        summary["dirs_delta"] += dirs_delta
        summary["bytes_delta"] += bytes_delta

    signals = []
    transitions = {root.get("transition") for root in roots}
    if "PRESENT_TO_ABSENT" in transitions or summary["removed"] > 0:
        signals.append("MẤT")
    if summary["removed"] > 0 or summary["files_delta"] < 0 or summary["dirs_delta"] < 0 or summary["bytes_delta"] < 0:
        signals.append("BỚT")
    if "ABSENT_TO_PRESENT" in transitions or summary["added"] > 0:
        signals.append("THÊM")
    if summary["files_delta"] > 0 or summary["dirs_delta"] > 0 or summary["bytes_delta"] > 0:
        signals.append("TĂNG")
    if summary["modified"] > 0:
        signals.append("ĐỔI")
    summary["signals"] = signals

    return {"summary": summary, "roots": roots}
