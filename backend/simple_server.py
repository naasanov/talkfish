import flask
from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import threading
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the backend directory to Python path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.mic_transcribe import MicrophoneTranscriber
from app.nlp_analysis import analyze_transcript

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes with detailed config

# Global variables
mic_transcriber = None
is_recording = False
current_transcript = ""
transcript_lock = threading.Lock()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint called")
    return jsonify({
        'status': 'healthy',
        'message': 'Simple server is running'
    }), 200

@app.route('/start-recording', methods=['POST'])
def start_recording():
    """Start recording microphone audio"""
    global mic_transcriber, is_recording
    
    logger.info("Start recording endpoint called")
    
    try:
        interview_type = request.json.get('interview_type', 'behavioral') if request.is_json else 'behavioral'
        logger.info(f"Using interview type: {interview_type}")
        
        # Create new transcriber if needed
        if mic_transcriber is None:
            logger.info("Creating new MicrophoneTranscriber")
            mic_transcriber = MicrophoneTranscriber(interview_type=interview_type)
        
        # Start recording
        logger.info("Starting recording")
        mic_transcriber.start_recording()
        is_recording = True
        
        # Start background thread to update transcript
        logger.info("Starting background thread for transcript updates")
        threading.Thread(target=update_transcript_periodically, daemon=True).start()
        
        return jsonify({
            'status': 'success',
            'message': 'Microphone recording started'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting microphone recording: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Error starting microphone recording: {str(e)}'
        }), 500

@app.route('/stop-recording', methods=['POST'])
def stop_recording():
    """Stop recording microphone audio"""
    global mic_transcriber, is_recording
    
    logger.info("Stop recording endpoint called")
    
    try:
        if mic_transcriber is None:
            logger.warning("No active microphone recording to stop")
            return jsonify({
                'error': 'No active microphone recording'
            }), 400
        
        # Stop recording and get final transcript
        logger.info("Stopping recording")
        mic_transcriber.stop_recording()
        final_transcript = mic_transcriber.get_transcription()
        is_recording = False
        
        # Clean up
        logger.info("Cleaning up")
        mic_transcriber = None
        
        return jsonify({
            'status': 'success',
            'transcript': final_transcript
        }), 200
        
    except Exception as e:
        logger.error(f"Error stopping microphone recording: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Error stopping microphone recording: {str(e)}'
        }), 500

@app.route('/get-feedback', methods=['GET'])
def get_feedback():
    """Get the latest microphone transcript and analysis"""
    global mic_transcriber, current_transcript
    
    logger.info("Get feedback endpoint called")
    
    try:
        if mic_transcriber is None:
            logger.warning("No active microphone recording for feedback")
            return jsonify({
                'error': 'No active microphone recording'
            }), 400
        
        with transcript_lock:
            transcript = current_transcript
        
        if not transcript:
            logger.info("No transcript available yet")
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
        logger.info(f"Analyzing transcript: {transcript[:50]}...")
        feedback = analyze_transcript(transcript)
        logger.info(f"Feedback generated: {str(feedback)[:100]}...")
        
        return jsonify({
            'status': 'success',
            'transcript': transcript,
            'feedback': feedback
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting microphone feedback: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Error getting microphone feedback: {str(e)}'
        }), 500

# Add this catch-all route for 404 errors to help diagnose issues
@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 error: {request.path}")
    return jsonify({
        'error': f'Endpoint not found: {request.path}',
        'status': 404,
        'message': 'The requested URL was not found on the server'
    }), 404

def update_transcript_periodically():
    """Update the current transcript periodically"""
    global mic_transcriber, current_transcript, is_recording
    
    logger.info("Starting periodic transcript updates")
    
    while is_recording and mic_transcriber is not None:
        try:
            # Get current transcription
            transcript = mic_transcriber.get_transcription()
            
            # Update the shared transcript
            with transcript_lock:
                current_transcript = transcript
                logger.debug(f"Updated transcript: {transcript[:50]}...")
            
            # Sleep for a short time
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error updating transcript: {str(e)}", exc_info=True)
            time.sleep(1)
    
    logger.info("Stopping periodic transcript updates")

if __name__ == '__main__':
    # Run the Flask app on port 5002 to avoid conflict with the main Flask app
    logger.info("Starting simple server on port 5002")
    app.run(debug=True, host='0.0.0.0', port=5002) 