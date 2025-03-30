from simple_server import app

if __name__ == '__main__':
    print("Starting simple server for microphone transcription and feedback...")
    app.run(debug=True, host='0.0.0.0', port=5002) 