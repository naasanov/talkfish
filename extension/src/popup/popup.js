document.getElementById('triggerModal').addEventListener('click', () => {
  console.log("clicked");

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      console.log("Tab found:", tabs[0].id);

      // Execute showModal function in the content script's context
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        func: function() {
          // This is the code that runs in the page's context
          if (window.showModal) {
            window.showModal();
          } else {
            console.error('showModal function is not defined in the content script.');
          }
        }
      }, (result) => {
        console.log("Script executed", result);
      });
    } else {
      console.error("No active tab found.");
    }
  });
});
