#!/usr/bin/env python3
"""
Runner script for the Metis RAG API test.
This script:
1. Verifies the API is running
2. Runs the direct API test
"""

import os
import sys
import subprocess
import time
import requests

def check_api_running():
    """Check if the Metis RAG API is running"""
    print("Checking if Metis RAG API is running...")
    
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("✓ Metis RAG API is running")
            return True
        else:
            print(f"✗ Metis RAG API returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Metis RAG API is not running at http://localhost:8000")
        return False
    except Exception as e:
        print(f"✗ Error checking API: {str(e)}")
        return False

def run_api_test():
    """Run the direct API test"""
    try:
        print("\n" + "="*80)
        print("Running Metis RAG API Test")
        print("="*80 + "\n")
        
        # Check if the test script exists
        if not os.path.exists("scripts/test_api_directly.py"):
            print("✗ Error: test_api_directly.py not found!")
            return 1
        
        # Run the test
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, "scripts/test_api_directly.py"], 
            check=False
        )
        end_time = time.time()
        
        # Print summary
        print("\n" + "="*80)
        print(f"Test execution completed in {end_time - start_time:.2f} seconds")
        if result.returncode == 0:
            print("✓ API test completed successfully!")
        else:
            print(f"✗ API test failed with exit code {result.returncode}")
        print("="*80 + "\n")
        
        return result.returncode
        
    except Exception as e:
        print(f"✗ Error running API test: {str(e)}")
        return 1

def main():
    """Main function"""
    print("\nMetis RAG API Test Runner\n")
    
    # Check if API is running
    if not check_api_running():
        print("\nPlease start the Metis RAG API before running the test.")
        print("You can start it with: python -m uvicorn app.main:app --reload")
        return 1
    
    # Run API test
    return run_api_test()

if __name__ == "__main__":
    sys.exit(main())