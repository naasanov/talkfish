// audioCapture.js
class AudioCapture {
    constructor() {
      this.audioContext = null;
      this.microphoneStream = null;
      this.tabAudioStream = null;
      this.mixedStream = null;
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
  
        // 1. Get microphone stream (interviewee)
        const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.microphoneStream = this.audioContext.createMediaStreamSource(micStream);
        console.log("Microphone stream initialized");
  
        // 2. Get tab audio stream (interviewer) using chrome.tabCapture
        await new Promise((resolve, reject) => {
          chrome.tabCapture.capture({ audio: true, video: false }, (tabStream) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
              return;
            }
            
            if (tabStream) {
              this.tabAudioStream = this.audioContext.createMediaStreamSource(tabStream);
              console.log("Tab audio stream initialized");
              resolve();
            } else {
              reject(new Error("Failed to capture tab audio"));
            }
          });
        });
  
        // 3. Mix both audio streams
        const merger = this.audioContext.createChannelMerger(2);
        this.microphoneStream.connect(merger, 0, 0); // Microphone to left channel
        this.tabAudioStream.connect(merger, 0, 1);  // Tab audio to right channel
  
        // Create a destination for the merged stream
        const destination = this.audioContext.createMediaStreamDestination();
        merger.connect(destination);
        this.mixedStream = destination.stream;
  
        // 4. Start recording the mixed stream
        this.mediaRecorder = new MediaRecorder(this.mixedStream);
        
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
      
      // Send to server for processing
      const serverCommunication = new ServerCommunication();
      const feedback = await serverCommunication.sendAudioForProcessing(audioBlob);
      
      // Display feedback
      const feedbackDisplay = new FeedbackDisplay();
      feedbackDisplay.showFeedback(feedback);
      
      this.cleanup();
    }
  
    cleanup() {
      // Close audio streams and reset state
      if (this.microphoneStream) {
        this.microphoneStream.mediaStream.getTracks().forEach(track => track.stop());
        this.microphoneStream = null;
      }
      
      if (this.tabAudioStream) {
        this.tabAudioStream.mediaStream.getTracks().forEach(track => track.stop());
        this.tabAudioStream = null;
      }
      
      this.audioChunks = [];
      this.mediaRecorder = null;
      this.mixedStream = null;
    }
  }
  
  // Export for use in other modules
  export default AudioCapture;