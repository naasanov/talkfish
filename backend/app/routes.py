from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from .audio_processing import process_audio, transcribe_audio
from .nlp_analysis import analyze_transcript

# Create blueprint
bp = Blueprint('main', __name__)

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

@bp.route('/transcript', methods=['POST'])
def get_transcript():
    """
    Get just the transcript from the audio without analysis
    Expects:
    - audio_file: Audio file in the request
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
        # Save the file temporarily and get transcript
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join('/tmp', filename)
        audio_file.save(temp_path)
        
        transcript = transcribe_audio(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({
            'transcript': transcript
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error transcribing audio: {str(e)}'
        }), 500
