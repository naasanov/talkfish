import subprocess
import sys
import os
import time
import signal

def run_servers():
    print("Starting both servers...")
    
    # Start the main Flask app
    main_server = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Start the simple server
    simple_server = subprocess.Popen(
        [sys.executable, "run_simple_server.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print(f"Main server started with PID: {main_server.pid}")
    print(f"Simple server started with PID: {simple_server.pid}")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        
        # Terminate both servers
        main_server.terminate()
        simple_server.terminate()
        
        # Wait for servers to terminate
        main_server.wait()
        simple_server.wait()
        
        print("Servers stopped.")

if __name__ == "__main__":
    run_servers() 