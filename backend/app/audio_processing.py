import speech_recognition as sr
import tempfile
import os
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
from .nlp_analysis import analyze_transcript

def process_audio(audio_file, interview_type='behavioral'):
    """
    Process the audio file to extract speech from both interviewer and interviewee
    and generate feedback.
    """
    # Create a temporary file to store the audio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_filename = temp_file.name
    temp_file.close()
    
    try:
        # Save the uploaded file to the temporary location
        audio_file.save(temp_filename)
        
        # Convert audio to WAV if needed
        if not temp_filename.endswith('.wav'):
            webm_audio = AudioSegment.from_file(temp_filename)
            temp_filename_wav = temp_filename.replace('.webm', '.wav')
            webm_audio.export(temp_filename_wav, format="wav")
            os.remove(temp_filename)
            temp_filename = temp_filename_wav
        
        # Split stereo channels (left: interviewee mic, right: interviewer from tab)
        sample_rate, audio_data = wavfile.read(temp_filename)
        
        # Check if audio is stereo (2 channels)
        if len(audio_data.shape) == 2 and audio_data.shape[1] == 2:
            interviewee_audio = audio_data[:, 0]  # Left channel (microphone)
            interviewer_audio = audio_data[:, 1]  # Right channel (tab audio)
            
            # Create temporary files for each channel
            interviewee_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            interviewer_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            
            # Save separate audio files
            wavfile.write(interviewee_temp.name, sample_rate, interviewee_audio)
            wavfile.write(interviewer_temp.name, sample_rate, interviewer_audio)
            
            interviewee_temp.close()
            interviewer_temp.close()
            
            # Transcribe both channels
            interviewee_transcript = transcribe_audio(interviewee_temp.name)
            interviewer_transcript = transcribe_audio(interviewer_temp.name)
            
            # Clean up temp files
            os.remove(interviewee_temp.name)
            os.remove(interviewer_temp.name)
            
            # Analyze the combined conversation context
            feedback = analyze_interview_conversation(
                interviewer_transcript, 
                interviewee_transcript, 
                interview_type
            )
            
            return feedback
        else:
            # If not stereo, process as a single channel
            transcript = transcribe_audio(temp_filename)
            feedback = analyze_transcript(transcript, interview_type)
            return feedback
            
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

def transcribe_audio(audio_file_path):
    """
    Transcribe audio file to text using Google Speech Recognition
    """
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source)
            # Record audio data
            audio_data = recognizer.record(source)
        
        # Convert speech to text
        transcript = recognizer.recognize_google(audio_data)
        return transcript
        
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"Speech recognition service error: {e}")
        return ""

def analyze_interview_conversation(interviewer_text, interviewee_text, interview_type='behavioral'):
    """
    Analyze both sides of the conversation to provide context-aware feedback
    """
    from .nlp_analysis import analyze_transcript
    
    # If we couldn't capture interviewer audio clearly
    if not interviewer_text:
        return analyze_transcript(interviewee_text, interview_type)
    
    # Process the full conversation context
    full_context = f"Interviewer: {interviewer_text}\n\nInterviewee: {interviewee_text}"
    
    # Extract the interview question type from interviewer text
    question_type = detect_question_type(interviewer_text)
    
    # Analyze interviewee response with full context
    return analyze_transcript(
        interviewee_text, 
        interview_type, 
        context=full_context,
        question_type=question_type
    )

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