import json
from pathlib import Path

p=Path(__file__).with_name("FACE_RECEIPTS_CURRENT.json")
d=json.loads(p.read_text(encoding="utf-8"))
faces=d.get("faces",{})
expected={str(i) for i in range(1,7)}
state_digest=(d.get("state_object") or {}).get("center_digest_sha256")

if set(faces) != expected:
    d["closed"]=False
    d["closed_faces"]=0
    d["error"]="FACE_SET_MISMATCH"
else:
    for v in faces.values():
        action=bool((v.get("action") or {}).get("observed"))
        consequence=bool((v.get("consequence") or {}).get("observed"))
        receipt=bool(v.get("receipt"))
        readback=bool(v.get("readback") and (v.get("readback") or {}).get("verified"))
        same_state=bool(state_digest and v.get("state_digest_sha256")==state_digest)
        v["proof_chain"]={
            "action":action,
            "consequence":consequence,
            "receipt":receipt,
            "readback":readback,
            "same_state":same_state
        }
        v["closed"]=all(v["proof_chain"].values())
    d["closed"]=all(v["closed"] for v in faces.values())
    d["closed_faces"]=sum(1 for v in faces.values() if v["closed"])
    d.pop("error",None)

d["conclusion_policy"]="ACTION -> CONSEQUENCE -> RECEIPT -> READBACK -> SAME_STATE -> CONCLUSION"
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({
    "closed":d["closed"],
    "closed_faces":d.get("closed_faces",0),
    "faces":{k:v.get("proof_chain",{}) for k,v in faces.items()}
},ensure_ascii=False))
