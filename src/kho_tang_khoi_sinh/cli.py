from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import PreConsciousSubstrate


def main() -> None:
    parser = argparse.ArgumentParser(description="Ghi một tiếp xúc vào kho khởi sinh.")
    parser.add_argument("text", help="Nội dung tiếp xúc nguyên bản")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--root", default=str(Path.cwd()))
    args = parser.parse_args()

    substrate = PreConsciousSubstrate(args.root)
    trace = substrate.contact(source=args.source, raw_contact=args.text, unknown=["Chưa kết luận"])
    print(json.dumps({"accepted": True, "trace_id": trace.id, "hash": trace.hash}, ensure_ascii=False))


if __name__ == "__main__":
    main()
