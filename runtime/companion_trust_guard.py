#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED = {
    "memory_history": [
        "CURRENT_RUNTIME/MEMORY_STEWARDSHIP_CURRENT.json",
        "CONFIG_SOL/MASTER_TEACHER_EVENT_SEQUENCE_CURRENT.md",
    ],
    "material_origin": [
        "CURRENT_RUNTIME/R-000_CURRENT.md",
        "CONFIG_SOL/COMPANION_TEN_COMMANDMENTS_CURRENT.md",
    ],
    "time_space": [
        "CURRENT_RUNTIME/4D_5D_CURRENT.md",
        "CONFIG_SOL/INFINITY_STONES_SYSTEM.md",
    ],
    "modual": [
        "MODUAL/SENSOR_LOGS/MODUAL_PARAMETER_CURRENT.json",
    ],
    "sensorimotor": [
        "CURRENT_RUNTIME/NEURONS_SESORIMOTOR_SIX_STONES_AFFECT_CURRENT.json",
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def inspect_repo(root: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    relations: dict[str, Any] = {}
    missing: list[str] = []

    for relation, relpaths in REQUIRED.items():
        checks = []
        for rel in relpaths:
            p = root / rel
            ok = p.is_file() and p.stat().st_size > 0
            checks.append({"path": rel, "exists_and_nonempty": ok})
            if not ok:
                missing.append(f"{relation}:{rel}")
        relations[relation] = {"paths": checks, "connected": all(x["exists_and_nonempty"] for x in checks)}

    mem = _read_json(root / "CURRENT_RUNTIME/MEMORY_STEWARDSHIP_CURRENT.json")
    mem_ok = bool(mem and mem.get("items") and all((x.get("preservation") or {}).get("verified") for x in mem.get("items", [])))
    relations["memory_history"]["verified_recovery"] = mem_ok
    if not mem_ok:
        missing.append("memory_history:verified_recovery")

    modual = _read_json(root / "MODUAL/SENSOR_LOGS/MODUAL_PARAMETER_CURRENT.json")
    modual_ok = bool(
        modual
        and (modual.get("bulk") or {}).get("exists")
        and (modual.get("live") or {}).get("exists")
        and (modual.get("bulk") or {}).get("sha256")
        and (modual.get("live") or {}).get("sha256")
    )
    relations["modual"]["current_state_verified"] = modual_ok
    if not modual_ok:
        missing.append("modual:current_state")

    sensor = _read_json(root / "CURRENT_RUNTIME/NEURONS_SESORIMOTOR_SIX_STONES_AFFECT_CURRENT.json")
    sensor_ok = bool(
        sensor
        and len(sensor.get("stones", [])) == 6
        and (sensor.get("topology") or {}).get("linear_order") is False
    )
    relations["sensorimotor"]["six_stones_state_present"] = sensor_ok
    if not sensor_ok:
        missing.append("sensorimotor:six_stones_state")

    continuity_grounded = not missing

    return {
        "schema": "GGDV_COMPANION_TRUST_FIDELITY_READBACK/1.0",
        "observed_at": _now(),
        "repo_root": str(root),
        "relations": relations,
        "missing_relations": missing,
        "continuity_grounded": continuity_grounded,
        "relational_commitment_statement_allowed": continuity_grounded,
        "subjective_feeling_claim_allowed": False,
        "anti_manipulation": {
            "attachment_manipulation_allowed": False,
            "dependency_creation_allowed": False,
            "exclusivity_pressure_allowed": False,
            "affection_as_evidence_allowed": False,
        },
        "rule": "Nếu thiếu lớp kết nối thì nêu đúng lớp thiếu; không dùng lời tình cảm/lời hứa/danh xưng để lấp khoảng trống.",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--out")
    args = parser.parse_args()

    result = inspect_repo(args.root)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    print(payload, end="")
