from __future__ import annotations
import json, re, sys

TERMS={
 "commit":"mốc ghi lên Git/GitHub",
 "branch":"nhánh",
 "readback":"đọc ngược để xác nhận hậu quả",
 "receipt":"biên nhận/vật chứng",
 "runtime":"lớp đang chạy",
 "provider":"dịch vụ/đích thật",
 "carrier":"vật mang",
 "daemon":"tiến trình chạy nền",
 "repository":"kho mã nguồn",
 "repo":"kho mã nguồn",
 "state":"trạng thái",
 "pointer":"con trỏ định vị",
 "sync":"đồng bộ",
 "closed":"khép kín",
 "verified":"đã được kiểm chứng"
}

def inspect(text:str):
    s=text.strip()
    low=s.lower()
    found=[]
    for k,v in TERMS.items():
        if re.search(r'(?<![\w./-])'+re.escape(k)+r'(?![\w./-])',low):
            found.append({"term":k,"meaning":v})
    starts_with_technical=False
    for k in TERMS:
        if re.match(r'^'+re.escape(k)+r'(?![\w./-])',low):
            starts_with_technical=True
            break
    return {
        "plain_vietnamese_first": bool(s) and not starts_with_technical,
        "technical_terms":found,
        "needs_explanation": bool(found),
        "starts_with_technical_term":starts_with_technical
    }

if __name__=="__main__":
    text=" ".join(sys.argv[1:]) if len(sys.argv)>1 else sys.stdin.read()
    print(json.dumps(inspect(text),ensure_ascii=False,indent=2))
