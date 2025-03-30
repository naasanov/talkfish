// background.js
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

async function injectOverlay() {
  const overlayContainer = document.createElement('div');
  overlayContainer.style.backgroundColor = 'transparent';
  overlayContainer.style.position = 'fixed';
  overlayContainer.style.top = '10px';
  overlayContainer.style.right = '10px';
  overlayContainer.style.left = 'auto';
  overlayContainer.style.width = '500px';
  overlayContainer.style.height = '300px';
  overlayContainer.style.border = 'none';
  overlayContainer.style.zIndex = '9999';

  // use shadow DOM for proper security and interface
  const shadow = overlayContainer.attachShadow({ mode: "open" });

  try {
    const response = await fetch(chrome.runtime.getURL("src/resources/overlay.html"));
    const html = await response.text();

    const overlayContent = document.createElement('div');
    overlayContent.innerHTML = html;

    shadow.appendChild(overlayContent);
    document.body.appendChild(overlayContainer);

    const scripts = ["overlay.js"].map(s => `src/scripts/${s}`)
    scripts.forEach((script) => {
      // Instead of injecting as a script tag, fetch and execute the code
      fetch(chrome.runtime.getURL(script))
        .then(response => response.text())
        .then(code => {
          const scriptElement = document.createElement("script");
          // Wrap the code to provide access to shadow DOM elements
          scriptElement.textContent = `
            (function(root) {
              ${code}
            })(document.querySelector('div').shadowRoot);
          `;
          shadow.appendChild(scriptElement);
        });
    });
  } catch (error) {
    console.error("Error loading overlay.html:", error);
  }
}
