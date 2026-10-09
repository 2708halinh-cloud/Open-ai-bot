#!/usr/bin/env python3
"""Source-bound Hostinger DMARC publisher. No secrets or raw zone logs."""
import argparse
import json
import os
import re
import sys
from urllib import request,error
from urllib.parse import quote

BASE = "https://developers.hostinger.com"
VALID = re.compile(r"(?i)^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")

def check_domain(d):
    d = d.strip().lower().rstrip(".")
    if not VALID.fullmatch(d): raise ValueError("invalid domain")
    return d

def check_mail(m, d):
    if not re.fullmatch(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+",m):
        raise ValueError("invalid DMARC mailbox")
    if m.lower().rsplit("@",1)[-1] != d:
        raise ValueError("external rua domain requires extra DNS authorization")
    return m.lower()

def api(method,path,data=None):
    key=os.environ.get("HOSTINGER_API_TOKEN","").strip()
    if not key: raise RuntimeError("HOSTINGER_API_TOKEN not bound")
    payload=None if data is None else json.dumps(data).encode("utf8")
    h={"Authorization":"Bearer "+key,"Accept":"application/json"}
    if payload is not None:h["Content-Type"]="application/json"
    r=request.Request(BASE+path,data=payload,headers=h,method=method)
    try:
        with request.urlopen(r,timeout=18) as ans:
            buf=ans.read(2_000_000)
            return json.loads(buf) if buf else {}
    except error.HTTPError as e:
        raise RuntimeError("Hostinger HTTP "+str(e.code)) from None
    except error.URLError:
        raise RuntimeError("Hostinger provider unreachable") from None

def inspect(zone,domain):
    if not isinstance(zone,list):raise ValueError("unknown provider DNS zone shape")
    found={"dmarc":[],"spf":False,"dkim_candidate":False,"mx":False}
    for row in zone:
        if not isinstance(row,dict):continue
        name=str(row.get("name","")).lower().rstrip(".")
        typ=str(row.get("type","")).upper()
        content=[str(r.get("content","")).strip('"') for r in row.get("records",[]) if isinstance(r,dict) and not r.get("is_disabled")]
        if name in ("_dmarc","_dmarc."+domain) and typ=="TXT":
            found["dmarc"] += [v for v in content if v.lower().startswith("v=dmarc1")]
        if name in ("@","",domain) and typ=="TXT":
            found["spf"] |= any(v.lower().startswith("v=spf1") for v in content)
        if "_domainkey" in name and typ in ("TXT","CNAME"):
            found["dkim_candidate"] |= bool(content)
        if name in ("@","",domain) and typ=="MX":
            found["mx"] |= bool(content)
    return found

def proposed(rua):
    return {"overwrite":False,"zone":[{"name":"_dmarc","type":"TXT","ttl":3600,
        "records":[{"content":"v=DMARC1; p=none; rua=mailto:"+rua+"; pct=100"}]}]}

def run(domain,mail,apply=False,mailbox_ok=False,auth_ok=False,api_fn=api):
    d=check_domain(domain)
    m=check_mail(mail,d)
    path="/api/dns/v1/zones/"+quote(d,safe="")
    old=inspect(api_fn("GET",path),d)
    result={"domain":d,"source":"HOSTINGER_API","existing_dmarc":bool(old["dmarc"]),
            "spf_seen":old["spf"],"dkim_candidate_seen":old["dkim_candidate"],
            "mx_seen":old["mx"],"applied":False,"readback":False}
    if old["dmarc"]:
        result["state"]="EXISTING_DMARC_PRESERVED"
        return result
    if not (old["spf"] or old["dkim_candidate"]):
        result["state"]="SPF_DKIM_NOT_VISIBLE"
        return result
    payload=proposed(m)
    result["proposed_txt"]=payload["zone"][0]["records"][0]["content"]
    if not apply:
        result["state"]="PLAN_ONLY"
        return result
    if not mailbox_ok or not auth_ok:
        raise ValueError("mailbox and SPF/DKIM checks required before update")
    api_fn("POST",path+"/validate",payload)
    api_fn("PUT",path,payload)
    new=inspect(api_fn("GET",path),d)
    result["applied"]=True
    result["readback"]=result["proposed_txt"] in new["dmarc"]
    result["state"]="VERIFIED_PROVIDER_READBACK" if result["readback"] else "READBACK_MISMATCH"
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--domain",required=True);p.add_argument("--report-mail",required=True)
    p.add_argument("--apply",action="store_true");p.add_argument("--mailbox-confirmed",action="store_true")
    p.add_argument("--auth-confirmed",action="store_true")
    a=p.parse_args()
    try:print(json.dumps(run(a.domain,a.report_mail,a.apply,a.mailbox_confirmed,a.auth_confirmed),indent=2))
    except (ValueError,RuntimeError) as e:
        print("BLOCKED_DMARС: "+str(e),file=sys.stderr)
        sys.exit(2)
