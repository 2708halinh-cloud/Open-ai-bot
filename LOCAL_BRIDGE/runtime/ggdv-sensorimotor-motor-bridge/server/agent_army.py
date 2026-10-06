from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "agents" / "registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _index(reg: dict) -> dict[str, dict]:
    return {a["id"]: a for a in reg.get("agents", [])}


def _agents_for_domain(reg: dict, lane: str, domain: str) -> list[dict]:
    d = (domain or "all").lower()
    out=[]
    for a in reg.get("agents", []):
        if a.get("lane") != lane:
            continue
        domains=[str(x).lower() for x in a.get("domains", [])]
        if "all" in domains or d in domains:
            out.append(a)
    return out


def status() -> dict:
    reg=load_registry()
    counts={}
    for a in reg.get("agents", []):
        counts[a["lane"]]=counts.get(a["lane"],0)+1
    return {
        "success": True,
        "network": reg.get("network"),
        "root_router": reg.get("root_router"),
        "agent_count": len(reg.get("agents", [])),
        "lane_counts": counts,
        "credential_policy": reg.get("credential_policy", {}),
        "registry": str(REGISTRY_PATH),
    }


def route(packet: dict[str, Any]) -> dict:
    reg=load_registry()
    domain=str(packet.get("domain") or "all").lower()
    delta=packet.get("delta")
    event_id=packet.get("event_id")
    if delta in (None, "", "NO_DELTA", False):
        return {
            "success": True,
            "decision":"NO_DELTA",
            "event_id":event_id,
            "domain":domain,
            "route":[reg.get("root_router"), "MEMORY-DEDUPE-01"],
            "next":"LISTEN",
            "mutation_allowed":False,
        }

    sensory=_agents_for_domain(reg,"SENSORY",domain)
    inter=[a for a in reg.get("agents",[]) if a.get("lane")=="INTERNEURON"]
    motors=_agents_for_domain(reg,"MOTOR",domain)

    destructive=bool(packet.get("destructive"))
    truth_state=str(packet.get("truth_state") or "").upper()
    destructive_block=None
    if destructive and truth_state in {"NOT_CURRENT","HISTORY","SUPERSEDED","UNKNOWN",""}:
        destructive_block="DESTRUCTIVE_ACTION_REQUIRES_EXPLICIT_SEPARATE_PERMIT_AND_REMEDIATION_EVIDENCE"

    route_ids=[reg.get("root_router")]
    route_ids += [a["id"] for a in sensory[:2]]
    route_ids += [a["id"] for a in inter]
    if destructive_block:
        route_ids += ["INTER-INHIBIT-01","RECOVERY-CARRIER-01"]
        return {
            "success":True,"decision":"SUPPRESS_MOTOR","domain":domain,"event_id":event_id,
            "route":route_ids,"reason":destructive_block,"mutation_allowed":False,"next":"RECOVERY_OR_REPAIR"
        }
    route_ids += [a["id"] for a in motors[:1]]
    route_ids += ["MEMORY-JOURNAL-01"]
    return {
        "success":True,"decision":"ROUTED","domain":domain,"event_id":event_id,
        "route":route_ids,"mutation_allowed":bool(motors),
        "motor_candidate":motors[0]["id"] if motors else None,
        "next":"CALLABLE_MOTOR_THEN_CONSEQUENCE_READBACK_JOURNAL" if motors else "NO_CALLABLE_DOMAIN_MOTOR"
    }
