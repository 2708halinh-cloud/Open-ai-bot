#!/usr/bin/env python3
import hashlib, json, os, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".runtime" / "RECOVERY_STATE_CURRENT.json"

CORE = [
    "AGENTS.md",
    "CURRENT_RUNTIME/00_DOC_KY_CURRENT_CORE.md",
    "CURRENT_RUNTIME/R-000_CURRENT.md",
    "CURRENT_RUNTIME/4D_5D_CURRENT.md",
    "CURRENT_RUNTIME/SOL_REENTRY_CURRENT.md",
    "CURRENT_RUNTIME/TESSERACT_LOCAL_BOOT_CURRENT.md",
    ".runtime/RUNTIME_N_PLUS.env",
    ".runtime/TESSERACT_BOOT_G.env",
]

def sh(cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {"returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

files=[]
for rel in CORE:
    p=ROOT/rel
    files.append({
        "path":rel,
        "present":p.exists(),
        "size":p.stat().st_size if p.exists() else None,
        "sha256":sha256(p) if p.is_file() else None,
    })

git_head=sh(["git","rev-parse","HEAD"])
git_branch=sh(["git","branch","--show-current"])
git_status=sh(["git","status","--porcelain=v1"])
git_recent=sh(["git","log","-n","25","--date=iso-strict","--pretty=format:%H%x09%ad%x09%s"])

caps={
    "python3":shutil.which("python3"),
    "bash":shutil.which("bash"),
    "git":shutil.which("git"),
    "powershell_exe":shutil.which("powershell.exe"),
    "wslpath":shutil.which("wslpath"),
}

state={
    "schema":"SOL_CONTINUITY_RECOVERY/1.0",
    "generated_at_unix":time.time(),
    "root":str(ROOT),
    "identity":{
        "hostname":sh(["hostname"])["stdout"],
        "uname":sh(["uname","-a"])["stdout"],
        "uid":os.getuid() if hasattr(os,"getuid") else None,
        "gid":os.getgid() if hasattr(os,"getgid") else None,
    },
    "git":{
        "head":git_head,
        "branch":git_branch,
        "status":git_status,
        "recent_commits":git_recent["stdout"].splitlines(),
    },
    "durable_runtime_files":files,
    "authorized_local_capabilities":caps,
    "memory_policy":"RECONSTRUCT_FROM_DURABLE_CARRIERS_NOT_CHAT_MEMORY",
    "secret_bytes_collected":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
tmp=OUT.with_suffix(".tmp")
tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
tmp.replace(OUT)
print(str(OUT))
