#!/usr/bin/env python3
from __future__ import annotations
import json, os, signal, subprocess, sys
from pathlib import Path
from runtime_core import *
from agent_army import status as agent_army_status_impl, route as agent_route_impl
from io_device import definition as io_device_definition_impl, ingress as io_ingress_impl, egress as io_egress_impl, status_table as io_status_table_impl, clear as io_clear_impl
from intermediate_device import definition as intermediate_device_definition_impl, observe as intermediate_observe_impl, transform as intermediate_transform_impl, status as intermediate_status_impl

TOOLS = [
 {"name":"intermediate_device_definition","description":"Read THIẾT_BỊ_TRUNG_GIAN semantics: mutable state/config carrier governed by freshness and provenance; not RAM and not memory by default.","inputSchema":{"type":"object","properties":{}}},
 {"name":"intermediate_observe","description":"Fresh-observe one intermediate carrier snapshot/revision and classify DELTA/NO_DELTA without mutating the carrier.","inputSchema":{"type":"object","properties":{"carrier_ref":{"type":"string"},"carrier_kind":{"type":"string"},"state":{},"revision":{"type":["string","null"]},"observed_at":{"type":["string","null"]}},"required":["carrier_ref","carrier_kind","state"]}},
 {"name":"intermediate_transform","description":"Record a bounded state/data transformation for an intermediate carrier with input/output hashes and provenance continuity. This does not itself mutate the external carrier.","inputSchema":{"type":"object","properties":{"carrier_ref":{"type":"string"},"carrier_kind":{"type":"string"},"input_state":{},"output_state":{},"rule_ref":{"type":["string","null"]},"input_revision":{"type":["string","null"]},"output_revision":{"type":["string","null"]}},"required":["carrier_ref","carrier_kind","input_state","output_state"]}},
 {"name":"intermediate_status","description":"Return recent volatile transformation receipts for THIẾT_BỊ_TRUNG_GIAN; external carrier persistence is separate from this observation cache.","inputSchema":{"type":"object","properties":{"limit":{"type":"integer","minimum":1,"maximum":256}}}},
 {"name":"io_device_definition","description":"Read the GGDV THIẾT_BỊ_ĐẦU_CUỐI definition. HEAD is the ingress role, TAIL is the egress role, and the working surface is volatile RAM, not durable memory or journal.","inputSchema":{"type":"object","properties":{}}},
 {"name":"io_ingress","description":"Put one signal into the volatile THIẾT_BỊ_ĐẦU role for NEURONS_SESORIMOTOR processing. This creates an in-process RAM frame only; it is not persisted as memory.","inputSchema":{"type":"object","properties":{"signal":{"type":"object"}},"required":["signal"]}},
 {"name":"io_egress","description":"Write NEXT/DONE/UNDONE/output_ref to the THIẾT_BỊ_CUỐI role of a volatile frame and emit a feedback signal back to THIẾT_BỊ_ĐẦU.","inputSchema":{"type":"object","properties":{"frame_id":{"type":"string"},"next":{"type":[]},"done":{"type":"array"},"undone":{"type":"array"},"output_ref":{}},"required":["frame_id"]}},
 {"name":"io_status_table","description":"Return the temporary endpoint status table for recent volatile I/O frames: input delta, NEXT, DONE, UNDONE, output reference and feedback-to-head.","inputSchema":{"type":"object","properties":{"limit":{"type":"integer","minimum":1,"maximum":256}}}},
 {"name":"io_clear","description":"Clear only the volatile THIẾT_BỊ_ĐẦU_CUỐI RAM working frames. This does not delete journal, memory, Drive, GitHub, or any durable carrier.","inputSchema":{"type":"object","properties":{}}},
 {"name":"agent_army_status","description":"Read the deployed NEURONS_SESORIMOTOR Agent-Sub registry, lane counts and credential policy without mutating anything.","inputSchema":{"type":"object","properties":{}}},
 {"name":"agent_route","description":"Route one provenance-bound delta packet through the distributed NEURONS_SESORIMOTOR network. This is planning/routing only; it does not execute the selected MOTOR.","inputSchema":{"type":"object","properties":{"packet":{"type":"object"}},"required":["packet"]}},
 {"name":"motor_status","description":"Observe local motor-provider callability, paths, cursor and state without mutating the environment.","inputSchema":{"type":"object","properties":{}}},
 {"name":"repo_observe","description":"Observe a local Git repository: branch, HEAD, status, remotes and workflow filenames; emit DELTA/NO_DELTA.","inputSchema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},
 {"name":"destructive_preflight","description":"Issue a one-use permit for an exact destructive command only after target snapshot, repair attempt/result, truth basis, and exact target confirmation are supplied. NOT_CURRENT alone can never authorize deletion.","inputSchema":{"type":"object","properties":{"command":{"type":"string"},"target":{"type":"string"},"target_snapshot":{"type":"object"},"repair_attempted":{"type":"boolean"},"repair_result":{"type":"string"},"truth_basis":{"type":"string"},"explicit_target_confirmation":{"type":"string"},"not_current_only":{"type":"boolean"}},"required":["command","target","target_snapshot","repair_attempted","repair_result","truth_basis","explicit_target_confirmation"]}},
 {"name":"powershell_exec","description":"Execute an authorized PowerShell command on the connected Windows machine. Requires GGDV_MOTOR_ENABLE=1. Destructive commands additionally require a one-use destructive permit.","inputSchema":{"type":"object","properties":{"command":{"type":"string"},"cwd":{"type":["string","null"]},"timeout_seconds":{"type":"integer","minimum":1,"maximum":600},"destructive_permit":{"type":["string","null"]}},"required":["command"]}},
 {"name":"wsl_exec","description":"Execute an authorized command in WSL. Requires GGDV_MOTOR_ENABLE=1. Destructive commands additionally require a one-use destructive permit.","inputSchema":{"type":"object","properties":{"command":{"type":"string"},"distro":{"type":"string"},"cwd":{"type":["string","null"]},"timeout_seconds":{"type":"integer","minimum":1,"maximum":600},"destructive_permit":{"type":["string","null"]}},"required":["command"]}},
 {"name":"adb_devices","description":"Read adb devices -l from local Android Platform-Tools; no device mutation.","inputSchema":{"type":"object","properties":{}}},
 {"name":"adb_action","description":"Run bounded ADB actions matching the existing GGDV Android bridge: status, shell_read, keyevent, tap, swipe, text, open_url, screenshot. Mutating actions require GGDV_MOTOR_ENABLE=1.","inputSchema":{"type":"object","properties":{"action":{"type":"string","enum":["status","shell_read","keyevent","tap","swipe","text","open_url","screenshot"]},"serial":{"type":["string","null"]},"command":{"type":["string","null"]},"key":{"type":["string","null"]},"x":{"type":["integer","null"]},"y":{"type":["integer","null"]},"x1":{"type":["integer","null"]},"y1":{"type":["integer","null"]},"x2":{"type":["integer","null"]},"y2":{"type":["integer","null"]},"duration_ms":{"type":"integer"},"text":{"type":["string","null"]},"url":{"type":["string","null"]},"timeout_seconds":{"type":"integer","minimum":1,"maximum":120}},"required":["action"]}},
 {"name":"app_adapter","description":"Invoke the canonical .vscode app_adapters.py lifecycle: status/launch/focus/close. Mutating actions require GGDV_MOTOR_ENABLE=1.","inputSchema":{"type":"object","properties":{"action":{"type":"string","enum":["status","launch","focus","close"]},"target":{"type":"string"},"adapter_path":{"type":["string","null"]},"force":{"type":"boolean"},"extra_args":{"type":"array","items":{"type":"string"}}},"required":["action"]}},
 {"name":"journal_record","description":"Append a compact domain/source/action/consequence/readback event and advance the local N-to-N+1 journal state.","inputSchema":{"type":"object","properties":{"domain":{"type":"string"},"source":{"type":"object"},"action":{"type":"object"},"consequence":{"type":"object"},"readback":{"type":"object"},"cursor":{"type":["string","null"]}},"required":["domain","source","action","consequence","readback"]}},
 {"name":"watcher_start","description":"Start the local sensory watcher. It observes configured repos/ADB and journals deltas; it never performs MOTOR actions. Requires GGDV_MOTOR_ENABLE=1.","inputSchema":{"type":"object","properties":{"repo_paths":{"type":"array","items":{"type":"string"}},"adb":{"type":"boolean"},"poll_seconds":{"type":"number","minimum":1,"maximum":3600}}}},
 {"name":"watcher_stop","description":"Stop the local sensory watcher. Requires GGDV_MOTOR_ENABLE=1.","inputSchema":{"type":"object","properties":{}}},
 {"name":"watcher_status","description":"Read watcher PID/aliveness and current config/cursor without mutation.","inputSchema":{"type":"object","properties":{}}}
]

def watcher_status():
    pid=None; alive=False
    if WATCHER_PID_FILE.exists():
        try:
            pid=int(WATCHER_PID_FILE.read_text().strip())
            if os.name=="nt":
                q=run(["tasklist","/FI",f"PID eq {pid}","/FO","CSV","/NH"],timeout=10); alive=q.get("success") and str(pid) in q.get("stdout","")
            else:
                os.kill(pid,0); alive=True
        except Exception: alive=False
    cfg=None
    if WATCHER_CONFIG_FILE.exists():
        try: cfg=json.loads(WATCHER_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception: cfg={"error":"INVALID_CONFIG"}
    st=load_state()
    return {"success":True,"pid":pid,"alive":alive,"config":cfg,"state_n":st.get("state_n",0),"cursor":st.get("cursor",0),"journal":str(JOURNAL_FILE)}

def watcher_start(repo_paths=None, adb=False, poll_seconds=3):
    if not motor_enabled(): return {"success":False,"error":"MOTOR_DISABLED"}
    current=watcher_status()
    if current.get("alive"): return {"success":True,"already_running":True,"pid":current.get("pid"),"status":current}
    cfg={"repo_paths":repo_paths or [],"adb":bool(adb),"poll_seconds":float(poll_seconds)}
    WATCHER_CONFIG_FILE.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8")
    script=Path(__file__).with_name("watcher.py")
    creationflags=0
    kwargs={}
    if os.name=="nt":
        creationflags = getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0) | getattr(subprocess,"DETACHED_PROCESS",0)
        kwargs["creationflags"]=creationflags
    else:
        kwargs["start_new_session"]=True
    log=(STATE_DIR/"watcher.log").open("a",encoding="utf-8")
    p=subprocess.Popen([sys.executable,str(script),"--config",str(WATCHER_CONFIG_FILE)],stdout=log,stderr=log,cwd=str(Path(__file__).parent),**kwargs)
    WATCHER_PID_FILE.write_text(str(p.pid),encoding="utf-8")
    return {"success":True,"pid":p.pid,"config":cfg,"log":str(STATE_DIR/"watcher.log")}

def watcher_stop():
    if not motor_enabled(): return {"success":False,"error":"MOTOR_DISABLED"}
    st=watcher_status(); pid=st.get("pid")
    if not pid or not st.get("alive"):
        WATCHER_PID_FILE.unlink(missing_ok=True); return {"success":True,"already_stopped":True}
    try:
        if os.name=="nt": run(["taskkill","/PID",str(pid),"/T","/F"],timeout=15)
        else: os.kill(pid,signal.SIGTERM)
        WATCHER_PID_FILE.unlink(missing_ok=True); return {"success":True,"stopped_pid":pid}
    except Exception as e: return {"success":False,"error":repr(e),"pid":pid}

def call_tool(name,args):
    args=args or {}
    if name=="intermediate_device_definition": return intermediate_device_definition_impl()
    if name=="intermediate_observe": return intermediate_observe_impl(args["carrier_ref"],args.get("carrier_kind","UNKNOWN"),args.get("state"),args.get("revision"),args.get("observed_at"))
    if name=="intermediate_transform": return intermediate_transform_impl(carrier_ref=args["carrier_ref"],carrier_kind=args.get("carrier_kind","UNKNOWN"),input_state=args.get("input_state"),output_state=args.get("output_state"),rule_ref=args.get("rule_ref"),input_revision=args.get("input_revision"),output_revision=args.get("output_revision"))
    if name=="intermediate_status": return intermediate_status_impl(args.get("limit",50))
    if name=="io_device_definition": return io_device_definition_impl()
    if name=="io_ingress": return io_ingress_impl(args.get("signal") or {})
    if name=="io_egress": return io_egress_impl(args["frame_id"], next_item=args.get("next"), done=args.get("done"), undone=args.get("undone"), output_ref=args.get("output_ref"))
    if name=="io_status_table": return io_status_table_impl(args.get("limit",50))
    if name=="io_clear": return io_clear_impl()
    if name=="agent_army_status": return agent_army_status_impl()
    if name=="agent_route": return agent_route_impl(args.get("packet") or {})
    if name=="motor_status": return motor_status()
    if name=="repo_observe": return repo_observe(args["path"])
    if name=="destructive_preflight": return destructive_preflight(command=args["command"],target=args["target"],target_snapshot=args["target_snapshot"],repair_attempted=args["repair_attempted"],repair_result=args["repair_result"],truth_basis=args["truth_basis"],explicit_target_confirmation=args["explicit_target_confirmation"],not_current_only=args.get("not_current_only",False))
    if name=="powershell_exec": return make_receipt(name,args,powershell_exec(args["command"],args.get("cwd"),args.get("timeout_seconds",30),args.get("destructive_permit")))
    if name=="wsl_exec": return make_receipt(name,args,wsl_exec(args["command"],args.get("distro","Ubuntu"),args.get("cwd"),args.get("timeout_seconds",30),args.get("destructive_permit")))
    if name=="adb_devices": return adb_devices()
    if name=="adb_action": return make_receipt(name,args,adb_action(**args),kind="MOTOR" if args.get("action") not in {"status","shell_read"} else "SENSORY")
    if name=="app_adapter": return make_receipt(name,args,app_adapter(args["action"],args.get("target","all"),args.get("adapter_path"),args.get("force",False),args.get("extra_args")),kind="SENSORY" if args["action"]=="status" else "MOTOR")
    if name=="journal_record": return journal_record(args["domain"],args["source"],args["action"],args["consequence"],args["readback"],args.get("cursor"))
    if name=="watcher_status": return watcher_status()
    if name=="watcher_start": return make_receipt(name,args,watcher_start(args.get("repo_paths"),args.get("adb",False),args.get("poll_seconds",3)))
    if name=="watcher_stop": return make_receipt(name,args,watcher_stop())
    return {"success":False,"error":"UNKNOWN_TOOL"}

def respond(id_, result=None, error=None):
    obj={"jsonrpc":"2.0","id":id_}
    if error is not None: obj["error"]=error
    else: obj["result"]=result
    sys.stdout.write(json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n"); sys.stdout.flush()

def main():
    for line in sys.stdin:
        line=line.strip()
        if not line: continue
        try:
            req=json.loads(line); mid=req.get("id"); method=req.get("method"); params=req.get("params") or {}
            if method=="initialize":
                respond(mid,{"protocolVersion":params.get("protocolVersion","2025-06-18"),"capabilities":{"tools":{}},"serverInfo":{"name":"ggdv-local-motor","version":"0.5.1"}})
            elif method=="notifications/initialized":
                continue
            elif method=="ping": respond(mid,{})
            elif method=="tools/list": respond(mid,{"tools":TOOLS})
            elif method=="tools/call":
                name=params.get("name"); args=params.get("arguments") or {}; out=call_tool(name,args)
                respond(mid,{"content":[{"type":"text","text":json.dumps(out,ensure_ascii=False,indent=2)}],"isError":not bool(out.get("success", out.get("result",{}).get("success", True)))})
            else:
                if mid is not None: respond(mid,error={"code":-32601,"message":f"Method not found: {method}"})
        except Exception as e:
            try: respond(req.get("id") if isinstance(req,dict) else None,error={"code":-32603,"message":repr(e)})
            except Exception: pass
if __name__=="__main__": main()
