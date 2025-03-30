import time
import json
import uuid
import threading
import queue
from flask import Response

# Dict to store active SSE sessions
active_sessions = {}

class TranscriptionStream:
    def __init__(self, session_id, interview_type='behavioral', stream_type='mic'):
        self.session_id = session_id
        self.interview_type = interview_type
        self.stream_type = stream_type  # 'mic' or 'tab'
        self.is_active = True
        self.clients = {}  # client_id -> queue
        self.transcriber = None
        self.last_transcript = ""
        self.last_update_time = time.time()
        
        # Initialize the appropriate transcriber
        self._init_transcriber()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_transcription)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def _init_transcriber(self):
        """Initialize the appropriate transcriber based on stream_type"""
        if self.stream_type == 'mic':
            from .mic_transcribe import MicTranscriber
            self.transcriber = MicTranscriber(interview_type=self.interview_type)
        else:  # tab
            from .tab_transcribe import TabTranscriber
            self.transcriber = TabTranscriber(interview_type=self.interview_type)
        
        # Start recording
        self.transcriber.start_recording()
    
    def add_client(self, client_id):
        """Add a new client to receive SSE updates"""
        self.clients[client_id] = queue.Queue()
        return self.clients[client_id]
    
    def remove_client(self, client_id):
        """Remove a client"""
        if client_id in self.clients:
            del self.clients[client_id]
    
    def _update_transcription(self):
        """Background thread that updates transcription at regular intervals"""
        update_interval = 5  # seconds
        
        while self.is_active:
            current_time = time.time()
            
            # Check if it's time for an update
            if current_time - self.last_update_time >= update_interval:
                try:
                    # Get current transcription
                    current_transcript = self.transcriber.get_transcription()
                    
                    # If transcript has changed, send update
                    if current_transcript != self.last_transcript:
                        self.last_transcript = current_transcript
                        
                        # Prepare update data
                        update_data = {
                            'session_id': self.session_id,
                            'transcript': current_transcript,
                            'timestamp': current_time,
                            'is_final': False
                        }
                        
                        # Send to all clients
                        self._send_update(update_data)
                    
                    self.last_update_time = current_time
                    
                except Exception as e:
                    print(f"Error updating transcription: {str(e)}")
            
            # Sleep to avoid high CPU usage
            time.sleep(0.5)
        
        # If thread is ending, clean up
        self._cleanup()
    
    def _send_update(self, data):
        """Send update to all connected clients"""
        message = f"data: {json.dumps(data)}\n\n"
        for client_queue in self.clients.values():
            client_queue.put(message)
    
    def add_audio_data(self, audio_data):
        """Add audio data to the transcriber (for tab streaming)"""
        if self.stream_type == 'tab' and self.transcriber:
            self.transcriber.add_audio_data(audio_data)
    
    def stop(self):
        """Stop the transcription stream"""
        self.is_active = False
        
        # Get final transcription and analysis
        if self.transcriber:
            try:
                final_transcript = self.transcriber.get_transcription()
                feedback = self.transcriber.analyze_transcript(final_transcript)
                
                # Send final update
                final_update = {
                    'session_id': self.session_id,
                    'transcript': final_transcript,
                    'feedback': feedback,
                    'timestamp': time.time(),
                    'is_final': True
                }
                
                # Send to all clients
                self._send_update(final_update)
                
            except Exception as e:
                print(f"Error getting final transcription: {str(e)}")
    
    def _cleanup(self):
        """Clean up resources"""
        try:
            # Stop transcriber
            if self.transcriber:
                self.transcriber.stop_recording()
            
            # Send stream closed event to any remaining clients
            closed_message = f"event: closed\ndata: {json.dumps({'session_id': self.session_id})}\n\n"
            for client_queue in self.clients.values():
                client_queue.put(closed_message)
            
            # Remove from active sessions if still there
            if self.session_id in active_sessions:
                del active_sessions[self.session_id]
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")


def start_transcription_stream(interview_type='behavioral', stream_type='mic'):
    """Start a new transcription stream and return the session ID"""
    session_id = str(uuid.uuid4())
    stream = TranscriptionStream(session_id, interview_type, stream_type)
    active_sessions[session_id] = stream
    return session_id


def stop_transcription_stream(session_id):
    """Stop a transcription stream"""
    if session_id in active_sessions:
        active_sessions[session_id].stop()
        return True
    return False


def add_audio_data(session_id, audio_data):
    """Add audio data to a tab transcription stream"""
    if session_id in active_sessions:
        stream = active_sessions[session_id]
        if stream.stream_type == 'tab':
            stream.add_audio_data(audio_data)
            return True
    return False


def stream_events(session_id):
    """Generate SSE events for a transcription stream"""
    if session_id not in active_sessions:
        return None
    
    # Create a unique client ID
    client_id = str(uuid.uuid4())
    client_queue = active_sessions[session_id].add_client(client_id)
    
    # Helper function to generate SSE events
    def generate():
        try:
            # Send initial event
            yield 'event: connected\ndata: {"session_id": "' + session_id + '"}\n\n'
            
            # Send current transcript if available
            stream = active_sessions[session_id]
            if stream.last_transcript:
                initial_data = {
                    'session_id': session_id,
                    'transcript': stream.last_transcript,
                    'timestamp': time.time()
                }
                yield f"data: {json.dumps(initial_data)}\n\n"
            
            # Send keepalive
            yield f"event: keepalive\ndata: {time.time()}\n\n"
            
            # Continue sending events while the stream is active
            while session_id in active_sessions and active_sessions[session_id].is_active:
                try:
                    # Wait for a message with timeout
                    message = client_queue.get(timeout=30)
                    yield message
                    
                    # Send keepalive every 30 seconds
                    yield f"event: keepalive\ndata: {time.time()}\n\n"
                except queue.Empty:
                    # Send keepalive on timeout
                    yield f"event: keepalive\ndata: {time.time()}\n\n"
            
            # Final message when stream ends
            yield 'event: closed\ndata: {"session_id": "' + session_id + '"}\n\n'
            
        finally:
            # Clean up this client when the connection closes
            if session_id in active_sessions:
                active_sessions[session_id].remove_client(client_id)
    
    return Response(generate(), mimetype='text/event-stream')


def get_stream_status(session_id):
    """Get status of a transcription stream"""
    if session_id in active_sessions:
        stream = active_sessions[session_id]
        return {
            'session_id': session_id,
            'stream_type': stream.stream_type,
            'interview_type': stream.interview_type,
            'is_active': stream.is_active,
            'transcript_length': len(stream.last_transcript),
            'clients': len(stream.clients)
        }
    return None 