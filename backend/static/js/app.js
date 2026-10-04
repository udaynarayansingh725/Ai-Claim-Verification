// ---------- State & Configuration ----------
let token = localStorage.getItem("token");
let currentUser = null;
let mode = "login"; // login | register
let claimInputMode = "text"; // text | url
let selectedImageFile = null;
let selectedBatchFile = null;
let currentLanguage = localStorage.getItem("lang") || "en";
let evalChartInstance = null;
let adminPieChartInstance = null;
let adminBarChartInstance = null;
let activeShareVerdict = "";

const $ = (id) => document.getElementById(id);

// ---------- Language Dictionary (English & Hindi) ----------
const translations = {
  en: {
    title: "VerifyEngine — AI & Claim Verification System",
    claimNav: "Claim Verification",
    textNav: "AI Text Detection",
    imageNav: "AI Image Detection",
    batchNav: "Batch CSV",
    historyNav: "History",
    evalNav: "Benchmark & ML",
    settingsNav: "API & Extension",
    adminNav: "Admin Panel",
    claimTitle: "Verify a Factual Claim",
    claimSub: "Enter a claim or news URL — extracts keywords, searches evidence, and classifies stance.",
    tryExamples: "Try example claims:",
    verifyBtn: "Verify Claim",
    textTitle: "AI-Generated Text Detection",
    textSub: "Paste text to estimate AI probability. Features sentence-by-sentence highlight analysis.",
    analyseTextBtn: "Analyse Text",
    imageTitle: "AI-Generated Image Detection",
    imageSub: "Upload an image (JPG/PNG/WEBP/BMP, max 10 MB). Includes Error Level Analysis (ELA) visual heatmap.",
    dropText: "Click or drag & drop an image file here",
    analyseImgBtn: "Analyse Image",
    historyTitle: "Analysis History",
  },
  hi: {
    title: "VerifyEngine — AI और दावा सत्यापन प्रणाली",
    claimNav: "दावा सत्यापन",
    textNav: "AI टेक्स्ट पहचान",
    imageNav: "AI इमेज पहचान",
    batchNav: "बैच CSV",
    historyNav: "इतिहास",
    evalNav: "बेंचमार्क और ML",
    settingsNav: "API और एक्सटेंशन",
    adminNav: "एडमिन पैनल",
    claimTitle: "तथ्यात्मक दावे का सत्यापन करें",
    claimSub: "दावा या समाचार URL दर्ज करें — कीवर्ड निकालेगा, साक्ष्य खोजेगा और रुख वर्गीकृत करेगा।",
    tryExamples: "उदाहरण दावे आज़माएं:",
    verifyBtn: "दावा सत्यापित करें",
    textTitle: "AI-जनरेटेड टेक्स्ट की पहचान",
    textSub: "AI संभावना का अनुमान लगाने के लिए टेक्स्ट पेस्ट करें। वाक्य-दर-वाक्य हाइलाइट विश्लेषण।",
    analyseTextBtn: "टेक्स्ट का विश्लेषण करें",
    imageTitle: "AI-जनरेटेड इमेज की पहचान",
    imageSub: "एक इमेज अपलोड करें (JPG/PNG/WEBP/BMP, अधिकतम 10 MB)। ELA विज़ुअल हीटमैप शामिल है।",
    dropText: "यहाँ क्लिक करें या इमेज फ़ाइल खींचकर छोड़ें",
    analyseImgBtn: "इमेज का विश्लेषण करें",
    historyTitle: "विश्लेषण का इतिहास",
  }
};

function toggleLanguage() {
  currentLanguage = currentLanguage === "en" ? "hi" : "en";
  localStorage.setItem("lang", currentLanguage);
  applyTranslations();
  showToast(currentLanguage === "hi" ? "भाषा बदलकर हिंदी कर दी गई है" : "Language switched to English", "info");
}

function applyTranslations() {
  const t = translations[currentLanguage];
  $("lang-toggle").textContent = currentLanguage === "en" ? "🌐 EN" : "🌐 HI";
  
  if ($("nav-claim")) $("nav-claim").textContent = t.claimNav;
  if ($("nav-text")) $("nav-text").textContent = t.textNav;
  if ($("nav-image")) $("nav-image").textContent = t.imageNav;
  if ($("nav-batch")) $("nav-batch").textContent = t.batchNav;
  if ($("nav-history")) $("nav-history").textContent = t.historyNav;
  if ($("nav-eval")) $("nav-eval").textContent = t.evalNav;
  if ($("nav-settings")) $("nav-settings").textContent = t.settingsNav;
  if ($("nav-admin")) $("nav-admin").textContent = t.adminNav;
  
  if ($("lbl-verify-claim-title")) $("lbl-verify-claim-title").textContent = t.claimTitle;
  if ($("lbl-verify-claim-sub")) $("lbl-verify-claim-sub").textContent = t.claimSub;
  if ($("lbl-try-examples")) $("lbl-try-examples").textContent = t.tryExamples;
  if ($("btn-verify-claim")) $("btn-verify-claim").textContent = t.verifyBtn;
  
  if ($("lbl-text-title")) $("lbl-text-title").textContent = t.textTitle;
  if ($("lbl-text-sub")) $("lbl-text-sub").textContent = t.textSub;
  if ($("btn-verify-text")) $("btn-verify-text").textContent = t.analyseTextBtn;
  
  if ($("lbl-image-title")) $("lbl-image-title").textContent = t.imageTitle;
  if ($("lbl-image-sub")) $("lbl-image-sub").textContent = t.imageSub;
  if ($("lbl-drop-text")) $("lbl-drop-text").textContent = t.dropText;
  if ($("btn-verify-image")) $("btn-verify-image").textContent = t.analyseImgBtn;
  
  if ($("lbl-history-title")) $("lbl-history-title").textContent = t.historyTitle;
}

// ---------- Theme switcher ----------
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
    showToast(isDark ? "Dark theme enabled" : "Light theme enabled", "info");
  };
}

// ---------- Toast Notifications ----------
function showToast(msg, type = "info") {
  const container = $("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>ℹ️ ${escapeHtml(msg)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ---------- Auth Handlers ----------
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
    if (!res.ok) {
      $("auth-error").textContent = data.detail || "Something went wrong";
      setButtonLoading(btn, false, mode === "register" ? "Create Account" : "Login");
      return;
    }
    token = data.access_token;
    localStorage.setItem("token", token);
    showToast("Welcome to VerifyEngine!", "info");
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
  showToast("Logged out successfully.", "info");
};

function showApp(user) {
  currentUser = user;
  $("auth-screen").style.display = "none";
  $("app-screen").style.display = "block";
  $("user-name").textContent = "👤 " + user.name;
  if (user.is_admin) {
    $("nav-admin").style.display = "inline-block";
  }
  if ($("user-api-key-input")) {
    $("user-api-key-input").value = user.api_key || "None";
  }
  applyTranslations();
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

// ---------- Navigation & Tabs ----------
document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.onclick = () => switchTab(btn.dataset.mode);
});

function switchTab(targetMode) {
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  
  const targetBtn = document.querySelector(`.nav-btn[data-mode="${targetMode}"]`);
  if (targetBtn) targetBtn.classList.add("active");
  const panel = $("panel-" + targetMode);
  if (panel) panel.classList.add("active");
  
  if (targetMode === "history") loadHistory();
  if (targetMode === "eval") loadEvalDashboard();
  if (targetMode === "admin") loadAdminDashboard();
  if (targetMode === "settings") loadApiKey();
}

// ---------- Speech Voice Input (Web Speech API) ----------
function startVoiceRecognition(inputId) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast("Voice recognition is not supported in this browser.", "error");
    return;
  }
  const btn = event.currentTarget;
  btn.classList.add("listening");
  showToast("Listening... Speak your claim now.", "info");
  
  const recognition = new SpeechRecognition();
  recognition.lang = currentLanguage === "hi" ? "hi-IN" : "en-US";
  recognition.interimResults = false;
  
  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    $(inputId).value = transcript;
    updateCharCount(inputId, inputId === "claim-input" ? "claim-char-count" : "text-char-count", 10, 20000);
    showToast("Voice captured successfully!", "info");
  };
  recognition.onerror = () => showToast("Could not recognize voice. Please try again.", "error");
  recognition.onend = () => btn.classList.remove("listening");
  recognition.start();
}

// ---------- Text-to-Speech Read Aloud ----------
function readVerdictAloud(text) {
  if (!('speechSynthesis' in window)) {
    showToast("Text-to-speech not supported on this browser.", "error");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
  showToast("Playing audio summary...", "info");
}

// ---------- UI Helpers ----------
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

// ---------- Verdict & Result Rendering ----------
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
  activeShareVerdict = `VerifyEngine Verdict: ${data.verdict} (${pct}% confidence)`;
  
  let html = `<div class="verdict-card ${verdictClass(data.verdict)}">
      Verdict: ${data.verdict} (${pct}% confidence)
      <button class="btn-ghost small" style="float:right;" onclick="readVerdictAloud('Verdict is ${escapeHtml(data.verdict)} with ${pct} percent confidence.')">🔊 Listen</button>
    </div>
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
    html += "<strong style='display:block; margin-top:12px;'>Retrieved Evidence & Stance:</strong>";
    data.evidence.forEach(ev => {
      html += `<div class="evidence-item">
        <h4>${stanceBadge(ev.stance)} ${escapeHtml(ev.title)}</h4>
        <p class="small muted">${escapeHtml(ev.source)} · Keyword Match ${Math.round(ev.similarity * 100)}%
        ${ev.url ? ` · <a href="${ev.url}" target="_blank">View Source</a>` : ""}</p>
        <p class="small">${escapeHtml(ev.snippet)}</p></div>`;
    });
  }

  // Action Buttons: PDF Export & Share Modal
  html += `<div style="margin-top:16px; display:flex; gap:10px;">
    <button class="btn-secondary" onclick="downloadPdfReport('${escapeHtml(data.analysis_type || 'verification')}', '${escapeHtml(data.verdict)}', ${pct})">📥 Download PDF Report</button>
    <button class="btn-primary" style="width:auto;" onclick="$('share-modal').style.display='flex'">🔗 Share Result</button>
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

// ---------- API Calls ----------
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
    showToast("Claim verified successfully!", "info");
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
    showToast("Text analysis complete!", "info");
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
    showToast("Image forensics analysis complete!", "info");
  } catch (e) {
    el.innerHTML = `<p class="error">Network error analysing image.</p>`;
  } finally {
    setButtonLoading(btn, false, "Analyse Image");
  }
}

// ---------- Batch CSV Processing ----------
function handleBatchCsvSelect(e) {
  if (e.target.files && e.target.files[0]) {
    selectedBatchFile = e.target.files[0];
    $("batch-file-name").textContent = `Selected: ${selectedBatchFile.name}`;
  }
}

function downloadSampleCsv() {
  const sampleContent = "claim\nWater boils at 100 degrees Celsius at sea level\nThe Earth orbits the Sun once per year\nHumans use 100 percent of their brains";
  const blob = new Blob([sampleContent], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "sample_claims_template.csv";
  a.click();
  showToast("Sample CSV downloaded.", "info");
}

async function submitBatchClaims() {
  if (!selectedBatchFile) {
    showToast("Please upload a CSV file first.", "error");
    return;
  }
  const btn = $("btn-process-batch");
  const container = $("batch-results-container");
  setButtonLoading(btn, true, "Processing Batch...");
  
  const reader = new FileReader();
  reader.onload = async (e) => {
    const text = e.target.result;
    const lines = text.split("\n").map(l => l.trim()).filter(l => l && !l.toLowerCase().startsWith("claim"));
    if (!lines.length) {
      container.innerHTML = "<p class='error'>No valid claim rows found in CSV.</p>";
      setButtonLoading(btn, false, "🚀 Verify All Claims");
      return;
    }
    
    try {
      const res = await fetch("/api/verify-batch", {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ claims: lines })
      });
      const data = await res.json();
      if (!res.ok) { container.innerHTML = `<p class="error">${data.detail || "Batch error"}</p>`; return; }
      
      let html = `<h4 style="margin-top:16px;">Batch Verification Results (${data.total_processed} Claims):</h4>
        <table class="batch-table">
          <thead><tr><th>#</th><th>Claim</th><th>Verdict</th><th>Confidence</th></tr></thead>
          <tbody>`;
      data.results.forEach((r, idx) => {
        html += `<tr>
          <td>${idx + 1}</td>
          <td>${escapeHtml(lines[idx] || '')}</td>
          <td><span class="badge ${r.verdict.includes('SUPPORTED') ? 'badge-agrees' : 'badge-disagrees'}">${r.verdict}</span></td>
          <td>${Math.round(r.confidence * 100)}%</td>
        </tr>`;
      });
      html += `</tbody></table>`;
      container.innerHTML = html;
      showToast(`Batch processing finished for ${data.total_processed} claims!`, "info");
    } catch (err) {
      container.innerHTML = "<p class='error'>Failed to process batch.</p>";
    } finally {
      setButtonLoading(btn, false, "🚀 Verify All Claims");
    }
  };
  reader.readAsText(selectedBatchFile);
}

// ---------- API Key & Settings ----------
async function loadApiKey() {
  if (!currentUser) return;
  if ($("user-api-key-input")) $("user-api-key-input").value = currentUser.api_key || "None";
}

function copyApiKey() {
  const keyInput = $("user-api-key-input");
  navigator.clipboard.writeText(keyInput.value);
  showToast("API Key copied to clipboard!", "info");
}

async function regenerateApiKey() {
  if (!confirm("Are you sure you want to generate a new API key? Existing integrations will stop working.")) return;
  try {
    const res = await fetch("/api/auth/api-key", { method: "POST", headers: authHeaders() });
    const data = await res.json();
    if (res.ok) {
      currentUser.api_key = data.api_key;
      $("user-api-key-input").value = data.api_key;
      showToast("New API Key generated successfully!", "info");
    }
  } catch (e) {
    showToast("Failed to regenerate API key.", "error");
  }
}

// ---------- History & Export ----------
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
      el.innerHTML = `<div style="text-align:center; padding:30px;"><p class="muted">No matching analysis history found.</p></div>`;
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
  showToast("Record deleted.", "info");
  loadHistory();
}

function exportHistoryCsv() {
  window.open("/api/history/export/csv", "_blank");
  showToast("Downloading CSV history export...", "info");
}

function showHistoryItem(item) {
  const target = $("panel-" + (item.analysis_type === "claim" ? "claim" : item.analysis_type));
  switchTab(item.analysis_type === "claim" ? "claim" : item.analysis_type);
  renderResult(target.querySelector(".result"), item, item.analysis_type === "claim");
  target.scrollIntoView({ behavior: "smooth" });
}

// ---------- Chart.js Visual Dashboards ----------
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
      <div class="stat-card"><div class="num">${evalData.dataset_size}</div><div class="lbl">Benchmark Samples</div></div>
    `;

    detailsBox.innerHTML = `
      <h4>Model Evaluation Details:</h4>
      <p><strong>Tested Classifier:</strong> ${evalData.ml_model}</p>
      <p><strong>Baseline Rule-based Accuracy:</strong> ${Math.round(evalData.heuristic_baseline_accuracy * 100)}%</p>
      <p><strong>Confusion Matrix:</strong> True Negatives: ${evalData.confusion_matrix.true_negatives}, True Positives: ${evalData.confusion_matrix.true_positives}, False Positives: ${evalData.confusion_matrix.false_positives}, False Negatives: ${evalData.confusion_matrix.false_negatives}</p>
      <p class="small muted" style="margin-top:8px;">${evalData.comparison_summary}</p>
    `;

    // Render Canvas Chart
    renderEvalChart(evalData.accuracy, evalData.heuristic_baseline_accuracy, evalData.precision, evalData.recall);
  } catch (e) {
    grid.innerHTML = "<p class='error'>Failed to load benchmark evaluation.</p>";
  }
}

function renderEvalChart(mlAcc, heuristicAcc, precision, recall) {
  const ctx = document.getElementById("chart-eval");
  if (!ctx || typeof Chart === "undefined") return;
  if (evalChartInstance) evalChartInstance.destroy();
  
  evalChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['ML Model Accuracy', 'Heuristic Baseline', 'Precision', 'Recall'],
      datasets: [{
        label: 'Performance Score (%)',
        data: [Math.round(mlAcc * 100), Math.round(heuristicAcc * 100), Math.round(precision * 100), Math.round(recall * 100)],
        backgroundColor: ['#1e3a8a', '#38bdf8', '#22c55e', '#eab308'],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, max: 100 } }
    }
  });
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

    renderAdminCharts(stats);

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

function renderAdminCharts(stats) {
  const pieCtx = document.getElementById("chart-admin-pie");
  const barCtx = document.getElementById("chart-admin-bar");
  if (typeof Chart === "undefined") return;
  
  if (pieCtx) {
    if (adminPieChartInstance) adminPieChartInstance.destroy();
    adminPieChartInstance = new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: ['Claims', 'AI Text', 'AI Image'],
        datasets: [{
          data: [stats.claim_count, stats.text_count, stats.image_count],
          backgroundColor: ['#1e3a8a', '#0284c7', '#38bdf8']
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  if (barCtx) {
    if (adminBarChartInstance) adminBarChartInstance.destroy();
    adminBarChartInstance = new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: ['Users', 'Total Analyses'],
        datasets: [{
          label: 'Platform Totals',
          data: [stats.total_users, stats.total_analyses],
          backgroundColor: ['#22c55e', '#1e3a8a'],
          borderRadius: 6
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
    });
  }
}

// ---------- Command Palette & Modal Shortcuts ----------
function toggleCmdPalette() {
  const modal = $("cmd-modal");
  const isHidden = modal.style.display === "none";
  modal.style.display = isHidden ? "flex" : "none";
  if (isHidden) $("cmd-input").focus();
}

function closeCmdPalette(e) {
  $("cmd-modal").style.display = "none";
}

document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    toggleCmdPalette();
  }
  if (e.key === "Escape") {
    $("cmd-modal").style.display = "none";
    $("share-modal").style.display = "none";
  }
});

function filterCmdOptions() {
  const q = $("cmd-input").value.toLowerCase();
  document.querySelectorAll(".cmd-item").forEach(item => {
    item.style.display = item.textContent.toLowerCase().includes(q) ? "flex" : "none";
  });
}

function execCmd(command) {
  closeCmdPalette();
  if (command === "theme") themeBtn.click();
  else if (command === "lang") toggleLanguage();
  else switchTab(command);
}

// ---------- Share Result Handler ----------
function shareSocial(platform) {
  const shareText = encodeURIComponent(activeShareVerdict || "Check out VerifyEngine AI Claim Verification!");
  const url = encodeURIComponent(window.location.origin);
  
  if (platform === "whatsapp") window.open(`https://api.whatsapp.com/send?text=${shareText}%20${url}`, "_blank");
  if (platform === "twitter") window.open(`https://twitter.com/intent/tweet?text=${shareText}&url=${url}`, "_blank");
  if (platform === "linkedin") window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, "_blank");
}

function copyShareLink() {
  navigator.clipboard.writeText(window.location.href);
  showToast("Share link copied to clipboard!", "info");
  $("share-modal").style.display = "none";
}

boot();
