#!/usr/bin/env python3
"""
Simple script to test the chat API with different queries.
This will help us compare the responses with the simplified system prompt.
"""

import requests
import json
import sys
import time
import os
import uuid
from datetime import datetime

# API endpoints
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/chat/query"
AUTH_URL = f"{BASE_URL}/api/auth/token"
REGISTER_URL = f"{BASE_URL}/api/auth/register"

# Test user credentials
TEST_USERNAME = f"test_user_{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = "Test@123456"
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"

# Test queries based on the example chat
TEST_QUERIES = [
    "hello",
    "where is Paris in comparison to Madrid",
    "distance and direction",
    "how can I get there from the US?",
    "I will be leaving from Washington DC"
]
# No longer skipping authentication since we're handling it properly
SKIP_AUTH = True

def register_user():
    """Register a test user."""
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "email": TEST_EMAIL,
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(REGISTER_URL, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"Successfully registered user: {TEST_USERNAME}")
            return True
        else:
            print(f"Failed to register user: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error registering user: {e}")
        return False

def get_access_token():
    """Get an access token for the test user."""
    data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(
            AUTH_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("Successfully obtained access token")
            return token_data["access_token"]
        else:
            print(f"Failed to get token: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")
        return None

def send_chat_request(message, conversation_id=None, access_token=None):
    """Send a chat request to the API."""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add authorization header if token is provided
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    payload = {
        "message": message,
        "use_rag": True,  # Enable RAG
        "stream": False   # Don't stream the response
    }
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

def run_test():
    """Run the test queries and print the responses."""
    print(f"Starting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Register a test user
    if not register_user():
        print("Failed to register test user. Exiting.")
        return
    
    # Get an access token
    access_token = get_access_token()
    if not access_token:
        print("Failed to get access token. Exiting.")
        return
    
    print(f"Testing with {len(TEST_QUERIES)} queries")
    print("-" * 80)
    
    conversation_id = None
    
    for i, query in enumerate(TEST_QUERIES):
        print(f"Query {i+1}: {query}")
        
        # Send the query with the access token
        result = send_chat_request(query, conversation_id, access_token)
        
        if result:
            # Save the conversation ID for the next query
            conversation_id = result.get("conversation_id")
            
            # Print the response
            print(f"Response: {result.get('message')}")
            
            # Print the sources if available
            sources = result.get("citations", [])
            if sources:
                print(f"Sources ({len(sources)}):")
                for source in sources:
                    print(f"  - {source}")
            else:
                print("No sources provided")
        else:
            print("Failed to get response")
        
        print("-" * 80)
        
        # Wait a bit between requests
        if i < len(TEST_QUERIES) - 1:
            time.sleep(1)
    
    print("Test completed")

if __name__ == "__main__":
    # Check if the API is available
    try:
        # Just try to connect to the server
        response = requests.get(BASE_URL)
        if response.status_code in [200, 404]:  # Either is fine, just checking if server is up
            run_test()
        else:
            print(f"API health check failed with status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to the API. Make sure the application is running.")
        sys.exit(1)