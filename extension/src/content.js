let isRecording = false;
let serverCommLoaded = false;

// Load server communication script immediately
function loadServerCommunication() {
  const script = document.createElement('script');
  script.src = chrome.runtime.getURL('src/scripts/serverCommunication.js');
  script.onload = function() {
    console.log('Server communication script loaded successfully');
    serverCommLoaded = true;
  };
  script.onerror = function(error) {
    console.error('Failed to load server communication script:', error);
  };
  (document.head || document.documentElement).appendChild(script);
}

// Load the script right away
loadServerCommunication();

// Global function to show the modal
window.showModal = async function () {
  const modal = document.createElement('div');

  let html = null;
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
    return;
  }

  if (!html) {
    throw new Error("Modal html retrieval failed");
  }

  // Modal content
  modal.innerHTML = html;

  const logoImg = modal.querySelector('.logo');
  if (logoImg) {
    logoImg.src = chrome.runtime.getURL('assets/logo.png');
  }

  // Append modal to the body
  document.body.appendChild(modal);

  // Show the modal
  modal.style.display = 'block';

  // Setup the toggle button
  const button = document.getElementById('toggle');
  if (!button) {
    console.error('Toggle button not found in overlay');
    return;
  }

  button.addEventListener('click', function () {
    console.log('toggle clicked');
    isRecording = !isRecording;
    
    if (isRecording) {
      // Check if server communication is loaded
      if (window.serverCommunication && serverCommLoaded) {
        window.serverCommunication.startMicRecording();
      } else {
        console.error('Server communication not initialized');
        isRecording = false;
        alert('Speech analysis is not ready yet. Please try again in a moment.');
        return;
      }
      
      button.classList.add('recording');
      button.textContent = '⏸';
    } else {
      // Stop recording
      if (window.serverCommunication && serverCommLoaded) {
        window.serverCommunication.stopMicRecording();
      } else {
        console.error('Server communication not initialized');
      }
      
      button.classList.remove('recording');
      button.textContent = '▶';
    }
  });
};
