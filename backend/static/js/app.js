// ---------- state ----------
let token = localStorage.getItem("token");
let currentUser = null;
let mode = "login"; // login | register
let claimInputMode = "text"; // text | url
let selectedImageFile = null;

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
  const btn = $("auth-btn");
  setButtonLoading(btn, true, mode === "register" ? "Creating Account..." : "Logging in...");
  const url = mode === "register" ? "/api/auth/register" : "/api/auth/login";
  const body = { email: $("auth-email").value, password: $("auth-password").value };
  if (mode === "register") body.name = $("auth-name").value;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { $("auth-error").textContent = data.detail || "Something went wrong"; setButtonLoading(btn, false, mode === "register" ? "Create Account" : "Login"); return; }
    token = data.access_token;
    localStorage.setItem("token", token);
    await boot();
  } catch (err) {
    $("auth-error").textContent = "Network error connecting to server.";
  } finally {
    setButtonLoading(btn, false, mode === "register" ? "Create Account" : "Login");
  }
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
    if (btn.dataset.mode === "eval") loadEvalDashboard();
    if (btn.dataset.mode === "admin") loadAdminDashboard();
  };
});

// ---------- UI Interactive Helpers ----------
function setButtonLoading(btn, loading, text) {
  if (loading) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Processing...`;
  } else {
    btn.disabled = false;
    btn.textContent = text;
  }
}

function updateCharCount(inputId, countId, minLen, maxLen) {
  const input = $(inputId);
  const countEl = $(countId);
  const len = input.value.length;
  countEl.textContent = `${len} / ${maxLen} chars`;
  if (len < minLen && len > 0) {
    countEl.style.color = "#dc2626";
    countEl.textContent = `${len} / ${maxLen} chars (Min ${minLen} required)`;
  } else {
    countEl.style.color = "var(--text-muted)";
  }
}

function fillClaim(claimText) {
  $("claim-input").value = claimText;
  updateCharCount('claim-input', 'claim-char-count', 10, 1000);
}

function setClaimInputMode(m) {
  claimInputMode = m;
  $("btn-claim-text-mode").classList.toggle("active", m === "text");
  $("btn-claim-url-mode").classList.toggle("active", m === "url");
  $("claim-text-group").style.display = m === "text" ? "block" : "none";
  $("claim-url-group").style.display = m === "url" ? "block" : "none";
}

// Drag & Drop Image Handling
const dropZone = $("drop-zone");
if (dropZone) {
  dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.style.borderColor = "var(--primary)"; });
  dropZone.addEventListener("dragleave", () => { dropZone.style.borderColor = "var(--border-color)"; });
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--border-color)";
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      selectedImageFile = e.dataTransfer.files[0];
      previewImage(selectedImageFile);
    }
  });
}

function handleImageSelect(e) {
  if (e.target.files && e.target.files[0]) {
    selectedImageFile = e.target.files[0];
    previewImage(selectedImageFile);
  }
}

function previewImage(file) {
  const preview = $("image-preview");
  const reader = new FileReader();
  reader.onload = (e) => {
    preview.src = e.target.result;
    preview.style.display = "inline-block";
  };
  reader.readAsDataURL(file);
}

// ---------- verdict & rendering ----------
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
    html += `
      <div class="legend">
        <div class="legend-item"><span class="dot-ai"></span> AI-like Sentence Pattern</div>
        <div class="legend-item"><span class="dot-human"></span> Human-like Sentence Structure</div>
      </div>
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
          body { font-family: sans-serif; padding: 40px; color: #0f172a; }
          .header { border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; margin-bottom: 20px; }
          .title { font-size: 24px; color: #1e3a8a; font-weight: bold; }
          .meta { font-size: 13px; color: #64748b; }
          .box { border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; margin: 20px 0; background: #f8fafc; }
          .verdict { font-size: 20px; font-weight: bold; color: #1e3a8a; }
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
        <p>This automated report provides a first-level probabilistic assessment based on signal extraction and evidence retrieval.</p>
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
  const btn = $("btn-verify-claim");
  const el = $("claim-result");
  setButtonLoading(btn, true);
  el.innerHTML = "<p class='muted'>Verifying claim & searching evidence…</p>";
  
  const isUrl = claimInputMode === "url";
  const endpoint = isUrl ? "/api/verify-url" : "/api/verify-claim";
  const payload = isUrl ? { url: $("url-input").value } : { claim: $("claim-input").value };

  try {
    const res = await fetch(endpoint, {
      method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) { el.innerHTML = `<p class="error">${data.detail || "Error processing claim"}</p>`; return; }
    renderResult(el, data, true);
  } catch (e) {
    el.innerHTML = `<p class="error">Network error verifying claim.</p>`;
  } finally {
    setButtonLoading(btn, false, "Verify Claim");
  }
}

async function submitText() {
  const btn = $("btn-verify-text");
  const el = $("text-result");
  setButtonLoading(btn, true);
  el.innerHTML = "<p class='muted'>Analysing sentence signals…</p>";
  
  try {
    const res = await fetch("/api/detect-text", {
      method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ text: $("text-input").value }),
    });
    const data = await res.json();
    if (!res.ok) { el.innerHTML = `<p class="error">${data.detail || "Error analysing text"}</p>`; return; }
    renderResult(el, data, false);
  } catch (e) {
    el.innerHTML = `<p class="error">Network error analysing text.</p>`;
  } finally {
    setButtonLoading(btn, false, "Analyse Text");
  }
}

async function submitImage() {
  const btn = $("btn-verify-image");
  const el = $("image-result");
  const file = selectedImageFile || ($("image-input").files && $("image-input").files[0]);
  if (!file) { el.innerHTML = `<p class="error">Please select or drop an image file first.</p>`; return; }
  
  setButtonLoading(btn, true);
  el.innerHTML = "<p class='muted'>Analysing ELA & FFT frequency spectrum…</p>";
  
  const fd = new FormData();
  fd.append("file", file);
  
  try {
    const res = await fetch("/api/detect-image", { method: "POST", headers: authHeaders(), body: fd });
    const data = await res.json();
    if (!res.ok) { el.innerHTML = `<p class="error">${data.detail || "Error analysing image"}</p>`; return; }
    renderResult(el, data, false);
  } catch (e) {
    el.innerHTML = `<p class="error">Network error analysing image.</p>`;
  } finally {
    setButtonLoading(btn, false, "Analyse Image");
  }
}

// ---------- History & Filters ----------
async function loadHistory() {
  const el = $("history-list");
  const typeFilter = $("history-filter-type").value;
  const searchQuery = $("history-search").value;
  
  el.innerHTML = `
    <div style="text-align:center; padding:20px;">
      <span class="spinner" style="border-top-color:var(--primary); width:24px; height:24px;"></span>
      <p class="muted small" style="margin-top:8px;">Loading analysis history…</p>
    </div>`;

  let url = `/api/history?type=${typeFilter}`;
  if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;

  try {
    const res = await fetch(url, { headers: authHeaders() });
    const data = await res.json();
    if (!data.length) {
      el.innerHTML = `
        <div style="text-align:center; padding:30px;">
          <p class="muted">No matching analysis history found.</p>
        </div>`;
      return;
    }
    el.innerHTML = data.map(item => `
      <div class="history-card">
        <div onclick='showHistoryItem(${JSON.stringify(item)})' style="cursor:pointer; flex:1;">
          <span class="badge">${item.analysis_type.toUpperCase()}</span>
          <span class="badge">${item.verdict}</span>
          <span class="muted small">${item.created_at}</span>
          <p class="small" style="margin-top:4px;">${escapeHtml((item.input_text || item.input_image || "").slice(0, 100))}</p>
        </div>
        <button class="btn-ghost small" style="color:#dc2626; border-color:#fee2e2;" onclick="deleteHistoryEntry(event, ${item.id})">Delete</button>
      </div>`).join("");
  } catch (e) {
    el.innerHTML = `<p class="error">Failed to load history.</p>`;
  }
}

async function deleteHistoryEntry(event, id) {
  event.stopPropagation();
  if (!confirm("Are you sure you want to delete this analysis record?")) return;
  await fetch(`/api/history/${id}`, { method: "DELETE", headers: authHeaders() });
  loadHistory();
}

function exportHistoryCsv() {
  window.open("/api/history/export/csv", "_blank");
}

function showHistoryItem(item) {
  const target = $("panel-" + (item.analysis_type === "claim" ? "claim" : item.analysis_type));
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  target.classList.add("active");
  renderResult(target.querySelector(".result"), item, item.analysis_type === "claim");
  target.scrollIntoView({ behavior: "smooth" });
}

// ---------- Benchmark & Admin Dashboards ----------
async function loadEvalDashboard() {
  const grid = $("eval-metrics-grid");
  const detailsBox = $("eval-details-box");
  grid.innerHTML = "<p class='muted'>Calculating benchmark evaluation metrics…</p>";
  
  try {
    const res = await fetch("/api/eval/benchmark");
    const evalData = await res.json();
    
    grid.innerHTML = `
      <div class="stat-card"><div class="num">${Math.round(evalData.accuracy * 100)}%</div><div class="lbl">ML Accuracy</div></div>
      <div class="stat-card"><div class="num">${Math.round(evalData.precision * 100)}%</div><div class="lbl">Precision</div></div>
      <div class="stat-card"><div class="num">${Math.round(evalData.recall * 100)}%</div><div class="lbl">Recall</div></div>
      <div class="stat-card"><div class="num">${Math.round(evalData.f1_score * 100)}%</div><div class="lbl">F1 Score</div></div>
      <div class="stat-card"><div class="num">${evalData.dataset_size}</div><div class="lbl">Labeled Samples</div></div>
    `;

    detailsBox.innerHTML = `
      <h4>Model Evaluation Details:</h4>
      <p><strong>Tested Classifier:</strong> ${evalData.ml_model}</p>
      <p><strong>Baseline Rule-based Accuracy:</strong> ${Math.round(evalData.heuristic_baseline_accuracy * 100)}%</p>
      <p><strong>Confusion Matrix:</strong> True Negatives: ${evalData.confusion_matrix.true_negatives}, True Positives: ${evalData.confusion_matrix.true_positives}, False Positives: ${evalData.confusion_matrix.false_positives}, False Negatives: ${evalData.confusion_matrix.false_negatives}</p>
      <p class="small muted" style="margin-top:8px;">${evalData.comparison_summary}</p>
    `;
  } catch (e) {
    grid.innerHTML = "<p class='error'>Failed to load benchmark evaluation.</p>";
  }
}

async function loadAdminDashboard() {
  const statsEl = $("admin-stats-grid");
  const usersEl = $("admin-users-list");
  statsEl.innerHTML = "<p class='muted'>Loading platform statistics…</p>";
  
  try {
    const statsRes = await fetch("/api/admin/stats", { headers: authHeaders() });
    if (!statsRes.ok) { statsEl.innerHTML = "<p class='error'>Admin authorization required.</p>"; return; }
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
          <div>
            <strong>${escapeHtml(u.name)}</strong> (${escapeHtml(u.email)})
            ${u.is_admin ? '<span class="badge badge-agrees">ADMIN</span>' : ''}
            <div class="muted small">API Key: <code>${u.api_key || 'None'}</code> · Joined: ${u.created_at}</div>
          </div>
        </div>
      `).join("");
    }
  } catch (e) {
    statsEl.innerHTML = "<p class='error'>Failed to load admin analytics.</p>";
  }
}

boot();
