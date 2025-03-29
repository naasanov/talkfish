chrome.runtime.onInstalled.addListener(() => {
  console.log("Mock Interview Feedback Extension Installed");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "startRecording") {
    // Handle recording initiation
    sendResponse({ status: "Recording started" });
  } else if (message.action === "stopRecording") {
    // Handle stopping recording
    sendResponse({ status: "Recording stopped" });
  }
});

chrome.action.onClicked.addListener((tab) => {
  console.log("clicked");
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: injectOverlay
  });
});

function injectOverlay() {
  const iframe = document.createElement('iframe');
  iframe.style.backgroundColor = 'transparent';
  iframe.style.position = 'fixed';
  iframe.style.top = '10px';
  iframe.style.right = '10px';
  iframe.style.left = 'auto';
  iframe.style.width = '500px';
  iframe.style.height = '300px';
  iframe.style.border = 'none';
  iframe.style.zIndex = '9999';
  iframe.src = chrome.runtime.getURL('src/resources/overlay.html');

  document.body.appendChild(iframe);
}
