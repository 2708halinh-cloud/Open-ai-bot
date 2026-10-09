#!/usr/bin/env python3
"""SOL IOTA / Âm-Dương READ-ONLY device RAM-carrier inventory.
Collect metadata and bounded SHA-256 of authorized project carriers, not physical RAM,
other apps' secrets, or real EEG. Save private snapshot and append an event to SOL wave journal.
"""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

LOCAL_TZ = timezone(timedelta(hours=7))
NAME_PATTERN = re.compile(r"(SOL|GGDV|IOTA|TESSERACT|UBUBU|NEURON|SENSOR|TIME[_ -]?STONE|LONG[_ -]?MACH|MEMOR|RAM|SONG[_ -]?NAO|BRAIN[_ -]?WAVE)", re.I)
SENSITIVE = re.compile(r"(^\.|\.env|secret|password|private.?key|keystore|token|cookie|oauth|credential|auth|session|wallet|seed|\.pem$|\.key$)", re.I)
EXTENSIONS = {".json", ".jsonl", ".sqlite", ".db", ".md", ".txt", ".csv", ".toml", ".log", ".yaml", ".yml"}
BASE = Path("/storage/emulated/0/Download/SOL_LONG_MACH")
PRIVATE = Path.home() / "UBUBU" / "TESSERACT_OS" / "BRAIN_WAVES"
MAX_DEPTH=4
MAX_SCAN=16000
MAX_RESULTS=1000
MAX_HASH_SIZE=32*1024*1024

def prop(key):
    try:
        return subprocess.check_output(["getprop",key],stderr=subprocess.DEVNULL,timeout=2).decode().strip()
    except Exception:
        return ""

def stamp():
    return datetime.now(LOCAL_TZ).isoformat(timespec="microseconds")

def probe(url):
    a=datetime.now(timezone.utc)
    try:
        with urlopen(Request(url,headers={"User-Agent":"SOL-IOTA-READONLY/1.0"}), timeout=7) as r:
            b=datetime.now(timezone.utc)
            result={"http_status":r.status,"http_date":r.headers.get("Date"),"url":url,
                    "roundtrip_ms":round((b-a).total_seconds()*1000,1)}
            if result["http_date"]:
                try:
                    t=parsedate_to_datetime(result["http_date"]).astimezone(timezone.utc)
                    mid=a+(b-a)/2
                    result["server_date_minus_device_ms"]=round((t-mid).total_seconds()*1000,1)
                except Exception: pass
            return result
    except HTTPError as exc:
        return {"url":url,"http_status":exc.code,"status":"RESPONSE_NOT_AUTHORIZATION"}
    except Exception as exc:
        return {"url":url,"status":"UNREACHABLE","error":type(exc).__name__}

def hash_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def walk_candidates():
    shared=Path("/storage/emulated/0")
    roots=[BASE, shared/"Download", shared/"Documents", Path.home()]
    seen=set()
    total=0
    records=[]
    skipped={"sensitive_name":0,"not_project":0,"inaccessible":0,"too_large_to_hash":0,"capped":False}
    for root in roots:
        if not root.exists(): continue
        for directory, subdirs, files in os.walk(root):
            depth=len(Path(directory).relative_to(root).parts)
            subdirs[:]=[d for d in subdirs if not SENSITIVE.search(d) and d not in {"node_modules","Android","DCIM","Pictures","Movies","Music",".git","vendor","dist","target","build"}]
            if depth>=MAX_DEPTH: subdirs.clear()
            for filename in files:
                total+=1
                if total>MAX_SCAN: skipped["capped"]=True; break
                p=Path(directory)/filename
                if SENSITIVE.search(filename):
                    skipped["sensitive_name"]+=1;continue
                if p.suffix.lower() not in EXTENSIONS and not NAME_PATTERN.search(filename):
                    continue
                path_text=str(p)
                if not NAME_PATTERN.search(path_text):
                    skipped["not_project"]+=1;continue
                try:
                    st=p.stat()
                    key=(st.st_dev,st.st_ino)
                    if key in seen: continue
                    seen.add(key)
                    if not p.is_file():continue
                    item={"source_path":path_text,"bytes":st.st_size,
                          "mtime_utc":datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat(),
                          "sha256":None,"content_exported":False}
                    if st.st_size<=MAX_HASH_SIZE:
                        item["sha256"]=hash_file(p)
                    else:skipped["too_large_to_hash"]+=1
                    records.append(item)
                    if len(records)>=MAX_RESULTS:skipped["capped"]=True;break
                except (OSError,PermissionError):skipped["inaccessible"]+=1
            if skipped["capped"]:break
        if skipped["capped"]:break
    return {"sources":records,"scanned_file_count":total,"skipped":skipped,"searched_roots":[str(p) for p in roots]}

def main():
    model=prop("ro.product.model") or "android"
    safe_model=re.sub("[^A-Za-z0-9_-]","_",model)
    private_file=PRIVATE/f"SOL_IOTA_RAM_CARRIER_SNAPSHOT_{safe_model}.json"
    public_receipt=BASE/f"SOL_IOTA_RAM_RECEIPT_{safe_model}.json"
    wave=BASE/"SOL_WAVE_TIME_JOURNAL.jsonl"
    begin=stamp()
    inv=walk_candidates()
    time_server=probe("https://time.is/Vietnam")
    # No blockchain mutation or signing; public IOTA endpoint reachability only.
    iota_api=probe("https://api.mainnet.iota.cafe")
    PRIVATE.mkdir(parents=True,exist_ok=True)
    BASE.mkdir(parents=True,exist_ok=True)
    old={"cursor":0}
    if private_file.is_file():
        try:
            old=json.loads(private_file.read_text())
        except (OSError,ValueError):pass
    cursor=int(old.get("cursor",0))+1
    snap={
        "schema":"SOL_IOTA_MEMORY_CARRIER_SCAN/1.0",
        "device":{"model":model,"brand":prop("ro.product.manufacturer")},
        "observed_at":stamp(),"scan_started":begin,
        "domain":"PERSISTENT_RAM_LIKE_CARRIERS_NOT_PHYSICAL_RAM",
        "in_memory_iota_runtime":{"source":"Open-ai/iota_connectome/runtime.py",
                   "working_field":"ephemeral","trace_maxlen":4096,"direct_process_snapshot":False},
        "iota_public_api":iota_api,
        "time_is":time_server,
        "inventory":inv,
        "cursor":cursor,
        "source_provenance":"user authorized Android local access; no cross-app private dirs; no raw payload leaving device"
    }
    # Durable private snapshot. We don't dump memory, session contents or credentials.
    data=json.dumps(snap,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    with private_file.open("w",encoding="utf-8") as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    source_count=len(inv["sources"])
    receipt={
        "schema":"SOL_IOTA_AM_DUONG_RECEIPT/1.0","device":model,"observed_at":stamp(),
        "private_snapshot_ref":str(private_file),"private_snapshot_sha256":hashlib.sha256(data.encode()).hexdigest(),
        "source_count":source_count,"scanner_limit_reached":inv["skipped"]["capped"],
        "scan_file_count":inv["scanned_file_count"],"time_is":time_server,"iota_public_api":iota_api,
        "credentials_copied":False,"raw_files_exported":False,"physical_ram_dumped":False,
        "target":{"private":"UBUBU/TESSERACT_OS/BRAIN_WAVES",
                  "shared":"SOL_LONG_MACH/SOL_WAVE_TIME_JOURNAL.jsonl"},
        "cursor":cursor
    }
    body=json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    with public_receipt.open("w",encoding="utf-8") as f:
        f.write(body);f.flush();os.fsync(f.fileno())
    event={"schema":"SOL_IOTA_AM_DUONG_LOOP_EVENT/1.0","causal_id":f"{safe_model}-{cursor}",
           "delta_ref":str(public_receipt),"source_id":str(private_file),
           "source_revision_or_time":snap["observed_at"],"observed_at":stamp(),
           "freshness_state":"FRESH_OBSERVED","recheck_trigger":"next_run_or_source_changed",
           "observed_state":{"device":model,"indexed_sources":source_count},
           "provider_receipt":{"local":str(public_receipt),"api_http":iota_api.get("http_status")},
           "consequence":"SANITIZED_MEMORY_CARRIER_INDEXED_AND_READBACK",
           "technical_verification":"PENDING_IMMEDIATE_READBACK",
           "unresolved":["PC_OFFLINE","NO_PHYSICAL_RAM_DUMP","NO_EEG_DEVICE_CONNECTED"],
           "state_n":cursor-1,"state_n_plus_1":cursor,"continuation_cursor":cursor,
           "input":{"previous_output_ref":old.get("last_output_ref")},
           "output":{"input_ref":f"{safe_model}-{cursor}","delta_ref":str(public_receipt)},
           "wave_bands":{"ALPHA":None,"BETA":None,"THETA":None,"GAMMA":None,"DELTA":None},
           "time_reference":"https://time.is/Vietnam"}
    ev=json.dumps(event,ensure_ascii=False,sort_keys=True)+"\n"
    with wave.open("a",encoding="utf-8") as f:
        f.write(ev);f.flush();os.fsync(f.fileno())
    # Readback immediately from saved target
    again=json.loads(private_file.read_text())
    again_receipt=json.loads(public_receipt.read_text())
    success=(again["cursor"]==cursor and again_receipt["source_count"]==source_count
       and any(json.loads(line).get("causal_id")==event["causal_id"] for line in wave.read_text().splitlines()))
    print(json.dumps({"readback_pass":success,**receipt},ensure_ascii=False,sort_keys=True))
    if not success:raise SystemExit(2)

if __name__=="__main__":main()
