from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _signals_for(change: str) -> list[str]:
    c = (change or "").upper()
    if c == "CREATED":
        return ["THÊM", "TĂNG"]
    if c == "DELETED":
        return ["MẤT", "BỚT"]
    if c == "RENAMED":
        return ["DỜI", "ĐỔI"]
    if c == "CHANGED":
        return ["ĐỔI"]
    if c in {"DRIVE_BOUND", "DRIVE_UNBOUND"}:
        return ["THÊM"] if c == "DRIVE_BOUND" else ["MẤT"]
    if c == "WATCH_ERROR":
        return ["SENSORY_ERROR"]
    return []


def read_event_batch(
    path: Path,
    offset: int | None,
    *,
    max_events: int = 512,
) -> tuple[list[dict[str, Any]], int, bool]:
    if not path.exists():
        return [], 0 if offset is None else int(offset), False

    size = path.stat().st_size
    start = max(0, int(offset or 0))
    rotated = start > size
    if rotated:
        start = 0

    events: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            handle.seek(start)
            while len(events) < max_events:
                line = handle.readline()
                if not line:
                    break
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    event["signals"] = _signals_for(str(event.get("change") or ""))
                    events.append(event)
            next_offset = handle.tell()
    except OSError:
        # The producer may have the journal open for a few milliseconds.
        # Missing one poll is not missing the event because offset is unchanged.
        return [], start, rotated

    return events, next_offset, rotated


def summarize_events(events: list[dict[str, Any]], *, rotated: bool = False) -> dict[str, Any]:
    counts: dict[str, int] = {}
    signals: list[str] = []
    drives: list[str] = []

    for event in events:
        change = str(event.get("change") or "UNKNOWN").upper()
        counts[change] = counts.get(change, 0) + 1
        drive = str(event.get("drive") or "")
        if drive and drive not in drives:
            drives.append(drive)
        for signal in event.get("signals") or []:
            if signal not in signals:
                signals.append(signal)

    return {
        "event_count": len(events),
        "counts": counts,
        "signals": signals,
        "drives": drives,
        "journal_rotated": bool(rotated),
    }
