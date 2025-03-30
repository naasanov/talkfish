let isRecording = false

// Global function to show the modal
window.showModal = async function () {
  const modal = document.createElement('div');

  let html = null
  try {
    const response = await fetch(chrome.runtime.getURL('src/resources/overlay.html'));
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    html = await response.text();
  } catch (error) {
    console.error('Failed to load overlay:', error);
    modal.textContent = 'Failed to load overlay.';
    document.body.appendChild(modal);
    modal.style.display = 'block';
  }

  if (!html) {
    throw new Error("Modal html retrieval failed")
  }

  // Modal content
  modal.innerHTML = html

  const logoImg = modal.querySelector('.logo');
  if (logoImg) {
    logoImg.src = chrome.runtime.getURL('assets/logo.png');
  }

  // Append modal to the body
  document.body.appendChild(modal);

  // Show the modal
  modal.style.display = 'block';


  function stopStreamOnServer() {
    fetch('http://localhost:5000/stop-stream', {
      method: 'POST',
    })
      .then(response => response.text())
      .then(data => {
        console.log(data);  // "Stream will stop"
      })
      .catch(error => {
        console.error("Error stopping the stream:", error);
      });
  }

  let eventSource = null

  // Example of running a script from the modal
  document.getElementById('toggle').addEventListener('click', function () {
    isRecording = !isRecording;
    const button = document.getElementById('toggle');
    if (isRecording) {
      const eventSource = new EventSource('http://localhost:5000/start-stream');
      eventSource.onmessage = (event) => {
        // add cards, etc.
      }
      button.classList.add('recording');
      button.textContent = '⏸';
    } else {
      if (eventSource) {
        eventSource.close()
      }
      stopStreamOnServer()
      button.classList.remove('recording');
      button.textContent = '▶';
    }
  });
};
