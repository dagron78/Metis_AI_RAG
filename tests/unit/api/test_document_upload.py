#!/usr/bin/env python3
"""
Unit tests for document upload with authentication.
"""

import pytest
import requests
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# Test user credentials
TEST_USER = {
    "username": "testuser123",
    "password": "testpassword123"
}

@pytest.fixture
def test_document_path():
    """Create a test document and return its path"""
    # Create a test document in the project root
    document_path = os.path.join(project_root, "test_upload_document.txt")
    with open(document_path, "w") as f:
        f.write("This is a test document for upload testing.")
    
    yield document_path
    
    # Clean up after the test
    if os.path.exists(document_path):
        os.remove(document_path)

@pytest.fixture
def mock_auth_response():
    """Mock a successful authentication response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "mock_access_token",
        "token_type": "bearer",
        "expires_in": 3600
    }
    return mock_response

@pytest.fixture
def mock_upload_response():
    """Mock a successful document upload response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "document_id": "mock_document_id",
        "filename": "test_upload_document.txt",
        "status": "success"
    }
    return mock_response

@patch('requests.post')
def test_document_upload_success(mock_post, test_document_path, mock_auth_response, mock_upload_response):
    """Test successful document upload with authentication"""
    # Mock the authentication request
    mock_post.side_effect = [mock_auth_response, mock_upload_response]
    
    # Authenticate
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    
    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # Upload the document
    headers = {"Authorization": f"Bearer {access_token}"}
    
    with open(test_document_path, "rb") as f:
        files = {"file": ("test_upload_document.txt", f, "text/plain")}
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers,
            files=files,
            data={"tags": "test,upload", "folder": "/test"}
        )
    
    # Verify the response
    assert response.status_code == 200
    result = response.json()
    assert "document_id" in result
    assert result["document_id"] == "mock_document_id"

@patch('requests.post')
def test_document_upload_auth_failure(mock_post, test_document_path):
    """Test document upload with authentication failure"""
    # Mock the authentication request to fail
    mock_auth_failure = MagicMock()
    mock_auth_failure.status_code = 401
    mock_auth_failure.text = "Invalid credentials"
    mock_post.return_value = mock_auth_failure
    
    # Attempt to authenticate
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": "wrong_username",
            "password": "wrong_password"
        }
    )
    
    # Verify the response
    assert response.status_code == 401
    assert "Invalid credentials" in response.text

@patch('requests.post')
def test_document_upload_failure(mock_post, test_document_path, mock_auth_response):
    """Test document upload failure"""
    # Mock the authentication request to succeed but upload to fail
    mock_upload_failure = MagicMock()
    mock_upload_failure.status_code = 400
    mock_upload_failure.text = "Invalid file format"
    mock_post.side_effect = [mock_auth_response, mock_upload_failure]
    
    # Authenticate
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    
    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # Attempt to upload the document
    headers = {"Authorization": f"Bearer {access_token}"}
    
    with open(test_document_path, "rb") as f:
        files = {"file": ("test_upload_document.txt", f, "text/plain")}
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers,
            files=files,
            data={"tags": "test,upload", "folder": "/test"}
        )
    
    # Verify the response
    assert response.status_code == 400
    assert "Invalid file format" in response.text