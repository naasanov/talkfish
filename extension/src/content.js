// Inject audio capture and feedback display scripts into the page
const scripts = ["scripts/audioCapture.js", "scripts/feedbackDisplay.js"];

scripts.forEach((script) => {
  const scriptElement = document.createElement("script");
  scriptElement.src = chrome.runtime.getURL(script);
  document.head.appendChild(scriptElement);
});
