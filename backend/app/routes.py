from flask import Blueprint, request, jsonify, Response
from werkzeug.utils import secure_filename
import os
import numpy as np
import time
import json
import threading
from .audio_processing import process_audio
from .mic_transcribe import MicrophoneTranscriber
from .nlp_analysis import analyze_transcript

# Create blueprint
bp = Blueprint('main', __name__)

# Global transcriber instance for microphone
mic_transcriber = None
mic_recording = False
current_transcript = ""
transcript_lock = threading.Lock()

# Configure upload settings
ALLOWED_EXTENSIONS = {'wav', 'webm', 'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Service is running'
    }), 200

@bp.route('/start-mic-recording', methods=['POST'])
def start_mic_recording():
    """Start recording microphone audio"""
    global mic_transcriber, mic_recording
    
    try:
        interview_type = request.json.get('interview_type', 'behavioral')
        
        # Create new transcriber if needed
        if mic_transcriber is None:
            mic_transcriber = MicrophoneTranscriber(interview_type=interview_type)
        
        mic_transcriber.start_recording()
        mic_recording = True
        
        # Start background thread to update transcript
        threading.Thread(target=update_transcript_periodically, daemon=True).start()
        
        return jsonify({
            'status': 'success',
            'message': 'Microphone recording started'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error starting microphone recording: {str(e)}'
        }), 500

@bp.route('/stop-mic-recording', methods=['POST'])
def stop_mic_recording():
    """Stop recording microphone audio"""
    global mic_transcriber, mic_recording
    
    try:
        if mic_transcriber is None:
            return jsonify({
                'error': 'No active microphone recording'
            }), 400
        
        # Stop recording and get final transcript
        mic_transcriber.stop_recording()
        final_transcript = mic_transcriber.get_transcription()
        mic_recording = False
        
        # Clean up
        mic_transcriber = None
        
        return jsonify({
            'status': 'success',
            'transcript': final_transcript
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error stopping microphone recording: {str(e)}'
        }), 500

@bp.route('/get-mic-feedback', methods=['GET'])
def get_mic_feedback():
    """Get the latest microphone transcript and analysis"""
    global mic_transcriber, current_transcript
    
    try:
        if mic_transcriber is None:
            return jsonify({
                'error': 'No active microphone recording'
            }), 400
        
        with transcript_lock:
            transcript = current_transcript
        
        if not transcript:
            return jsonify({
                'status': 'success',
                'message': 'No transcript available yet',
                'feedback': {
                    'message': 'Start speaking to get feedback',
                    'type': 'neutral',
                    'details': {
                        'suggestion': 'Speak clearly into your microphone'
                    }
                }
            }), 200
        
        # Analyze the transcript
        feedback = analyze_transcript(transcript)
        
        return jsonify({
            'status': 'success',
            'transcript': transcript,
            'feedback': feedback
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting microphone feedback: {str(e)}'
        }), 500

def update_transcript_periodically():
    """Update the current transcript periodically"""
    global mic_transcriber, current_transcript, mic_recording
    
    while mic_recording and mic_transcriber is not None:
        try:
            # Get current transcription
            transcript = mic_transcriber.get_transcription()
            
            # Update the shared transcript
            with transcript_lock:
                current_transcript = transcript
            
            # Sleep for a short time
            time.sleep(1)
            
        except Exception as e:
            print(f"Error updating transcript: {e}")
            time.sleep(1)

@bp.route('/analyze', methods=['POST'])
def analyze_interview():
    """
    Process uploaded audio file and return interview feedback
    Expects:
    - audio_file: Audio file in the request
    - interview_type: Type of interview (optional, defaults to 'behavioral')
    """
    # Check if audio file is present in request
    if 'audio_file' not in request.files:
        return jsonify({
            'error': 'No audio file provided'
        }), 400
        
    audio_file = request.files['audio_file']
    
    # Check if a file was actually selected
    if audio_file.filename == '':
        return jsonify({
            'error': 'No file selected'
        }), 400
        
    # Validate file type
    if not allowed_file(audio_file.filename):
        return jsonify({
            'error': f'Invalid file type. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # Get interview type from request or use default
        interview_type = request.form.get('interview_type', 'behavioral')
        
        # Process the audio and get feedback
        feedback = process_audio(audio_file, interview_type)
        
        return jsonify(feedback), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error processing audio: {str(e)}'
        }), 500
