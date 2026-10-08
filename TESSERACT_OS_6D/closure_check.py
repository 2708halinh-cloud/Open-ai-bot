import json
from pathlib import Path

p=Path(__file__).with_name("FACE_RECEIPTS_CURRENT.json")
d=json.loads(p.read_text(encoding="utf-8"))
expected={str(i) for i in range(1,7)}
faces=d.get("faces",{})
if set(faces)!=expected:
    d["closed"]=False
    d["error"]="FACE_SET_MISMATCH"
else:
    state_digest=d["state_object"]["center_digest_sha256"]
    for v in faces.values():
        state_ok=(v.get("verification_state")=="VERIFIED_ACTIVE")
        receipt_ok=bool(v.get("receipt"))
        readback=v.get("readback") or {}
        readback_ok=(readback.get("verified") is True)
        same_state=(v.get("state_digest_sha256")==state_digest)
        v["closed"]=bool(state_ok and receipt_ok and readback_ok and same_state)
    d["closed"]=all(v["closed"] for v in faces.values())
    d["closed_faces"]=sum(1 for v in faces.values() if v["closed"])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"closed":d["closed"],"closed_faces":d.get("closed_faces",0),"faces":{k:v["closed"] for k,v in faces.items()}},ensure_ascii=False))
