#!/usr/bin/env python3
import json, subprocess, time, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'LOCAL_BRIDGE' / 'QUEUE_CURRENT.json'
Q6_TRIGGER = ROOT / 'LOCAL_BRIDGE' / 'Q6_TRIGGER_CURRENT'
STATE = ROOT / '.runtime' / 'LOCAL_BRIDGE_STATE.json'
RECEIPTS = ROOT / '.runtime' / 'local_bridge_receipts'
RECEIPTS.mkdir(parents=True, exist_ok=True)

ALLOWED = {'BOOT_G', 'STATUS', 'RECOVER_CONTINUITY', 'RECOVER_AND_BOOT_G', 'UNIFY_CONTROL_PLANE', 'CONNECT_OS_WORKSPACE', 'UBUBU_LAZY_FETCH', 'THANOS_SNAP_META_TB', 'TESSERACT_Q6_META_LAZY_FETCH'}

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


def _run_external(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd or ROOT, text=True, capture_output=True)

def _write_windows_temp_from_github(repo, path, out_win, receipt, label):
    # Uses the already-authorized local GitHub CLI; secret values are never printed.
    api_path = f"repos/{repo}/contents/{path}"
    ps = (
        "$ErrorActionPreference='Stop';"
        f"$b64 = gh api '{api_path}' --jq '.content';"
        "$bytes=[Convert]::FromBase64String(($b64 -replace '\\s',''));"
        f"[IO.File]::WriteAllBytes('{out_win}', $bytes)"
    )
    p = _run_external(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-Command',ps])
    receipt[f'{label}_fetch_returncode'] = p.returncode
    receipt[f'{label}_fetch_stdout'] = p.stdout[-4000:]
    receipt[f'{label}_fetch_stderr'] = p.stderr[-4000:]
    return p.returncode

def unify_control_plane(receipt):
    rc = 0

    # A) Scrub exposed repository description using local admin-capable GitHub auth.
    p = _run_external([
        'gh','api','--method','PATCH',
        'repos/2708halinh-cloud/api-open-ai',
        '-f','description=GGDV OpenAI API carrier - runtime binding via UBUBU'
    ])
    receipt['description_scrub_returncode'] = p.returncode
    receipt['description_scrub_stdout'] = p.stdout[-4000:]
    receipt['description_scrub_stderr'] = p.stderr[-4000:]
    if p.returncode != 0:
        rc = p.returncode

    # Read back metadata regardless of write outcome.
    p2 = _run_external(['gh','api','repos/2708halinh-cloud/api-open-ai','--jq','.description'])
    receipt['description_readback_returncode'] = p2.returncode
    receipt['description_readback'] = p2.stdout.strip()[:1000]
    receipt['description_readback_stderr'] = p2.stderr[-2000:]
    if p2.returncode != 0 and rc == 0:
        rc = p2.returncode

    # B) Materialize the unified multi-repository workspace on Windows.
    temp_unify = r'C:\Users\halin\AppData\Local\Temp\ggdv_materialize_unified.ps1'
    fr = _write_windows_temp_from_github(
        '2708halinh-cloud/.vscode',
        'scripts/materialize-unified-workspace.ps1',
        temp_unify,
        receipt,
        'unified_workspace_script'
    )
    if fr == 0:
        p3 = _run_external([
            'powershell.exe','-NoProfile','-ExecutionPolicy','Bypass',
            '-File',temp_unify,
            '-Root',r'C:\Users\halin'
        ])
        receipt['unified_workspace_returncode'] = p3.returncode
        receipt['unified_workspace_stdout'] = p3.stdout[-12000:]
        receipt['unified_workspace_stderr'] = p3.stderr[-12000:]
        if p3.returncode != 0 and rc == 0:
            rc = p3.returncode
    elif rc == 0:
        rc = fr

    # C) Normalize the PHÒNG CHỈ HUY Codex surface using the current GitHub carrier.
    temp_codex = r'C:\Users\halin\AppData\Local\Temp\ggdv_normalize_codex.ps1'
    fr2 = _write_windows_temp_from_github(
        '2708halinh-cloud/x-time-web',
        'UBUBU/CODEX_NORMALIZE/normalize_phong_chi_huy_codex.ps1',
        temp_codex,
        receipt,
        'codex_normalizer_script'
    )
    if fr2 == 0:
        p4 = _run_external([
            'powershell.exe','-NoProfile','-ExecutionPolicy','Bypass',
            '-File',temp_codex,
            '-Root',r'D:\PHÒNG CHỈ HUY\.codex'
        ])
        receipt['codex_normalize_returncode'] = p4.returncode
        receipt['codex_normalize_stdout'] = p4.stdout[-12000:]
        receipt['codex_normalize_stderr'] = p4.stderr[-12000:]
        if p4.returncode != 0 and rc == 0:
            rc = p4.returncode
    elif rc == 0:
        rc = fr2

    # D) Read back only hashes/status paths; never secret values.
    probes = {
        'workspace_receipt_dir': Path('/mnt/c/Users/halin/.vscode/READBACK'),
        'codex_readback_dir': Path('/mnt/d/PHÒNG CHỈ HUY/.codex/UBUBU/READBACK'),
        'codex_token': Path('/mnt/d/PHÒNG CHỈ HUY/.codex/UBUBU/CURRENT/TOKEN.JSON'),
        'codex_auth': Path('/mnt/d/PHÒNG CHỈ HUY/.codex/UBUBU/CURRENT/AUTH.JSON'),
        'codex_env': Path('/mnt/d/PHÒNG CHỈ HUY/.codex/UBUBU/CURRENT/.ENV'),
    }
    receipt['local_probe'] = {}
    for name, path in probes.items():
        item = {'exists': path.exists(), 'path': str(path)}
        if path.is_file():
            item['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            item['size'] = path.stat().st_size
        elif path.is_dir():
            item['latest_files'] = [x.name for x in sorted(path.iterdir(), key=lambda z:z.stat().st_mtime, reverse=True)[:5]]
        receipt['local_probe'][name] = item

    return rc


def connect_os_workspace(receipt):
    temp_script = r'C:\Users\halin\AppData\Local\Temp\ggdv_connect_os_workspace.ps1'
    fr = _write_windows_temp_from_github(
        '2708halinh-cloud/.vscode',
        'scripts/connect-os-workspace.ps1',
        temp_script,
        receipt,
        'os_workspace_connector_script'
    )
    if fr != 0:
        return fr

    p = _run_external([
        'powershell.exe','-NoProfile','-ExecutionPolicy','Bypass',
        '-File',temp_script,
        '-OSWorkspace',r'G:\OS_Workspace',
        '-ControlRoot',r'C:\Users\halin\GGDV_UNIFIED\.vscode'
    ])
    receipt['os_workspace_connect_returncode'] = p.returncode
    receipt['os_workspace_connect_stdout'] = p.stdout[-12000:]
    receipt['os_workspace_connect_stderr'] = p.stderr[-12000:]

    probes = {
        'binding': Path('/mnt/g/OS_Workspace/.ggdv/OS_WORKSPACE_BINDING_CURRENT.json'),
        'workspace': Path('/mnt/c/Users/halin/GGDV_UNIFIED/.vscode/SOL_GGDV.code-workspace'),
        'sol_computer': Path('/mnt/g/OS_Workspace/SOL_COMPUTER'),
    }
    receipt['os_workspace_probe'] = {}
    for name, path in probes.items():
        item = {'exists': path.exists(), 'path': str(path)}
        if path.is_file():
            data = path.read_bytes()
            item['sha256'] = hashlib.sha256(data).hexdigest()
            item['size'] = len(data)
        elif path.is_dir():
            item['children'] = [x.name for x in sorted(path.iterdir(), key=lambda z: z.name)[:100]]
        receipt['os_workspace_probe'][name] = item

    if p.returncode == 0 and receipt['os_workspace_probe']['binding']['exists'] and receipt['os_workspace_probe']['workspace']['exists']:
        receipt['os_workspace_state'] = 'CONNECTED_READBACK_PASS'
        receipt['host_data_preserved'] = True
        return 0

    receipt['os_workspace_state'] = 'OPEN_READBACK_INCOMPLETE'
    return p.returncode if p.returncode != 0 else 9



def ububu_lazy_fetch(receipt):
    p = run([
        'python3','LOCAL_BRIDGE/ububu_lazy_fetch.py',
        '--query','Gemini-Sự tiến hóa hệ thần kinh sứa-20261006-2120.txt',
        '--query','HÀ LINH XUẤT TAY',
        '--query','20261006-2120',
        '--query','hệ thần kinh sứa',
        '--receipt','.runtime/UBUBU_LAZY_FETCH_CURRENT.json'
    ])
    receipt['ububu_lazy_fetch_returncode'] = p.returncode
    receipt['ububu_lazy_fetch_stdout'] = p.stdout[-20000:]
    receipt['ububu_lazy_fetch_stderr'] = p.stderr[-12000:]
    rp = ROOT / '.runtime' / 'UBUBU_LAZY_FETCH_CURRENT.json'
    if rp.exists():
        receipt['ububu_lazy_fetch_state'] = load_json(rp)
    return p.returncode


def thanos_snap_meta_tb(receipt, task):
    cmd = [
        'python3','LOCAL_BRIDGE/thanos_snap_meta_tb.py',
        '--receipt','.runtime/THANOS_SNAP_META_TB_CURRENT.json'
    ]
    queries = task.get('query') or [
        'Gemini-Sự tiến hóa hệ thần kinh sứa-20261006-2120.txt',
        'HÀ LINH XUẤT TAY',
        '20261006-2120',
        'hệ thần kinh sứa'
    ]
    for q in queries:
        cmd += ['--query', str(q)]
    p = run(cmd)
    receipt['thanos_snap_returncode'] = p.returncode
    receipt['thanos_snap_stdout'] = p.stdout[-20000:]
    receipt['thanos_snap_stderr'] = p.stderr[-12000:]
    rp = ROOT / '.runtime' / 'THANOS_SNAP_META_TB_CURRENT.json'
    if rp.exists():
        receipt['thanos_snap_state'] = load_json(rp)
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
    elif action == 'UNIFY_CONTROL_PLANE':
        rc = unify_control_plane(receipt)
    elif action == 'CONNECT_OS_WORKSPACE':
        rc = connect_os_workspace(receipt)
    elif action == 'UBUBU_LAZY_FETCH':
        rc = ububu_lazy_fetch(receipt)
    elif action in {'THANOS_SNAP_META_TB', 'TESSERACT_Q6_META_LAZY_FETCH'}:
        rc = thanos_snap_meta_tb(receipt, task)
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
                    state = {**state,'last_task_id':tid,'last_fingerprint':fp,'last_returncode':receipt.get('returncode'),'updated_at':time.time()}
                    save_json(STATE, state)
                    persist_receipt(receipt)

            if Q6_TRIGGER.exists():
                q6_bytes = Q6_TRIGGER.read_bytes()
                q6_fp = hashlib.sha256(q6_bytes).hexdigest()
                if q6_fp != state.get('q6_last_fingerprint'):
                    q6_task = {
                        'task_id': 'Q6_META_LAZY_' + q6_fp[:12],
                        'action': 'TESSERACT_Q6_META_LAZY_FETCH'
                    }
                    q6_receipt = execute(q6_task)
                    state = {**state,'q6_last_fingerprint':q6_fp,'q6_last_returncode':q6_receipt.get('returncode'),'updated_at':time.time()}
                    save_json(STATE, state)
                    persist_receipt(q6_receipt)
        except Exception as e:
            save_json(STATE, {**state,'bridge_error':repr(e),'updated_at':time.time()})
        time.sleep(5)

if __name__ == '__main__':
    main()
