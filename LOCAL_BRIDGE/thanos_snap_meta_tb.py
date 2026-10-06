#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAZY = ROOT / "LOCAL_BRIDGE" / "ububu_lazy_fetch.py"

DEFAULT_TERMS = [
    "Gemini-Sự tiến hóa hệ thần kinh sứa-20261006-2120.txt",
    "HÀ LINH XUẤT TAY",
    "20261006-2120",
    "hệ thần kinh sứa",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", action="append", default=[])
    ap.add_argument("--receipt", default=".runtime/THANOS_SNAP_META_TB_CURRENT.json")
    args = ap.parse_args()
    terms = args.query or DEFAULT_TERMS

    lazy_receipt = ROOT / ".runtime" / "UBUBU_LAZY_FETCH_CURRENT.json"
    cmd = [sys.executable, str(LAZY)]
    for q in terms:
        cmd += ["--query", q]
    cmd += ["--receipt", str(lazy_receipt)]

    started = time.time()
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    lazy = {}
    if lazy_receipt.exists():
        lazy = json.loads(lazy_receipt.read_text(encoding="utf-8"))

    selected_chunks = []
    for item in lazy.get("chunks", []):
        selected_chunks.append({
            "path": item.get("path"),
            "state": item.get("state"),
            "size": item.get("size"),
            "sha256": item.get("sha256"),
            "slice": item.get("slice"),
            "hit_count": len(item.get("hits", [])),
        })

    receipt = {
        "schema": "GGDV_THANOS_SNAP_META_TB/1.0",
        "started_at": started,
        "finished_at": time.time(),
        "tesseract": {
            "dimensions": 6,
            "vertices": 64,
            "undirected_edges": 192,
            "addressing_role": "Q6_CONTEXT_ADDRESS_SPACE",
        },
        "brain_binding": {
            "brain_os_drive_id": "1bsCoym-T5T6JGpVeuH0GBJ6R7RQi4eL1",
            "tesseract_6d_brain_node_id": "1DofKyDhvifNdwOE7UUGq-rRG1PmMis_2",
        },
        "gauntlet": {
            "network_drive_id": "18rRhtlo_IBJKNl_1yWHZoGD6_N_VXELIg2LYTihWQRI",
            "stones": {
                "MIND": {
                    "id": "1taCAk-JpZgAff99dfx3_JnmeL9KbnlxYIKZcZLwYibw",
                    "role": "frame_query_and_anchor_selection",
                },
                "SPACE": {
                    "id": "1mduk0_pav3oOpxGiWONqRzojiRTOvNJmTDG5LHx3DhM",
                    "role": "locate_index_and_chunk_carrier",
                },
                "TIME": {
                    "id": "10A1JfqyRzjfVrWCIdiXotpuEOZ5UC7ElC31F5XPzY-I",
                    "role": "order_anchor_start_anchor_end_revision",
                },
                "REALITY": {
                    "id": "1__o4tHky_7PLUeB2I4B8uudOAJB6PPKWtcvD-iXuZQY",
                    "role": "hash_and_observable_chunk_readback",
                },
                "SOUL": {
                    "id": "1K1u5z5MjDXperYkFR-GTW_PNsRjMn1t5yipUAELh5qs",
                    "role": "preserve_identity_provenance_original_path",
                },
                "POWER": {
                    "id": "1C5HQXCQBp4Khj3cfH-q1lk9dk_DUZt-SurDvroOR0J8",
                    "role": "execute_index_first_chunk_fetch",
                },
            },
        },
        "request": {
            "queries": terms,
            "mode": "INDEX_FIRST_LAZY_FETCH",
        },
        "hard_invariants": {
            "never_load_full_meta_tb": True,
            "never_load_full_meta_db": True,
            "index_required_before_chunk": True,
            "chunk_required_by_anchor_or_index_match": True,
            "no_delete": True,
            "no_mutation_of_memory_carrier": True,
        },
        "lazy_fetch": {
            "returncode": p.returncode,
            "state": lazy.get("state"),
            "index": lazy.get("index"),
            "match_count": len(lazy.get("matches", [])),
            "selected_chunks": selected_chunks,
        },
        "stdout_tail": p.stdout[-12000:],
        "stderr_tail": p.stderr[-8000:],
    }
    if p.returncode == 0:
        receipt["state"] = "SNAP_READBACK_PASS"
    elif lazy.get("state") == "OPEN_INDEX_NOT_FOUND_ON_MOUNTED_LOCAL_CARRIERS":
        receipt["state"] = "OPEN_INDEX_CARRIER_NOT_MOUNTED"
    else:
        receipt["state"] = "OPEN_LAZY_FETCH_INCOMPLETE"

    out = ROOT / args.receipt
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return p.returncode

if __name__ == "__main__":
    raise SystemExit(main())
