from __future__ import annotations
import hashlib, json, os, platform, shutil, subprocess, time, shlex, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("GGDV_SENSORIMOTOR_STATE_DIR") or (Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GGDV" / "sensorimotor-motor"))
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "state.json"
JOURNAL_FILE = STATE_DIR / "journal.jsonl"
WATCHER_PID_FILE = STATE_DIR / "watcher.pid"
WATCHER_CONFIG_FILE = STATE_DIR / "watcher-config.json"

READ_PREFIXES = (
    "getprop", "dumpsys", "cmd package list", "pm list", "settings get",
    "cat /proc", "cat /sys", "ls", "df", "mount", "ip ", "service list",
    "lshal", "logcat -d", "uname", "id", "which"
)

# Destructive actions require a separate, exact-command, one-use permit.
# MOTOR_ENABLE alone is intentionally insufficient.
DESTRUCTIVE_PATTERNS = (
    r"(?i)(^|[;&|\s])(rm\s+(-[^\s]*[rf][^\s]*\s+|--recursive\s+|--force\s+))",
    r"(?i)\b(remove-item|del|erase|rmdir|rd)\b",
    r"(?i)\b(format(\.com)?|diskpart|clear-disk|remove-partition|remove-volume)\b",
    r"(?i)\bgit\s+(clean\s+-[^\n]*[fdx]|reset\s+--hard)\b",
    r"(?i)\b(shred|sdelete|cipher\s+/w)\b",
)

def destructive_enabled() -> bool:
    return os.environ.get("GGDV_DESTRUCTIVE_ENABLE", "0").strip().lower() in {"1", "true", "yes", "on"}

def destructive_reason(command: str) -> str | None:
    c = command or ""
    for pat in DESTRUCTIVE_PATTERNS:
        if re.search(pat, c):
            return pat
    return None

def _permit_store(state: dict) -> dict:
    permits = state.get("destructive_permits")
    if not isinstance(permits, dict):
        permits = {}
        state["destructive_permits"] = permits
    return permits

def destructive_preflight(*, command: str, target: str, target_snapshot: dict, repair_attempted: bool, repair_result: str, truth_basis: str, explicit_target_confirmation: str, not_current_only: bool=False):
    if not motor_enabled():
        return {"success": False, "error": "MOTOR_DISABLED"}
    if not destructive_enabled():
        return {"success": False, "error": "DESTRUCTIVE_MOTOR_DISABLED", "remediation": "Set GGDV_DESTRUCTIVE_ENABLE=1 only for an explicitly authorized irreversible operation."}
    reason = destructive_reason(command)
    if not reason:
        return {"success": False, "error": "COMMAND_NOT_CLASSIFIED_DESTRUCTIVE"}
    target = (target or "").strip()
    if not target or explicit_target_confirmation != target:
        return {"success": False, "error": "TARGET_CONFIRMATION_MISMATCH"}
    if not isinstance(target_snapshot, dict) or not target_snapshot:
        return {"success": False, "error": "TARGET_SNAPSHOT_REQUIRED"}
    if not repair_attempted or not (repair_result or "").strip():
        return {"success": False, "error": "REPAIR_ATTEMPT_AND_RESULT_REQUIRED"}
    if not (truth_basis or "").strip():
        return {"success": False, "error": "TRUTH_BASIS_REQUIRED"}
    if not_current_only:
        return {"success": False, "error": "NOT_CURRENT_IS_NOT_DELETE_AUTHORITY"}
    state = load_state()
    material = {
        "command_hash": sha256_text(command),
        "target": target,
        "target_snapshot_hash": sha256_text(canonical(target_snapshot)),
        "repair_attempted": True,
        "repair_result": repair_result,
        "truth_basis": truth_basis,
        "issued_at": now_iso(),
        "nonce": f"{time.time_ns()}:{os.getpid()}",
    }
    permit = sha256_text(canonical(material))
    _permit_store(state)[permit] = {**material, "used": False}
    save_state(state)
    event = {"event_id": permit[:24], "observed_at": now_iso(), "kind": "DESTRUCTIVE_PREFLIGHT", "target": target, "command_hash": material["command_hash"], "target_snapshot_hash": material["target_snapshot_hash"], "repair_result": repair_result, "truth_basis": truth_basis, "success": True}
    append_journal(event)
    return {"success": True, "permit": permit, "target": target, "command_hash": material["command_hash"], "one_use": True}

def consume_destructive_permit(command: str, permit: str | None):
    reason = destructive_reason(command)
    if not reason:
        return {"success": True, "destructive": False}
    if not motor_enabled():
        return {"success": False, "error": "MOTOR_DISABLED", "destructive": True}
    if not destructive_enabled():
        return {"success": False, "error": "DESTRUCTIVE_MOTOR_DISABLED", "destructive": True}
    if not permit:
        return {"success": False, "error": "DESTRUCTIVE_PERMIT_REQUIRED", "destructive": True}
    state = load_state(); permits = _permit_store(state); rec = permits.get(permit)
    if not rec:
        return {"success": False, "error": "DESTRUCTIVE_PERMIT_UNKNOWN", "destructive": True}
    if rec.get("used"):
        return {"success": False, "error": "DESTRUCTIVE_PERMIT_ALREADY_USED", "destructive": True}
    if rec.get("command_hash") != sha256_text(command):
        return {"success": False, "error": "DESTRUCTIVE_PERMIT_COMMAND_MISMATCH", "destructive": True}
    rec["used"] = True; rec["used_at"] = now_iso(); save_state(state)
    return {"success": True, "destructive": True, "target": rec.get("target"), "permit": permit}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def canonical(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()

def compact_text(s: str, limit: int = 12000) -> str:
    s = s or ""
    return s if len(s) <= limit else s[:limit] + f"\n...[truncated {len(s)-limit} chars]"

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"state_n": 0, "cursor": 0, "last_snapshot_hash": None, "last_event_hash": None}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def append_journal(event: dict):
    with JOURNAL_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

def make_receipt(tool: str, args: dict, result: dict, *, kind: str = "MOTOR", delta: Any = None):
    state = load_state()
    state_n = int(state.get("state_n", 0))
    event_material = {"tool": tool, "args": args, "result": result, "state_n": state_n}
    event_hash = sha256_text(canonical(event_material))
    duplicate = event_hash == state.get("last_event_hash")
    succeeded = bool(result.get("success", result.get("ok", False)))
    # Failed/blocked attempts are evidence events, not world-state transitions.
    if not duplicate and succeeded:
        state["state_n"] = state_n + 1
        state["cursor"] = int(state.get("cursor", 0)) + 1
        state["last_event_hash"] = event_hash
        save_state(state)
    event = {
        "event_id": event_hash[:24], "observed_at": now_iso(), "kind": kind,
        "tool": tool, "args_digest": sha256_text(canonical(args)),
        "delta": delta, "duplicate": duplicate,
        "state_n": state_n, "state_n_plus_1": int(state.get("state_n", state_n)),
        "cursor": int(state.get("cursor", 0)),
        "success": succeeded,
        "exit_code": result.get("exit_code"),
        "stdout_sha256": sha256_text(str(result.get("stdout", ""))),
        "stderr_sha256": sha256_text(str(result.get("stderr", ""))),
    }
    append_journal(event)
    return {"receipt": event, "result": result}

def motor_enabled() -> bool:
    return os.environ.get("GGDV_MOTOR_ENABLE", "0").strip().lower() in {"1", "true", "yes", "on"}

def which_any(names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None

def run(cmd, cwd=None, timeout=30, env=None):
    started = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd or None, capture_output=True, text=True, timeout=max(1, int(timeout)), env=env, shell=False)
        return {"success": p.returncode == 0, "exit_code": p.returncode, "stdout": compact_text(p.stdout), "stderr": compact_text(p.stderr), "duration_seconds": round(time.time()-started, 3), "command": cmd}
    except subprocess.TimeoutExpired as e:
        return {"success": False, "error": "TIMEOUT", "stdout": compact_text((e.stdout or "") if isinstance(e.stdout, str) else ""), "stderr": compact_text((e.stderr or "") if isinstance(e.stderr, str) else ""), "duration_seconds": round(time.time()-started, 3), "command": cmd}
    except Exception as e:
        return {"success": False, "error": repr(e), "stdout": "", "stderr": repr(e), "duration_seconds": round(time.time()-started, 3), "command": cmd}

def powershell_path():
    explicit = os.environ.get("GGDV_POWERSHELL_PATH")
    if explicit and Path(explicit).exists(): return explicit
    return which_any(["pwsh", "powershell.exe", "powershell"])

def adb_path():
    explicit = os.environ.get("GGDV_ADB_PATH")
    if explicit and Path(explicit).exists(): return explicit
    return which_any(["adb.exe", "adb"])

def git_path():
    return which_any(["git.exe", "git"])

def wsl_path():
    return which_any(["wsl.exe", "wsl"])

def motor_status():
    s = load_state()
    return {"success": True, "platform": platform.platform(), "python": os.sys.executable, "plugin_root": str(PLUGIN_ROOT), "state_dir": str(STATE_DIR), "journal": str(JOURNAL_FILE), "state_n": s.get("state_n",0), "cursor": s.get("cursor",0), "motor_enabled": motor_enabled(), "destructive_enabled": destructive_enabled(), "powershell": powershell_path(), "wsl": wsl_path(), "adb": adb_path(), "git": git_path(), "app_adapter_env": os.environ.get("GGDV_APP_ADAPTER"), "watcher_pid_file": str(WATCHER_PID_FILE)}

def repo_observe(path: str):
    # Direct filesystem on POSIX/Windows, with WSL-aware fallback on Windows.
    p = Path(path)
    use_wsl = False
    distro = os.environ.get("GGDV_WSL_DISTRO", "Ubuntu")
    linux_path = path
    if os.name == "nt":
        m = re.match(r"^\\\\wsl\$\\([^\\]+)\\(.*)$", path, re.I)
        if m:
            distro = m.group(1)
            linux_path = "/" + m.group(2).replace("\\", "/")
            use_wsl = True
        elif path.startswith("/") and wsl_path():
            use_wsl = True
    if use_wsl:
        wsl = wsl_path()
        if not wsl:
            return {"success": False, "error": "WSL_NOT_FOUND", "path": path}
        def g(*args):
            cmd = "git -C " + shlex.quote(linux_path) + " " + " ".join(shlex.quote(str(a)) for a in args)
            return run([wsl, "-d", distro, "--", "bash", "-lc", cmd], timeout=20)
        def list_workflows():
            cmd = "find " + shlex.quote(linux_path.rstrip('/') + '/.github/workflows') + " -maxdepth 1 -type f -printf '%f\\n' 2>/dev/null | sort"
            r = run([wsl, "-d", distro, "--", "bash", "-lc", cmd], timeout=20)
            return r.get("stdout", "").splitlines() if r.get("success") else []
        resolved_path = f"wsl://{distro}{linux_path}"
    else:
        git = git_path()
        if not git:
            return {"success": False, "error": "GIT_NOT_FOUND", "path": path}
        if not p.exists():
            return {"success": False, "error": "PATH_NOT_FOUND", "path": path}
        def g(*args): return run([git, "-C", str(p), *args], timeout=20)
        def list_workflows():
            wf = p / ".github" / "workflows"
            return sorted(x.name for x in wf.iterdir() if x.is_file()) if wf.exists() else []
        resolved_path = str(p.resolve())
    inside = g("rev-parse", "--is-inside-work-tree")
    if not inside.get("success"):
        return {"success": False, "error": "NOT_GIT_REPO", "path": path, "detail": inside}
    branch = g("branch", "--show-current")
    head = g("rev-parse", "HEAD")
    status = g("status", "--porcelain=v1", "--branch")
    remotes = g("remote", "-v")
    workflows = list_workflows()
    snap = {"path": resolved_path, "branch": branch.get("stdout","").strip(), "head": head.get("stdout","").strip(), "status": status.get("stdout","").splitlines(), "remotes": remotes.get("stdout","").splitlines(), "workflows": workflows}
    snap_hash = sha256_text(canonical(snap))
    state = load_state(); prev = state.get("last_repo_snapshot_hash")
    delta = "NO_DELTA" if prev == snap_hash else "DELTA"
    state["last_repo_snapshot_hash"] = snap_hash; save_state(state)
    return {"success": True, "delta": delta, "snapshot_hash": snap_hash, "snapshot": snap}

def powershell_exec(command: str, cwd: str|None=None, timeout_seconds: int=30, destructive_permit: str|None=None):
    if not motor_enabled(): return {"success": False, "error": "MOTOR_DISABLED", "remediation": "Set GGDV_MOTOR_ENABLE=1 in the local MCP process after authorizing local mutations."}
    gate = consume_destructive_permit(command, destructive_permit)
    if not gate.get("success"): return gate
    ps = powershell_path()
    if not ps: return {"success": False, "error": "POWERSHELL_NOT_FOUND"}
    return run([ps, "-NoProfile", "-Command", command], cwd=cwd, timeout=timeout_seconds)

def wsl_exec(command: str, distro: str="Ubuntu", cwd: str|None=None, timeout_seconds: int=30, destructive_permit: str|None=None):
    if not motor_enabled(): return {"success": False, "error": "MOTOR_DISABLED", "remediation": "Set GGDV_MOTOR_ENABLE=1 in the local MCP process after authorizing local mutations."}
    gate = consume_destructive_permit(command, destructive_permit)
    if not gate.get("success"): return gate
    wsl = wsl_path()
    if not wsl: return {"success": False, "error": "WSL_NOT_FOUND"}
    shell_cmd = command if not cwd else f"cd {shlex.quote(cwd)} && {command}"
    return run([wsl, "-d", distro, "--", "bash", "-lc", shell_cmd], timeout=timeout_seconds)

def adb_devices():
    adb = adb_path()
    if not adb: return {"success": False, "error": "ADB_NOT_FOUND", "remediation": "Install Android SDK Platform-Tools or set GGDV_ADB_PATH to adb.exe."}
    return run([adb, "devices", "-l"], timeout=20)

def _adb_cmd(serial: str|None, *args):
    adb = adb_path()
    if not adb: return None
    cmd=[adb]
    if serial: cmd += ["-s", serial]
    cmd += list(args)
    return cmd

def adb_action(action: str, serial: str|None=None, command: str|None=None, key: str|None=None, x: int|None=None, y: int|None=None, x1: int|None=None, y1: int|None=None, x2: int|None=None, y2: int|None=None, duration_ms: int=300, text: str|None=None, url: str|None=None, timeout_seconds: int=30):
    adb = adb_path()
    if not adb: return {"success": False, "error": "ADB_NOT_FOUND", "remediation": "Install Android SDK Platform-Tools or set GGDV_ADB_PATH to adb.exe."}
    read_only = action in {"status", "shell_read"}
    if not read_only and not motor_enabled(): return {"success": False, "error": "MOTOR_DISABLED", "remediation": "Set GGDV_MOTOR_ENABLE=1 in the local MCP process after authorizing device mutations."}
    if action == "status":
        return run(_adb_cmd(serial, "shell", "sh", "-c", "getprop ro.product.model; getprop ro.product.device; getprop ro.build.fingerprint; id"), timeout=timeout_seconds)
    if action == "shell_read":
        c=(command or "").strip()
        if not c.startswith(READ_PREFIXES): return {"success": False, "error": "COMMAND_NOT_IN_READ_ALLOWLIST"}
        return run(_adb_cmd(serial, "shell", c), timeout=timeout_seconds)
    if action == "keyevent": return run(_adb_cmd(serial, "shell", "input", "keyevent", str(key or "")), timeout=timeout_seconds)
    if action == "tap": return run(_adb_cmd(serial, "shell", "input", "tap", str(int(x)), str(int(y))), timeout=timeout_seconds)
    if action == "swipe": return run(_adb_cmd(serial, "shell", "input", "swipe", str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(duration_ms))), timeout=timeout_seconds)
    if action == "text": return run(_adb_cmd(serial, "shell", "input", "text", (text or "").replace(" ", "%s")), timeout=timeout_seconds)
    if action == "open_url":
        u=url or ""
        if not u.startswith(("https://","http://")): return {"success": False, "error": "INVALID_URL"}
        return run(_adb_cmd(serial, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", u), timeout=timeout_seconds)
    if action == "screenshot":
        if not motor_enabled(): return {"success": False, "error": "MOTOR_DISABLED"}
        out = STATE_DIR / f"screenshot_{int(time.time())}.png"
        cmd=_adb_cmd(serial, "exec-out", "screencap", "-p")
        try:
            p=subprocess.run(cmd, capture_output=True, timeout=timeout_seconds, shell=False)
            if p.returncode!=0: return {"success":False,"exit_code":p.returncode,"stderr":compact_text(p.stderr.decode(errors="replace"))}
            out.write_bytes(p.stdout)
            return {"success":True,"artifact":str(out),"bytes":len(p.stdout),"sha256":hashlib.sha256(p.stdout).hexdigest()}
        except Exception as e: return {"success":False,"error":repr(e)}
    return {"success": False, "error": "UNKNOWN_ACTION", "supported": ["status","shell_read","keyevent","tap","swipe","text","open_url","screenshot"]}

def resolve_app_adapter(explicit: str|None=None):
    candidates=[]
    if explicit:
        candidates.append(explicit)
    if os.environ.get("GGDV_APP_ADAPTER"):
        candidates.append(os.environ["GGDV_APP_ADAPTER"])

    repo_path = os.environ.get("GGDV_REPO_PATH")
    if repo_path:
        candidates.append(str(Path(repo_path) / ".vscode" / "scripts" / "app_adapters.py"))

    # Root-neutral discovery inside the current process tree.
    for base in (Path.cwd(), PLUGIN_ROOT):
        for root in (base, *base.parents):
            candidates.append(str(root / ".vscode" / "scripts" / "app_adapters.py"))

    # On POSIX/WSL, discover the active Open-ai-bot worktree by Git provenance,
    # not by a generated worktree directory name.
    worktrees = Path.home() / "kepler" / "worktrees"
    git = git_path()
    if git and worktrees.is_dir():
        for wt in sorted(worktrees.iterdir(), key=lambda p: p.name):
            adapter = wt / ".vscode" / "scripts" / "app_adapters.py"
            if not adapter.exists():
                continue
            origin = run([git, "-C", str(wt), "remote", "get-url", "origin"], timeout=5)
            if origin.get("success") and "2708halinh-cloud/Open-ai-bot" in origin.get("stdout", ""):
                candidates.append(str(adapter))

    seen=set()
    for c in candidates:
        if not c or c in seen:
            continue
        seen.add(c)
        try:
            if Path(c).exists():
                return str(Path(c))
        except Exception:
            pass
    return None

def app_adapter(action: str, target: str="all", adapter_path: str|None=None, force: bool=False, extra_args: list[str]|None=None):
    adapter=resolve_app_adapter(adapter_path)
    if not adapter: return {"success":False,"error":"APP_ADAPTER_NOT_FOUND","source_drive_id":"1zKvEAJ5O3-tsZoZUS3UM0O4j-UAEm_gJ","remediation":"Set GGDV_APP_ADAPTER to the current local .vscode/scripts/app_adapters.py path."}
    if action != "status" and not motor_enabled(): return {"success":False,"error":"MOTOR_DISABLED"}
    py=os.sys.executable
    cmd=[py,adapter,action]
    if action=="status": cmd += [target]
    elif action in {"launch","focus","close"}:
        cmd += [target]
        if action=="launch" and extra_args: cmd += list(extra_args)
        if action=="close" and force: cmd += ["--force"]
    else: return {"success":False,"error":"UNSUPPORTED_APP_ACTION","supported":["status","launch","focus","close"]}
    return run(cmd, timeout=45)

def journal_record(domain: str, source: dict, action: dict, consequence: dict, readback: dict, cursor: str|None=None):
    payload={"domain":domain,"source":source,"action":action,"consequence":consequence,"readback":readback,"external_cursor":cursor}
    result={"success":True,"recorded":True,"payload_digest":sha256_text(canonical(payload))}
    return make_receipt("journal_record", payload, result, kind="JOURNAL")
