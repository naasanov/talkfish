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

  // Append modal to the body
  document.body.appendChild(modal);

  // Show the modal
  modal.style.display = 'block';

  // Close modal function
  function closeModal() {
    modal.style.display = 'none';
  }

  // Event listeners
  // document.getElementById('closeModal').addEventListener('click', closeModal);

  // Example of running a script from the modal
  document.getElementById('toggle').addEventListener('click', function () {
    isRecording = !isRecording;
    const button = document.getElementById('toggle');
    if (isRecording) {
      button.classList.add('recording');
      button.textContent = '⏸';
    } else {
      button.classList.remove('recording');
      button.textContent = '▶';
    }
  });
};
