// background.js
chrome.runtime.onInstalled.addListener(() => {
    console.log("Mock Interview Feedback Extension Installed");
  });
  
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "startRecording") {
      // Request tab capture permission if needed
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]) {
          chrome.tabCapture.capture({
            audio: true,
            video: false
          }, (stream) => {
            if (chrome.runtime.lastError) {
              sendResponse({
                status: "error",
                message: chrome.runtime.lastError.message
              });
            } else if (stream) {
              // We don't need to do anything with the stream here
              // The AudioCapture class will handle it
              stream.getTracks().forEach(track => track.stop());
              sendResponse({
                status: "success",
                message: "Tab capture permission granted"
              });
            }
          });
        }
      });
      return true; // Required to use sendResponse asynchronously
    } else if (message.action === "stopRecording") {
      sendResponse({ status: "Recording stopped" });
    }
  });