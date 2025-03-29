import requests
import os
from scipy.io import wavfile
import numpy as np
import time
import json

def create_test_audio():
    """Create a simple test WAV file with a sine wave"""
    # Generate a 2-second sine wave at 440 Hz
    sample_rate = 44100
    duration = 2
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * 440 * t)
    
    # Scale to 16-bit integer range
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create stereo audio (duplicate mono to both channels)
    stereo_data = np.column_stack((audio_data, audio_data))
    
    # Save the file
    filename = 'test_audio.wav'
    wavfile.write(filename, sample_rate, stereo_data)
    return filename

def test_endpoints():
    """Test the backend endpoints"""
    base_url = 'http://localhost:5001'
    
    # Test health endpoint
    print("\n1. Testing /health endpoint...")
    response = requests.get(f'{base_url}/health')
    print(f"Status: {response.status_code}")
    print(f"Raw Response Text: {response.text}")
    try:
        print(f"JSON Response: {response.json()}")
    except Exception as e:
        print(f"Error parsing JSON: {str(e)}")
    
    # Create test audio file
    print("\n2. Creating test audio file...")
    audio_file = create_test_audio()
    
    # Test analyze endpoint
    print("\n3. Testing /analyze endpoint...")
    with open(audio_file, 'rb') as f:
        files = {'audio_file': ('test_audio.wav', f, 'audio/wav')}
        data = {'interview_type': 'behavioral'}
        response = requests.post(f'{base_url}/analyze', files=files, data=data)
        print(f"Status: {response.status_code}")
        print(f"Raw Response Text: {response.text}")
        try:
            print(f"JSON Response: {response.json()}")
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}")
    
    # Test transcript endpoint
    print("\n4. Testing /transcript endpoint...")
    with open(audio_file, 'rb') as f:
        files = {'audio_file': ('test_audio.wav', f, 'audio/wav')}
        response = requests.post(f'{base_url}/transcript', files=files)
        print(f"Status: {response.status_code}")
        print(f"Raw Response Text: {response.text}")
        try:
            print(f"JSON Response: {response.json()}")
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}")
    
    # Clean up
    print("\n5. Cleaning up...")
    os.remove(audio_file)
    print("Test audio file removed")

def test_simple_text():
    """Test the analysis with a simple text input"""
    from app.nlp_analysis import analyze_transcript
    
    print("\nTesting direct analysis with sample text...")
    test_text = "In my previous role, I had to deal with a difficult customer who was unhappy with our service. I listened to their concerns, acknowledged their frustration, and worked with our team to find a solution. We ended up not only resolving their immediate issue but also implementing a new process to prevent similar problems. The customer became one of our strongest advocates."
    
    result = analyze_transcript(test_text, interview_type='behavioral')
    print("\nAnalysis result:")
    print(json.dumps(result, indent=2))

def test_with_file(audio_file_path):
    """Test the endpoints with an existing audio file"""
    base_url = 'http://localhost:5001'
    
    # Test health endpoint
    print("\n1. Testing /health endpoint...")
    response = requests.get(f'{base_url}/health')
    print(f"Status: {response.status_code}")
    print(f"Raw Response Text: {response.text}")
    
    # Test analyze endpoint
    print("\n2. Testing /analyze endpoint with your audio file...")
    with open(audio_file_path, 'rb') as f:
        files = {'audio_file': (os.path.basename(audio_file_path), f, 'audio/wav')}
        data = {'interview_type': 'behavioral'}
        response = requests.post(f'{base_url}/analyze', files=files, data=data)
        print(f"Status: {response.status_code}")
        print(f"Raw Response Text: {response.text}")
    
    # Test transcript endpoint
    print("\n3. Testing /transcript endpoint with your audio file...")
    with open(audio_file_path, 'rb') as f:
        files = {'audio_file': (os.path.basename(audio_file_path), f, 'audio/wav')}
        response = requests.post(f'{base_url}/transcript', files=files)
        print(f"Status: {response.status_code}")
        print(f"Raw Response Text: {response.text}")

if __name__ == '__main__':
    import sys
    
    # Always run the simple text test first
    test_simple_text()
    
    # Then test with audio file if provided
    if len(sys.argv) > 1:
        test_with_file(sys.argv[1])
    else:
        print("\nNo audio file provided. Only ran text analysis test.")
        print("To test with audio, run: python3 test_endpoints.py path/to/your/audio.wav") 