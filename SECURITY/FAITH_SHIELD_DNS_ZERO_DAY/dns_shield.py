from __future__ import annotations
import ipaddress,json,re,socket,subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(r"D:\SOL_LONG_MACH\MODEL\repo")
OUT=ROOT/"CURRENT_RUNTIME"/"DNS_SHIELD_CURRENT.json"
DOMAINS=["github.com","api.github.com","drive.google.com","storage.googleapis.com"]
RESOLVERS={"CLOUDFLARE":"1.1.1.1","QUAD9":"9.9.9.9"}
IP_RE=re.compile(r"(?<![\w:])(?:\d{1,3}\.){3}\d{1,3}(?![\w:])")

def now(): return datetime.now(timezone.utc).astimezone().isoformat()
def public_ips(values):
    out=[]
    for x in values:
        try:
            ip=ipaddress.ip_address(x)
            if ip.is_global: out.append(str(ip))
        except ValueError: pass
    return sorted(set(out))
def system_lookup(name):
    try:
        return sorted(set(x[4][0] for x in socket.getaddrinfo(name,None)))
    except Exception:
        return []
def explicit_lookup(name,server):
    try:
        p=subprocess.run(["nslookup",name,server],capture_output=True,text=True,timeout=8,errors="replace")
        ips=IP_RE.findall((p.stdout or "")+"\n"+(p.stderr or ""))
        return sorted(set(x for x in ips if x!=server))
    except Exception:
        return []
def main():
    domains={}
    risk=[]
    for d in DOMAINS:
        sys_all=system_lookup(d); sys_pub=public_ips(sys_all)
        indep={}
        for label,server in RESOLVERS.items():
            raw=explicit_lookup(d,server)
            indep[label]={"server":server,"raw":raw,"public":public_ips(raw)}
        if not sys_pub: risk.append({"domain":d,"reason":"SYSTEM_RESOLVER_NO_PUBLIC_IP","raw":sys_all})
        for label,v in indep.items():
            if not v["public"]: risk.append({"domain":d,"reason":label+"_NO_PUBLIC_IP","raw":v["raw"]})
        domains[d]={"system":{"raw":sys_all,"public":sys_pub},"independent":indep}
    state={
      "schema":"FAITH_SHIELD_DNS_ZERO_DAY/1.0",
      "observed_at":now(),
      "semantics":"ZERO_DAY = bootstrap origin of defensive DNS observation; NOT exploit discovery/use",
      "mode":"DEFENSIVE_OBSERVATION_NO_DNS_MUTATION",
      "critical_domains":DOMAINS,
      "independent_resolvers":RESOLVERS,
      "domains":domains,
      "risk_flags":risk,
      "healthy":len(risk)==0,
      "guard":"If risk_flags is non-empty, do not use DNS-dependent destructive mutation until a fresh independent readback clears it."
    }
    OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"healthy":state["healthy"],"risk_count":len(risk),"output":str(OUT)},ensure_ascii=False))
if __name__=="__main__": main()
