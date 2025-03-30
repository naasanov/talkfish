chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'makeRequest') {
    fetch(request.url)
      .then(response => response.json())
      .then(data => {
        sendResponse({ status: 'success', data: data });
      })
      .catch(error => {
        sendResponse({ status: 'error', error: error.message });
      });
    return true;  // Required to send response asynchronously
  }
});
