const API_BASE = "https://fde-financial-assistant.onrender.com/";
let isLoading = false;

// ── Status check ──────────────────────────────────────────────────────────────
async function checkStatus() {
  const dot = document.getElementById("statusDot");
  const txt = document.getElementById("statusText");
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    if (data.ready) {
      dot.className = "status-dot online";
      txt.textContent = "Connected & Ready";
    } else {
      dot.className = "status-dot";
      txt.textContent = "Initializing...";
      setTimeout(checkStatus, 3000);
    }
  } catch {
    dot.className = "status-dot error";
    txt.textContent = "Backend offline";
    setTimeout(checkStatus, 5000);
  }
}

// ── Message rendering ─────────────────────────────────────────────────────────
function addUserMessage(text) {
  removeWelcome();
  const row = document.createElement("div");
  row.className = "message-row user";
  row.innerHTML = `
    <div class="avatar user-avatar">👤</div>
    <div class="message-content">
      <div class="bubble">${escapeHtml(text)}</div>
    </div>`;
  document.getElementById("messages").appendChild(row);
  scrollBottom();
}

function addTypingIndicator() {
  removeWelcome();
  const row = document.createElement("div");
  row.className = "message-row bot";
  row.id = "typing";
  row.innerHTML = `
    <div class="avatar bot-avatar">${botIcon()}</div>
    <div class="message-content">
      <div class="bubble bot-bubble">
        <div class="typing-indicator"><span></span><span></span><span></span></div>
      </div>
    </div>`;
  document.getElementById("messages").appendChild(row);
  scrollBottom();
}

function removeTypingIndicator() {
  document.getElementById("typing")?.remove();
}

function addBotMessage(answer, sources) {
  const row = document.createElement("div");
  row.className = "message-row bot";

  const sourcesHtml = buildSourcesHtml(sources);

  row.innerHTML = `
    <div class="avatar bot-avatar">${botIcon()}</div>
    <div class="message-content">
      <div class="bubble">${formatAnswer(answer)}</div>
      ${sourcesHtml}
    </div>`;
  document.getElementById("messages").appendChild(row);
  scrollBottom();
}

function addErrorMessage(msg) {
  const row = document.createElement("div");
  row.className = "message-row bot";
  row.innerHTML = `
    <div class="avatar bot-avatar">${botIcon()}</div>
    <div class="message-content">
      <div class="bubble" style="border-color:#ef4444;color:#fca5a5;">${escapeHtml(msg)}</div>
    </div>`;
  document.getElementById("messages").appendChild(row);
  scrollBottom();
}

// ── Sources panel ─────────────────────────────────────────────────────────────
function buildSourcesHtml(sources) {
  if (!sources || sources.length === 0) return "";

  const cards = sources.map(s => `
    <div class="source-card">
      <div class="source-name">${escapeHtml(s.source)}</div>
      <div class="source-snippet">${escapeHtml(s.snippet)}${s.snippet.length >= 300 ? "…" : ""}</div>
    </div>`).join("");

  const id = `src-${Date.now()}`;
  return `
    <button class="sources-toggle" onclick="toggleSources(this,'${id}')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 9l-7 7-7-7"/>
      </svg>
      ${sources.length} source${sources.length > 1 ? "s" : ""} retrieved
    </button>
    <div class="sources-panel" id="${id}">${cards}</div>`;
}

function toggleSources(btn, panelId) {
  const panel = document.getElementById(panelId);
  const isOpen = panel.classList.toggle("visible");
  btn.classList.toggle("open", isOpen);
  btn.querySelector("svg").style.transform = isOpen ? "rotate(180deg)" : "";
  const label = btn.querySelector("span") || btn;
  if (isOpen) btn.innerHTML = btn.innerHTML.replace("retrieved", "hide");
  else btn.innerHTML = btn.innerHTML.replace("hide", "retrieved");
}

// ── Query flow ────────────────────────────────────────────────────────────────
async function sendQuery() {
  if (isLoading) return;
  const input = document.getElementById("queryInput");
  const question = input.value.trim();
  if (!question) return;

  input.value = "";
  autoResize(input);
  setLoading(true);

  addUserMessage(question);
  addTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Server error" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    removeTypingIndicator();
    addBotMessage(data.answer, data.sources);
  } catch (err) {
    removeTypingIndicator();
    addErrorMessage(`Error: ${err.message}. Make sure the backend is running.`);
  } finally {
    setLoading(false);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuery(); }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}

function setLoading(state) {
  isLoading = state;
  document.getElementById("sendBtn").disabled = state;
}

function scrollBottom() {
  const msgs = document.getElementById("messages");
  requestAnimationFrame(() => msgs.scrollTop = msgs.scrollHeight);
}

function removeWelcome() {
  document.getElementById("welcomeState")?.remove();
}

function clearChat() {
  const msgs = document.getElementById("messages");
  msgs.innerHTML = `
    <div class="welcome-state" id="welcomeState">
      <div class="welcome-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
      </div>
      <h3>Conversation cleared</h3>
      <p>Ask me anything about reimbursements, travel, vendor payments, procurement, or tax compliance.</p>
    </div>`;
}

function useSample(btn) {
  document.getElementById("queryInput").value = btn.textContent;
  sendQuery();
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatAnswer(text) {
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[•\-]\s(.+)$/gm, "<li>$1</li>")
    .replace(/(<li>[\s\S]*?<\/li>(\n|<br>)*)+/g, m => `<ul>${m.replace(/<br>/g, "")}</ul>`)
    .replace(/\n/g, "<br>");
}

function botIcon() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
    <path d="M2 17l10 5 10-5"/>
    <path d="M2 12l10 5 10-5"/>
  </svg>`;
}

// ── Init ──────────────────────────────────────────────────────────────────────
checkStatus();
document.getElementById("queryInput").focus();
