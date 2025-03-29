import os
import speech_recognition as sr
import sys
from pydub import AudioSegment
import tempfile
from app.nlp_analysis import analyze_transcript  # Import the analyze_transcript function

def test_transcription(audio_file_path):
    """Test audio transcription directly"""
    print(f"\nTesting transcription of: {audio_file_path}")
    print(f"File exists: {os.path.exists(audio_file_path)}")
    print(f"File size: {os.path.getsize(audio_file_path)} bytes")
    
    # If the file is not a .wav, convert it
    if not audio_file_path.lower().endswith('.wav'):
        print(f"Converting {audio_file_path} to WAV format...")
        try:
            # Create temp file for WAV
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_wav = temp_file.name
            
            # Convert to WAV
            audio = AudioSegment.from_file(audio_file_path)
            audio.export(temp_wav, format="wav")
            print(f"Converted to {temp_wav}")
            audio_file_path = temp_wav
        except Exception as e:
            print(f"Error converting audio: {str(e)}")
            return
    
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    try:
        # Use sr.AudioFile to get audio data
        with sr.AudioFile(audio_file_path) as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)
            print("Recording audio from file...")
            audio_data = recognizer.record(source)
            
            print("Sending to Google Speech Recognition...")
            transcript = recognizer.recognize_google(audio_data)
            
            print(f"\nTranscription successful!")
            print(f"Transcript: {transcript}")
            
            # Add analysis step
            print("\nAnalyzing transcript...")
            feedback = analyze_transcript(transcript, interview_type='behavioral', question_type='conflict')
            
            print("\n==== FEEDBACK ====")
            print(f"Message: {feedback.get('message', 'No message')}")
            print(f"Type: {feedback.get('type', 'No type')}")
            
            if 'details' in feedback:
                details = feedback['details']
                print("\nDetails:")
                
                # Print STAR analysis if available
                if 'STAR' in details:
                    star = details['STAR']
                    print("\nSTAR Analysis:")
                    for key, value in star.items():
                        print(f"  {key}: {value}")
                
                # Print language quality if available
                if 'language_quality' in details:
                    lang = details['language_quality']
                    print("\nLanguage Quality:")
                    for key, value in lang.items():
                        print(f"  {key}: {value}")
                
                # Print improvement suggestions if available
                if 'improvement_suggestions' in details:
                    print("\nImprovement Suggestions:")
                    for suggestion in details['improvement_suggestions']:
                        print(f"  - {suggestion}")
                
                # Print overall score if available
                if 'overall_score' in details:
                    print(f"\nOverall Score: {details['overall_score']}/10")
            
            return transcript
    except sr.UnknownValueError:
        print("\nGoogle Speech Recognition could not understand audio (no speech detected)")
    except sr.RequestError as e:
        print(f"\nCould not request results from Google Speech Recognition service: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    # Clean up temp file if created
    if 'temp_wav' in locals() and os.path.exists(temp_wav):
        os.remove(temp_wav)
        print(f"Cleaned up temporary file: {temp_wav}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_transcription(sys.argv[1])
    else:
        print("Please provide the path to an audio file:")
        print("python3 test_transcription.py path/to/your/audio.wav") 