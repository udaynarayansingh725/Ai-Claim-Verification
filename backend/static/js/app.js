// ---------- state ----------
let token = localStorage.getItem("token");
let mode = "login"; // login | register

const $ = (id) => document.getElementById(id);

// ---------- auth ----------
$("tab-login").onclick = () => setTab("login");
$("tab-register").onclick = () => setTab("register");

function setTab(t) {
  mode = t;
  $("tab-login").classList.toggle("active", t === "login");
  $("tab-register").classList.toggle("active", t === "register");
  $("auth-name").style.display = t === "register" ? "block" : "none";
  $("auth-btn").textContent = t === "register" ? "Create Account" : "Login";
  $("auth-error").textContent = "";
}

$("auth-form").onsubmit = async (e) => {
  e.preventDefault();
  const url = mode === "register" ? "/api/auth/register" : "/api/auth/login";
  const body = { email: $("auth-email").value, password: $("auth-password").value };
  if (mode === "register") body.name = $("auth-name").value;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) { $("auth-error").textContent = data.detail || "Something went wrong"; return; }
  token = data.access_token;
  localStorage.setItem("token", token);
  showApp(data.name);
};

$("logout-btn").onclick = () => {
  localStorage.removeItem("token");
  token = null;
  $("app-screen").style.display = "none";
  $("auth-screen").style.display = "flex";
};

function showApp(name) {
  $("auth-screen").style.display = "none";
  $("app-screen").style.display = "block";
  $("user-name").textContent = "👤 " + name;
}

async function boot() {
  if (!token) return;
  const res = await fetch("/api/auth/me", { headers: authHeaders() });
  if (res.ok) { const u = await res.json(); showApp(u.name); }
  else localStorage.removeItem("token");
}
function authHeaders() { return { "Authorization": "Bearer " + token }; }

// ---------- navigation ----------
document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    $("panel-" + btn.dataset.mode).classList.add("active");
    if (btn.dataset.mode === "history") loadHistory();
  };
});

// ---------- helpers ----------
function verdictClass(v) {
  v = v.toLowerCase();
  if (v.includes("supported") || v.includes("human") || v.includes("real photo")) return "verdict-supported";
  if (v.includes("refuted") || v.includes("likely ai")) return "verdict-refuted";
  return "verdict-possibly";
}

function renderResult(el, data, withEvidence) {
  const pct = Math.round((data.confidence || 0) * 100);
  let html = `<div class="verdict-card ${verdictClass(data.verdict)}">Verdict: ${data.verdict} (${pct}% confidence)</div>
    <div class="confidence-bar"><div class="confidence-fill" style="width:${pct}%"></div></div>
    <strong>Signals & explanation:</strong><ul class="signals">` +
    data.signals.map(s => `<li>${escapeHtml(s)}</li>`).join("") + "</ul>";
  if (withEvidence && data.evidence && data.evidence.length) {
    html += "<strong>Evidence:</strong>";
    data.evidence.forEach(ev => {
      html += `<div class="evidence-item"><h4>${escapeHtml(ev.title)}</h4>
        <p class="small muted">${escapeHtml(ev.source)} · match ${Math.round(ev.similarity * 100)}%
        ${ev.url ? ` · <a href="${ev.url}" target="_blank">source</a>` : ""}</p>
        <p class="small">${escapeHtml(ev.snippet)}</p></div>`;
    });
  }
  el.innerHTML = html;
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- API calls ----------
async function submitClaim() {
  const el = $("claim-result");
  el.innerHTML = "<p class='muted'>Verifying claim…</p>";
  const res = await fetch("/api/verify-claim", {
    method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ claim: $("claim-input").value }),
  });
  const data = await res.json();
  if (!res.ok) { el.innerHTML = `<p class="error">${data.detail || "Error"}</p>`; return; }
  renderResult(el, data, true);
}

async function submitText() {
  const el = $("text-result");
  el.innerHTML = "<p class='muted'>Analysing text…</p>";
  const res = await fetch("/api/detect-text", {
    method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text: $("text-input").value }),
  });
  const data = await res.json();
  if (!res.ok) { el.innerHTML = `<p class="error">${data.detail || "Error"}</p>`; return; }
  renderResult(el, data, false);
}

async function submitImage() {
  const el = $("image-result");
  const file = $("image-input").files[0];
  if (!file) { el.innerHTML = `<p class="error">Please choose an image first.</p>`; return; }
  el.innerHTML = "<p class='muted'>Analysing image…</p>";
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/detect-image", { method: "POST", headers: authHeaders(), body: fd });
  const data = await res.json();
  if (!res.ok) { el.innerHTML = `<p class="error">${data.detail || "Error"}</p>`; return; }
  renderResult(el, data, false);
}

async function loadHistory() {
  const el = $("history-list");
  el.innerHTML = "<p class='muted'>Loading…</p>";
  const res = await fetch("/api/history", { headers: authHeaders() });
  const data = await res.json();
  if (!data.length) { el.innerHTML = "<p class='muted'>No analyses yet.</p>"; return; }
  el.innerHTML = data.map(item => `
    <div class="history-card" onclick='showHistoryItem(${JSON.stringify(item)})'>
      <span class="badge">${item.analysis_type.toUpperCase()}</span>
      <span class="badge">${item.verdict}</span>
      <span class="muted small">${item.created_at}</span>
      <p class="small">${escapeHtml((item.input_text || item.input_image || "").slice(0, 120))}</p>
    </div>`).join("");
}
function showHistoryItem(item) {
  const target = $("panel-" + (item.analysis_type === "claim" ? "claim" : item.analysis_type));
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  target.classList.add("active");
  renderResult(target.querySelector(".result"), item, item.analysis_type === "claim");
  target.scrollIntoView({ behavior: "smooth" });
}

boot();
