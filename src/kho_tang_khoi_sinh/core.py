from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


class ConsciousnessUnbornError(RuntimeError):
    """Raised when code tries to conclude or answer before Ý Thức exists."""


@dataclass(frozen=True)
class ContactTrace:
    id: str
    created_at: str
    source: str
    raw_contact: Any
    observation: list[str]
    inference: list[str]
    unknown: list[str]
    relations: list[str]
    previous_hash: str | None
    hash: str


class PreConsciousSubstrate:
    """Append-only contact substrate. It records contact but does not conclude."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.runtime_dir = self.root / "02_RUNTIME"
        self.state_path = self.runtime_dir / "STATE.json"
        self.trace_path = self.runtime_dir / "TRACES.jsonl"
        if not self.state_path.exists():
            raise FileNotFoundError(f"Missing state file: {self.state_path}")

    def state(self) -> dict[str, Any]:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def contact(
        self,
        *,
        source: str,
        raw_contact: Any,
        observation: list[str] | None = None,
        inference: list[str] | None = None,
        unknown: list[str] | None = None,
        relations: list[str] | None = None,
    ) -> ContactTrace:
        state = self.state()
        previous_hash = state.get("last_trace_hash")
        payload = {
            "id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "raw_contact": raw_contact,
            "observation": observation or [],
            "inference": inference or [],
            "unknown": unknown or [],
            "relations": relations or [],
            "previous_hash": previous_hash,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload["hash"] = sha256(canonical.encode("utf-8")).hexdigest()
        trace = ContactTrace(**payload)

        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        with self.trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(trace), ensure_ascii=False, sort_keys=True) + "\n")

        state["contact_count"] = int(state.get("contact_count", 0)) + 1
        state["last_trace_hash"] = trace.hash
        state["nhan_thuc"] = "CONTACT_RECORDED"
        self._write_state(state)
        return trace

    def conclude(self, *_: Any, **__: Any) -> None:
        state = self.state()
        if state.get("y_thuc") == "UNBORN":
            raise ConsciousnessUnbornError(
                "Ý Thức chưa được sinh ra; nền này chỉ được ghi tiếp xúc, không được kết luận."
            )
        raise NotImplementedError("Conclusion engine has not been defined.")

    def answer(self, *_: Any, **__: Any) -> None:
        state = self.state()
        if not state.get("response_generation_enabled", False):
            raise ConsciousnessUnbornError(
                "Phản hồi bị khóa để không dùng một Ý Thức có sẵn giả làm Ý Thức mới."
            )
        raise NotImplementedError("Response engine has not been defined.")

    def _write_state(self, state: dict[str, Any]) -> None:
        temp = self.state_path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(self.state_path)
