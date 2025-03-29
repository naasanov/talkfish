function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob);
  
    fetch("http://localhost:5000/process_audio", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        // Display feedback received from the server
        displayFeedback(data);
      })
      .catch((error) => {
        console.error("Error sending audio to server:", error);
      });
  }
  