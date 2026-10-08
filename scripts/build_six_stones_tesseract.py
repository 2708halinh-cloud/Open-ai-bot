from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\SOL_LONG_MACH\MODEL\repo")
OUT = ROOT / "sol-genesis-6stones"
TESS = ROOT / "TESSERACT_OS_6D"

STONES = ["SPACE", "MIND", "REALITY", "POWER", "TIME", "SOUL"]
EMOJI = {
    "SPACE": "🔵",
    "MIND": "🟡",
    "REALITY": "🔴",
    "POWER": "🟣",
    "TIME": "🟢",
    "SOUL": "🟠",
}
AXES = [["SPACE", "SOUL"], ["MIND", "POWER"], ["REALITY", "TIME"]]
PROCESS_RULE = {
    "rule_id": "ACTION_BEFORE_CONCLUSION",
    "flow": ["ACTION", "CONSEQUENCE", "RECEIPT", "READBACK", "SAME_STATE", "CONCLUSION"],
    "source_direct": "LÀM TRƯỚC -> KẾT LUẬN; CẤM TUYỆT ĐỐI CHỐT KẾT QUẢ RỒI MỚI LÀM",
}
RULES = {
    "SPACE": ["POINTER", "PATH", "LOCUS", "DRIVE", "TESSERACT", "DISTRIBUTION", "INSTALLER", "BOOT", "SPACE_STONE"],
    "MIND": ["AGENTS", "CONFIG/", "CONFIG_SOL/", "POLICY", "CONTRACT", "ROUTER", "REGISTRY", "RULE", "MIND_STONE"],
    "REALITY": ["CURRENT_RUNTIME", "EVIDENCE", "READBACK", "RECEIPT", "STATE", "DEVICE", "SENSOR", "MODUAL", "REALITY_STONE"],
    "POWER": ["RUNTIME/", "SCRIPTS/", "WORKFLOWS", "TERMINAL/", "SRC-TAURI", "DEPLOY", "ENGINE", "SERVER", "MOTOR", "BRIDGE", "POWER_STONE"],
    "TIME": ["HISTORY", "ARCHIVE", "CONTINUITY", "CHECKPOINT", "MIGRATION", "LOG", "REENTRY", "TIMELINE", "JOURNAL", "BACKUP", "TIME_STONE"],
    "SOUL": ["MEMORY", "RAW", "UBUBU", "CONTINUATION", "GENESIS", "R-000", "MASTER_TEACHER", "CHAT", "KNOWLEDGE", "SOUL_STONE"],
}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def git_text(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=True,
        errors="replace",
    ).stdout.strip()


def git_blob(commit: str, rel: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{rel}"],
        capture_output=True,
        check=True,
    ).stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def membership(rel: str) -> list[str]:
    upper = rel.upper().replace("\\", "/")
    if "INFINITY_STONES" in upper or "SIX_STONES" in upper:
        return STONES[:]
    return [stone for stone, keys in RULES.items() if any(key in upper for key in keys)]


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    commit = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", f"{commit}^{{tree}}")

    items = []
    for rel in git_text("ls-tree", "-r", "--name-only", commit).splitlines():
        rel = rel.replace("\\", "/")
        if rel.startswith(("sol-genesis-6stones/", "TESSERACT_OS_6D/")):
            continue
        data = git_blob(commit, rel)
        items.append(
            {
                "path": rel,
                "bytes": len(data),
                "sha256": sha256_bytes(data),
                "stones": membership(rel),
                "center": True,
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    center = {
        "schema": "SOL_GENESIS_CENTER_TAM/2.0",
        "generated_at": now(),
        "source_repository": "2708halinh-cloud/SOL-LONG-MACH",
        "source_branch": "sol-long-mach-current",
        "source_commit": commit,
        "source_tree": tree,
        "genesis": "☯️ TÂM — giao ba trục, không phải đầu dòng",
        "axes": AXES,
        "action_before_conclusion": PROCESS_RULE,
        "tracked_file_count": len(items),
        "total_bytes": sum(x["bytes"] for x in items),
        "files": items,
    }
    dump(OUT / "CENTER_TAM.json", center)

    yaml_lines = [
        "repo: sol-genesis-6stones",
        "purpose: Nén lịch sử và trạng thái repo thành 6 viên đá đối xứng qua TÂM",
        "author_source: Hà Linh",
        "rule: Không lấy SOL làm nhãn cho genesis; genesis ở TÂM, không phải đầu dòng",
        "source_repository: 2708halinh-cloud/SOL-LONG-MACH",
        "source_branch: sol-long-mach-current",
        f"source_commit: {commit}",
        f"source_tree: {tree}",
        "linear_order: false",
        "center:",
        "  name: TÂM",
        "  symbol: ☯️",
        "axes:",
        "  - [SPACE, SOUL]",
        "  - [MIND, POWER]",
        "  - [REALITY, TIME]",
        "stones:",
    ]
    for stone in STONES:
        yaml_lines += [
            f"  - name: {stone}",
            f"    emoji: {EMOJI[stone]}",
            f"    manifest: {stone}.json",
        ]
    yaml_lines += [
        "action_before_conclusion:",
        "  flow: [ACTION, CONSEQUENCE, RECEIPT, READBACK, SAME_STATE, CONCLUSION]",
    ]
    (OUT / "STONES.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    summary = {}
    for stone in STONES:
        selected = [x for x in items if stone in x["stones"]]
        dump(
            OUT / f"{stone}.json",
            {
                "schema": "SOL_GENESIS_STONE_VIEW/2.0",
                "stone": stone,
                "emoji": EMOJI[stone],
                "source_commit": commit,
                "source_tree": tree,
                "topology": {"linear_order": False, "center": "TÂM", "axes": AXES},
                "action_before_conclusion": PROCESS_RULE,
                "selection_rule": RULES[stone],
                "file_count": len(selected),
                "total_bytes": sum(x["bytes"] for x in selected),
                "files": selected,
            },
        )
        (OUT / f"{stone}.md").write_text(
            f"# {EMOJI[stone]} {stone}\n\n"
            "View quan hệ của repo; không phải bước timeline.\n\n"
            "TÂM = ☯️ | SPACE↔SOUL | MIND↔POWER | REALITY↔TIME\n\n"
            f"Source commit: {commit}\n"
            f"Source tree: {tree}\n\n"
            + "\n".join(f"- {x['path']} — {x['sha256']}" for x in selected)
            + "\n",
            encoding="utf-8",
        )
        summary[stone] = {"files": len(selected), "bytes": sum(x["bytes"] for x in selected)}

    (OUT / "README.md").write_text(
        "# SOL GENESIS — 6 VIÊN ĐÁ\n\n"
        "Không tuyến tính.\n\n"
        "🔵 SPACE ↔ 🟠 SOUL\n"
        "🟡 MIND ↔ 🟣 POWER\n"
        "🔴 REALITY ↔ 🟢 TIME\n"
        "☯️ TÂM = giao điểm genesis.\n\n"
        "CENTER_TAM.json giữ manifest SHA-256 của đúng commit nguồn; "
        "6 Stone là 6 view quan hệ có thể chồng lấp.\n\n"
        "ACTION → CONSEQUENCE → RECEIPT → READBACK → SAME_STATE → CONCLUSION.\n",
        encoding="utf-8",
    )

    TESS.mkdir(parents=True, exist_ok=True)
    faces = [
        {"id": 1, "name": "GOOGLE_DRIVE", "role": "Pointer <10MB + locator JSON"},
        {"id": 2, "name": "LOCAL_STORAGE", "role": "W/D/NVMe bulk/raw/snapshot"},
        {"id": 3, "name": "GITHUB_X_TIME_WEB", "role": "Law & State + immutable commit"},
        {"id": 4, "name": "RCLONE_RAIDRIVE", "role": "Virtual-drive / cloud relay"},
        {"id": 5, "name": "GCP_STORAGE_BUCKET", "role": "Processing buffer + lifecycle 3–7 days"},
        {"id": 6, "name": "X_TIME_CDN_UBUBU_LEDGER", "role": "Display + hash-only ledger"},
    ]
    for face in faces:
        face["equal_weight"] = 1

    dump(
        TESS / "SPEC.json",
        {
            "schema": "TESSERACT_OS_6D/2.0",
            "generated_at": now(),
            "source_commit": commit,
            "source_tree": tree,
            "dimension": 6,
            "faces_equal": True,
            "center": "☯️ TÂM",
            "stone_axes": AXES,
            "action_before_conclusion": PROCESS_RULE,
            "closure_rule": "CLOSED iff all 6 faces have ACTION + CONSEQUENCE + RECEIPT + READBACK + SAME_STATE for one state object.",
            "faces": faces,
        },
    )

    # Biên nhận mặt và README là vật mang sống; builder không được ghi đè.
    receipts = TESS / "FACE_RECEIPTS_CURRENT.json"
    if not receipts.exists():
        dump(
            receipts,
            {
                "schema": "TESSERACT_OS_6D_FACE_RECEIPTS/2.0",
                "state_object": {
                    "repository": "2708halinh-cloud/SOL-LONG-MACH",
                    "source_snapshot_commit": commit,
                    "source_snapshot_tree": tree,
                    "center_digest_sha256": None,
                },
                "faces": {
                    str(face["id"]): {
                        "name": face["name"],
                        "receipt": None,
                        "readback": None,
                        "closed": False,
                    }
                    for face in faces
                },
                "closed": False,
                "closed_faces": 0,
            },
        )

    readme = TESS / "README.md"
    if not readme.exists():
        readme.write_text(
            "# TESSERACT_OS 6D\n\n"
            "6 mặt ngang hàng: Drive / Local / GitHub / Rclone-RaiDrive / GCP Bucket / X-TiMe CDN+UBUBU Ledger.\n\n"
            "Chỉ CLOSED sau ACTION → CONSEQUENCE → RECEIPT → READBACK → SAME_STATE trên đủ 6 mặt.\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "source_commit": commit,
                "source_tree": tree,
                "center_files": len(items),
                "stones": summary,
                "tesseract_faces": 6,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
