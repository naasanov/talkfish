import time
import threading
from typing import Optional, List, Dict
import whisper
import numpy as np
from queue import Queue
import time


class TranscriptionService:
    def __init__(self, model_name: str = "base", interval: float = 0.5):
        """
        Initialize the transcription service.
        
        Args:
            model_name: Whisper model to use for transcription
            interval: Time interval in seconds for processing audio chunks
        """
        self.model = whisper.load_model(model_name)
        self.interval = interval
        self.audio_queues = {
            'mic': Queue(),
            'tab': Queue()
        }
        self.transcription_buffers = {
            'mic': [],
            'tab': []
        }
        self.is_running = False
        self.processing_threads: Dict[str, Optional[threading.Thread]] = {
            'mic': None,
            'tab': None
        }

    def start(self):
        """Start the transcription service for both channels."""
        if not self.is_running:
            self.is_running = True
            for channel in ['mic', 'tab']:
                self.processing_threads[channel] = threading.Thread(
                    target=self._process_audio,
                    args=(channel,)
                )
                self.processing_threads[channel].start()

    def stop(self):
        """Stop the transcription service and process any remaining audio."""
        self.is_running = False
        for channel in ['mic', 'tab']:
            # Process any remaining audio in the queue
            self._process_remaining_audio(channel)
            if self.processing_threads[channel]:
                self.processing_threads[channel].join()

    def add_audio_data(self, audio_data: np.ndarray, channel: str):
        """
        Add audio data to the processing queue for the specified channel.
        
        Args:
            audio_data: numpy array of audio samples (should be float32)
            channel: 'mic' for microphone or 'tab' for tab audio
        """
        if channel in self.audio_queues:
            self.audio_queues[channel].put(audio_data)

    def get_transcription(self, channel: str = None) -> str:
        """
        Get the current accumulated transcription.
        
        Args:
            channel: 'mic', 'tab', or None for both channels combined
        """
        if channel:
            return " ".join(self.transcription_buffers[channel])
        else:
            mic_text = " ".join(self.transcription_buffers['mic'])
            tab_text = " ".join(self.transcription_buffers['tab'])
            return f"Microphone: {mic_text}\n\nTab Audio: {tab_text}"

    def _process_remaining_audio(self, channel: str):
        """Process any remaining audio in the queue."""
        accumulated_audio = np.array([], dtype=np.float32)
        
        # Get all remaining audio from the queue
        while not self.audio_queues[channel].empty():
            try:
                audio_chunk = self.audio_queues[channel].get_nowait()
                accumulated_audio = np.concatenate([accumulated_audio, audio_chunk])
            except:
                break

        if len(accumulated_audio) > 0:
            # Transcribe the remaining audio
            result = self.model.transcribe(accumulated_audio)
            if result["text"].strip():
                self.transcription_buffers[channel].append(result["text"].strip())

    def _process_audio(self, channel: str):
        """Process audio chunks for a specific channel and update transcription."""
        accumulated_audio = np.array([], dtype=np.float32)
        last_process_time = time.time()

        while self.is_running:
            try:
                audio_chunk = self.audio_queues[channel].get(timeout=0.1)
                accumulated_audio = np.concatenate([accumulated_audio, audio_chunk])
            except:
                continue

            current_time = time.time()
            if current_time - last_process_time >= self.interval:
                if len(accumulated_audio) > 0:
                    # Transcribe the accumulated audio
                    result = self.model.transcribe(accumulated_audio)
                    if result["text"].strip():
                        self.transcription_buffers[channel].append(result["text"].strip())
                    
                    # Reset the audio buffer
                    accumulated_audio = np.array([], dtype=np.float32)
                    last_process_time = current_time

# # Example usage:
# service = TranscriptionService()
# service.start()
# # # Add audio data as it comes in:
# service.add_audio_data(audio_chunk, 'mic')
# service.add_audio_data(audio_chunk, 'tab')
# # # Get transcription at any time:
# transcript = service.get_transcription()
# transcript = service.get_transcription('mic')
# transcript = service.get_transcription('tab')

# time.sleep(10)
# service.stop()
