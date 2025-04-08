#!/usr/bin/env python3
"""
Test script for text formatting improvements in Metis RAG.
This script tests the formatting of lists, paragraphs, and HTML content in responses.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary modules
from app.core.config import SETTINGS as settings

# Configuration
API_URL = "http://localhost:8000"
LOG_FILE = "text_formatting_improvements_test.log"

# Test credentials
USERNAME = "metistest"
PASSWORD = "metistest123"

def log_message(message):
    """Log a message to both console and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def get_auth_token():
    """Get authentication token."""
    log_message("Getting authentication token...")
    try:
        response = requests.post(
            f"{API_URL}/api/auth/token",
            data={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        token_data = response.json()
        log_message("Authentication successful")
        return token_data["access_token"]
    except Exception as e:
        log_message(f"Authentication failed: {str(e)}")
        if hasattr(response, 'text'):
            log_message(f"Response: {response.text}")
        return None

def send_test_query(token, query, test_name):
    """Send a test query to the API."""
    log_message(f"Running test: {test_name}")
    log_message(f"Query: {query}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "message": query,
        "model": "gemma3:4b",  # Adjust as needed
        "use_rag": True,
        "stream": False,
        "model_parameters": {
            "temperature": 0.7,
            "max_results": 5
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/chat/query",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        log_message(f"Response received for {test_name}")
        log_message(f"Response length: {len(result.get('message', ''))}")
        log_message(f"Response: {result.get('message', '')[:500]}...")  # Log first 500 chars
        return result
    except Exception as e:
        log_message(f"Query failed: {str(e)}")
        if hasattr(response, 'text'):
            log_message(f"Response: {response.text}")
        return None

def run_formatting_tests(token):
    """Run a series of tests for text formatting."""
    tests = [
        {
            "name": "List Formatting Test",
            "query": "List the 11th through 20th largest cities by population."
        },
        {
            "name": "Paragraph Formatting Test",
            "query": "Write a short paragraph about climate change, followed by another paragraph about renewable energy."
        },
        {
            "name": "HTML Example Test",
            "query": "Show me how to format a list with a line break between each item using HTML."
        },
        {
            "name": "Code Block Test",
            "query": "Show me a Python function that sorts a list of dictionaries by a specific key."
        },
        {
            "name": "Mixed Content Test",
            "query": "Explain the difference between REST and GraphQL. Include a code example for each."
        }
    ]
    
    results = {}
    for test in tests:
        result = send_test_query(token, test["query"], test["name"])
        if result:
            results[test["name"]] = result
        time.sleep(2)  # Add a small delay between tests
    
    return results

def main():
    """Main function to run the tests."""
    # Initialize log file
    with open(LOG_FILE, "w") as f:
        f.write(f"Text Formatting Improvements Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
    
    log_message("Starting text formatting tests")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        log_message("Failed to get authentication token. Exiting.")
        return
    
    # Run formatting tests
    results = run_formatting_tests(token)
    
    # Save results to log file
    log_message(f"Tests completed. Results saved to {LOG_FILE}")
    with open(LOG_FILE, "a") as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write("TEST RESULTS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        for test_name, result in results.items():
            f.write(f"Test: {test_name}\n")
            f.write("-" * 40 + "\n")
            if result and "message" in result:
                f.write(f"Response:\n{result['message']}\n\n")
            else:
                f.write("No response or error occurred.\n\n")

if __name__ == "__main__":
    main()