import numpy as np
import time
import threading
from typing import Optional
import os
import sys
from queue import Queue

# Add the backend directory to Python path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.transcription_service import TranscriptionService
from app.nlp_analysis import analyze_transcript

class TabTranscriber:
    def __init__(self, chunk_size: int = 1024, sample_rate: int = 16000, interview_type: str = 'behavioral'):
        """
        Initialize the tab audio transcriber.
        
        Args:
            chunk_size: Number of audio frames per buffer
            sample_rate: Audio sample rate (Hz)
            interview_type: Type of interview for analysis
        """
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.interview_type = interview_type
        
        # Initialize transcription service
        self.transcription_service = TranscriptionService(interval=0.5)  # Process every 0.5 seconds
        self.transcription_service.start()
        
        # Recording control
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None
        self.audio_queue = Queue()
        
        # Buffer for accumulating audio data
        self.buffer_size = int(self.sample_rate * 0.5)  # 0.5 seconds of audio
        self.audio_buffer = np.array([], dtype=np.float32)

    def start_recording(self):
        """Start processing tab audio."""
        if not self.is_recording:
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._process_audio)
            self.recording_thread.start()

    def stop_recording(self):
        """Stop processing tab audio."""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        self.transcription_service.stop()

    def add_audio_data(self, audio_data: np.ndarray):
        """
        Add audio data from the tab to the processing queue.
        
        Args:
            audio_data: Audio data as numpy array (float32)
        """
        if self.is_recording:
            # Ensure audio data is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize if not already in [-1, 1]
            if np.abs(audio_data).max() > 1.0:
                audio_data = audio_data / np.abs(audio_data).max()
            
            # Add to buffer
            self.audio_buffer = np.concatenate([self.audio_buffer, audio_data])
            
            # Process buffer when it reaches the target size
            while len(self.audio_buffer) >= self.buffer_size:
                # Extract chunk and update buffer
                chunk = self.audio_buffer[:self.buffer_size]
                self.audio_buffer = self.audio_buffer[self.buffer_size:]
                
                # Send to transcription service
                self.audio_queue.put(chunk)

    def get_transcription(self) -> str:
        """Get the current transcription."""
        return self.transcription_service.get_transcription('tab')

    def analyze_transcript(self, transcript: str) -> dict:
        """
        Analyze the transcript using the NLP service.
        
        Args:
            transcript: Text to analyze
        
        Returns:
            Dictionary containing feedback and analysis
        """
        return analyze_transcript(transcript, self.interview_type)

    def _process_audio(self):
        """Process audio data from the tab and send to transcription service."""
        print("Tab audio processing started...")
        
        try:
            while self.is_recording:
                try:
                    # Get audio data from queue
                    audio_data = self.audio_queue.get(timeout=0.1)
                    
                    # Send to transcription service
                    self.transcription_service.add_audio_data(audio_data, 'tab')
                    
                except:  # Queue empty or other error
                    continue
                    
        finally:
            # Process any remaining audio in the buffer
            if len(self.audio_buffer) > 0:
                self.transcription_service.add_audio_data(self.audio_buffer, 'tab')
            print("Tab audio processing stopped.")

def main():
    """
    Example usage of TabTranscriber.
    Note: This is just for testing. In practice, audio data should come from the browser.
    """
    print("Initializing tab transcriber...")
    transcriber = TabTranscriber()
    
    try:
        print("Starting tab audio processing. Will run for 30 seconds...")
        transcriber.start_recording()
        
        # Simulate receiving tab audio for 30 seconds
        start_time = time.time()
        timer = 0
        print("Processing started...\n\n")
        
        while time.time() - start_time < 30:
            time.sleep(1)  # Check every 1 second
            if timer % 5 == 0:
                print("Current time: ", timer, "seconds")
            timer += 1
            
            # Get and show current transcription
            transcript = transcriber.get_transcription()
            print("\rCurrent transcription:", transcript, end="", flush=True)
            
            # Simulate receiving audio data (in practice, this comes from the browser)
            dummy_audio = np.zeros(16000 // 10, dtype=np.float32)  # 0.1s of silence
            transcriber.add_audio_data(dummy_audio)
        
        # Stop recording and get final transcription
        print("\n\nStopping processing...")
        transcriber.stop_recording()
        
        # Get and print final transcription
        final_transcript = transcriber.get_transcription()
        print("\nFinal Transcription:")
        print(final_transcript)
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
    finally:
        # Clean up and analyze
        print("Done! \n Now getting the API evaluation...")
        analysis = transcriber.analyze_transcript(final_transcript)
        print("\nAPI evaluation complete.")
        print("Analysis:", analysis)

if __name__ == "__main__":
    main()
