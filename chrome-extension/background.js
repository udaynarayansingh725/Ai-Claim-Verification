chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "verify-engine-claim",
    title: "🔍 Verify Claim with VerifyEngine",
    contexts: ["selection"]
  });
  chrome.contextMenus.create({
    id: "verify-engine-ai",
    title: "🤖 Check AI Text Likelihood",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const selectedText = info.selectionText;
  if (!selectedText) return;

  const endpoint = info.menuItemId === "verify-engine-claim" ? "/api/verify-claim" : "/api/detect-text";
  const payload = info.menuItemId === "verify-engine-claim" ? { claim: selectedText } : { text: selectedText };

  fetch(`https://ai-claim-verification.onrender.com${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(data => {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: (verdict, confidence) => {
        alert(`🔍 VerifyEngine Result:\n\nVerdict: ${verdict}\nConfidence: ${Math.round(confidence * 100)}%`);
      },
      args: [data.verdict, data.confidence]
    });
  })
  .catch(err => {
    console.error("VerifyEngine Error:", err);
  });
});
