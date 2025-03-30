const ServerCommunication = require("./serverCommunication");

class AudioCapture {
    constructor() {
      this.audioContext = null;
      this.microphoneStream = null;
      this.mediaRecorder = null;
      this.audioChunks = [];
      this.isRecording = false;
    }
  
    async initialize() {
      try {
        // Create audio context
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log("Audio context initialized");
      } catch (error) {
        console.error("Failed to initialize audio context:", error);
        throw error;
      }
    }
  
    async startRecording() {
      if (this.isRecording) {
        console.log("Already recording");
        return;
      }
  
      try {
        if (!this.audioContext) {
          await this.initialize();
        }
  
        // Reset audio chunks
        this.audioChunks = [];
  
        // Get microphone stream (interviewee)
        const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.microphoneStream = this.audioContext.createMediaStreamSource(micStream);
        console.log("Microphone stream initialized");
  
        // Create a destination for the microphone stream
        const destination = this.audioContext.createMediaStreamDestination();
        this.microphoneStream.connect(destination);
  
        // Start recording the microphone stream
        this.mediaRecorder = new MediaRecorder(destination.stream);
        
        this.mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            this.audioChunks.push(event.data);
          }
        };
  
        this.mediaRecorder.onstop = () => {
          console.log("Recording stopped, processing audio...");
          this.processAudio();
        };
  
        this.mediaRecorder.start(1000); // Collect data every second
        this.isRecording = true;
        console.log("Recording started");
  
        return true;
      } catch (error) {
        console.error("Failed to start recording:", error);
        this.cleanup();
        throw error;
      }
    }
  
    stopRecording() {
      if (!this.isRecording || !this.mediaRecorder) {
        console.log("Not recording");
        return;
      }
  
      console.log("Stopping recording...");
      this.mediaRecorder.stop();
      this.isRecording = false;
    }
  
    async processAudio() {
      if (this.audioChunks.length === 0) {
        console.log("No audio data to process");
        return;
      }
  
      // Create a blob from the audio chunks
      const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm; codecs=opus' });
      console.log(audioBlob);
      
      this.cleanup();
    }
  
    cleanup() {
      // Close audio streams and reset state
      if (this.microphoneStream) {
        this.microphoneStream.mediaStream.getTracks().forEach(track => track.stop());
        this.microphoneStream = null;
      }
      
      this.audioChunks = [];
      this.mediaRecorder = null;
    }
  }
  
  // Export for use in other modules
  module.exports = AudioCapture;