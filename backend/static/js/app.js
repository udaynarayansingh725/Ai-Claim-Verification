// ---------- state ----------
let token = localStorage.getItem("token");
let currentUser = null;
let mode = "login"; // login | register

const $ = (id) => document.getElementById(id);

// ---------- theme switcher ----------
const themeBtn = $("theme-toggle");
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark-mode");
  if (themeBtn) themeBtn.textContent = "☀️ Light";
}
if (themeBtn) {
  themeBtn.onclick = () => {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    themeBtn.textContent = isDark ? "☀️ Light" : "🌙 Dark";
  };
}

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
  await boot();
};

$("logout-btn").onclick = () => {
  localStorage.removeItem("token");
  token = null;
  currentUser = null;
  $("app-screen").style.display = "none";
  $("auth-screen").style.display = "flex";
};

function showApp(user) {
  currentUser = user;
  $("auth-screen").style.display = "none";
  $("app-screen").style.display = "block";
  $("user-name").textContent = "👤 " + user.name;
  if (user.is_admin) {
    $("nav-admin").style.display = "inline-block";
  }
}

async function boot() {
  if (!token) return;
  const res = await fetch("/api/auth/me", { headers: authHeaders() });
  if (res.ok) {
    const u = await res.json();
    showApp(u);
  } else {
    localStorage.removeItem("token");
  }
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
    if (btn.dataset.mode === "admin") loadAdminDashboard();
  };
});

// ---------- helpers ----------
function verdictClass(v) {
  v = v.toLowerCase();
  if (v.includes("supported") || v.includes("human") || v.includes("real photo")) return "verdict-supported";
  if (v.includes("refuted") || v.includes("likely ai")) return "verdict-refuted";
  return "verdict-possibly";
}

function stanceBadge(s) {
  s = (s || "NEUTRAL").toUpperCase();
  if (s === "AGREES") return `<span class="badge badge-agrees">AGREES</span>`;
  if (s === "DISAGREES") return `<span class="badge badge-disagrees">DISAGREES</span>`;
  return `<span class="badge badge-neutral">NEUTRAL</span>`;
}

function renderResult(el, data, withEvidence) {
  const pct = Math.round((data.confidence || 0) * 100);
  let html = `<div class="verdict-card ${verdictClass(data.verdict)}">Verdict: ${data.verdict} (${pct}% confidence)</div>
    <div class="confidence-bar"><div class="confidence-fill" style="width:${pct}%"></div></div>`;
    
  // Sentence highlighting breakdown for text detection
  if (data.sentence_analysis && data.sentence_analysis.length) {
    html += `<strong>Sentence-level AI Breakdown:</strong>
      <div class="sentence-box">` +
      data.sentence_analysis.map(s => {
        const cls = s.is_ai ? "sentence-ai" : "sentence-human";
        const title = s.reasons && s.reasons.length ? s.reasons.join(", ") : (s.is_ai ? "High AI likelihood" : "Human-like structure");
        return `<span class="${cls}" title="${escapeHtml(title)}">${escapeHtml(s.text)}</span> `;
      }).join("") + `</div>`;
  }

  // Visual ELA Heatmap Toggle for Images
  if (data.ela_heatmap) {
    html += `<div style="margin:12px 0;">
      <button class="btn-secondary" onclick="toggleElaMap(this)">🔍 Toggle ELA Heatmap View</button>
      <div class="ela-container" style="display:none; margin-top:10px;">
        <p class="small muted" style="color:#fff; margin-bottom:6px;">Error Level Analysis Map (High brightness = Modified/AI noise)</p>
        <img src="${data.ela_heatmap}" alt="ELA Heatmap" />
      </div>
    </div>`;
  }

  html += `<strong>Signals & Explanation:</strong><ul class="signals">` +
    data.signals.map(s => `<li>${escapeHtml(s)}</li>`).join("") + "</ul>";

  if (withEvidence && data.evidence && data.evidence.length) {
    html += "<strong>Retrieved Evidence & Stance:</strong>";
    data.evidence.forEach(ev => {
      html += `<div class="evidence-item">
        <h4>${stanceBadge(ev.stance)} ${escapeHtml(ev.title)}</h4>
        <p class="small muted">${escapeHtml(ev.source)} · Keyword Match ${Math.round(ev.similarity * 100)}%
        ${ev.url ? ` · <a href="${ev.url}" target="_blank">View Source</a>` : ""}</p>
        <p class="small">${escapeHtml(ev.snippet)}</p></div>`;
    });
  }

  // Export PDF Report Button
  html += `<div style="margin-top:16px;">
    <button class="btn-secondary" onclick="downloadPdfReport('${escapeHtml(data.analysis_type || 'verification')}', '${escapeHtml(data.verdict)}', ${pct})">📥 Download Verification Report (PDF)</button>
  </div>`;

  el.innerHTML = html;
}

function toggleElaMap(btn) {
  const container = btn.nextElementSibling;
  const isHidden = container.style.display === "none";
  container.style.display = isHidden ? "block" : "none";
  btn.textContent = isHidden ? "❌ Hide ELA Heatmap" : "🔍 Toggle ELA Heatmap View";
}

function downloadPdfReport(type, verdict, confidence) {
  const reportWindow = window.open("", "_blank");
  reportWindow.document.write(`
    <html>
      <head>
        <title>VerifyEngine Verification Report</title>
        <style>
          body { font-family: sans-serif; padding: 40px; color: #1f2937; }
          .header { border-bottom: 2px solid #14345c; padding-bottom: 10px; margin-bottom: 20px; }
          .title { font-size: 24px; color: #14345c; font-weight: bold; }
          .meta { font-size: 13px; color: #6b7280; }
          .box { border: 1px solid #d1d5db; border-radius: 8px; padding: 20px; margin: 20px 0; background: #f9fafb; }
          .verdict { font-size: 20px; font-weight: bold; color: #14345c; }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="title">🔍 VerifyEngine Report</div>
          <div class="meta">Generated on ${new Date().toLocaleString()} · Analysis Type: ${type.toUpperCase()}</div>
        </div>
        <div class="box">
          <div class="verdict">Official Verdict: ${verdict}</div>
          <p>Confidence Level: ${confidence}%</p>
        </div>
        <p>This automated report provides a first-level probabilistic assessment based on signal extraction and evidence verification.</p>
        <script>window.onload = function() { window.print(); }</script>
      </body>
    </html>
  `);
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
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  target.classList.add("active");
  renderResult(target.querySelector(".result"), item, item.analysis_type === "claim");
  target.scrollIntoView({ behavior: "smooth" });
}

async function loadAdminDashboard() {
  const statsEl = $("admin-stats-grid");
  const usersEl = $("admin-users-list");
  statsEl.innerHTML = "<p class='muted'>Loading analytics…</p>";
  
  const statsRes = await fetch("/api/admin/stats", { headers: authHeaders() });
  if (!statsRes.ok) { statsEl.innerHTML = "<p class='error'>Failed to load admin stats.</p>"; return; }
  const stats = await statsRes.json();
  
  statsEl.innerHTML = `
    <div class="stat-card"><div class="num">${stats.total_users}</div><div class="lbl">Users</div></div>
    <div class="stat-card"><div class="num">${stats.total_analyses}</div><div class="lbl">Total Analyses</div></div>
    <div class="stat-card"><div class="num">${stats.claim_count}</div><div class="lbl">Claims Checked</div></div>
    <div class="stat-card"><div class="num">${stats.text_count}</div><div class="lbl">AI Text Checks</div></div>
    <div class="stat-card"><div class="num">${stats.image_count}</div><div class="lbl">AI Image Checks</div></div>
  `;

  const usersRes = await fetch("/api/admin/users", { headers: authHeaders() });
  if (usersRes.ok) {
    const users = await usersRes.json();
    usersEl.innerHTML = users.map(u => `
      <div class="history-card">
        <strong>${escapeHtml(u.name)}</strong> (${escapeHtml(u.email)})
        ${u.is_admin ? '<span class="badge badge-agrees">ADMIN</span>' : ''}
        <div class="muted small">Joined: ${u.created_at}</div>
      </div>
    `).join("");
  }
}

boot();
