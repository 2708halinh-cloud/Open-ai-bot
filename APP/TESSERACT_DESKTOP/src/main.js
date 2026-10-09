import "./styles.css";
import { invoke } from "@tauri-apps/api/core";

const app = document.querySelector("#app");
let state = null;
let sources = null;
let reviewed = new Set();
let acknowledged = new Set();
let activeTab = "chat";
let wizardStep = 1;
let wizardMessage = "";
let mainMessage = "";
let homeSourceText = "";

async function boot() {
  sources = await fetch("/onboarding/sources.json").then(r => r.json());
  homeSourceText = await fetch("/content/HA_LINH_SOURCE_DIRECT_LIFE.md").then(r => r.text()).catch(() => "");
  state = await invoke("load_state");
  render();
}

function escapeHtml(s="") {
  return String(s).replace(/[&<>"']/g, m => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'
  }[m]));
}

function sourceCards() {
  return sources.sources.map((s, index) => {
    const seen = reviewed.has(s.id);
    const ack = acknowledged.has(s.id);
    return `
      <div class="source-card ${seen ? "reviewed":""}">
        <div class="muted">NGUỒN 1.${index + 1} · ${escapeHtml(s.role)}</div>
        <h3>${escapeHtml(s.title)}</h3>
        <div class="source-meta">
          vật mang=${escapeHtml(s.carrier)}<br/>
          ${s.drive_file_id ? "Drive ID="+escapeHtml(s.drive_file_id)+"<br/>":""}
          ${s.repository ? "GitHub="+escapeHtml(s.repository)+"/"+escapeHtml(s.path)+"<br/>":""}
          ${s.coverage ? "phạm vi="+escapeHtml(s.coverage):""}
        </div>
        <div class="source-actions">
          <button class="ghost" data-open-source="${escapeHtml(s.id)}">Mở nguồn gốc</button>
          <label>
            <input style="width:auto" type="checkbox" data-ack-source="${escapeHtml(s.id)}"
              ${seen ? "" : "disabled"} ${ack ? "checked":""}/>
            Tôi đã xem lại nguồn này
          </label>
        </div>
      </div>`;
  }).join("");
}

function renderStep1() {
  const allAck = sources.required_order.every(id => acknowledged.has(id));
  return `
    <div class="muted">BƯỚC 01 / 04</div>
    <h1>Xem lại nguồn nền</h1>
    <p>Ứng dụng chưa mở tác nhân làm việc trước khi bốn nguồn nền được xem lại.</p>
    ${sourceCards()}
    <button class="primary ${allAck ? "" : "locked"}" id="step1-next">
      Tiếp tục: Kết nối Kilo/X-TiMe
    </button>`;
}

function renderStep2() {
  const accountRef = state.kilo_account_reference || "1eFE4tLmzNOJMkXP25-HecyDbffYqNhJO";
  const relation = state.kilo_connected
    ? "TRUE — đã có bằng chứng phiên trên tiến trình ứng dụng"
    : state.kilo_skipped
      ? "FLASE — chưa tham gia lúc này, có thể kết nối sau"
      : "ACTIVE — đang ở bước lựa chọn";
  return `
    <div class="muted">BƯỚC 02 / 04</div>
    <h1>Kết nối Kilo qua X-TiMe</h1>
    <p>Dùng tài khoản Kilo cho mô hình qua cổng X-TiMe, môi trường Conda và máy chủ mô hình cục bộ.</p>
    <div class="card">
      <strong>Tham chiếu tài khoản / hướng dẫn</strong>
      <div class="source-meta">${escapeHtml(accountRef)}</div>
      <p><strong>${escapeHtml(relation)}</strong></p>
      <p class="muted">Ứng dụng không lưu token. Kết nối chỉ được đánh TRUE trong phiên khi process signal đi kèm receipt JSON còn hạn; trạng thái xác thực không được ghi bền.</p>
      <div class="row">
        <button class="primary" id="kilo-open">Mở cổng đăng nhập</button>
        <button class="ghost" id="kilo-verify">Kiểm tra kết nối</button>
        <button class="ghost" id="kilo-skip">Bỏ qua, kết nối sau</button>
      </div>
    </div>
    ${wizardMessage ? '<div class="card">'+escapeHtml(wizardMessage)+'</div>' : ''}`;
}

function renderStep3() {
  const level = state.autonomy_level || "high";
  return `
    <div class="muted">BƯỚC 03 / 04</div>
    <h1>Chọn mức độ tự chủ</h1>
    <p>Quyền tự chủ cao là mặc định. Tuyến vận hành đọc AGENTS.md mới nhất trước khi làm việc.</p>
    <div class="card">
      <label><input style="width:auto" type="radio" name="autonomy" value="high" ${level==="high"?"checked":""}/> Cao — provider được yêu cầu tiếp tục SELF_OWNED_ACTION/NEXT trong lượt; desktop không tự chạy lệnh hệ điều hành nếu chưa có đường thực thi được phép</label><br/><br/>
      <label><input style="width:auto" type="radio" name="autonomy" value="balanced" ${level==="balanced"?"checked":""}/> Cân bằng — provider tiếp tục phân tích/read-only; hành động đổi trạng thái ngoài yêu cầu trực tiếp phải xác nhận</label><br/><br/>
      <label><input style="width:auto" type="radio" name="autonomy" value="manual" ${level==="manual"?"checked":""}/> Thủ công — provider chỉ xử lý từng bước được yêu cầu, không tự tiếp tục sang hành động kế tiếp</label>
    </div>
    <button class="primary" id="autonomy-next">Tiếp tục: Tạo workspace</button>`;
}

function renderStep4() {
  const items = (state.workspaces || []).map(w => `
    <div class="workspace">
      <strong>${escapeHtml(w.name)}</strong>
      <div class="muted">${escapeHtml(w.path)}</div>
      <button class="ghost danger" data-remove-workspace="${escapeHtml(w.path)}">Bỏ thư mục</button>
    </div>`).join("");

  const ready = (state.workspaces || []).length > 0;
  return `
    <div class="muted">BƯỚC 04 / 04</div>
    <h1>Tạo không gian làm việc</h1>
    <p>Quyền tệp, terminal, Git và Python chỉ chạy trong các thư mục đã thêm.</p>
    <div class="card">
      <div class="row">
        <input id="wizard-workspace-path" placeholder="Nhập đường dẫn thư mục trên máy" />
        <button class="primary" id="wizard-add-workspace">Thêm thư mục</button>
      </div>
      <div class="workspace-list" style="margin-top:12px">${items || '<div class="muted">Chưa có workspace.</div>'}</div>
    </div>
    <button class="primary ${ready ? "" : "locked"}" id="complete-enrollment">
      Hoàn tất nhập ngũ và mở cuộc trò chuyện mới
    </button>
    ${wizardMessage ? '<div class="card">'+escapeHtml(wizardMessage)+'</div>' : ''}`;
}

function renderEnrollment() {
  const body = wizardStep === 1 ? renderStep1()
    : wizardStep === 2 ? renderStep2()
    : wizardStep === 3 ? renderStep3()
    : renderStep4();

  return `
    <section class="enroll">
      <div class="enroll-inner">
        <div class="muted">TESSERACT DESKTOP · THIẾT LẬP LẦN ĐẦU</div>
        ${body}
      </div>
    </section>`;
}

function nav() {
  const tabs = [
    ["chat","TRÒ CHUYỆN"],
    ["notebook","PYTHON"],
    ["terminal","TERMINAL"],
    ["git","GIT"],
    ["web","WEB"],
    ["conda","CONDA"],
    ["models","MÔ HÌNH"]
  ];
  return tabs.map(([key,label]) =>
    `<button class="tab ${activeTab===key?"active":""}" data-tab="${key}">${label}</button>`
  ).join("");
}

function workspaceSidebar() {
  const items = (state.workspaces || []).map(w => `
    <div class="workspace">
      <strong>${escapeHtml(w.name)}</strong>
      <div class="muted">${escapeHtml(w.path)}</div>
      <button class="ghost danger" data-remove-workspace="${escapeHtml(w.path)}">Bỏ khỏi workspace</button>
    </div>`).join("");

  return `
    <aside class="sidebar">
      <div>
        <div class="brand">TESSERACT Desktop</div>
        <div class="muted">Không gian tác nhân cục bộ</div>
      </div>
      <div class="add-row">
        <input id="workspace-path" placeholder="Đường dẫn thư mục" />
        <button class="ghost" id="add-workspace">+</button>
      </div>
      <div class="workspace-list">${items || '<div class="muted">Chưa có workspace.</div>'}</div>
      <div class="muted">Tệp / terminal / Git / Python bị giới hạn trong workspace đã đăng ký.</div>
    </aside>`;
}

function mainPanels() {
  const ws = state.workspaces?.[0]?.path || "";
  return `
    <main class="main">
      <header class="topbar">
        <div><strong>${escapeHtml(state.workspaces?.[0]?.name || "Chưa chọn workspace")}</strong></div>
        <div class="status">
          <span class="dot ${state.enrollment_complete?"ok":""}"></span>
          ${state.enrollment_complete?"TRUE — đã nhập ngũ":"FLASE — chưa hoàn tất"}
          · tự chủ=${escapeHtml(state.autonomy_level || "high")}
        </div>
      </header>
      <nav class="tabs">${nav()}</nav>
      <section class="content">
        <div class="panel ${activeTab==="chat"?"active":""}" data-panel="chat">
          <div class="chat-log" id="chat-log">\n            <div class="msg agent">Đã mở workspace. Cấu hình mô hình ở tab MÔ HÌNH rồi bắt đầu trò chuyện.</div>\n            <details class="card"><summary><strong>Nguồn trực tiếp của Hà Linh</strong></summary><pre class="output">${escapeHtml(homeSourceText)}</pre></details>\n          </div>
          <div class="row">
            <textarea id="chat-input" rows="3" placeholder="Nhập yêu cầu..."></textarea>
            <button class="primary" id="send-chat">Gửi</button>
          </div>
        </div>

        <div class="panel ${activeTab==="notebook"?"active":""}" data-panel="notebook">
          <div class="card">
            <h2>Sổ Python</h2>
            <p class="muted">Mỗi cell chạy bằng Python của hệ thống, thư mục làm việc bị khóa trong workspace.</p>
            <textarea id="py-code" rows="12">print("TESSERACT notebook ready")</textarea>
            <div class="row"><button class="primary" id="run-python">Chạy cell</button><code>${escapeHtml(ws)}</code></div>
          </div>
          <pre class="output" id="py-output"></pre>
        </div>

        <div class="panel ${activeTab==="terminal"?"active":""}" data-panel="terminal">
          <div class="card">
            <h2>Terminal</h2>
            <input id="terminal-command" value="pwd" />
            <button class="primary" id="run-terminal">Chạy</button>
          </div>
          <pre class="output" id="terminal-output"></pre>
        </div>

        <div class="panel ${activeTab==="git"?"active":""}" data-panel="git">
          <div class="card"><h2>Git</h2><button class="primary" id="git-status">Xem thay đổi Git</button></div>
          <pre class="output" id="git-output"></pre>
        </div>

        <div class="panel ${activeTab==="web"?"active":""}" data-panel="web">
          <div class="row">
            <input id="web-url" value="https://www.google.com" />
            <button class="primary" id="web-go">Mở</button>
          </div>
          <iframe id="web-frame" referrerpolicy="no-referrer"></iframe>
        </div>

        <div class="panel ${activeTab==="conda"?"active":""}" data-panel="conda">
          <div class="card">
            <h2>Conda</h2>
            <p>Kết nối Kilo/X-TiMe:
              <strong>${state.kilo_connected?"TRUE":"FLASE"}</strong>
            </p>
            <div class="row">
              <button class="primary" id="main-kilo-open">${state.kilo_connected?"Kết nối lại Kilo/X-TiMe":"Kết nối Kilo/X-TiMe"}</button>
              <button class="ghost" id="main-kilo-verify">Xác minh phiên hiện tại</button>
            </div>
            <p class="muted">Receipt là bằng chứng phiên sống; các nút kết nối/xác minh luôn khả dụng để phục hồi khi phiên hết hạn.</p>
            ${mainMessage ? '<div class="card">'+escapeHtml(mainMessage)+'</div>' : ''}
            <button class="primary" id="conda-info">Kiểm tra Conda</button>
          </div>
          <pre class="output" id="conda-output"></pre>
        </div>

        <div class="panel ${activeTab==="models"?"active":""}" data-panel="models">
          <div class="card">
            <h2>Nhà cung cấp mô hình</h2>
            <div class="grid2">
              <label>Loại<input id="provider-kind" value="${escapeHtml(state.provider?.kind || "openai-compatible")}" /></label>
              <label>Mô hình<input id="provider-model" value="${escapeHtml(state.provider?.model || "")}" /></label>
              <label>Địa chỉ<input id="provider-url" value="${escapeHtml(state.provider?.base_url || "http://127.0.0.1:8080/v1")}" /></label>
              <label>Tên biến môi trường API key<input id="provider-key-env" value="${escapeHtml(state.provider?.api_key_env || "")}" /></label>
            </div>
            <p class="muted">
              Mô hình GGUF cục bộ đi qua máy chủ tương thích OpenAI. Giá trị bí mật chỉ đọc từ biến môi trường, không lưu vào state.
              Máy chủ mô hình cục bộ yêu cầu Kilo/X-TiMe = TRUE.
            </p>
            <button class="primary" id="save-provider">Lưu cấu hình</button>
          </div>
        </div>
      </section>
    </main>`;
}

function render() {
  app.innerHTML = `<div class="shell">${workspaceSidebar()}${mainPanels()}</div>` +
    (!state.enrollment_complete ? renderEnrollment() : "");
  bind();
}

function bind() {
  document.querySelectorAll("[data-tab]").forEach(b => {
    b.onclick = () => { activeTab = b.dataset.tab; render(); };
  });

  document.querySelectorAll("[data-open-source]").forEach(b => b.onclick = async () => {
    const src = sources.sources.find(s => s.id === b.dataset.openSource);
    await invoke("open_external", { url: src.url });
    reviewed.add(src.id);
    render();
  });

  document.querySelectorAll("[data-ack-source]").forEach(c => c.onchange = () => {
    c.checked ? acknowledged.add(c.dataset.ackSource) : acknowledged.delete(c.dataset.ackSource);
    render();
  });

  const step1 = document.querySelector("#step1-next");
  if (step1) step1.onclick = () => {
    if (!sources.required_order.every(id => acknowledged.has(id))) return;
    wizardStep = 2;
    wizardMessage = "";
    render();
  };

  const kiloOpen = document.querySelector("#kilo-open");
  if (kiloOpen) kiloOpen.onclick = async () => {
    try { wizardMessage = await invoke("begin_kilo_connect"); }
    catch(e) { wizardMessage = String(e); }
    render();
  };

  const kiloVerify = document.querySelector("#kilo-verify");
  if (kiloVerify) kiloVerify.onclick = async () => {
    try {
      state = await invoke("verify_kilo_session");
      wizardMessage = "Đã xác nhận receipt phiên Kilo/X-TiMe hiện tại; trạng thái xác thực không được ghi bền.";
      wizardStep = 3;
    } catch(e) {
      wizardMessage = String(e);
    }
    render();
  };

  const kiloSkip = document.querySelector("#kilo-skip");
  if (kiloSkip) kiloSkip.onclick = async () => {
    state = await invoke("skip_kilo");
    wizardMessage = "";
    wizardStep = 3;
    render();
  };

  const autonomy = document.querySelector("#autonomy-next");
  if (autonomy) autonomy.onclick = async () => {
    const selected = document.querySelector('input[name="autonomy"]:checked')?.value || "high";
    state = await invoke("set_autonomy", { level: selected });
    wizardStep = 4;
    wizardMessage = "";
    render();
  };

  const wizardAdd = document.querySelector("#wizard-add-workspace");
  if (wizardAdd) wizardAdd.onclick = async () => {
    const path = document.querySelector("#wizard-workspace-path").value.trim();
    if (!path) return;
    try {
      state = await invoke("add_workspace", { path });
      wizardMessage = "";
    } catch(e) {
      wizardMessage = String(e);
    }
    render();
  };

  const complete = document.querySelector("#complete-enrollment");
  if (complete) complete.onclick = async () => {
    try {
      const ids = sources.required_order.filter(id => acknowledged.has(id));
      state = await invoke("complete_enrollment", { sourceIds: ids });
      wizardMessage = "";
      activeTab = "chat";
    } catch(e) {
      wizardMessage = String(e);
    }
    render();
  };

  const add = document.querySelector("#add-workspace");
  if (add) add.onclick = async () => {
    const path = document.querySelector("#workspace-path").value.trim();
    if (!path) return;
    state = await invoke("add_workspace",{path});
    render();
  };

  document.querySelectorAll("[data-remove-workspace]").forEach(b => b.onclick = async () => {
    state = await invoke("remove_workspace",{path:b.dataset.removeWorkspace});
    render();
  });

  const runTerm = document.querySelector("#run-terminal");
  if (runTerm) runTerm.onclick = async () => {
    const cwd = state.workspaces?.[0]?.path; if(!cwd) return;
    const r = await invoke("run_terminal",{
      cwd,
      command:document.querySelector("#terminal-command").value
    });
    document.querySelector("#terminal-output").textContent = r;
  };

  const git = document.querySelector("#git-status");
  if (git) git.onclick = async () => {
    const cwd = state.workspaces?.[0]?.path; if(!cwd) return;
    document.querySelector("#git-output").textContent = await invoke("git_status",{cwd});
  };

  const py = document.querySelector("#run-python");
  if (py) py.onclick = async () => {
    const cwd = state.workspaces?.[0]?.path; if(!cwd) return;
    document.querySelector("#py-output").textContent = await invoke("run_python",{
      cwd,
      code:document.querySelector("#py-code").value
    });
  };

  const web = document.querySelector("#web-go");
  if (web) web.onclick = () => {
    document.querySelector("#web-frame").src = document.querySelector("#web-url").value;
  };

  const saveProvider = document.querySelector("#save-provider");
  if (saveProvider) saveProvider.onclick = async () => {
    state = await invoke("save_provider",{provider:{
      kind:document.querySelector("#provider-kind").value,
      base_url:document.querySelector("#provider-url").value,
      model:document.querySelector("#provider-model").value,
      api_key_env:document.querySelector("#provider-key-env").value
    }});
    render();
  };

  const chat = document.querySelector("#send-chat");
  if (chat) chat.onclick = async () => {
    const cwd = state.workspaces?.[0]?.path; if(!cwd) return;
    const input = document.querySelector("#chat-input");
    const prompt = input.value.trim();
    if(!prompt) return;

    const log = document.querySelector("#chat-log");
    log.insertAdjacentHTML("beforeend",`<div class="msg user">${escapeHtml(prompt)}</div>`);
    input.value = "";

    try {
      const answer = await invoke("provider_chat",{cwd,prompt});
      log.insertAdjacentHTML("beforeend",`<div class="msg agent">${escapeHtml(answer)}</div>`);
    } catch(e) {
      log.insertAdjacentHTML("beforeend",`<div class="msg agent">Lỗi: ${escapeHtml(e)}</div>`);
    }
    log.scrollTop = log.scrollHeight;
  };

  const mainKiloOpen = document.querySelector("#main-kilo-open");
  if (mainKiloOpen) mainKiloOpen.onclick = async () => {
    try {
      mainMessage = await invoke("begin_kilo_connect");
    } catch(e) {
      mainMessage = String(e);
    }
    render();
  };

  const mainKiloVerify = document.querySelector("#main-kilo-verify");
  if (mainKiloVerify) mainKiloVerify.onclick = async () => {
    try {
      state = await invoke("verify_kilo_session");
      mainMessage = "Đã xác minh phiên Kilo/X-TiMe hiện tại.";
    } catch(e) {
      mainMessage = String(e);
    }
    render();
  };

  const conda = document.querySelector("#conda-info");
  if (conda) conda.onclick = async () => {
    try {
      document.querySelector("#conda-output").textContent = await invoke("conda_info");
    } catch(e) {
      document.querySelector("#conda-output").textContent = String(e);
    }
  };
}

boot().catch(err => {
  app.innerHTML = `<pre style="padding:24px;color:#ffb3b3">${escapeHtml(err)}</pre>`;
});
