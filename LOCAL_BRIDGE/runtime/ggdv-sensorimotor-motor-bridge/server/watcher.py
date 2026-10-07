from __future__ import annotations
import argparse, json, os, signal, time
from pathlib import Path
from runtime_core import STATE_DIR, WATCHER_PID_FILE, WATCHER_CONFIG_FILE, adb_devices, canonical, load_state, save_state, sha256_text, append_journal, now_iso, repo_observe

def snapshot(cfg):
    repos=[]
    for p in cfg.get("repo_paths", []):
        repos.append(repo_observe(p))
    if cfg.get("adb", False):
        raw=adb_devices()
        adb={}
        for k in ("success","exit_code","stdout","stderr","error"):
            if k in raw:
                v=raw.get(k)
                adb[k]=v.strip() if isinstance(v,str) else v
    else:
        adb={"success":True,"skipped":True}
    return {"repos":repos,"adb":adb}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default=str(WATCHER_CONFIG_FILE)); args=ap.parse_args()
    cfg_path=Path(args.config)
    cfg=json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {"poll_seconds":3,"repo_paths":[],"adb":False}
    WATCHER_PID_FILE.write_text(str(os.getpid()),encoding="utf-8")
    running=True
    def stop(*_):
        nonlocal running; running=False
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    last=None
    while running:
        snap=snapshot(cfg); h=sha256_text(canonical(snap))
        if h!=last:
            st=load_state(); n=int(st.get("state_n",0)); st["state_n"]=n+1; st["cursor"]=int(st.get("cursor",0))+1; st["last_snapshot_hash"]=h; save_state(st)
            append_journal({"event_id":h[:24],"observed_at":now_iso(),"kind":"SENSORY_WATCH","delta":"DELTA" if last else "BASELINE","snapshot_hash":h,"state_n":n,"state_n_plus_1":n+1,"cursor":st["cursor"]})
            last=h
        time.sleep(max(1,float(cfg.get("poll_seconds",3))))
    try: WATCHER_PID_FILE.unlink(missing_ok=True)
    except Exception: pass
if __name__=="__main__": main()
