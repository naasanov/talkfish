// Simple server communication module
const SERVER_URL = "http://localhost:5002";
let feedbackIntervalId = null;
let isRecording = false;

// Check server health before using it
function checkServerHealth() {
  return fetch(`${SERVER_URL}/health`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Server health check failed: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log("Server health check:", data);
      return true;
    })
    .catch(error => {
      console.error("Server health check failed:", error);
      return false;
    });
}

// Start microphone recording
function startMicRecording() {
  // Check server health first
  checkServerHealth().then(isHealthy => {
    if (!isHealthy) {
      console.error("Cannot start recording - server is not healthy");
      alert("Unable to connect to the feedback server. Please make sure it's running.");
      return;
    }
    
    isRecording = true;
    
    // Make the request to start recording
    fetch(`${SERVER_URL}/start-recording`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        interview_type: "behavioral", 
      }),
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Start recording failed: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("Recording started:", data);
        
        // Start fetching feedback every 8 seconds
        startFeedbackInterval();
      })
      .catch(error => {
        console.error("Error starting recording:", error);
        isRecording = false;
      });
  });
}

// Stop microphone recording
function stopMicRecording() {
  isRecording = false;
  
  // Stop the feedback interval
  if (feedbackIntervalId) {
    clearInterval(feedbackIntervalId);
    feedbackIntervalId = null;
  }
  
  // Only make the request if server was healthy
  checkServerHealth().then(isHealthy => {
    if (!isHealthy) {
      console.error("Cannot stop recording properly - server is not healthy");
      return;
    }
    
    fetch(`${SERVER_URL}/stop-recording`, {
      method: "POST",
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Stop recording failed: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("Recording stopped:", data);
      })
      .catch(error => {
        console.error("Error stopping recording:", error);
      });
  });
}

// Start interval to fetch feedback
function startFeedbackInterval() {
  // Clear existing interval if any
  if (feedbackIntervalId) {
    clearInterval(feedbackIntervalId);
  }
  
  // Set new interval to fetch feedback every 8 seconds
  feedbackIntervalId = setInterval(getFeedback, 8000);
  
  // Also get feedback immediately
  getFeedback();
}

// Get feedback from the server
function getFeedback() {
  if (!isRecording) {
    return;
  }
  
  fetch(`${SERVER_URL}/get-feedback`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Get feedback failed: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.status === "success" && data.feedback) {
        // Display feedback in the overlay
        displayFeedback(data.feedback, data.transcript);
      }
    })
    .catch(error => {
      console.error("Error getting feedback:", error);
    });
}

// Display feedback in the overlay
function displayFeedback(feedback, transcript) {
  // Clear existing cards
  const cardContainer = document.querySelector('.card-container');
  if (!cardContainer) {
    console.error('Card container not found');
    return;
  }
  
  // Clear all existing cards
  cardContainer.innerHTML = '';
  
  // Create transcript card
  if (transcript) {
    const transcriptCard = document.createElement('div');
    transcriptCard.className = 'card question';
    
    const transcriptTitle = document.createElement('h3');
    transcriptTitle.textContent = 'You Said';
    transcriptCard.appendChild(transcriptTitle);
    
    const transcriptContent = document.createElement('p');
    transcriptContent.textContent = transcript;
    transcriptCard.appendChild(transcriptContent);
    
    cardContainer.appendChild(transcriptCard);
  }
  
  // Create feedback card
  const feedbackCard = document.createElement('div');
  feedbackCard.className = `card ${feedback.type || 'neutral'}`;
  
  const feedbackTitle = document.createElement('h3');
  feedbackTitle.textContent = 'Feedback';
  feedbackCard.appendChild(feedbackTitle);
  
  const feedbackContent = document.createElement('p');
  feedbackContent.textContent = feedback.message;
  feedbackCard.appendChild(feedbackContent);
  
  cardContainer.appendChild(feedbackCard);
  
  // Create suggestion card if available
  if (feedback.details && feedback.details.suggestion) {
    const suggestionCard = document.createElement('div');
    suggestionCard.className = 'card tips';
    
    const suggestionTitle = document.createElement('h3');
    suggestionTitle.textContent = 'Suggestion';
    suggestionCard.appendChild(suggestionTitle);
    
    const suggestionContent = document.createElement('p');
    suggestionContent.textContent = feedback.details.suggestion;
    suggestionCard.appendChild(suggestionContent);
    
    cardContainer.appendChild(suggestionCard);
  }
}

// Export functions
window.serverCommunication = {
  startMicRecording,
  stopMicRecording,
  getFeedback
};
  