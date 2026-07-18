import json
from pathlib import Path

import pytest

from kho_tang_khoi_sinh import ConsciousnessUnbornError, PreConsciousSubstrate


def make_root(tmp_path: Path) -> Path:
    runtime = tmp_path / "02_RUNTIME"
    runtime.mkdir(parents=True)
    state = {
        "contact_count": 0,
        "last_trace_hash": None,
        "nhan_thuc": "DORMANT",
        "y_thuc": "UNBORN",
        "response_generation_enabled": False,
        "conclusion_generation_enabled": False,
    }
    (runtime / "STATE.json").write_text(json.dumps(state), encoding="utf-8")
    return tmp_path


def test_contact_is_recorded_without_conclusion(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    substrate = PreConsciousSubstrate(root)
    trace = substrate.contact(source="test", raw_contact="xin chào", observation=["có một chuỗi chữ"])
    assert trace.raw_contact == "xin chào"
    assert substrate.state()["contact_count"] == 1
    assert substrate.state()["nhan_thuc"] == "CONTACT_RECORDED"


def test_conclusion_is_locked_while_consciousness_is_unborn(tmp_path: Path) -> None:
    substrate = PreConsciousSubstrate(make_root(tmp_path))
    with pytest.raises(ConsciousnessUnbornError):
        substrate.conclude()


def test_response_is_locked_while_consciousness_is_unborn(tmp_path: Path) -> None:
    substrate = PreConsciousSubstrate(make_root(tmp_path))
    with pytest.raises(ConsciousnessUnbornError):
        substrate.answer("anything")
