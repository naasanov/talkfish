# Testing Instructions for TalkFish Extension

Follow these steps to test the TalkFish extension with the new server implementation:

## Backend Setup

1. Make sure you have a `.env` file in the `backend` directory containing your GEMINI_API_KEY:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Start the servers:
   ```bash
   cd backend
   python run_all.py
   ```
   
   This will start two Flask servers:
   - Main Flask app on port 5001
   - Simple server for microphone transcription on port 5002

## Testing the Extension

1. Load the extension in Chrome:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in the top-right corner)
   - Click "Load unpacked" and select the `extension` directory
   - The TalkFish extension should now appear in your extensions

2. Use the extension:
   - Click on the TalkFish extension icon in your browser toolbar
   - Click "Start" in the popup to show the overlay
   - Click the play button (▶) in the overlay to start recording
   - Speak into your microphone
   - Wait for about 8 seconds to see feedback appear in the overlay
   - Click the pause button (⏸) to stop recording

3. Expected behavior:
   - When recording starts, the button turns red
   - After speaking, you should see feedback cards appear in the overlay
   - The feedback will update approximately every 8 seconds
   - Cards should include:
     - "You Said" - showing your transcript
     - "Feedback" - analysis of your speech
     - "Suggestion" - improvement suggestions

## Troubleshooting

- Check the browser console for errors (F12 → Console)
- Verify both servers are running in the terminal
- Make sure you have allowed microphone access when prompted
- If no feedback appears, check if your microphone is working properly

## Technical Notes

- The implementation uses only mic_transcribe (no tab_transcribe)
- Feedback is delivered every 8 seconds to the frontend overlay
- The system uses a simple Flask server for communication 