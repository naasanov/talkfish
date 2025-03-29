function displayFeedback(feedbackData) {
    let feedbackElement = document.getElementById("feedback");
    if (!feedbackElement) {
      feedbackElement = document.createElement("div");
      feedbackElement.id = "feedback";
      document.body.appendChild(feedbackElement);
    }
  
    feedbackElement.innerText = feedbackData.message;
    feedbackElement.className = feedbackData.type; // Apply styling based on feedback type
  }
  