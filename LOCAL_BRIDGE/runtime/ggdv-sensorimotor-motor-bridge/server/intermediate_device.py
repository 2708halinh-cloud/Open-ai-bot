from __future__ import annotations
from collections import deque
from datetime import datetime, timezone
import hashlib, json
from typing import Any

_MAX_TRANSITIONS = 256
_TRANSITIONS: deque[dict[str, Any]] = deque(maxlen=_MAX_TRANSITIONS)
_LAST_BY_CARRIER: dict[str, str] = {}

DEFINITION = {
    "success": True,
    "id": "INTERMEDIATE-TRANSFORM-01",
    "device_class": "THIET_BI_TRUNG_GIAN",
    "class": "TRANSFORMABLE_OPERATIONAL_CARRIER",
    "role": "CARRIER_BETWEEN_HEAD_AND_END",
    "project_semantics": "BAO_TOAN_NANG_LUONG_QUA_CHUYEN_HOA",
    "meaning": "Preserve causal/provenance continuity while state/data/config/instructions may transform; do not freeze bytes or truth-state.",
    "is_ram": False,
    "is_memory_by_default": False,
    "is_journal_by_default": False,
    "is_immutable": False,
    "is_eternally_current": False,
    "may_be_persistent_carrier": True,
    "examples": ["IOAT/IOTA", "IOTA", ".env", "CONFIG/*", "config", "instruction", "pointer", "route registry", "adapter/runtime configuration"],
    "route": "STATE_N -> FRESH_READ -> DELTA -> VALIDATE -> TRANSFORM/RECONFIGURE -> CONSEQUENCE -> READBACK -> STATE_N+1",
    "freshness_rule": "VALID_AT_STATE_N does not imply VALID_AT_STATE_N_PLUS_1; fresh-read authoritative carrier before use when stale or changed.",
    "currentness_rule": "CONFIG_AT_T may be correct/callable at T_n without becoming eternal truth at T_n+1.",
    "energy_conservation_semantic": "Preserve traceable work/state/information across transformation via provenance + input + transform + consequence + readback.",
    "physical_energy_boundary": "Physical-energy claims require explicit system boundary, source, carrier, transfer/transformation and measured evidence."
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def _digest(v: Any) -> str:
    return hashlib.sha256(_canonical(v).encode("utf-8", errors="replace")).hexdigest()


def definition() -> dict:
    return dict(DEFINITION)


def observe(carrier_ref: str, carrier_kind: str, state: Any, revision: str|None=None, observed_at: str|None=None) -> dict:
    if not carrier_ref:
        return {"success":False,"error":"CARRIER_REF_REQUIRED"}
    snap={"carrier_ref":carrier_ref,"carrier_kind":carrier_kind or "UNKNOWN","revision":revision,"state":state}
    h=_digest(snap); prev=_LAST_BY_CARRIER.get(carrier_ref)
    delta="NO_DELTA" if prev==h else "DELTA"
    _LAST_BY_CARRIER[carrier_ref]=h
    return {"success":True,"carrier_ref":carrier_ref,"carrier_kind":carrier_kind or "UNKNOWN","revision":revision,"observed_at":observed_at or _now(),"snapshot_hash":h,"delta":delta,"freshness":"FRESH_OBSERVATION","eternal_validity":False,"memory_semantics":False}


def transform(*, carrier_ref: str, carrier_kind: str, input_state: Any, output_state: Any, rule_ref: str|None=None, input_revision: str|None=None, output_revision: str|None=None) -> dict:
    if not carrier_ref:
        return {"success":False,"error":"CARRIER_REF_REQUIRED"}
    input_hash=_digest(input_state); output_hash=_digest(output_state)
    changed=input_hash!=output_hash or input_revision!=output_revision
    receipt={"transition_id":_digest({"carrier_ref":carrier_ref,"input":input_hash,"output":output_hash,"rule_ref":rule_ref,"ts":_now()})[:24],"carrier_ref":carrier_ref,"carrier_kind":carrier_kind or "UNKNOWN","rule_ref":rule_ref,"input_revision":input_revision,"output_revision":output_revision,"input_hash":input_hash,"output_hash":output_hash,"delta":"DELTA" if changed else "NO_DELTA","observed_at":_now(),"conservation":{"mode":"CAUSAL_PROVENANCE_CONTINUITY","input_ref_preserved":True,"output_ref_preserved":True,"bytes_may_change":True,"state_may_change":True,"meaning_may_require_revalidation":True},"eternal_validity":False,"is_memory":False,"is_journal":False}
    _TRANSITIONS.append(receipt)
    _LAST_BY_CARRIER[carrier_ref]=_digest({"carrier_ref":carrier_ref,"carrier_kind":carrier_kind,"revision":output_revision,"state":output_state})
    return {"success":True,"receipt":receipt,"next":"FRESH_READ_ON_NEXT_USE_OR_TRIGGER"}


def transition(*, carrier_type: str, state_n: Any, delta: Any, transform: Any, state_n_plus_1: Any, readback: Any, provenance: Any=None, physical_energy_claim: bool=False, measurement_evidence: Any=None) -> dict:
    required={"carrier_type":carrier_type,"state_n":state_n,"delta":delta,"transform":transform,"state_n_plus_1":state_n_plus_1,"readback":readback}
    missing=[k for k,v in required.items() if v is None or v==""]
    if missing: return {"success":False,"error":"MISSING_TRANSITION_FIELDS","missing":missing}
    if physical_energy_claim and not measurement_evidence:
        return {"success":False,"error":"PHYSICAL_ENERGY_EVIDENCE_REQUIRED","rule":DEFINITION["physical_energy_boundary"]}
    carrier_ref=f"legacy:{carrier_type}"
    out=globals()["transform"](carrier_ref=carrier_ref,carrier_kind=carrier_type,input_state=state_n,output_state=state_n_plus_1,rule_ref=_digest({"delta":delta,"transform":transform,"provenance":provenance})[:24])
    if out.get("success"):
        out["receipt"]["readback_hash"]=_digest(readback)
        out["receipt"]["physical_energy_claim"]=bool(physical_energy_claim)
        out["receipt"]["physical_energy_evidence_present"]=bool(measurement_evidence)
    return out


def status(limit: int=50) -> dict:
    n=max(1,min(int(limit or 50),_MAX_TRANSITIONS))
    return {"success":True,"definition":definition(),"transitions":list(_TRANSITIONS)[-n:],"count":len(_TRANSITIONS),"volatile_observation_cache":True}
