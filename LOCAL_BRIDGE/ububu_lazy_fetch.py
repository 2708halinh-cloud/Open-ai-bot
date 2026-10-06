#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, sys
from pathlib import Path

DEFAULT_TERMS = [
    "Gemini-Sự tiến hóa hệ thần kinh sứa-20261006-2120.txt",
    "HÀ LINH XUẤT TAY",
    "20261006-2120",
    "hệ thần kinh sứa",
]
CHUNK_RE = re.compile(r"meta_chunk_\d+\.tb", re.I)
MAX_CHUNK_BYTES = 64 * 1024 * 1024

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def candidate_indexes():
    seen = set()
    env = os.environ.get("UBUBU_META_INDEX")
    fixed = [
        env,
        "/mnt/g/OS_Workspace/UBUBU/meta_tb_index.json",
        "/mnt/g/Drive của tôi/.codex/UBUBU/meta_tb_index.json",
        "/mnt/w/Drive của tôi/.codex/UBUBU/meta_tb_index.json",
        "/mnt/d/PHÒNG CHỈ HUY/.codex/UBUBU/meta_tb_index.json",
        "/mnt/c/Users/halin/GGDV_UNIFIED/.vscode/UBUBU/meta_tb_index.json",
    ]
    for x in fixed:
        if not x: continue
        p = Path(x)
        if p not in seen:
            seen.add(p); yield p
    roots = [
        Path("/mnt/g/OS_Workspace"),
        Path("/mnt/g/Drive của tôi/.Assistant/LONG MẠCH SOL - HẬU THIÊN TĨNH/BRAIN_OS"),
        Path("/mnt/w/Drive của tôi/.Assistant/LONG MẠCH SOL - HẬU THIÊN TĨNH/BRAIN_OS"),
        Path("/mnt/d/PHÒNG CHỈ HUY/.codex"),
        Path("/mnt/c/Users/halin/GGDV_UNIFIED"),
    ]
    for root in roots:
        if not root.exists(): continue
        try:
            for p in root.rglob("meta_tb_index.json"):
                if p not in seen:
                    seen.add(p); yield p
        except Exception:
            pass

def scalar_text(obj):
    if isinstance(obj, dict):
        return " ".join(scalar_text(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(scalar_text(v) for v in obj)
    if obj is None:
        return ""
    return str(obj)

def walk(obj, path="$"):
    yield path, obj
    if isinstance(obj, dict):
        for k,v in obj.items():
            yield from walk(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")

def extract_refs(node):
    refs = []
    if isinstance(node, dict):
        for k,v in node.items():
            key = str(k).lower()
            if isinstance(v, str):
                for m in CHUNK_RE.findall(v):
                    refs.append(m)
            if key in {"chunk","chunk_file","chunk_name","file","filename","path"} and isinstance(v,str):
                m = CHUNK_RE.search(v)
                if m: refs.append(m.group(0))
    return sorted(set(refs))

def extract_anchor(node):
    out = {}
    if isinstance(node, dict):
        for key in ("anchor_start","anchor_end","start","end","offset_start","offset_end"):
            if key in node and isinstance(node[key], (int,float)):
                out[key] = int(node[key])
    return out

def read_chunk(chunk: Path, terms, anchor):
    size = chunk.stat().st_size
    if size > MAX_CHUNK_BYTES and not anchor:
        return {"path":str(chunk),"size":size,"state":"SKIPPED_NO_ANCHOR_CHUNK_TOO_LARGE"}
    start = anchor.get("anchor_start", anchor.get("offset_start", anchor.get("start", 0)))
    end = anchor.get("anchor_end", anchor.get("offset_end", anchor.get("end", None)))
    if end is None:
        end = min(size, start + MAX_CHUNK_BYTES)
    start = max(0, min(start, size))
    end = max(start, min(end, size))
    # keep a small context margin around the indexed slice
    lo = max(0, start - 4096)
    hi = min(size, end + 4096)
    with chunk.open("rb") as f:
        f.seek(lo)
        data = f.read(hi-lo)
    text = data.decode("utf-8", errors="replace")
    hits = []
    low = text.lower()
    for term in terms:
        pos = 0
        tl = term.lower()
        while True:
            i = low.find(tl, pos)
            if i < 0: break
            hits.append({
                "term":term,
                "absolute_offset_approx":lo+i,
                "excerpt":text[max(0,i-1200):min(len(text),i+4000)]
            })
            pos = i + len(tl)
            if len(hits) >= 50: break
    return {
        "path":str(chunk),
        "size":size,
        "sha256":sha256_file(chunk),
        "slice":[lo,hi],
        "hits":hits,
        "state":"READ"
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", action="append", default=[])
    ap.add_argument("--receipt", default=".runtime/UBUBU_LAZY_FETCH_CURRENT.json")
    args = ap.parse_args()
    terms = args.query or DEFAULT_TERMS

    indexes = [p for p in candidate_indexes() if p.exists() and p.is_file()]
    receipt = {
        "schema":"UBUBU_LAZY_FETCH/1.0",
        "policy":"INDEX_FIRST_CHUNK_ONLY_NEVER_META_DB",
        "queries":terms,
        "indexes":[str(p) for p in indexes],
        "matches":[],
        "chunks":[]
    }
    if not indexes:
        receipt["state"] = "OPEN_INDEX_NOT_FOUND_ON_MOUNTED_LOCAL_CARRIERS"
    else:
        idx = indexes[0]
        raw = idx.read_bytes()
        receipt["index"] = {
            "path":str(idx),"size":len(raw),
            "sha256":hashlib.sha256(raw).hexdigest()
        }
        doc = json.loads(raw.decode("utf-8"))
        match_nodes = []
        for jpath,node in walk(doc):
            st = scalar_text(node)
            if any(t.lower() in st.lower() for t in terms):
                refs = extract_refs(node)
                anc = extract_anchor(node)
                if refs or anc or isinstance(node,dict):
                    item={"json_path":jpath,"chunk_refs":refs,"anchor":anc}
                    match_nodes.append((item,node))
                    receipt["matches"].append(item)
                    if len(match_nodes) >= 200: break

        # Only chunk refs from matched index nodes are eligible.
        seen = set()
        chunks_root = idx.parent / "meta_chunks"
        for item,node in match_nodes:
            for ref in item["chunk_refs"]:
                if ref in seen: continue
                seen.add(ref)
                p = chunks_root / ref
                if p.exists() and p.is_file():
                    receipt["chunks"].append(read_chunk(p, terms, item["anchor"]))
                else:
                    receipt["chunks"].append({"path":str(p),"state":"REFERENCED_CHUNK_NOT_FOUND"})
        receipt["state"] = "INDEX_READ_CHUNKS_RESOLVED" if receipt["chunks"] else "INDEX_READ_NO_CHUNK_MATCH"

    out = Path(args.receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt.get("state") in {"INDEX_READ_CHUNKS_RESOLVED","INDEX_READ_NO_CHUNK_MATCH"} else 2

if __name__ == "__main__":
    raise SystemExit(main())
