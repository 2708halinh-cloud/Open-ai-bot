#!/usr/bin/env python3
import json, subprocess, time, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'LOCAL_BRIDGE' / 'QUEUE_CURRENT.json'
STATE = ROOT / '.runtime' / 'LOCAL_BRIDGE_STATE.json'
RECEIPTS = ROOT / '.runtime' / 'local_bridge_receipts'
RECEIPTS.mkdir(parents=True, exist_ok=True)

ALLOWED = {'BOOT_G', 'STATUS', 'RECOVER_CONTINUITY', 'RECOVER_AND_BOOT_G'}

def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, **kw)

def pull():
    p = run(['git','pull','--ff-only'])
    return p.returncode == 0

def load_json(p):
    return json.loads(p.read_text(encoding='utf-8'))

def save_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(p)

def task_fingerprint(task):
    raw = json.dumps(task, sort_keys=True, separators=(',',':')).encode()
    return hashlib.sha256(raw).hexdigest()

def recover(receipt):
    p = run(['python3','RECOVERY/recover_continuity.py'])
    receipt['recovery_returncode'] = p.returncode
    receipt['recovery_stdout'] = p.stdout[-12000:]
    receipt['recovery_stderr'] = p.stderr[-12000:]
    state_path = ROOT / '.runtime' / 'RECOVERY_STATE_CURRENT.json'
    if state_path.exists():
        receipt['recovery_state'] = load_json(state_path)
    return p.returncode

def boot_g(receipt):
    p = run(['bash','terminal/tesseract_boot_g_from_wsl.sh'])
    receipt['boot_returncode'] = p.returncode
    receipt['boot_stdout'] = p.stdout[-12000:]
    receipt['boot_stderr'] = p.stderr[-12000:]
    boot_receipt = ROOT / '.runtime' / 'BOOT_RECEIPT_G.json'
    if boot_receipt.exists():
        receipt['boot_receipt'] = load_json(boot_receipt)
    return p.returncode

def execute(task):
    action = task.get('action')
    task_id = task.get('task_id')
    if action not in ALLOWED: raise RuntimeError(f'forbidden action: {action}')
    receipt = {'task_id':task_id,'action':action,'started_at':time.time()}
    rc = 0
    if action == 'STATUS':
        receipt['stdout'] = 'bridge_alive'
    elif action == 'RECOVER_CONTINUITY':
        rc = recover(receipt)
    elif action == 'BOOT_G':
        rc = boot_g(receipt)
    elif action == 'RECOVER_AND_BOOT_G':
        rc = recover(receipt)
        if rc == 0:
            rc = boot_g(receipt)
    receipt['returncode'] = rc
    receipt['finished_at'] = time.time()
    return receipt

def persist_receipt(receipt):
    p = RECEIPTS / f"{receipt['task_id']}.json"
    save_json(p, receipt)
    add = [str(p.relative_to(ROOT))]
    for rel in ['.runtime/RECOVERY_STATE_CURRENT.json','.runtime/BOOT_RECEIPT_G.json']:
        if (ROOT/rel).exists():
            add.append(rel)
    run(['git','add',*add])
    c = run(['git','commit','-m',f"LOCAL_BRIDGE receipt {receipt['task_id']}"])
    if c.returncode == 0:
        run(['git','push'])

def main():
    state = {'last_task_id': None, 'last_fingerprint': None}
    if STATE.exists():
        try: state.update(load_json(STATE))
        except Exception: pass
    while True:
        try:
            pull()
            if QUEUE.exists():
                task = load_json(QUEUE)
                tid = task.get('task_id')
                fp = task_fingerprint(task)
                if tid and (tid != state.get('last_task_id') or fp != state.get('last_fingerprint')):
                    receipt = execute(task)
                    state = {'last_task_id':tid,'last_fingerprint':fp,'last_returncode':receipt.get('returncode'),'updated_at':time.time()}
                    save_json(STATE, state)
                    persist_receipt(receipt)
        except Exception as e:
            save_json(STATE, {**state,'bridge_error':repr(e),'updated_at':time.time()})
        time.sleep(5)

if __name__ == '__main__':
    main()
