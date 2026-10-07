from __future__ import annotations
import argparse, json, os, signal, time
from pathlib import Path
from runtime_core import STATE_DIR, WATCHER_PID_FILE, WATCHER_CONFIG_FILE, adb_devices, canonical, load_state, save_state, sha256_text, append_journal, now_iso, repo_observe
from filesystem_sensor import observe_paths, diff_observations
from carrier_events import read_event_batch, summarize_events

def snapshot(cfg):
    repos=[]
    for p in cfg.get("repo_paths", []):
        raw_repo=repo_observe(p)
        repo={}
        for k in ("success","error","snapshot_hash","snapshot"):
            if k in raw_repo:
                repo[k]=raw_repo.get(k)
        repos.append(repo)
    if cfg.get("adb", False):
        raw=adb_devices()
        adb={}
        for k in ("success","exit_code","stdout","stderr","error"):
            if k in raw:
                v=raw.get(k)
                adb[k]=v.strip() if isinstance(v,str) else v
    else:
        adb={"success":True,"skipped":True}
    filesystem=observe_paths(cfg.get("fs_paths", []))
    return {"repos":repos,"adb":adb,"filesystem":filesystem}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default=str(WATCHER_CONFIG_FILE)); args=ap.parse_args()
    cfg_path=Path(args.config)
    cfg=json.loads(cfg_path.read_text(encoding="utf-8-sig")) if cfg_path.exists() else {"poll_seconds":3,"repo_paths":[],"adb":False}
    WATCHER_PID_FILE.write_text(str(os.getpid()),encoding="utf-8")
    running=True
    def stop(*_):
        nonlocal running; running=False
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    st=load_state()
    last_snap=st.get("last_sensory_snapshot") if isinstance(st.get("last_sensory_snapshot"),dict) else None
    last_hash=st.get("last_snapshot_hash")
    carrier_log=STATE_DIR / "carrier-events.jsonl"
    while running:
        st=load_state()
        carrier_events, carrier_offset, carrier_rotated = read_event_batch(
            carrier_log,
            st.get("carrier_event_offset", 0),
            max_events=int(cfg.get("carrier_batch_max", 512)),
        )
        if carrier_events:
            n=int(st.get("state_n",0))
            st["state_n"]=n+1
            st["cursor"]=int(st.get("cursor",0))+1
            st["carrier_event_offset"]=carrier_offset
            save_state(st)
            append_journal({
                "event_id":sha256_text(canonical(carrier_events))[:24],
                "observed_at":now_iso(),
                "kind":"SENSORY_CARRIER_EVENTS",
                "delta":summarize_events(carrier_events, rotated=carrier_rotated),
                "events":carrier_events,
                "state_n":n,
                "state_n_plus_1":n+1,
                "cursor":st["cursor"],
            })
        elif carrier_rotated:
            st["carrier_event_offset"]=carrier_offset
            save_state(st)

        snap=snapshot(cfg); h=sha256_text(canonical(snap))
        if h!=last_hash:
            st=load_state(); n=int(st.get("state_n",0))
            if last_snap is None:
                delta={"kind":"BASELINE","filesystem":{"summary":{"signals":[]},"roots":[]}}
            else:
                delta={
                    "kind":"DELTA",
                    "filesystem":diff_observations(last_snap.get("filesystem",[]),snap.get("filesystem",[])),
                    "repo_changed":last_snap.get("repos")!=snap.get("repos"),
                    "adb_changed":last_snap.get("adb")!=snap.get("adb"),
                }
            st["state_n"]=n+1
            st["cursor"]=int(st.get("cursor",0))+1
            st["last_snapshot_hash"]=h
            st["last_sensory_snapshot"]=snap
            save_state(st)
            append_journal({"event_id":h[:24],"observed_at":now_iso(),"kind":"SENSORY_WATCH","delta":delta,"snapshot_hash":h,"state_n":n,"state_n_plus_1":n+1,"cursor":st["cursor"]})
            last_snap=snap; last_hash=h
        elif last_snap is None:
            st=load_state(); st["last_sensory_snapshot"]=snap; save_state(st); last_snap=snap
        time.sleep(max(1,float(cfg.get("poll_seconds",3))))
    try: WATCHER_PID_FILE.unlink(missing_ok=True)
    except Exception: pass
if __name__=="__main__": main()
