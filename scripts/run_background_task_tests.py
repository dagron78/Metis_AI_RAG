#!/usr/bin/env python3
"""
Run all tests for the Background Task System
"""
import os
import sys
import subprocess
import time
import signal
import argparse

def run_tests(skip_migrations=False):
    """
    Run all tests for the Background Task System
    
    Args:
        skip_migrations: Skip running migrations
        
    Returns:
        Exit code
    """
    print("=== Background Task System Tests ===")
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Change to the project root directory
    os.chdir(project_root)
    
    # Run migrations if not skipped
    if not skip_migrations:
        print("\n1. Running database migrations...")
        try:
            migration_result = subprocess.run(
                ["python", "scripts/run_migrations.py"],
                check=True,
                capture_output=True,
                text=True
            )
            print(migration_result.stdout)
            print("Migrations completed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error running migrations: {e}")
            print(e.stdout)
            print(e.stderr)
            return 1
    else:
        print("\n1. Skipping database migrations...")
    
    # Start the application
    print("\n2. Starting the application...")
    try:
        app_process = subprocess.Popen(
            ["uvicorn", "app.main:app", "--reload"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Wait for the application to start
        print("Waiting for application to start...")
        started = False
        for _ in range(30):  # Wait up to 30 seconds
            try:
                # Check if the application is running
                response = subprocess.run(
                    ["curl", "-s", "http://localhost:8000/api/v1/system/health"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                if "status" in response.stdout:
                    started = True
                    break
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(1)
        
        if not started:
            print("Error: Application failed to start")
            app_process.terminate()
            app_process.wait()
            return 1
        
        print("Application started successfully!")
        
        # Run the tests
        print("\n3. Running background task tests...")
        try:
            test_result = subprocess.run(
                ["python", "scripts/test_background_tasks.py"],
                check=True,
                capture_output=True,
                text=True
            )
            print(test_result.stdout)
            print("Tests completed successfully!")
            
            # Run pytest tests
            print("\n4. Running pytest tests...")
            pytest_result = subprocess.run(
                ["pytest", "tests/test_background_tasks.py", "-v"],
                check=True,
                capture_output=True,
                text=True
            )
            print(pytest_result.stdout)
            print("Pytest tests completed successfully!")
            
            return 0
        except subprocess.CalledProcessError as e:
            print(f"Error running tests: {e}")
            print(e.stdout)
            print(e.stderr)
            return 1
        finally:
            # Stop the application
            print("\nStopping application...")
            app_process.terminate()
            app_process.wait()
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def parse_args():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run Background Task System tests")
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip running database migrations"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    try:
        sys.exit(run_tests(skip_migrations=args.skip_migrations))
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        # Ensure any running processes are terminated
        for proc in subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE).communicate()[0].splitlines():
            if b'uvicorn' in proc:
                pid = int(proc.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)
        sys.exit(1)