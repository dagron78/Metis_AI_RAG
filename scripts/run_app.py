#!/usr/bin/env python3
"""
Run the Metis_RAG application
"""
import os
import sys
import subprocess
import time
import webbrowser

def run_app():
    """
    Run the Metis_RAG application
    """
    print("Starting Metis_RAG application...")
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Change to the project root directory
    os.chdir(project_root)
    
    # Run the application
    try:
        # Start the application
        process = subprocess.Popen(
            ["uvicorn", "app.main:app", "--reload"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Wait for the application to start
        print("Waiting for application to start...")
        started = False
        for line in process.stdout:
            print(line, end="")
            if "Application startup complete" in line:
                started = True
                break
        
        if started:
            print("\nApplication started successfully!")
            
            # Open the browser
            print("Opening browser...")
            webbrowser.open("http://localhost:8000")
            
            # Keep the application running
            print("\nPress Ctrl+C to stop the application")
            try:
                while True:
                    line = process.stdout.readline()
                    if line:
                        print(line, end="")
                    if process.poll() is not None:
                        break
            except KeyboardInterrupt:
                print("\nStopping application...")
            finally:
                process.terminate()
                process.wait()
        else:
            print("Error: Application failed to start")
            return 1
        
        return 0
    except Exception as e:
        print(f"Error running application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_app())