document.addEventListener("DOMContentLoaded", async () => {
  const textEl = document.getElementById("check-text");
  const resultEl = document.getElementById("result");
  const apiUrlEl = document.getElementById("api-url");

  // Auto-fill selected text from active tab
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.id) {
      const [{ result }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => window.getSelection().toString()
      });
      if (result) textEl.value = result.trim();
    }
  } catch (e) {}

  document.getElementById("btn-claim").onclick = async () => {
    const text = textEl.value.trim();
    if (!text) return;
    resultEl.innerHTML = "Verifying claim...";
    try {
      const res = await fetch(`${apiUrlEl.value}/api/verify-claim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claim: text })
      });
      const data = await res.json();
      resultEl.innerHTML = `<strong>Verdict: ${data.verdict}</strong> (${Math.round(data.confidence * 100)}% confidence)`;
    } catch (e) {
      resultEl.innerHTML = "Error connecting to server.";
    }
  };

  document.getElementById("btn-text").onclick = async () => {
    const text = textEl.value.trim();
    if (!text) return;
    resultEl.innerHTML = "Analysing text...";
    try {
      const res = await fetch(`${apiUrlEl.value}/api/detect-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
      });
      const data = await res.json();
      resultEl.innerHTML = `<strong>Verdict: ${data.verdict}</strong> (${Math.round(data.confidence * 100)}% confidence)`;
    } catch (e) {
      resultEl.innerHTML = "Error connecting to server.";
    }
  };
});
