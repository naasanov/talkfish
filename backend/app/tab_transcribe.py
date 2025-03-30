import pyaudio
import numpy as np
import time
import os
import sys

# Add the backend directory to Python path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.transcription_service import TranscriptionService

class VirtualInputDevice:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1  # Mono input
        self.RATE = 44100
        self.source_device = None  # The real device with 2 output channels
        self.stream = None
        self.audio_data = []
        
        # Initialize transcription service
        self.transcription_service = TranscriptionService()
        self.transcription_service.start()
        
    def list_devices(self):
        """List all available audio devices"""
        info = self.p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        
        print("\nAvailable Audio Devices:")
        print("------------------------")
        output_devices = []
        
        for i in range(numdevices):
            device_info = self.p.get_device_info_by_host_api_device_index(0, i)
            print(f"Device {i}: {device_info['name']}")
            print(f"  Output channels: {device_info['maxOutputChannels']}")
            print(f"  Input channels: {device_info['maxInputChannels']}")
            print(f"  Sample Rate: {int(device_info['defaultSampleRate'])}Hz")
            print("------------------------")
            
            # Store devices with 2 output channels
            if device_info['maxOutputChannels'] == 2:
                output_devices.append((i, device_info['name']))
                
        return output_devices

    def create_virtual_input_device(self, source_device_index):
        """Create a virtual input device that receives from a 2-channel output device"""
        self.source_device = self.p.get_device_info_by_index(source_device_index)
        
        # Open stream for virtual input device
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.audio_callback
        )
        
        print("\nVirtual input device created successfully!")
        print(f"Source device: {self.source_device['name']}")
        print(f"Input channels: {self.CHANNELS}")
        print(f"Sample rate: {self.RATE}Hz")
        print("\nPress Ctrl+C to stop the virtual device...")
        
        # Start the stream
        self.stream.start_stream()
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback function that receives audio from the source device
        and converts it to mono for the virtual input device
        """
        if status:
            print(f"Status: {status}")
            
        # Convert input data to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Store audio data for transcription
        self.audio_data.append(audio_data.copy())
        
        # Send to transcription service
        self.transcription_service.add_audio_data(audio_data, 'tab')
        
        return (in_data, pyaudio.paContinue)

    def get_transcription(self):
        """Get the current transcription."""
        return self.transcription_service.get_transcription('tab')

    def stop_recording(self):
        """Stop recording and clean up."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.transcription_service.stop()
        self.p.terminate()

def main():
    print("Initializing system audio transcriber...")
    virtual_device = VirtualInputDevice()
    
    # List available devices and get devices with 2 output channels
    output_devices = virtual_device.list_devices()
    
    if not output_devices:
        print("No devices with 2 output channels found!")
        return
    
    print("\nAvailable source devices (2 output channels):")
    for idx, (device_id, name) in enumerate(output_devices):
        print(f"{idx}: {name} (Device ID: {device_id})")
    
    try:
        selection = int(input("\nSelect source device number: "))
        if 0 <= selection < len(output_devices):
            source_device_id = output_devices[selection][0]
            
            print("Starting recording. Will record for 30 seconds...")
            virtual_device.create_virtual_input_device(source_device_id)
            
            # Record for 30 seconds while showing intermediate transcriptions
            start_time = time.time()
            timer = 0
            print("Recording started...\n\n")
            
            while time.time() - start_time < 10:
                time.sleep(1)  # Check every 1 second
                if timer % 5 == 0:
                    print("Current time: ", timer, "seconds")
                timer += 1
                transcript = virtual_device.get_transcription()
                if transcript:
                    print("\rCurrent transcription:", transcript, end="", flush=True)
            
            # Stop recording and get final transcription
            print("\n\nStopping recording...")
            virtual_device.stop_recording()
            
            # Get and print final transcription
            final_transcript = virtual_device.get_transcription()
            print("\nFinal Transcription:")
            print(final_transcript)
            
        else:
            print("Invalid selection!")
    except ValueError:
        print("Invalid input!")
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        if hasattr(virtual_device, 'stream') and virtual_device.stream:
            virtual_device.stop_recording()

if __name__ == "__main__":
    main()