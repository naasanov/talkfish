# TalkFish SSE Transcription API

This document explains how to use the TalkFish Server-Sent Events (SSE) transcription API for real-time transcription streaming.

## Overview

The SSE Transcription API allows you to:

1. Start a transcription stream from either microphone or tab audio
2. Receive real-time transcription updates via Server-Sent Events
3. Get final feedback when stopping the stream

This approach provides a seamless way to display real-time transcription to users while they speak, with updates sent every 5 seconds automatically.

## API Endpoints

### Start Transcription Stream

```
POST /start-stream
```

**Request Body:**
```json
{
  "stream_type": "mic",  // or "tab"
  "interview_type": "behavioral"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Mic transcription stream started",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Stop Transcription Stream

```
POST /stop-stream
```

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Transcription stream stopped"
}
```

### SSE Transcription Events

```
GET /stream/{session_id}/events
```

**Response:**
- SSE stream with transcription updates
- Event types: `connected`, `message`, `keepalive`, `closed`

### Send Audio Data (Tab Audio Only)

```
POST /stream/{session_id}/audio
```

**Request Body:**
```json
{
  "audio_data": [0.1, 0.2, -0.1, ...]  // Array of float audio samples
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Audio data added to stream"
}
```

### Get Stream Status

```
GET /stream/{session_id}/status
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stream_type": "mic",
  "interview_type": "behavioral",
  "is_active": true,
  "transcript_length": 253,
  "clients": 1
}
```

## Event Types

The SSE endpoint emits several types of events:

1. **connected** - Emitted when the client first connects
   ```
   event: connected
   data: {"session_id": "550e8400-e29b-41d4-a716-446655440000"}
   ```

2. **message** - Regular transcription updates (every 5 seconds)
   ```
   data: {
     "session_id": "550e8400-e29b-41d4-a716-446655440000",
     "transcript": "This is the current transcript...",
     "timestamp": 1682494567.123,
     "is_final": false
   }
   ```

3. **keepalive** - Sent every 30 seconds to keep the connection alive
   ```
   event: keepalive
   data: 1682494567.123
   ```

4. **closed** - Sent when the stream is stopped
   ```
   event: closed
   data: {"session_id": "550e8400-e29b-41d4-a716-446655440000"}
   ```

## Client Implementation

Here's a basic JavaScript implementation for connecting to the SSE stream:

```javascript
// Start a transcription stream
async function startTranscription() {
  const response = await fetch('http://localhost:5001/start-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      stream_type: 'mic',
      interview_type: 'behavioral'
    })
  });
  
  const data = await response.json();
  const sessionId = data.session_id;
  
  // Connect to SSE stream
  const eventSource = new EventSource(`http://localhost:5001/stream/${sessionId}/events`);
  
  // Connected event
  eventSource.addEventListener('connected', function(event) {
    console.log('Connected:', JSON.parse(event.data));
  });
  
  // Regular updates
  eventSource.addEventListener('message', function(event) {
    const data = JSON.parse(event.data);
    console.log('Transcript:', data.transcript);
    
    // Update your UI with the transcript
    document.getElementById('transcript').textContent = data.transcript;
    
    // Handle final update with feedback
    if (data.is_final && data.feedback) {
      console.log('Feedback:', data.feedback);
      // Update your UI with the feedback
    }
  });
  
  // Keepalive
  eventSource.addEventListener('keepalive', function(event) {
    console.log('Keepalive:', event.data);
  });
  
  // Closed
  eventSource.addEventListener('closed', function(event) {
    console.log('Closed:', JSON.parse(event.data));
    eventSource.close();
  });
  
  // Error
  eventSource.onerror = function(error) {
    console.error('Error:', error);
  };
  
  return { sessionId, eventSource };
}

// Stop a transcription stream
async function stopTranscription(sessionId) {
  const response = await fetch('http://localhost:5001/stop-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  
  return await response.json();
}
```

## Example Implementation

For a complete frontend implementation, see:
- `frontend/transcription-sse-example.html` - Full HTML example with UI and JavaScript

## Differences Between Stream Types

### Mic Transcription

For microphone transcription:
1. Start the stream with `stream_type: "mic"`
2. The server will automatically access the microphone and handle audio processing
3. Receive transcription updates via SSE

### Tab Transcription

For tab audio transcription:
1. Start the stream with `stream_type: "tab"`
2. Capture audio from the browser tab in your frontend
3. Send the audio data to the `/stream/{session_id}/audio` endpoint
4. Receive transcription updates via SSE

## Best Practices

1. **Error Handling**: Always implement proper error handling in your client code.
2. **Reconnection**: Implement automatic reconnection if the SSE connection is lost.
3. **Cleanup**: Always stop the stream when done to free up server resources.
4. **Browser Support**: SSE is supported in all modern browsers, but for older browsers, consider using a polyfill.
5. **Connection Limit**: Be aware that browsers typically limit the number of concurrent SSE connections (usually 6 per domain).

## Limitations

- Updates are sent approximately every 5 seconds to balance responsiveness with server load.
- Microphone transcription requires proper permissions in the browser.
- Tab audio transcription requires sending audio data from the client, which can increase network traffic. 