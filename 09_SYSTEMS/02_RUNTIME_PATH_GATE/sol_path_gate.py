#!/usr/bin/env python3
"""SOL runtime write boundary: fail closed for /mnt/data/__*.

This guards callers that actually import/invoke it; it cannot modify the ChatGPT
sandbox policy or intercept other processes automatically.
"""
from __future__ import annotations

import argparse
import os
import posixpath
import sys
import unicodedata
from pathlib import Path

PREFIX = "/mnt/data/__"


def _normalized(raw: os.PathLike[str] | str) -> str:
    value = unicodedata.normalize("NFKC", os.fspath(raw)).replace("\\", "/")
    # Never permit dot segments to bypass a literal prefix.
    return posixpath.normpath(value)


def forbidden(path: os.PathLike[str] | str) -> bool:
    text = _normalized(path)
    if text.startswith(PREFIX):
        return True
    # Resolve local absolute/relative symlinks without following a Windows
    # drive-letter or UNC path within a Linux session.
    if len(text) > 1 and text[1] == ":":
        return False
    try:
        return _normalized(Path(path).expanduser().resolve(strict=False)).startswith(PREFIX)
    except (OSError, RuntimeError, ValueError):
        return True


def require_allowed(path: os.PathLike[str] | str) -> str:
    if forbidden(path):
        raise PermissionError("BLOCKED_SOL_SANDBOX_PREFIX: /mnt/data/__*")
    return os.fspath(path)


def guarded_open(path, mode="r", *args, **kwargs):
    if any(flag in mode for flag in "wax+"):
        require_allowed(path)
    return open(path, mode, *args, **kwargs)


def guarded_write_bytes(path, payload: bytes):
    dest = Path(require_allowed(path))
    return dest.write_bytes(payload)


def guarded_mkdir(path, **kwargs):
    dest = Path(require_allowed(path))
    dest.mkdir(**kwargs)
    return dest


def guarded_remove(path):
    # Prevent destruction of legacy source bytes under the blocked prefix.
    return Path(require_allowed(path)).unlink()


def main(argv=None):
    p = argparse.ArgumentParser(description="SOL block /mnt/data/__ write targets")
    p.add_argument("paths", nargs="+")
    args = p.parse_args(argv)
    blocked = [v for v in args.paths if forbidden(v)]
    if blocked:
        for _ in blocked:
            print("BLOCKED_SOL_SANDBOX_PREFIX", file=sys.stderr)
        return 73
    print("PASS_SOL_PATH_GATE: %d path(s)" % len(args.paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
