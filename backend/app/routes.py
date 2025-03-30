from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import numpy as np
from .audio_processing import process_audio
from .tab_transcribe import TabTranscriber
from .sse_transcribe import (
    start_transcription_stream, 
    stop_transcription_stream, 
    add_audio_data, 
    stream_events, 
    get_stream_status
)

# Create blueprint
bp = Blueprint('main', __name__)

# Global transcriber instance
tab_transcriber = None

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

# --- SSE Transcription Routes ---

@bp.route('/start-stream', methods=['POST'])
def start_stream():
    """
    Start a new SSE transcription stream
    
    Expects JSON with:
    - stream_type: 'mic' or 'tab' (default: 'mic')
    - interview_type: Type of interview (default: 'behavioral')
    
    Returns:
    - session_id: Unique ID for the streaming session
    """
    try:
        data = request.json or {}
        stream_type = data.get('stream_type', 'mic')
        interview_type = data.get('interview_type', 'behavioral')
        
        # Validate stream type
        if stream_type not in ['mic', 'tab']:
            return jsonify({
                'error': 'Invalid stream_type. Must be "mic" or "tab"'
            }), 400
        
        # Start the stream
        session_id = start_transcription_stream(
            interview_type=interview_type,
            stream_type=stream_type
        )
        
        return jsonify({
            'status': 'success',
            'message': f'{stream_type.capitalize()} transcription stream started',
            'session_id': session_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error starting transcription stream: {str(e)}'
        }), 500

@bp.route('/stop-stream', methods=['POST'])
def stop_stream():
    """
    Stop an SSE transcription stream
    
    Expects JSON with:
    - session_id: ID of the stream to stop
    
    Returns:
    - Success message or error
    """
    try:
        data = request.json
        
        if not data or 'session_id' not in data:
            return jsonify({
                'error': 'No session ID provided'
            }), 400
        
        session_id = data['session_id']
        
        # Stop the stream
        success = stop_transcription_stream(session_id)
        
        if not success:
            return jsonify({
                'error': 'Invalid session ID or session already stopped'
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Transcription stream stopped'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error stopping transcription stream: {str(e)}'
        }), 500

@bp.route('/stream/<session_id>/events', methods=['GET'])
def transcription_events(session_id):
    """
    SSE endpoint to receive real-time transcription updates
    
    Returns:
    - Server-Sent Events stream with transcription updates
    """
    response = stream_events(session_id)
    
    if response is None:
        return jsonify({
            'error': 'Invalid session ID or session expired'
        }), 404
    
    return response

@bp.route('/stream/<session_id>/status', methods=['GET'])
def transcription_status(session_id):
    """
    Get status of a transcription stream
    
    Returns:
    - Status details or error
    """
    try:
        status = get_stream_status(session_id)
        
        if not status:
            return jsonify({
                'error': 'Invalid session ID or session expired'
            }), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting stream status: {str(e)}'
        }), 500

@bp.route('/stream/<session_id>/audio', methods=['POST'])
def stream_audio(session_id):
    """
    Add audio data to a tab transcription stream
    
    Expects JSON with:
    - audio_data: Array of audio samples
    
    Returns:
    - Success message or error
    """
    try:
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON'
            }), 400
        
        audio_data = request.json.get('audio_data')
        if not audio_data:
            return jsonify({
                'error': 'No audio data provided'
            }), 400
        
        # Convert to numpy array
        audio_array = np.array(audio_data, dtype=np.float32)
        
        # Add to stream
        success = add_audio_data(session_id, audio_array)
        
        if not success:
            return jsonify({
                'error': 'Invalid session ID, wrong stream type, or session expired'
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Audio data added to stream'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error adding audio data: {str(e)}'
        }), 500

# --- Original Routes ---

@bp.route('/start-tab-recording', methods=['POST'])
def start_tab_recording():
    """Start recording tab audio"""
    global tab_transcriber
    
    try:
        interview_type = request.json.get('interview_type', 'behavioral')
        
        # Create new transcriber if needed
        if tab_transcriber is None:
            tab_transcriber = TabTranscriber(interview_type=interview_type)
        
        tab_transcriber.start_recording()
        
        return jsonify({
            'status': 'success',
            'message': 'Tab recording started'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error starting tab recording: {str(e)}'
        }), 500

@bp.route('/stop-tab-recording', methods=['POST'])
def stop_tab_recording():
    """Stop recording tab audio and return final transcript"""
    global tab_transcriber
    
    try:
        if tab_transcriber is None:
            return jsonify({
                'error': 'No active tab recording'
            }), 400
        
        # Stop recording and get final transcript
        tab_transcriber.stop_recording()
        final_transcript = tab_transcriber.get_transcription()
        
        # Analyze the transcript
        feedback = tab_transcriber.analyze_transcript(final_transcript)
        
        # Clean up
        tab_transcriber = None
        
        return jsonify({
            'status': 'success',
            'transcript': final_transcript,
            'feedback': feedback
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error stopping tab recording: {str(e)}'
        }), 500

@bp.route('/stream-tab-audio', methods=['POST'])
def stream_tab_audio():
    """Stream audio data from the tab"""
    global tab_transcriber
    
    try:
        if tab_transcriber is None:
            return jsonify({
                'error': 'No active tab recording'
            }), 400
        
        # Get audio data from request
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON'
            }), 400
        
        # Extract audio data from request
        audio_data = request.json.get('audio_data')
        if not audio_data:
            return jsonify({
                'error': 'No audio data provided'
            }), 400
        
        # Convert audio data to numpy array
        audio_array = np.array(audio_data, dtype=np.float32)
        
        # Add to transcriber
        tab_transcriber.add_audio_data(audio_array)
        
        # Get current transcription
        current_transcript = tab_transcriber.get_transcription()
        
        return jsonify({
            'status': 'success',
            'transcript': current_transcript
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error processing tab audio: {str(e)}'
        }), 500

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
