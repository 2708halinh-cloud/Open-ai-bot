#!/usr/bin/env python3
"""TESSERACT_OS continuity guard.

Persistent continuation is modeled as an unbounded sequence of bounded cycles.
It is NOT a scheduler and NOT a busy-spin loop.

Core invariant:
SOURCE_DIRECT -> DURABLE_CHECKPOINT -> RESTORE_UNFINISHED_EDGES
-> ROUTE_NEXT_CALLABLE_EDGE -> ACTION -> CONSEQUENCE -> READBACK
-> CHECKPOINT_DELTA -> NEXT_EDGE.

OPEN is ingress/unfinished relation data, never an automatic STOP signal.
A visible report/status must not replace a callable self-owned action.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Callable, Iterable
import json
import os
import tempfile


@dataclass
class Edge:
    edge_id: str
    target: str
    callable_now: bool = False
    user_input_required: bool = False
    candidate_carriers: list[str] = field(default_factory=list)
    exhausted_carriers: list[str] = field(default_factory=list)
    required: bool = True
    action_kind: str | None = None
    provider_receipt: Any = None
    observable_consequence: Any = None
    readback: Any = None
    done: bool = False
    evidence: dict[str, Any] = field(default_factory=dict)

    def self_owned_callable(self) -> bool:
        return bool(self.callable_now and not self.user_input_required and not self.done)

    def grounded_done(self) -> bool:
        return bool(
            self.done
            and self.action_kind
            and self.provider_receipt is not None
            and self.observable_consequence is not None
        )

    def next_carrier(self) -> str | None:
        for carrier in self.candidate_carriers:
            if carrier not in self.exhausted_carriers:
                return carrier
        return None


@dataclass
class Checkpoint:
    objective_id: str
    source_marker: str
    lineage_ref: str
    last_consequence_ref: str | None = None
    edges: list[Edge] = field(default_factory=list)
    state_n: int = 0
    cycle_count: int = 0

    def unfinished_edges(self) -> list[Edge]:
        return [e for e in self.edges if not e.grounded_done()]

    def callable_edges(self) -> list[Edge]:
        return [e for e in self.edges if e.self_owned_callable()]

    def user_dependencies(self) -> list[Edge]:
        return [e for e in self.edges if e.user_input_required and not e.grounded_done()]

    def objective_done(self) -> bool:
        required = [e for e in self.edges if e.required]
        return bool(required) and all(e.grounded_done() for e in required)


def to_dict(cp: Checkpoint) -> dict[str, Any]:
    return {
        "objective_id": cp.objective_id,
        "source_marker": cp.source_marker,
        "lineage_ref": cp.lineage_ref,
        "last_consequence_ref": cp.last_consequence_ref,
        "state_n": cp.state_n,
        "cycle_count": cp.cycle_count,
        "edges": [asdict(e) for e in cp.edges],
    }


def from_dict(data: dict[str, Any]) -> Checkpoint:
    return Checkpoint(
        objective_id=data["objective_id"],
        source_marker=data["source_marker"],
        lineage_ref=data["lineage_ref"],
        last_consequence_ref=data.get("last_consequence_ref"),
        state_n=int(data.get("state_n", 0)),
        cycle_count=int(data.get("cycle_count", 0)),
        edges=[Edge(**e) for e in data.get("edges", [])],
    )


def save_checkpoint(path: str | os.PathLike[str], cp: Checkpoint) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(to_dict(cp), ensure_ascii=False, indent=2) + "\n"
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


def load_checkpoint(path: str | os.PathLike[str]) -> Checkpoint | None:
    p = Path(path)
    if not p.exists():
        return None
    return from_dict(json.loads(p.read_text(encoding="utf-8")))


def select_next_callable_edge(cp: Checkpoint) -> Edge | None:
    """Select the next self-owned callable edge; do not hand it to the user."""
    for edge in cp.edges:
        if edge.self_owned_callable() and edge.next_carrier() is not None:
            return edge
    for edge in cp.edges:
        if edge.self_owned_callable() and not edge.candidate_carriers:
            return edge
    return None


def user_token(cp: Checkpoint) -> str | None:
    """Return one concrete user-dependency token without granting STOP to other edges."""
    for edge in cp.user_dependencies():
        return f"NEXT_HA_LINH:{edge.edge_id}:{edge.target}"
    return None


def visible_output_allowed(cp: Checkpoint, *, output_kind: str) -> bool:
    """Status/report/progress cannot substitute for unfinished callable action."""
    if output_kind.upper() in {"REPORT", "STATUS", "PROGRESS", "COMPLETION"}:
        return select_next_callable_edge(cp) is None
    if output_kind.upper() == "USER_DEPENDENCY_TOKEN":
        return user_token(cp) is not None
    return True


def stop_allowed(cp: Checkpoint) -> bool:
    """STOP only when objective is grounded-done or no self-owned action remains and user input is required."""
    if cp.objective_done():
        return True
    if select_next_callable_edge(cp) is not None:
        return False
    return bool(cp.user_dependencies())


def mark_carrier_failure(edge: Edge, carrier: str, evidence: Any) -> None:
    if carrier not in edge.exhausted_carriers:
        edge.exhausted_carriers.append(carrier)
    edge.evidence.setdefault("carrier_failures", []).append({
        "carrier": carrier,
        "evidence": evidence,
    })
    edge.callable_now = edge.next_carrier() is not None


def apply_action_result(
    cp: Checkpoint,
    edge_id: str,
    *,
    action_kind: str,
    provider_receipt: Any,
    observable_consequence: Any,
    readback: Any = None,
    last_consequence_ref: str | None = None,
) -> None:
    edge = next(e for e in cp.edges if e.edge_id == edge_id)
    edge.action_kind = action_kind
    edge.provider_receipt = provider_receipt
    edge.observable_consequence = observable_consequence
    edge.readback = readback
    edge.done = True
    edge.callable_now = False
    cp.state_n += 1
    cp.cycle_count += 1
    if last_consequence_ref is not None:
        cp.last_consequence_ref = last_consequence_ref


def continue_bounded(
    cp: Checkpoint,
    executor: Callable[[Edge, str | None], dict[str, Any]],
    *,
    max_steps: int = 32,
) -> dict[str, Any]:
    """Execute callable edges inside this runtime slice.

    The function never claims infinite background execution. If work remains after
    max_steps, the durable checkpoint stays OPEN for immediate/re-entry continuation.
    """
    steps = 0
    receipts: list[dict[str, Any]] = []
    while steps < max_steps:
        edge = select_next_callable_edge(cp)
        if edge is None:
            break
        carrier = edge.next_carrier()
        result = executor(edge, carrier)
        receipts.append(result)
        steps += 1

        if not result.get("success"):
            if carrier is not None:
                mark_carrier_failure(edge, carrier, result)
            else:
                edge.callable_now = False
            continue

        consequence = result.get("observable_consequence")
        provider_receipt = result.get("provider_receipt")
        if provider_receipt is None or consequence is None:
            # Boolean success/report-only is not grounded completion.
            edge.evidence.setdefault("rejected_results", []).append(result)
            if carrier is not None:
                mark_carrier_failure(edge, carrier, "missing receipt/consequence")
            else:
                edge.callable_now = False
            continue

        apply_action_result(
            cp,
            edge.edge_id,
            action_kind=result.get("action_kind") or "ACTION",
            provider_receipt=provider_receipt,
            observable_consequence=consequence,
            readback=result.get("readback"),
            last_consequence_ref=result.get("last_consequence_ref"),
        )

    return {
        "objective_id": cp.objective_id,
        "steps": steps,
        "objective_done": cp.objective_done(),
        "open": not cp.objective_done(),
        "next_callable_edge": (
            select_next_callable_edge(cp).edge_id
            if select_next_callable_edge(cp) is not None else None
        ),
        "user_token": user_token(cp),
        "stop_allowed": stop_allowed(cp),
        "receipts": receipts,
        "checkpoint": to_dict(cp),
    }


__all__ = [
    "Edge", "Checkpoint", "save_checkpoint", "load_checkpoint",
    "select_next_callable_edge", "user_token", "visible_output_allowed",
    "stop_allowed", "mark_carrier_failure", "apply_action_result",
    "continue_bounded",
]
