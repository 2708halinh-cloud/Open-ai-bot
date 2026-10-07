use base64::Engine as _;
use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
    sync::Mutex,
    time::{SystemTime, UNIX_EPOCH},
};
use tauri::State;

const CURRENT_STATE_SCHEMA: &str = "TESSERACT_DESKTOP_STATE/1.1";

const REQUIRED_SOURCES: [&str; 4] = [
    "R-000",
    "0000_TUYEN_NGON",
    "0000_THE_MASTER_TEACHER",
    "152_ITEM",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Workspace {
    name: String,
    path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Provider {
    kind: String,
    base_url: String,
    model: String,
    api_key_env: String,
}

impl Default for Provider {
    fn default() -> Self {
        Self {
            kind: "openai-compatible".into(),
            base_url: "http://127.0.0.1:8080/v1".into(),
            model: String::new(),
            api_key_env: String::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
struct AppState {
    schema: String,
    enrollment_complete: bool,
    enrollment_sources: Vec<String>,
    account_authenticated: bool,
    kilo_connected: bool,
    kilo_skipped: bool,
    kilo_account_reference: String,
    autonomy_level: String,
    workspaces: Vec<Workspace>,
    provider: Provider,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            schema: CURRENT_STATE_SCHEMA.into(),
            enrollment_complete: false,
            enrollment_sources: vec![],
            account_authenticated: false,
            kilo_connected: false,
            kilo_skipped: false,
            kilo_account_reference: "1eFE4tLmzNOJMkXP25-HecyDbffYqNhJO".into(),
            autonomy_level: "high".into(),
            workspaces: vec![],
            provider: Provider::default(),
        }
    }
}

struct RuntimeState {
    state: Mutex<AppState>,
    path: PathBuf,
}

fn state_path() -> PathBuf {
    let base = dirs::data_local_dir().unwrap_or_else(|| PathBuf::from("."));
    base.join("TESSERACTDesktop").join("CURRENT_STATE.json")
}

fn decode_state(raw: &str) -> Result<AppState, String> {
    let mut state: AppState = serde_json::from_str(raw)
        .map_err(|e| format!("STATE_JSON_INVALID: {e}"))?;

    // Enrollment gates were expanded in schema 1.1. Only a known older schema
    // may be migrated. Unknown/future schemas must stay untouched rather than
    // being destructively downgraded by an older binary.
    match state.schema.as_str() {
        CURRENT_STATE_SCHEMA => {}
        "TESSERACT_DESKTOP_STATE/1.0" => {
            state.schema = CURRENT_STATE_SCHEMA.into();
            state.enrollment_complete = false;
            state.enrollment_sources.clear();
            state.kilo_connected = false;
            state.kilo_skipped = false;
            state.account_authenticated = false;
        }
        other => return Err(format!("STATE_SCHEMA_UNSUPPORTED: {other}")),
    }

    // Kilo authentication is live session evidence, never durable state.
    state.kilo_connected = false;
    state.account_authenticated = false;
    Ok(state)
}

fn read_state(path: &Path) -> (AppState, bool) {
    match fs::read_to_string(path) {
        Ok(raw) => match decode_state(&raw) {
            Ok(state) => (state, true),
            Err(_) => {
                // Preserve the malformed carrier byte-for-byte. Do not overwrite it
                // with defaults; keep a sibling backup for explicit repair/recovery.
                let backup = path.with_extension("json.invalid.bak");
                let _ = fs::copy(path, &backup);
                (AppState::default(), false)
            }
        },
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => (AppState::default(), true),
        Err(_) => (AppState::default(), false),
    }
}

fn persist(runtime: &RuntimeState, value: &AppState) -> Result<(), String> {
    if let Some(parent) = runtime.path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let tmp = runtime.path.with_extension("json.tmp");

    // Persist preferences and enrollment metadata, but never persist a live
    // authentication assertion from an environment/process signal.
    let mut durable = value.clone();
    durable.schema = CURRENT_STATE_SCHEMA.into();
    durable.kilo_connected = false;
    durable.account_authenticated = false;

    fs::write(&tmp, serde_json::to_vec_pretty(&durable).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    fs::rename(tmp, &runtime.path).map_err(|e| e.to_string())
}

fn verify_kilo_receipt_envelope(
    raw: &str,
    expected_account_reference: &str,
    trusted_public_key_b64: &str,
) -> Result<String, String> {
    let envelope: serde_json::Value = serde_json::from_str(raw)
        .map_err(|e| format!("KILO_SESSION_RECEIPT_INVALID_JSON: {e}"))?;
    if envelope["schema"].as_str() != Some("XTIME_KILO_SESSION_RECEIPT/2.0") {
        return Err("KILO_SESSION_RECEIPT_SCHEMA_UNTRUSTED".into());
    }

    let payload_b64 = envelope["signed_payload_b64"]
        .as_str()
        .ok_or_else(|| "KILO_SIGNED_PAYLOAD_MISSING".to_string())?;
    let signature_b64 = envelope["signature_b64"]
        .as_str()
        .ok_or_else(|| "KILO_SIGNATURE_MISSING".to_string())?;

    let decoder = base64::engine::general_purpose::STANDARD;
    let public_key_bytes = decoder
        .decode(trusted_public_key_b64.trim())
        .map_err(|_| "KILO_TRUST_PUBLIC_KEY_INVALID_BASE64".to_string())?;
    let public_key: [u8; 32] = public_key_bytes
        .try_into()
        .map_err(|_| "KILO_TRUST_PUBLIC_KEY_INVALID_LENGTH".to_string())?;
    let verifying_key = VerifyingKey::from_bytes(&public_key)
        .map_err(|_| "KILO_TRUST_PUBLIC_KEY_INVALID".to_string())?;

    let payload = decoder
        .decode(payload_b64)
        .map_err(|_| "KILO_SIGNED_PAYLOAD_INVALID_BASE64".to_string())?;
    let signature_bytes = decoder
        .decode(signature_b64)
        .map_err(|_| "KILO_SIGNATURE_INVALID_BASE64".to_string())?;
    let signature_array: [u8; 64] = signature_bytes
        .try_into()
        .map_err(|_| "KILO_SIGNATURE_INVALID_LENGTH".to_string())?;
    let signature = Signature::from_bytes(&signature_array);

    verifying_key
        .verify(&payload, &signature)
        .map_err(|_| "KILO_SIGNATURE_VERIFICATION_FAILED".to_string())?;

    let value: serde_json::Value = serde_json::from_slice(&payload)
        .map_err(|e| format!("KILO_SIGNED_PAYLOAD_INVALID_JSON: {e}"))?;
    if value["issuer"].as_str() != Some("KILO_XTIME") {
        return Err("KILO_ISSUER_MISMATCH".into());
    }
    if value["account_reference"].as_str() != Some(expected_account_reference) {
        return Err("KILO_ACCOUNT_REFERENCE_MISMATCH".into());
    }
    if value["authenticated"].as_bool() != Some(true) {
        return Err("KILO_SESSION_NOT_AUTHENTICATED".into());
    }
    let session_id = value["session_id"].as_str().unwrap_or("").trim();
    if session_id.is_empty() {
        return Err("KILO_SESSION_ID_MISSING".into());
    }
    let expires_at = value["expires_at_unix"]
        .as_u64()
        .ok_or_else(|| "KILO_SESSION_EXPIRY_MISSING".to_string())?;
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_secs();
    if expires_at <= now {
        return Err("KILO_SESSION_EXPIRED".into());
    }

    let mut hasher = Sha256::new();
    hasher.update(raw.as_bytes());
    Ok(format!("{:x}", hasher.finalize()))
}

fn validate_kilo_session_receipt(expected_account_reference: &str) -> Result<String, String> {
    let connected = std::env::var("XTIME_KILO_CONNECTED")
        .map(|v| v == "1" || v.eq_ignore_ascii_case("true"))
        .unwrap_or(false);
    if !connected {
        return Err("KILO_PROCESS_SIGNAL_MISSING".into());
    }

    let trusted_public_key_b64 = option_env!("XTIME_KILO_RECEIPT_ED25519_PUBLIC_KEY_B64")
        .filter(|v| !v.trim().is_empty())
        .ok_or_else(|| "KILO_TRUSTED_ISSUER_KEY_NOT_CONFIGURED_AT_BUILD".to_string())?;
    let receipt_path = std::env::var("XTIME_KILO_SESSION_RECEIPT_PATH")
        .map_err(|_| "KILO_SESSION_RECEIPT_PATH_MISSING".to_string())?;
    let raw = fs::read_to_string(&receipt_path)
        .map_err(|e| format!("KILO_SESSION_RECEIPT_UNREADABLE: {e}"))?;

    verify_kilo_receipt_envelope(&raw, expected_account_reference, trusted_public_key_b64)
}

fn autonomy_policy(level: &str) -> &'static str {
    match level {
        "manual" => "AUTONOMY=manual: do not self-continue into additional actions; keep one explicit user-directed step at a time and never claim automatic execution.",
        "balanced" => "AUTONOMY=balanced: continue safe analysis/read-only work, but require explicit confirmation before state-changing actions not already directly requested.",
        _ => "AUTONOMY=high: continue self-owned safe/reversible work within the current objective and evidence boundary; do not stop at report/status while a grounded next step exists.",
    }
}

fn provider_requires_kilo(provider: &Provider) -> bool {
    let Ok(url) = reqwest::Url::parse(provider.base_url.trim()) else {
        return false;
    };
    let Some(host) = url.host_str() else {
        return false;
    };
    let host = host.trim_matches(|c| c == '[' || c == ']');
    if host.eq_ignore_ascii_case("localhost") {
        return true;
    }
    host.parse::<std::net::IpAddr>()
        .map(|ip| ip.is_loopback())
        .unwrap_or(false)
}

fn canonical(path: &str) -> Result<PathBuf, String> {
    PathBuf::from(path)
        .canonicalize()
        .map_err(|e| format!("PATH_NOT_AVAILABLE: {path}: {e}"))
}

fn ensure_scoped(runtime: &RuntimeState, requested: &str) -> Result<PathBuf, String> {
    let req = canonical(requested)?;
    let state = runtime.state.lock().map_err(|_| "STATE_LOCK".to_string())?;
    let ok = state.workspaces.iter().any(|w| {
        canonical(&w.path)
            .map(|root| req.starts_with(root))
            .unwrap_or(false)
    });
    if ok {
        Ok(req)
    } else {
        Err(format!("OUTSIDE_WORKSPACE_SCOPE: {}", req.display()))
    }
}

#[tauri::command]
fn load_state(runtime: State<'_, RuntimeState>) -> Result<AppState, String> {
    runtime
        .state
        .lock()
        .map(|s| s.clone())
        .map_err(|_| "STATE_LOCK".into())
}

#[tauri::command]
fn complete_enrollment(
    source_ids: Vec<String>,
    runtime: State<'_, RuntimeState>,
) -> Result<AppState, String> {
    let mut normalized = source_ids;
    normalized.sort();
    normalized.dedup();
    let mut required = REQUIRED_SOURCES.iter().map(|s| s.to_string()).collect::<Vec<_>>();
    required.sort();
    if normalized != required {
        return Err("ENROLLMENT_GATE_INCOMPLETE".into());
    }
    let mut state = runtime.state.lock().map_err(|_| "STATE_LOCK".to_string())?;
    if !(state.kilo_connected || state.kilo_skipped) {
        return Err("Hãy kết nối Kilo/X-TiMe hoặc chọn Bỏ qua".into());
    }
    if state.workspaces.is_empty() {
        return Err("Cần ít nhất một workspace trước khi hoàn tất nhập ngũ".into());
    }
    state.enrollment_complete = true;
    state.enrollment_sources = REQUIRED_SOURCES.iter().map(|s| s.to_string()).collect();
    persist(&runtime, &state)?;
    Ok(state.clone())
}


#[tauri::command]
fn begin_kilo_connect() -> Result<String, String> {
    let url = std::env::var("XTIME_KILO_AUTH_URL")
        .or_else(|_| std::env::var("KILO_AUTH_URL"))
        .map_err(|_| "Chưa có địa chỉ đăng nhập Kilo/X-TiMe trên máy này; có thể Bỏ qua và kết nối sau.".to_string())?;
    if !(url.starts_with("https://") || url.starts_with("http://")) {
        return Err("Địa chỉ đăng nhập Kilo/X-TiMe không hợp lệ".into());
    }
    open::that(url).map_err(|e| e.to_string())?;
    Ok("Đã mở cổng đăng nhập Kilo/X-TiMe.".into())
}

#[tauri::command]
fn verify_kilo_session(runtime: State<'_, RuntimeState>) -> Result<AppState, String> {
    verify_kilo(runtime)
}

#[tauri::command]
fn skip_kilo(runtime: State<'_, RuntimeState>) -> Result<AppState, String> {
    let mut state = runtime.state.lock().map_err(|_| "Không khóa được trạng thái ứng dụng".to_string())?;
    state.kilo_connected = false;
    state.kilo_skipped = true;
    state.account_authenticated = false;
    persist(&runtime, &state)?;
    Ok(state.clone())
}

#[tauri::command]
fn verify_kilo(runtime: State<'_, RuntimeState>) -> Result<AppState, String> {
    let account_reference = runtime
        .state
        .lock()
        .map_err(|_| "Không khóa được trạng thái ứng dụng".to_string())?
        .kilo_account_reference
        .clone();
    let _receipt_hash = validate_kilo_session_receipt(&account_reference)?;
    let mut state = runtime.state.lock().map_err(|_| "Không khóa được trạng thái ứng dụng".to_string())?;
    state.kilo_connected = true;
    state.kilo_skipped = false;
    state.account_authenticated = true;
    // persist() deliberately strips the ephemeral authentication assertion.
    persist(&runtime, &state)?;
    Ok(state.clone())
}

#[tauri::command]
fn set_autonomy(level: String, runtime: State<'_, RuntimeState>) -> Result<AppState, String> {
    if !matches!(level.as_str(), "high" | "balanced" | "manual") {
        return Err("Mức tự chủ không hợp lệ".into());
    }
    let mut state = runtime.state.lock().map_err(|_| "Không khóa được trạng thái ứng dụng".to_string())?;
    state.autonomy_level = level;
    persist(&runtime, &state)?;
    Ok(state.clone())
}

#[tauri::command]
fn add_workspace(path: String, runtime: State<'_, RuntimeState>) -> Result<AppState, String> {
    let p = canonical(&path)?;
    if !p.is_dir() {
        return Err("WORKSPACE_NOT_DIRECTORY".into());
    }
    let name = p
        .file_name()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_else(|| p.display().to_string());
    let mut state = runtime.state.lock().map_err(|_| "STATE_LOCK".to_string())?;
    if !state.workspaces.iter().any(|w| PathBuf::from(&w.path) == p) {
        state.workspaces.push(Workspace {
            name,
            path: p.display().to_string(),
        });
    }
    persist(&runtime, &state)?;
    Ok(state.clone())
}

#[tauri::command]
fn remove_workspace(path: String, runtime: State<'_, RuntimeState>) -> Result<AppState, String> {
    let mut state = runtime.state.lock().map_err(|_| "STATE_LOCK".to_string())?;
    state.workspaces.retain(|w| w.path != path);
    persist(&runtime, &state)?;
    Ok(state.clone())
}

#[tauri::command]
fn open_external(url: String) -> Result<(), String> {
    if !(url.starts_with("https://") || url.starts_with("http://")) {
        return Err("URL_SCHEME_NOT_ALLOWED".into());
    }
    open::that(url).map_err(|e| e.to_string())
}

fn shell_output(cwd: &Path, command: &str) -> Result<String, String> {
    let output = if cfg!(target_os = "windows") {
        Command::new("cmd")
            .args(["/C", command])
            .current_dir(cwd)
            .output()
    } else {
        Command::new("sh")
            .args(["-lc", command])
            .current_dir(cwd)
            .output()
    }
    .map_err(|e| e.to_string())?;

    Ok(format!(
        "exit={}\n--- stdout ---\n{}\n--- stderr ---\n{}",
        output.status.code().unwrap_or(-1),
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    ))
}

#[tauri::command]
fn run_terminal(
    cwd: String,
    command: String,
    runtime: State<'_, RuntimeState>,
) -> Result<String, String> {
    let scoped = ensure_scoped(&runtime, &cwd)?;
    shell_output(&scoped, &command)
}

#[tauri::command]
fn git_status(cwd: String, runtime: State<'_, RuntimeState>) -> Result<String, String> {
    let scoped = ensure_scoped(&runtime, &cwd)?;
    shell_output(&scoped, "git status --short --branch")
}

#[tauri::command]
fn run_python(
    cwd: String,
    code: String,
    runtime: State<'_, RuntimeState>,
) -> Result<String, String> {
    let scoped = ensure_scoped(&runtime, &cwd)?;
    let exe = if cfg!(target_os = "windows") { "python" } else { "python3" };
    let output = Command::new(exe)
        .args(["-c", &code])
        .current_dir(scoped)
        .output()
        .map_err(|e| e.to_string())?;
    Ok(format!(
        "exit={}\n{}{}",
        output.status.code().unwrap_or(-1),
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    ))
}

#[tauri::command]
fn conda_info(runtime: State<'_, RuntimeState>) -> Result<String, String> {
    let account_reference = runtime
        .state
        .lock()
        .map_err(|_| "STATE_LOCK".to_string())?
        .kilo_account_reference
        .clone();
    validate_kilo_session_receipt(&account_reference)
        .map_err(|e| format!("Cần receipt phiên Kilo/X-TiMe sống để dùng Conda: {e}"))?;
    let output = Command::new("conda")
        .args(["info", "--json"])
        .output()
        .map_err(|e| e.to_string())?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

#[tauri::command]
fn save_provider(provider: Provider, runtime: State<'_, RuntimeState>) -> Result<AppState, String> {
    if !(provider.base_url.starts_with("http://") || provider.base_url.starts_with("https://")) {
        return Err("PROVIDER_URL_INVALID".into());
    }
    let mut state = runtime.state.lock().map_err(|_| "STATE_LOCK".to_string())?;
    state.provider = provider;
    persist(&runtime, &state)?;
    Ok(state.clone())
}


fn validate_repo_relative_path(path: &str, label: &str) -> Result<String, String> {
    let path = path.trim();
    if path.is_empty()
        || path.starts_with('/')
        || path.starts_with('\\')
        || path.split('/').any(|part| part == "..")
        || path.split('\\').any(|part| part == "..")
    {
        return Err(format!("{label}_INVALID"));
    }
    Ok(path.replace('\\', "/"))
}

fn required_carrier_paths(route_pointer: &str) -> Result<Vec<String>, String> {
    let value: serde_json::Value = serde_json::from_str(route_pointer)
        .map_err(|e| format!("ROUTE_POINTER_INVALID_JSON: {e}"))?;
    let items = value["required_carriers"]
        .as_array()
        .ok_or_else(|| "ROUTE_REQUIRED_CARRIERS_MISSING".to_string())?;
    if items.is_empty() {
        return Err("ROUTE_REQUIRED_CARRIERS_EMPTY".into());
    }

    let mut paths = Vec::with_capacity(items.len());
    for item in items {
        let raw = item
            .as_str()
            .ok_or_else(|| "ROUTE_REQUIRED_CARRIER_NOT_STRING".to_string())?;
        let path = validate_repo_relative_path(raw, "ROUTE_REQUIRED_CARRIER_PATH")?;
        if !paths.contains(&path) {
            paths.push(path);
        }
    }
    Ok(paths)
}

fn carrier_block(path: &str, bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!(
        "CARRIER_PATH={}\nCARRIER_SHA256={}\n{}",
        path,
        format!("{:x}", hasher.finalize()),
        String::from_utf8_lossy(bytes)
    )
}

fn load_local_required_carriers(root: &Path, route_pointer: &str) -> Result<String, String> {
    let paths = required_carrier_paths(route_pointer)?;
    let mut blocks = Vec::with_capacity(paths.len());
    for rel in paths {
        let path = root.join(&rel);
        let bytes = fs::read(&path)
            .map_err(|e| format!("REQUIRED_CARRIER_READ_FAILED:{rel}:{e}"))?;
        blocks.push(carrier_block(&rel, &bytes));
    }
    Ok(blocks.join("\n\n--- REQUIRED CARRIER ---\n\n"))
}

fn route_target_path(route_pointer: &str) -> Result<String, String> {
    let value: serde_json::Value = serde_json::from_str(route_pointer)
        .map_err(|e| format!("ROUTE_POINTER_INVALID_JSON: {e}"))?;
    let path = value["route"]
        .as_str()
        .ok_or_else(|| "ROUTE_POINTER_TARGET_MISSING".to_string())?
        .trim();
    validate_repo_relative_path(path, "ROUTE_POINTER_TARGET")
}

fn local_resume_checkpoint(cwd: &Path, resume: &str) -> Result<String, String> {
    if resume.trim().is_empty() {
        return Ok(String::new());
    }
    let value: serde_json::Value = serde_json::from_str(resume)
        .map_err(|e| format!("RESUME_POINTER_INVALID_JSON: {e}"))?;
    let Some(checkpoint) = value["checkpoint"].as_str().map(str::trim).filter(|v| !v.is_empty()) else {
        return Ok(String::new());
    };
    if checkpoint.starts_with('/')
        || checkpoint.starts_with('\\')
        || checkpoint.split('/').any(|part| part == "..")
        || checkpoint.split('\\').any(|part| part == "..")
    {
        return Err("RESUME_CHECKPOINT_PATH_INVALID".into());
    }
    let path = cwd.join(checkpoint.replace('\\', "/"));
    if !path.is_file() {
        return Ok(format!("CHECKPOINT_LOCAL=NOT_PRESENT\nCHECKPOINT_PATH={}", path.display()));
    }
    let bytes = fs::read(&path).map_err(|e| format!("RESUME_CHECKPOINT_READ_FAILED: {e}"))?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    Ok(format!(
        "CHECKPOINT_LOCAL=LOADED\nCHECKPOINT_PATH={}\nCHECKPOINT_SHA256={}\n\n{}",
        path.display(),
        format!("{:x}", hasher.finalize()),
        String::from_utf8_lossy(&bytes)
    ))
}

async fn fetch_remote_canonical(repo: &str, cwd: &Path) -> Result<String, String> {
    let client = reqwest::Client::new();
    let base = format!("https://raw.githubusercontent.com/{repo}/main");

    let agents_text = client
        .get(format!("{base}/AGENTS.md"))
        .send().await.map_err(|e| format!("REMOTE_AGENTS_FETCH_FAILED:{repo}:{e}"))?
        .error_for_status().map_err(|e| format!("REMOTE_AGENTS_STATUS_FAILED:{repo}:{e}"))?
        .text().await.map_err(|e| format!("REMOTE_AGENTS_TEXT_FAILED:{repo}:{e}"))?;

    let route = client
        .get(format!("{base}/CONFIG/AGENTS_LOAD_ROUTE_CURRENT.json"))
        .send().await.map_err(|e| format!("REMOTE_ROUTE_FETCH_FAILED:{repo}:{e}"))?
        .error_for_status().map_err(|e| format!("REMOTE_ROUTE_STATUS_FAILED:{repo}:{e}"))?
        .text().await.map_err(|e| format!("REMOTE_ROUTE_TEXT_FAILED:{repo}:{e}"))?;

    if route.trim().is_empty() {
        return Err(format!("REMOTE_ROUTE_EMPTY:{repo}"));
    }
    let route_target = route_target_path(&route)?;
    let route_resolved = client
        .get(format!("{base}/{route_target}"))
        .send().await.map_err(|e| format!("REMOTE_ROUTE_TARGET_FETCH_FAILED:{repo}:{route_target}:{e}"))?
        .error_for_status().map_err(|e| format!("REMOTE_ROUTE_TARGET_STATUS_FAILED:{repo}:{route_target}:{e}"))?
        .text().await.map_err(|e| format!("REMOTE_ROUTE_TARGET_TEXT_FAILED:{repo}:{route_target}:{e}"))?;
    if route_resolved.trim().is_empty() {
        return Err(format!("REMOTE_ROUTE_TARGET_EMPTY:{repo}:{route_target}"));
    }

    let required_paths = required_carrier_paths(&route)?;
    let mut required_blocks = Vec::with_capacity(required_paths.len());
    for rel in required_paths {
        let bytes = client
            .get(format!("{base}/{rel}"))
            .send().await.map_err(|e| format!("REMOTE_REQUIRED_CARRIER_FETCH_FAILED:{repo}:{rel}:{e}"))?
            .error_for_status().map_err(|e| format!("REMOTE_REQUIRED_CARRIER_STATUS_FAILED:{repo}:{rel}:{e}"))?
            .bytes().await.map_err(|e| format!("REMOTE_REQUIRED_CARRIER_BYTES_FAILED:{repo}:{rel}:{e}"))?;
        required_blocks.push(carrier_block(&rel, &bytes));
    }
    let required_context = required_blocks.join("\n\n--- REQUIRED CARRIER ---\n\n");

    let resume = match client
        .get(format!("{base}/CURRENT_RUNTIME/TASK_RESUME_POINTER.json"))
        .send().await
    {
        Ok(response) => match response.error_for_status() {
            Ok(response) => response.text().await.unwrap_or_default(),
            Err(_) => String::new(),
        },
        Err(_) => String::new(),
    };

    let checkpoint = local_resume_checkpoint(cwd, &resume)?;

    let mut hasher = Sha256::new();
    hasher.update(agents_text.as_bytes());
    let agents_hash = format!("{:x}", hasher.finalize());

    Ok(format!(
        "NGUỒN LUẬT VỪA FRESH-READ TỪ CANONICAL GITHUB\nCANONICAL_REPO={}\nAGENTS_SHA256={}\n\n{}\n\nTUYẾN NẠP CURRENT\n{}\n\nTUYẾN NẠP ĐÃ GIẢI QUYẾT\nROUTE_TARGET={}\n{}\n\nCARRIER BẮT BUỘC ĐÃ FRESH-READ\n{}\n\nĐIỂM TIẾP TỤC CÔNG VIỆC\n{}\n\nCHECKPOINT HIỆN HÀNH\n{}",
        repo, agents_hash, agents_text, route, route_target, route_resolved, required_context, resume, checkpoint
    ))
}

async fn load_agents_context(cwd: &Path) -> Result<String, String> {
    let mut candidates: Vec<PathBuf> = Vec::new();

    if let Ok(p) = std::env::var("GGDV_AGENTS_CANONICAL_PATH") {
        if !p.trim().is_empty() {
            candidates.push(PathBuf::from(p));
        }
    }

    if cfg!(target_os = "windows") {
        candidates.push(PathBuf::from(r"G:\OS_Workspace\Open-ai-bot\AGENTS.md"));
        candidates.push(PathBuf::from(r"C:\Users\halin\GGDV_UNIFIED\Open-ai-bot\AGENTS.md"));
    }
    if let Some(parent) = cwd.parent() {
        candidates.push(parent.join("Open-ai-bot").join("AGENTS.md"));
    }

    for agents_path in candidates.into_iter().filter(|p| p.is_file()) {
        let root = agents_path.parent().unwrap_or(cwd);
        let route_path = root.join("CONFIG").join("AGENTS_LOAD_ROUTE_CURRENT.json");
        if !route_path.is_file() {
            continue;
        }

        let agents_bytes = match fs::read(&agents_path) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let route = match fs::read_to_string(&route_path) {
            Ok(v) if !v.trim().is_empty() => v,
            _ => continue,
        };
        let route_target = match route_target_path(&route) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let route_resolved_path = root.join(&route_target);
        let route_resolved = match fs::read_to_string(&route_resolved_path) {
            Ok(v) if !v.trim().is_empty() => v,
            _ => continue,
        };
        let resume = fs::read_to_string(root.join("CURRENT_RUNTIME").join("TASK_RESUME_POINTER.json"))
            .unwrap_or_default();
        let checkpoint = local_resume_checkpoint(cwd, &resume)?;
        let required_context = match load_local_required_carriers(root, &route) {
            Ok(v) => v,
            Err(_) => continue,
        };

        let mut hasher = Sha256::new();
        hasher.update(&agents_bytes);
        let agents_hash = format!("{:x}", hasher.finalize());
        let agents_text = String::from_utf8_lossy(&agents_bytes).to_string();

        return Ok(format!(
            "NGUỒN LUẬT VỪA ĐỌC TỪ BYTES THẬT\nAGENTS_PATH={}\nAGENTS_SHA256={}\n\n{}\n\nTUYẾN NẠP CURRENT\n{}\n\nTUYẾN NẠP ĐÃ GIẢI QUYẾT\nROUTE_TARGET={}\nROUTE_PATH={}\n{}\n\nCARRIER BẮT BUỘC ĐÃ FRESH-READ\n{}\n\nĐIỂM TIẾP TỤC CÔNG VIỆC\n{}\n\nCHECKPOINT HIỆN HÀNH\n{}",
            agents_path.display(),
            agents_hash,
            agents_text,
            route,
            route_target,
            route_resolved_path.display(),
            route_resolved,
            required_context,
            resume,
            checkpoint
        ));
    }

    // Canonical first, then configured mirror. Route load is mandatory.
    match fetch_remote_canonical("2708halinh-cloud/SOL-LONG-MACH", cwd).await {
        Ok(v) => Ok(v),
        Err(primary) => fetch_remote_canonical("2708halinh-cloud/Open-ai", cwd).await
            .map_err(|mirror| format!("CANONICAL_AND_MIRROR_LOAD_FAILED: primary={primary}; mirror={mirror}")),
    }
}

fn load_workspace_agents_context(cwd: &Path) -> Result<String, String> {
    let path = cwd.join("AGENTS.md");
    if !path.is_file() {
        return Ok(String::new());
    }
    let bytes = fs::read(&path).map_err(|e| format!("WORKSPACE_AGENTS_READ_FAILED: {e}"))?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    let hash = format!("{:x}", hasher.finalize());
    let text = String::from_utf8_lossy(&bytes).to_string();
    Ok(format!(
        "WORKSPACE-SCOPED AGENTS — LOADED AFTER CANONICAL\nWORKSPACE_AGENTS_PATH={}\nWORKSPACE_AGENTS_SHA256={}\n\n{}",
        path.display(), hash, text
    ))
}

#[tauri::command]
async fn provider_chat(
    cwd: String,
    prompt: String,
    runtime: State<'_, RuntimeState>,
) -> Result<String, String> {
    let scoped = ensure_scoped(&runtime, &cwd)?;
    let agents_context = load_agents_context(&scoped).await?;
    let workspace_context = load_workspace_agents_context(&scoped)?;
    let state_snapshot = runtime
        .state
        .lock()
        .map_err(|_| "STATE_LOCK".to_string())?
        .clone();
    let provider = state_snapshot.provider.clone();

    if provider_requires_kilo(&provider) {
        validate_kilo_session_receipt(&state_snapshot.kilo_account_reference)
            .map_err(|e| format!("LOCAL_MODEL_KILO_GATE: {e}"))?;
    }

    let policy = autonomy_policy(&state_snapshot.autonomy_level);
    let system_context = if workspace_context.is_empty() {
        format!("{agents_context}\n\nRUNTIME AUTONOMY POLICY\n{policy}")
    } else {
        format!("{agents_context}\n\n{workspace_context}\n\nRUNTIME AUTONOMY POLICY\n{policy}")
    };

    if provider.model.trim().is_empty() {
        return Err("MODEL_NOT_CONFIGURED".into());
    }
    let url = format!("{}/chat/completions", provider.base_url.trim_end_matches('/'));
    let mut req = reqwest::Client::new().post(url).json(&json!({
        "model": provider.model,
        "messages": [
            {"role":"system","content":system_context},
            {"role":"user","content":prompt}
        ]
    }));
    if !provider.api_key_env.trim().is_empty() {
        let value = std::env::var(&provider.api_key_env)
            .map_err(|_| format!("API_KEY_ENV_NOT_SET: {}", provider.api_key_env))?;
        req = req.bearer_auth(value);
    }
    let value: serde_json::Value = req
        .send()
        .await
        .map_err(|e| e.to_string())?
        .error_for_status()
        .map_err(|e| e.to_string())?
        .json()
        .await
        .map_err(|e| e.to_string())?;
    value["choices"][0]["message"]["content"]
        .as_str()
        .map(|s| s.to_string())
        .ok_or_else(|| format!("PROVIDER_RESPONSE_SHAPE: {value}"))
}

fn main() {
    let path = state_path();
    let (initial, safe_to_persist) = read_state(&path);
    let runtime = RuntimeState {
        state: Mutex::new(initial.clone()),
        path,
    };
    // Persist only successfully decoded/default-created state. Malformed JSON
    // stays untouched (plus backup) so repair/recovery remains possible.
    if safe_to_persist {
        let _ = persist(&runtime, &initial);
    }

    tauri::Builder::default()
        .manage(runtime)
        .invoke_handler(tauri::generate_handler![
            load_state,
            begin_kilo_connect,
            verify_kilo_session,
            skip_kilo,
            verify_kilo,
            set_autonomy,
            complete_enrollment,
            add_workspace,
            remove_workspace,
            open_external,
            run_terminal,
            git_status,
            run_python,
            conda_info,
            save_provider,
            provider_chat
        ])
        .run(tauri::generate_context!())
        .expect("error while running TESSERACT Desktop");
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn legacy_completed_state_reopens_enrollment_gates() {
        let raw = r#"{
          "schema":"TESSERACT_DESKTOP_STATE/1.0",
          "enrollment_complete":true,
          "enrollment_sources":["R-000"],
          "account_authenticated":true,
          "kilo_connected":true,
          "kilo_skipped":false,
          "kilo_account_reference":"ref",
          "autonomy_level":"high",
          "workspaces":[],
          "provider":{"kind":"openai-compatible","base_url":"http://127.0.0.1:8080/v1","model":"","api_key_env":""}
        }"#;
        let state = decode_state(raw).expect("valid legacy state");
        assert_eq!(state.schema, CURRENT_STATE_SCHEMA);
        assert!(!state.enrollment_complete);
        assert!(state.enrollment_sources.is_empty());
        assert!(!state.kilo_connected);
        assert!(!state.account_authenticated);
    }

    #[test]
    fn future_state_schema_is_rejected_without_downgrade() {
        let raw = r#"{
          "schema":"TESSERACT_DESKTOP_STATE/1.2",
          "enrollment_complete":true,
          "enrollment_sources":["R-000"],
          "account_authenticated":false,
          "kilo_connected":false,
          "kilo_skipped":false,
          "kilo_account_reference":"ref",
          "autonomy_level":"high",
          "workspaces":[],
          "provider":{"kind":"openai-compatible","base_url":"https://api.example.com/v1","model":"","api_key_env":""},
          "future_field":{"must_survive":true}
        }"#;
        let err = decode_state(raw).expect_err("future schema must not be migrated by an older binary");
        assert!(err.contains("STATE_SCHEMA_UNSUPPORTED"));
    }

    #[test]
    fn current_state_never_restores_ephemeral_authentication() {
        let raw = r#"{
          "schema":"TESSERACT_DESKTOP_STATE/1.1",
          "enrollment_complete":true,
          "enrollment_sources":["R-000","0000_TUYEN_NGON","0000_THE_MASTER_TEACHER","152_ITEM"],
          "account_authenticated":true,
          "kilo_connected":true,
          "kilo_skipped":false,
          "kilo_account_reference":"ref",
          "autonomy_level":"balanced",
          "workspaces":[],
          "provider":{"kind":"openai-compatible","base_url":"http://127.0.0.1:8080/v1","model":"","api_key_env":""}
        }"#;
        let state = decode_state(raw).expect("valid current state");
        assert!(state.enrollment_complete);
        assert!(!state.kilo_connected);
        assert!(!state.account_authenticated);
    }


    #[test]
    fn required_carrier_route_is_explicit_and_rejects_escape() {
        let route = r#"{"required_carriers":["CONFIG/POINTERS_CURRENT.json","CURRENT_RUNTIME/R-000_CURRENT.md"]}"#;
        let paths = required_carrier_paths(route).expect("required carriers");
        assert_eq!(paths.len(), 2);
        assert_eq!(paths[0], "CONFIG/POINTERS_CURRENT.json");

        let escaped = r#"{"required_carriers":["../secret"]}"#;
        assert!(required_carrier_paths(escaped).is_err());
    }

    #[test]
    fn route_pointer_resolves_repo_relative_target() {
        let pointer = r#"{"route":"CONFIG/AGENTS_LOAD_ROUTE.json"}"#;
        assert_eq!(
            route_target_path(pointer).expect("valid route pointer"),
            "CONFIG/AGENTS_LOAD_ROUTE.json"
        );
    }

    #[test]
    fn route_pointer_rejects_parent_escape() {
        let pointer = r#"{"route":"../outside.json"}"#;
        assert!(route_target_path(pointer).is_err());
    }

    #[test]
    fn malformed_state_decode_is_error() {
        assert!(decode_state("{not-json").is_err());
    }

    #[test]
    fn local_provider_requires_kilo_gate() {
        for base_url in [
            "http://127.0.0.1:8080/v1",
            "http://127.0.0.2:8080/v1",
            "http://user@127.0.0.1:8080/v1",
            "http://[::1]:8080/v1",
            "http://[0:0:0:0:0:0:0:1]:8080/v1",
            "http://localhost:8080/v1",
        ] {
            let local = Provider {
                base_url: base_url.into(),
                ..Provider::default()
            };
            assert!(provider_requires_kilo(&local), "{base_url} must be gated");
        }

        let remote = Provider {
            base_url: "https://api.example.com/v1".into(),
            ..Provider::default()
        };
        assert!(!provider_requires_kilo(&remote));
    }

    #[test]
    fn signed_kilo_receipt_rejects_forged_payload() {
        use ed25519_dalek::{Signer, SigningKey};

        let signing = SigningKey::from_bytes(&[7u8; 32]);
        let payload = serde_json::to_vec(&json!({
            "issuer": "KILO_XTIME",
            "account_reference": "trusted-ref",
            "authenticated": true,
            "session_id": "session-1",
            "expires_at_unix": u64::MAX
        }))
        .expect("payload");
        let signature = signing.sign(&payload);
        let encoder = base64::engine::general_purpose::STANDARD;
        let envelope = json!({
            "schema": "XTIME_KILO_SESSION_RECEIPT/2.0",
            "signed_payload_b64": encoder.encode(&payload),
            "signature_b64": encoder.encode(signature.to_bytes())
        })
        .to_string();
        let public_key = encoder.encode(signing.verifying_key().to_bytes());

        assert!(verify_kilo_receipt_envelope(&envelope, "trusted-ref", &public_key).is_ok());

        let forged_payload = serde_json::to_vec(&json!({
            "issuer": "KILO_XTIME",
            "account_reference": "trusted-ref",
            "authenticated": true,
            "session_id": "forged",
            "expires_at_unix": u64::MAX
        }))
        .expect("forged payload");
        let forged = json!({
            "schema": "XTIME_KILO_SESSION_RECEIPT/2.0",
            "signed_payload_b64": encoder.encode(&forged_payload),
            "signature_b64": encoder.encode(signature.to_bytes())
        })
        .to_string();
        assert!(verify_kilo_receipt_envelope(&forged, "trusted-ref", &public_key).is_err());
    }

    #[test]
    fn autonomy_levels_change_runtime_policy() {
        assert_ne!(autonomy_policy("manual"), autonomy_policy("high"));
        assert_ne!(autonomy_policy("balanced"), autonomy_policy("manual"));
        assert!(autonomy_policy("manual").contains("do not self-continue"));
        assert!(autonomy_policy("high").contains("continue self-owned"));
    }
}

