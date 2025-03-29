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
  