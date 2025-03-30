import speech_recognition as sr
import tempfile
import os
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
from .nlp_analysis import analyze_transcript
from .transcription_service import TranscriptionService
from typing import Union, BinaryIO

# Global transcription service instance
transcription_service = TranscriptionService()
transcription_service.start()

def process_streaming_audio(audio_data: np.ndarray, channel: str = 'mic'):
    """
    Process streaming audio data in real-time.
    
    Args:
        audio_data: numpy array of audio samples (should be float32)
        channel: 'mic' for microphone or 'tab' for tab audio
    
    Returns:
        str: Current transcription for the specified channel
    """
    transcription_service.add_audio_data(audio_data.astype(np.float32), channel)
    return transcription_service.get_transcription(channel)

def process_audio(audio_file: Union[str, BinaryIO], interview_type='behavioral'):
    """
    Process the audio file to extract speech from both interviewer and interviewee
    and generate feedback.
    
    Args:
        audio_file: Path to audio file or file-like object
        interview_type: Type of interview for analysis
    
    Returns:
        dict: Feedback based on the interview analysis
    """
    # Create a temporary file to store the audio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_filename = temp_file.name
    temp_file.close()
    
    try:
        print(f"\nProcessing audio file: {audio_file.filename}")
        print(f"Temporary file: {temp_filename}")
        
        # Save the uploaded file to the temporary location
        if isinstance(audio_file, str):
            if os.path.exists(audio_file):
                if audio_file.endswith('.wav'):
                    temp_filename = audio_file
                else:
                    audio = AudioSegment.from_file(audio_file)
                    audio.export(temp_filename, format="wav")
        else:
            audio_file.save(temp_filename)
            if not temp_filename.endswith('.wav'):
                webm_audio = AudioSegment.from_file(temp_filename)
                temp_filename_wav = temp_filename.replace('.webm', '.wav')
                webm_audio.export(temp_filename_wav, format="wav")
                os.remove(temp_filename)
                temp_filename = temp_filename_wav
        
        # Split stereo channels (left: interviewee mic, right: interviewer from tab)
        sample_rate, audio_data = wavfile.read(temp_filename)
        print(f"Audio sample rate: {sample_rate} Hz")
        print(f"Audio data shape: {audio_data.shape}")
        
        # Check if audio is stereo (2 channels)
        if len(audio_data.shape) == 2 and audio_data.shape[1] == 2:
            print("Processing stereo audio (2 channels)")
            interviewee_audio = audio_data[:, 0]  # Left channel (microphone)
            interviewer_audio = audio_data[:, 1]  # Right channel (tab audio)
            
            # Add audio data to transcription service
            transcription_service.add_audio_data(interviewee_audio.astype(np.float32), 'mic')
            transcription_service.add_audio_data(interviewer_audio.astype(np.float32), 'tab')
            
            # Get transcripts from both channels
            interviewee_transcript = transcription_service.get_transcription('mic')
            interviewer_transcript = transcription_service.get_transcription('tab')
            
            # Analyze the combined conversation context
            print(f"Analyzing with transcript lengths - Interviewer: {len(interviewer_transcript)} chars, Interviewee: {len(interviewee_transcript)} chars")
            if not interviewee_transcript.strip():
                print("WARNING: Interviewee transcript is empty!")
                interviewee_transcript = "This is a placeholder text for analysis since the transcription was empty. Please speak more clearly or check your microphone."
            
            feedback = analyze_interview_conversation(
                interviewer_transcript, 
                interviewee_transcript, 
                interview_type
            )
            
            return feedback
        else:
            print("Processing mono audio (single channel)")
            transcription_service.add_audio_data(audio_data.astype(np.float32), 'mic')
            transcript = transcription_service.get_transcription('mic')
            print(f"Transcript length: {len(transcript)} chars")
            print(f"Transcript content: '{transcript[:100]}...'")
            
            if not transcript.strip():
                print("WARNING: Transcript is empty!")
                transcript = "This is a placeholder text for analysis since the transcription was empty. Please speak more clearly or check your microphone."
            
            print("Calling analyze_transcript function...")
            feedback = analyze_transcript(transcript, interview_type)
            print(f"Feedback received from analyze_transcript. Type: {type(feedback)}")
            return feedback
            
    finally:
        # Clean up the temporary file if it was created
        if temp_filename != audio_file and os.path.exists(temp_filename):
            os.remove(temp_filename)

def get_current_transcription(channel: str = None) -> str:
    """
    Get the current transcription from the transcription service.
    
    Args:
        channel: Optional channel to get transcription from ('mic', 'tab', or None for both)
    
    Returns:
        str: Current transcription(s)
    """
    return transcription_service.get_transcription(channel)

def analyze_interview_conversation(interviewer_text, interviewee_text, interview_type='behavioral'):
    """
    Analyze both sides of the conversation to provide context-aware feedback
    """
    from .nlp_analysis import analyze_transcript
    
    print("\nIn analyze_interview_conversation function")
    print(f"Interviewer text length: {len(interviewer_text)} chars")
    print(f"Interviewee text length: {len(interviewee_text)} chars")
    
    # If we couldn't capture interviewer audio clearly
    if not interviewer_text:
        print("No interviewer text, analyzing just interviewee response")
        return analyze_transcript(interviewee_text, interview_type)
    
    # Process the full conversation context
    full_context = f"Interviewer: {interviewer_text}\n\nInterviewee: {interviewee_text}"
    print(f"Created full context with length: {len(full_context)} chars")
    
    # Extract the interview question type from interviewer text
    question_type = detect_question_type(interviewer_text)
    print(f"Detected question type: {question_type}")
    
    # Analyze interviewee response with full context
    print("Calling analyze_transcript with full context...")
    result = analyze_transcript(
        interviewee_text, 
        interview_type, 
        context=full_context,
        question_type=question_type
    )
    print(f"Result received from analyze_transcript. Type: {type(result)}")
    return result

def detect_question_type(interviewer_text):
    """
    Detect the type of behavioral question being asked
    """
    interviewer_text = interviewer_text.lower()
    
    # Define question type patterns
    question_types = {
        'challenge': ['challenge', 'difficult', 'overcome', 'problem', 'obstacle'],
        'leadership': ['lead', 'leadership', 'team', 'influence', 'guide', 'mentor'],
        'failure': ['fail', 'mistake', 'wrong', 'unsuccessful', 'learned'],
        'success': ['success', 'achievement', 'proud', 'accomplish'],
        'conflict': ['conflict', 'disagree', 'tension', 'resolution', 'solve'],
        'teamwork': ['team', 'collaborate', 'group', 'cooperation'],
        'initiative': ['initiative', 'beyond', 'proactive', 'volunteer']
    }
    
    # Find matches
    matches = {}
    for qtype, keywords in question_types.items():
        count = sum(1 for keyword in keywords if keyword in interviewer_text)
        if count > 0:
            matches[qtype] = count
    
    if not matches:
        return 'general'
    
    # Return the type with the most keyword matches
    return max(matches.keys(), key=matches.get)