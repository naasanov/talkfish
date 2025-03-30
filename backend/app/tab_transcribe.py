import pyaudio
import wave
import numpy as np
import time
import os
import subprocess
import threading
from typing import Optional
import sys
from datetime import datetime

# Add the backend directory to Python path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.transcription_service import TranscriptionService
from app.nlp_analysis import analyze_transcript

class BlackHoleRecorder:
    """
    Records system audio via BlackHole on macOS and transcribes it.
    
    This class follows the same structure as MicrophoneTranscriber but is specialized
    for capturing system audio through BlackHole instead of microphone input.
    """
    
    def __init__(self, chunk_size=1024, sample_rate=16000, interview_type='behavioral'):
        """
        Initialize the BlackHole recorder.
        
        Args:
            chunk_size: Number of audio frames per buffer
            sample_rate: Audio sample rate (Hz)
            interview_type: Type of interview for analysis
        """
        # Audio settings
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.format = pyaudio.paFloat32
        self.channels = 2  # Stereo for system audio
        self.interview_type = interview_type
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Initialize transcription service
        self.transcription_service = TranscriptionService()
        self.transcription_service.start()
        
        # Recording control
        self.is_recording = False
        self.recording_thread = None
        self.frames = []  # For storing audio frames for WAV file
        
        # Create recordings directory if it doesn't exist
        self.recordings_dir = os.path.join(os.path.dirname(__file__), "recordings")
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # Find audio devices
        self.blackhole_input, self.blackhole_output, self.system_output = self.find_audio_devices()
        
        # Store original audio output device
        self.original_output = self.get_current_audio_output()
    
    def find_audio_devices(self):
        """Find BlackHole and system audio devices"""
        print("\nSearching for audio devices...")
        
        blackhole_input = None
        blackhole_output = None
        system_output = None
        
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            device_name = device_info['name']
            
            print(f"Device {i}: {device_name}")
            print(f"  Input channels: {device_info['maxInputChannels']}")
            print(f"  Output channels: {device_info['maxOutputChannels']}")
            print(f"  Default Sample Rate: {device_info['defaultSampleRate']}Hz")
            
            # Check for BlackHole
            if 'BlackHole' in device_name or 'blackhole' in device_name.lower():
                if device_info['maxInputChannels'] > 0:
                    blackhole_input = i
                    print(f"✅ Found BlackHole input device: {device_name} (ID: {i})")
                if device_info['maxOutputChannels'] > 0:
                    blackhole_output = i
                    print(f"✅ Found BlackHole output device: {device_name} (ID: {i})")
            
            # Check for system output (speakers/headphones)
            elif device_info['maxOutputChannels'] > 0 and ('speaker' in device_name.lower() or 
                                                         'headphone' in device_name.lower() or
                                                         'macbook air' in device_name.lower()):
                system_output = i
                print(f"✅ Found system output device: {device_name} (ID: {i})")
        
        if blackhole_input is None:
            print("❌ BlackHole input device not found!")
        if blackhole_output is None:
            print("❌ BlackHole output device not found!")
        if system_output is None:
            print("❌ System output device not found!")
            
        return blackhole_input, blackhole_output, system_output
    
    def get_current_audio_output(self):
        """Get the current audio output device name"""
        try:
            result = subprocess.run(
                ["system_profiler", "SPAudioDataType"], 
                capture_output=True, 
                text=True
            )
            
            output = result.stdout
            
            # Look for the default output device
            current_device = None
            for line in output.split('\n'):
                if "Default Output Device: Yes" in line:
                    # Find the device name from nearby lines
                    for nearby_line in output.split('\n'):
                        if ":" in nearby_line and "Default Output Device" not in nearby_line:
                            current_device = nearby_line.split(":")[0].strip()
                            break
                    break
            
            if current_device:
                print(f"\nCurrent audio output device: {current_device}")
                return current_device
            else:
                print("❓ Could not determine current audio output device.")
                return None
                
        except Exception as e:
            print(f"Error getting current audio output: {e}")
            return None
    
    def set_audio_output(self, device_name):
        """Set the system audio output device using SwitchAudioSource"""
        try:
            # Check if SwitchAudioSource is installed
            try:
                subprocess.run(["which", "SwitchAudioSource"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("\n⚠️ SwitchAudioSource not found. Installing...")
                subprocess.run(["brew", "install", "switchaudio-osx"], check=True)
            
            # Set the audio output device
            print(f"\nSetting audio output to: {device_name}")
            subprocess.run(["SwitchAudioSource", "-s", device_name, "-t", "output"], check=True)
            print(f"✅ Audio output set to: {device_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error setting audio output: {e}")
            return False
    
    def setup_audio_routing(self):
        """Set up audio routing from system speakers to BlackHole"""
        print("\n=== Setting up audio routing ===")
        
        # Store the original output device
        self.original_output = self.get_current_audio_output()
        print(f"Original audio output: {self.original_output}")
        
        # Find the BlackHole device name and system speakers name
        blackhole_name = None
        speakers_name = None
        
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            device_name = device_info['name']
            
            if 'BlackHole' in device_name or 'blackhole' in device_name.lower():
                blackhole_name = device_name
            
            if ('speaker' in device_name.lower() or 'macbook air' in device_name.lower()) and device_info['maxOutputChannels'] > 0:
                speakers_name = device_name
        
        if not blackhole_name:
            print("❌ Could not find BlackHole device name.")
            return False
            
        if not speakers_name:
            print("❌ Could not find system speakers device name.")
            return False
            
        print(f"Found BlackHole: {blackhole_name}")
        print(f"Found Speakers: {speakers_name}")
        
        # Check if a Multi-Output device already exists
        try:
            result = subprocess.run(
                ["SwitchAudioSource", "-a"], 
                capture_output=True, 
                text=True
            )
            
            output = result.stdout
            
            # Look for the default output device
            multi_output_exists = "Multi-Output Device" in output
            
            if multi_output_exists:
                print("✅ Multi-Output Device already exists.")
                # Set audio output to Multi-Output Device
                if self.set_audio_output("Multi-Output Device"):
                    print("✅ Audio routing set up successfully to existing Multi-Output Device.")
                    return True
            else:
                print("Creating new Multi-Output Device...")
                
                # Create a Multi-Output Device using AppleScript
                # This is a bit complex but allows us to create and configure the Multi-Output Device
                applescript = f'''
                tell application "Audio MIDI Setup"
                    -- Create new aggregate device
                    set multiOutputDevice to make new aggregate device
                    
                    -- Rename it
                    set name of multiOutputDevice to "Multi-Output Device"
                    
                    -- Add BlackHole and Speakers to the device
                    set subdevices of multiOutputDevice to {{"{blackhole_name}", "{speakers_name}"}}
                    
                    -- Set as default output
                    set default output device to multiOutputDevice
                end tell
                '''
                
                # Save the AppleScript to a temporary file
                script_path = "/tmp/create_multi_output.scpt"
                with open(script_path, "w") as f:
                    f.write(applescript)
                
                # Run the AppleScript
                try:
                    subprocess.run(["osascript", script_path], check=True)
                    print("✅ Multi-Output Device created successfully.")
                    
                    # Set audio output to Multi-Output Device
                    if self.set_audio_output("Multi-Output Device"):
                        print("✅ Audio routing set up successfully to new Multi-Output Device.")
                        return True
                except Exception as e:
                    print(f"❌ Error creating Multi-Output Device: {e}")
                    
                    # Fallback: Just use BlackHole
                    print("Falling back to using BlackHole only...")
                    if self.set_audio_output(blackhole_name):
                        print("✅ Audio routing set up successfully (BlackHole only).")
                        print("⚠️ You won't hear audio during recording.")
                        return True
        except Exception as e:
            print(f"❌ Error setting up audio routing: {e}")
            
            # Fallback: Just use BlackHole
            print("Falling back to using BlackHole only...")
            if self.set_audio_output(blackhole_name):
                print("✅ Audio routing set up successfully (BlackHole only).")
                print("⚠️ You won't hear audio during recording.")
                return True
                
        return False
    
    def restore_audio_routing(self):
        """Restore the original audio output device"""
        if self.original_output:
            print(f"\nRestoring audio output to: {self.original_output}")
            self.set_audio_output(self.original_output)
            print(f"✅ Audio output restored to: {self.original_output}")
    
    def test_blackhole_audio(self, duration=3):
        """Test if BlackHole is receiving audio by recording for a short duration"""
        if self.blackhole_input is None:
            print("No BlackHole device found. Cannot test audio.")
            return False
            
        try:
            print(f"\nTesting BlackHole audio for {duration} seconds...")
            print("Please make sure audio is playing on your system...")
            
            device_info = self.audio.get_device_info_by_index(self.blackhole_input)
            
            # Open input stream
            stream = self.audio.open(
                format=self.format,
                channels=min(self.channels, int(device_info['maxInputChannels'])),
                rate=int(device_info['defaultSampleRate']),
                input=True,
                input_device_index=self.blackhole_input,
                frames_per_buffer=self.chunk_size
            )
            
            # Record a short sample
            has_audio = False
            start_time = time.time()
            
            while time.time() - start_time < duration:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.float32)
                
                # Check if we have any non-zero audio
                rms = np.sqrt(np.mean(np.square(audio_chunk)))
                if rms > 0.0001:  # Threshold for detecting audio
                    has_audio = True
                    break
                
                # Print progress
                seconds = time.time() - start_time
                print(f"\rTesting: {seconds:.1f}s | RMS: {rms:.6f}", end='', flush=True)
            
            # Close the stream
            stream.stop_stream()
            stream.close()
            
            if has_audio:
                print("\n\n✅ BlackHole is receiving audio! You're good to go.")
                return True
            else:
                print("\n\n❌ No audio detected in BlackHole.")
                print("   Please check your system audio settings and make sure audio is playing.")
                return False
                
        except Exception as e:
            print(f"Error testing BlackHole audio: {e}")
            return False
    
    def start_recording(self, duration=10, auto_route=True):
        """Start recording from BlackHole."""
        if self.is_recording:
            print("Already recording!")
            return False
        
        if self.blackhole_input is None:
            print("No BlackHole device found. Please install BlackHole and try again.")
            print("Install with: brew install blackhole-2ch")
            return False
        
        # Set up audio routing if requested
        if auto_route:
            self.setup_audio_routing()
        
        # Check if BlackHole is receiving audio
        if not self.test_blackhole_audio():
            print("\nWould you like to continue recording anyway? (y/n)")
            response = input().lower()
            if response != 'y':
                print("Recording canceled.")
                if auto_route:
                    self.restore_audio_routing()
                return False
        
        # Reset frames list
        self.frames = []
        
        # Store recording duration
        self.recording_duration = duration
        self.start_time = time.time()
        
        # Start recording
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        return True

    def stop_recording(self):
        """Stop recording from BlackHole."""
        if not self.is_recording:
            print("Not currently recording!")
            return None
        
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        
        # Stop the transcription service
        self.transcription_service.stop()
        
        # Save the recorded audio to a WAV file
        output_file = self._save_wav_file()
        
        # Restore original audio routing
        self.restore_audio_routing()
        
        # Terminate PyAudio
        self.audio.terminate()
        
        return output_file

    def get_transcription(self) -> str:
        """Get the current transcription."""
        return self.transcription_service.get_transcription('tab')
    
    def _record_audio(self):
        """Record audio from BlackHole and send to transcription service."""
        try:
            device_info = self.audio.get_device_info_by_index(self.blackhole_input)
            device_name = device_info['name']
            
            # Store device info for WAV file
            self.device_sample_rate = int(device_info['defaultSampleRate'])
            self.device_channels = min(self.channels, int(device_info['maxInputChannels']))
            
            print(f"\nRecording from: {device_name}")
            print(f"Input channels: {device_info['maxInputChannels']}")
            print(f"Sample rate: {device_info['defaultSampleRate']}Hz")
            print(f"Recording for {self.recording_duration} seconds...")
            
            # Open input stream
            stream = self.audio.open(
                format=self.format,
                channels=self.device_channels,
                rate=self.device_sample_rate,
                input=True,
                input_device_index=self.blackhole_input,
                frames_per_buffer=self.chunk_size
            )
            
            print("\nRecording started...")
            print("Please play audio on your system now...")
            
            # For audio level monitoring
            zero_chunks_count = 0
            total_chunks_count = 0
            
            # Record until stop_recording is called or duration is reached
            while self.is_recording:
                # Check if we've reached the recording duration
                if time.time() - self.start_time >= self.recording_duration:
                    print("\nRecording duration reached.")
                    self.is_recording = False
                    break
                
                try:
                    # Read audio data
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    self.frames.append(data)
                    
                    # Convert to numpy array for level analysis
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    
                    # Debug audio levels
                    total_chunks_count += 1
                    if np.all(np.abs(audio_data) < 0.0001):  # Detect near-zero audio
                        zero_chunks_count += 1
                    
                    # Apply volume increase for transcription
                    amplified_data = self.increase_volume(audio_data, gain_factor=5.0)
                    
                    # Resample if needed for the transcription service
                    if self.device_sample_rate != 16000:
                        # Simple resampling - in production you'd want a better resampling method
                        resampled = amplified_data[::int(self.device_sample_rate/16000)]
                        self.transcription_service.add_audio_data(resampled, 'tab')
                    else:
                        self.transcription_service.add_audio_data(amplified_data, 'tab')
                    
                    # Print progress and current transcription every second
                    elapsed = time.time() - self.start_time
                    if int(elapsed) != int(elapsed - 0.1):
                        current_transcript = self.get_transcription()
                        transcript_preview = current_transcript[-50:] if current_transcript else "No transcription yet"
                        
                        print(f"\rRecording: {elapsed:.1f}s/{self.recording_duration}s | "
                              f"Silent: {zero_chunks_count}/{total_chunks_count} | "
                              f"Transcript: ...{transcript_preview}", end='', flush=True)
                    
                except Exception as e:
                    print(f"\nError reading audio chunk: {e}")
                    continue
            
            # Close the stream
            stream.stop_stream()
            stream.close()
            
            print("\n\nFinished recording!")
            
            # Check if we recorded silence
            if zero_chunks_count == total_chunks_count:
                print("\n⚠️ WARNING: All audio chunks were silent! No audio was captured.")
                self._print_audio_troubleshooting_guide()
            elif zero_chunks_count > total_chunks_count * 0.9:  # More than 90% silence
                print(f"\n⚠️ WARNING: Recording was {zero_chunks_count/total_chunks_count*100:.1f}% silent!")
                self._print_audio_troubleshooting_guide()
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_wav_file(self):
        """Save the recorded audio to a WAV file"""
        if not self.frames:
            print("No audio data to save.")
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recordings_dir, f"blackhole_audio_{timestamp}.wav")
            
            # Process the recorded audio
            print("\nProcessing audio data...")
            audio_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
            
            # Check if we have any audio data
            if len(audio_data) == 0:
                print("No audio data recorded!")
                return None
                
            # Apply volume increase for the saved WAV file
            print("Applying volume amplification...")
            amplified_audio = self.increase_volume(audio_data, gain_factor=5.0)
                
            # Print audio stats for debugging
            print(f"Original audio stats: min={np.min(audio_data)}, max={np.max(audio_data)}, mean={np.mean(audio_data)}")
            print(f"Amplified audio stats: min={np.min(amplified_audio)}, max={np.max(amplified_audio)}, mean={np.mean(amplified_audio)}")
            
            # Save as WAV file
            print("\nSaving audio file...")
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.device_channels)
                wf.setsampwidth(2)  # 2 bytes for int16
                wf.setframerate(self.device_sample_rate)
                
                # Scale and convert to int16
                print("Converting to 16-bit audio...")
                audio_int16 = (amplified_audio * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
            
            print(f"\nRecording saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error saving audio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def increase_volume(self, audio_chunk, gain_factor=5.0):
        """
        Increase the volume of audio data using a logarithmic scale.
        
        Args:
            audio_chunk: NumPy array of audio data
            gain_factor: Amount to increase volume by (default: 5.0)
                         Higher values = louder audio
        
        Returns:
            Amplified audio data
        """
        # Make sure we're working with a NumPy array
        if not isinstance(audio_chunk, np.ndarray):
            audio_chunk = np.frombuffer(audio_chunk, dtype=np.float32)
            
        # Apply logarithmic gain - this properly handles the logarithmic nature of sound
        # We use a combination of compression and gain to preserve dynamics while increasing volume
        
        # 1. Normalize the audio (find the max amplitude and scale accordingly)
        max_val = np.max(np.abs(audio_chunk))
        if max_val > 0:  # Avoid division by zero
            normalized = audio_chunk / max_val
        else:
            normalized = audio_chunk
            
        # 2. Apply soft compression to prevent clipping
        # This reduces the dynamic range before applying gain
        compressed = np.sign(normalized) * (1 - np.exp(-3 * np.abs(normalized)))
        
        # 3. Apply gain factor (logarithmic scale)
        amplified = compressed * gain_factor
        
        # 4. Clip to prevent distortion (-1.0 to 1.0 for float32 audio)
        amplified = np.clip(amplified, -1.0, 1.0)
        
        return amplified

    def _print_audio_troubleshooting_guide(self):
        """Print a guide for troubleshooting audio recording issues"""
        print("\n=== Audio Troubleshooting Guide ===")
        print("1. Make sure BlackHole is selected as your system output:")
        print("   - Go to System Preferences/Settings > Sound > Output")
        print("   - Select 'BlackHole 2ch'")
        print("\n2. Create a Multi-Output Device (to hear audio while recording):")
        print("   - Open Audio MIDI Setup (in Applications/Utilities)")
        print("   - Click the + button in the bottom left corner")
        print("   - Select 'Create Multi-Output Device'")
        print("   - Check both your speakers and BlackHole 2ch")
        print("   - Select this Multi-Output Device as your system output")
        print("   This allows you to hear the audio while it's being recorded")
        print("=====================================")

def print_blackhole_setup_instructions():
    """Print instructions for setting up BlackHole"""
    print("\n=== BlackHole Setup Instructions ===")
    print("To record system audio with BlackHole:")
    print("1. Go to System Preferences/Settings > Sound > Output")
    print("2. Select 'BlackHole 2ch' as your output device")
    print("3. Play audio from any application (YouTube, Spotify, etc.)")
    print("\nAdvanced setup (recommended):")
    print("1. Open Audio MIDI Setup (in Applications/Utilities)")
    print("2. Click the + button in the bottom left corner")
    print("3. Select 'Create Multi-Output Device'")
    print("4. Check both your speakers and BlackHole 2ch")
    print("5. Select this Multi-Output Device as your system output")
    print("   This allows you to hear the audio while it's being recorded")
    print("=====================================")

def main():
    # Print setup instructions
    print_blackhole_setup_instructions()
    
    # Create recorder
    recorder = BlackHoleRecorder(chunk_size=1024, sample_rate=16000)
    
    try:
        # Start recording with automatic routing
        print("\n=== System Audio Recording & Transcription ===")
        print("This script will:")
        print("1. Save your current audio output setting")
        print("2. Create a Multi-Output Device that routes audio to both:")
        print("   - BlackHole (for recording)")
        print("   - Your speakers (so you can hear it)")
        print("3. Record audio for 10 seconds")
        print("4. Restore your original audio output setting")
        print("=====================================")
        
        # Start recording (10 seconds by default)
        if recorder.start_recording(duration=10, auto_route=True):
            # Wait for recording to complete
            start_time = time.time()
            while recorder.is_recording and time.time() - start_time < 15:  # 5 second buffer
                time.sleep(0.5)
            
            # Stop recording and get the output file
            output_file = recorder.stop_recording()
            
            if output_file:
                # Get the final transcription
                final_transcript = recorder.get_transcription()
                print(f"\nAudio successfully recorded and saved to: {output_file}\n\n")
                print(f"Final Transcription: {final_transcript}")
                
                # Only analyze if we have a transcript
                if final_transcript and len(final_transcript.strip()) > 0:
                    print("\nAnalyzing transcript...")
                    feedback = analyze_transcript(final_transcript, 'behavioral')
                    if feedback:
                        print("\nTranscript Analysis:")
                        print(feedback)
                else:
                    print("\nNo transcription was generated. The audio may not contain speech or may be too quiet.")
                
                # Provide instructions for using the recorded file
                print("\nYou can play this file with:")
                print(f"  afplay {output_file}")
                print("Or open it in QuickTime Player or any audio application.")
            else:
                print("Failed to record audio. Please check the error messages above.")
        
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
        recorder.stop_recording()
    finally:
        print("Done!")

if __name__ == "__main__":
    main()
