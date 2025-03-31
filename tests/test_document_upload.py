#!/usr/bin/env python3
"""
Script to test document upload with authentication.
"""

import requests
import json
import os

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# Test user credentials
TEST_USER = {
    "username": "testuser123",
    "password": "testpassword123"
}

def main():
    print("Testing document upload with authentication...")
    
    # Get authentication token
    print(f"Authenticating as {TEST_USER['username']}...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    
    if response.status_code != 200:
        print(f"Authentication failed: {response.status_code} - {response.text}")
        return False
    
    token_data = response.json()
    access_token = token_data["access_token"]
    print(f"Authentication successful, received token: {access_token[:20]}...")
    
    # Create a test document
    with open("test_upload_document.txt", "w") as f:
        f.write("This is a test document for upload testing.")
    
    # Upload the document
    print("Uploading document...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    with open("test_upload_document.txt", "rb") as f:
        files = {"file": ("test_upload_document.txt", f, "text/plain")}
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers,
            files=files,
            data={"tags": "test,upload", "folder": "/test"}
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Document uploaded successfully: {result['document_id']}")
        return True
    else:
        print(f"Document upload failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "="*80)
    print(f"Document Upload Test: {'✓ Success' if success else '✗ Failed'}")
    print("="*80)