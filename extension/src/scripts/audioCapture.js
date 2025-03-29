navigator.mediaDevices.getUserMedia({ audio: true })
  .then((stream) => {
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    mediaRecorder.ondataavailable = (event) => {
      const audioBlob = event.data;
      // Send audioBlob to the server for processing
      sendAudioToServer(audioBlob);
    };

    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());
    };

    // Stop recording after a predefined duration
    setTimeout(() => {
      mediaRecorder.stop();
    }, 60000); // Record for 60 seconds
  })
  .catch((error) => {
    console.error("Microphone access denied:", error);
  });
