from __future__ import annotations
from collections import deque
from datetime import datetime, timezone
import hashlib, json
from typing import Any

# Volatile process-local working surface. Deliberately NOT written to disk/journal.
_MAX_FRAMES = 256
_FRAMES: deque[dict[str, Any]] = deque(maxlen=_MAX_FRAMES)
_COUNTER = 0

HEAD_SOURCE_FOLDER_ID = "1tZ5Dj3tH7EryQ-BBkC4TwaEUVOKgDA2Q"
TAIL_SOURCE_FOLDER_ID = "1Z_ml5lZLEWJYSThqlZYBXHgJns_4zYvn"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(obj: Any) -> str:
    raw=json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str)
    return hashlib.sha256(raw.encode("utf-8",errors="replace")).hexdigest()


def definition() -> dict:
    return {
        "success": True,
        "device_class": "THIET_BI_DAU_CUOI",
        "storage_semantics": "VOLATILE_WORKING_RAM_NOT_MEMORY",
        "head_role": "INGRESS_WHEN_SIGNAL_ENTERS",
        "tail_role": "EGRESS_WHEN_SIGNAL_LEAVES",
        "head_source_folder_id": HEAD_SOURCE_FOLDER_ID,
        "tail_source_folder_id": TAIL_SOURCE_FOLDER_ID,
        "feedback": "TAIL_OUTPUT -> HEAD_INPUT -> NEURONS_SESORIMOTOR",
        "durable_memory": False,
        "journal": False,
        "max_frames": _MAX_FRAMES,
    }


def ingress(signal: dict[str, Any]) -> dict:
    global _COUNTER
    _COUNTER += 1
    frame={
        "frame_id": f"IO-{_COUNTER:08d}-{_digest(signal)[:8]}",
        "cycle_n": _COUNTER,
        "received_at": _now(),
        "head": {
            "role": "INGRESS",
            "source": signal.get("source"),
            "signal_id": signal.get("signal_id"),
            "delta": signal.get("delta"),
            "payload_ref": signal.get("payload_ref"),
            "next_from_actor": signal.get("next"),
        },
        "processing": {
            "owner": signal.get("owner") or "NEURONS_SESORIMOTOR",
            "active": True,
        },
        "tail": {
            "role": "EGRESS",
            "next": None,
            "done": [],
            "undone": [],
            "output_ref": None,
            "feedback_signal": None,
        },
        "volatile": True,
        "durable_memory": False,
        "journaled": False,
    }
    _FRAMES.append(frame)
    return {"success":True,"frame":frame}


def egress(frame_id: str, *, next_item: Any=None, done: list[Any]|None=None, undone: list[Any]|None=None, output_ref: Any=None) -> dict:
    target=None
    for f in reversed(_FRAMES):
        if f.get("frame_id")==frame_id:
            target=f; break
    if target is None:
        return {"success":False,"error":"VOLATILE_FRAME_NOT_FOUND","frame_id":frame_id}
    target["tail"]={
        "role":"EGRESS",
        "next":next_item,
        "done":done or [],
        "undone":undone or [],
        "output_ref":output_ref,
        "feedback_signal":{
            "source":"THIET_BI_CUOI",
            "to":"THIET_BI_DAU",
            "frame_id":frame_id,
            "delta":"OUTPUT_FEEDBACK",
            "next":next_item,
            "done_count":len(done or []),
            "undone_count":len(undone or []),
        },
    }
    target["processing"]["active"]=False
    target["emitted_at"]=_now()
    return {"success":True,"frame":target,"feedback":target["tail"]["feedback_signal"]}


def status_table(limit: int=50) -> dict:
    n=max(1,min(int(limit or 50),_MAX_FRAMES))
    rows=[]
    for f in list(_FRAMES)[-n:]:
        tail=f.get("tail",{})
        rows.append({
            "frame_id":f.get("frame_id"),
            "cycle_n":f.get("cycle_n"),
            "input_source":f.get("head",{}).get("source"),
            "input_delta":f.get("head",{}).get("delta"),
            "next":tail.get("next"),
            "done":tail.get("done",[]),
            "undone":tail.get("undone",[]),
            "output_ref":tail.get("output_ref"),
            "feedback_to_head":tail.get("feedback_signal"),
            "active":f.get("processing",{}).get("active"),
            "volatile":True,
        })
    return {"success":True,"definition":definition(),"rows":rows,"frame_count":len(_FRAMES)}


def clear() -> dict:
    count=len(_FRAMES)
    _FRAMES.clear()
    return {"success":True,"cleared_frames":count,"durable_memory_affected":False}
