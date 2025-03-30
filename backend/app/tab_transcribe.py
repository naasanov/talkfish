import pyaudio
import wave
import numpy as np
import time
import os
from datetime import datetime

class SystemAudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 2  # Stereo for system audio
        self.RATE = 44100  # Standard audio rate
        self.RECORD_SECONDS = 10
        self.p = pyaudio.PyAudio()
        
        # Create recordings directory if it doesn't exist
        self.recordings_dir = os.path.join(os.path.dirname(__file__), "recordings")
        os.makedirs(self.recordings_dir, exist_ok=True)
        
    def list_devices(self):
        """List all available audio devices"""
        print("\nAvailable Audio Devices:")
        print("------------------------")
        
        blackhole_input_index = None
        blackhole_output_index = None
        all_devices = []
        
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            device_name = device_info['name']
            
            print(f"Device {i}: {device_name}")
            print(f"  Input channels: {device_info['maxInputChannels']}")
            print(f"  Output channels: {device_info['maxOutputChannels']}")
            print(f"  Default Sample Rate: {device_info['defaultSampleRate']}")
            print("------------------------")
            
            all_devices.append((i, device_name, device_info))
            
            # Check for BlackHole
            if 'BlackHole' in device_name or 'blackhole' in device_name.lower():
                if device_info['maxInputChannels'] > 0:
                    blackhole_input_index = i
                if device_info['maxOutputChannels'] > 0:
                    blackhole_output_index = i
        
        return all_devices, blackhole_input_index, blackhole_output_index
    
    def record_audio(self, input_device_index):
        """Record audio from the specified input device"""
        try:
            device_info = self.p.get_device_info_by_index(input_device_index)
            device_name = device_info['name']
            
            print(f"\nRecording from: {device_name}")
            print(f"Input channels: {device_info['maxInputChannels']}")
            print(f"Sample rate: {device_info['defaultSampleRate']}Hz")
            
            # Open input stream
            stream = self.p.open(
                format=self.FORMAT,
                channels=min(self.CHANNELS, int(device_info['maxInputChannels'])),
                rate=int(device_info['defaultSampleRate']),
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=self.CHUNK
            )
            
            print(f"\nRecording for {self.RECORD_SECONDS} seconds...")
            print("Please play audio on your system now...")
            
            frames = []
            
            # Record audio
            start_time = time.time()
            while time.time() - start_time < self.RECORD_SECONDS:
                try:
                    data = stream.read(self.CHUNK)
                    frames.append(data)
                    
                    # Print progress
                    seconds = time.time() - start_time
                    if int(seconds) != int(seconds - 0.1):
                        # Convert to numpy array for level analysis
                        audio_chunk = np.frombuffer(data, dtype=np.float32)
                        rms = np.sqrt(np.mean(np.square(audio_chunk)))
                        peak = np.max(np.abs(audio_chunk))
                        
                        print(f"\rRecording: {seconds:.1f}s | "
                              f"RMS: {rms:.3f} | "
                              f"Peak: {peak:.3f}", end='', flush=True)
                        
                except Exception as e:
                    print(f"\nError reading audio chunk: {e}")
                    continue
            
            print("\n\nFinished recording!")
            
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            
            # Save the recorded audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recordings_dir, f"system_audio_{timestamp}.wav")
            
            # Process the recorded audio
            print("\nProcessing audio data...")
            audio_data = np.frombuffer(b''.join(frames), dtype=np.float32)
            
            # Save as WAV file
            print("\nSaving audio file...")
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(min(self.CHANNELS, int(device_info['maxInputChannels'])))
                wf.setsampwidth(2)  # 2 bytes for int16
                wf.setframerate(int(device_info['defaultSampleRate']))
                
                # Scale and convert to int16
                print("Converting to 16-bit audio...")
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
            
            print(f"\nRecording saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.p.terminate()

def main():
    recorder = SystemAudioRecorder()
    
    # List available devices and check for BlackHole
    all_devices, blackhole_input, blackhole_output = recorder.list_devices()
    
    if blackhole_input is not None:
        print(f"\n✅ BlackHole input device detected! (Device ID: {blackhole_input})")
        print(f"To record system audio:")
        print(f"1. Go to System Preferences/Settings > Sound > Output")
        print(f"2. Select 'BlackHole 2ch' as your output device")
        print(f"3. Play audio that you want to capture")
        print(f"4. Select BlackHole as the input device below")
    else:
        print("\n❌ BlackHole input device not detected.")
        print("\nTo record system audio on macOS, please follow these steps:")
        print("1. Install BlackHole: brew install blackhole-2ch")
        print("2. Restart your computer")
        print("3. Run this script again")
    
    # Create a list of input devices
    input_devices = [(idx, name) for idx, name, info in all_devices if info['maxInputChannels'] > 0]
    
    if not input_devices:
        print("No input devices found!")
        return
    
    print("\nSelect an input device to record from:")
    for i, (device_id, name) in enumerate(input_devices):
        if device_id == blackhole_input:
            print(f"{i}: {name} (Device ID: {device_id}) ← RECOMMENDED for system audio")
        else:
            print(f"{i}: {name} (Device ID: {device_id})")
    
    try:
        selection = int(input("\nSelect device number: "))
        if 0 <= selection < len(input_devices):
            device_id = input_devices[selection][0]
            recorder.record_audio(device_id)
        else:
            print("Invalid selection!")
    except ValueError:
        print("Invalid input!")
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")

if __name__ == "__main__":
    main()