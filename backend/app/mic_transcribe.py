import pyaudio
import numpy as np
import time
import threading
from typing import Optional
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.transcription_service import TranscriptionService

class MicrophoneTranscriber:
    def __init__(self, chunk_size: int = 1024, sample_rate: int = 16000):
        """
        Initialize the microphone transcriber.
        
        Args:
            chunk_size: Number of audio frames per buffer
            sample_rate: Audio sample rate (Hz)
        """
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.format = pyaudio.paFloat32
        self.channels = 1
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Initialize transcription service
        self.transcription_service = TranscriptionService(interval=0.5)  # Process every 0.5 seconds
        self.transcription_service.start()
        
        # Recording control
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None

    def start_recording(self):
        """Start recording from the microphone."""
        if not self.is_recording:
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()

    def stop_recording(self):
        """Stop recording from the microphone."""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        self.transcription_service.stop()
        self.audio.terminate()

    def get_transcription(self) -> str:
        """Get the current transcription."""
        return self.transcription_service.get_transcription('mic')

    def _record_audio(self):
        """Record audio from microphone and send to transcription service."""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

        print("Recording started...")
        
        try:
            while self.is_recording:
                # Read audio data
                data = stream.read(self.chunk_size)
                audio_data = np.frombuffer(data, dtype=np.float32)
                
                # Send to transcription service
                self.transcription_service.add_audio_data(audio_data, 'mic')
                
        finally:
            stream.stop_stream()
            stream.close()

if __name__ == "__main__":
    print("Initializing microphone transcriber...")
    transcriber = MicrophoneTranscriber()
    
    try:
        print("Starting recording. Will record for 10 seconds...")
        transcriber.start_recording()
        
        # Record for 10 seconds while showing intermediate transcriptions
        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(0.5)  # Check every 0.5 seconds
            transcript = transcriber.get_transcription()
            if transcript:  # Only print if there's actual transcription
                print("\rCurrent transcription:", transcript, end="", flush=True)
        
        # Stop recording and get final transcription
        print("\n\nStopping recording...")
        transcriber.stop_recording()
        
        # Get and print final transcription
        final_transcript = transcriber.get_transcription()
        print("\nFinal Transcription:")
        print(final_transcript)
        
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        # Clean up
        print("Done!")
