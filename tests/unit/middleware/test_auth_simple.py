#!/usr/bin/env python3
"""
Unit tests for authentication with a known user.
"""

import pytest
import logging
import sys
import os
import requests
import json
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_auth_simple")

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
    document_path = os.path.join(project_root, "test_document.txt")
    with open(document_path, "w") as f:
        f.write("This is a test document for authentication testing.")
    
    yield document_path
    
    # Clean up after the test
    if os.path.exists(document_path):
        os.remove(document_path)

@pytest.fixture
def mock_token_response():
    """Mock a successful token response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "mock_access_token_12345",
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": "mock_refresh_token"
    }
    return mock_response

@pytest.fixture
def mock_me_response():
    """Mock a successful /me response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "user123",
        "username": TEST_USER["username"],
        "email": "testuser123@example.com",
        "is_active": True,
        "is_admin": False
    }
    return mock_response

@pytest.fixture
def mock_upload_response():
    """Mock a successful document upload response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "document_id": "doc123",
        "filename": "test_document.txt",
        "status": "success"
    }
    return mock_response

@patch('requests.post')
@patch('requests.get')
def test_authentication_success(mock_get, mock_post, test_document_path, mock_token_response, mock_me_response, mock_upload_response):
    """Test successful authentication and protected endpoint access"""
    # Mock the responses
    mock_post.side_effect = [mock_token_response, mock_upload_response]
    mock_get.return_value = mock_me_response
    
    # Try to get a token
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    
    # Verify token response
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    
    # Test accessing a protected endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # Try to get user info
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["username"] == TEST_USER["username"]
    
    # Try to upload a document
    with open(test_document_path, "rb") as f:
        files = {"file": ("test_document.txt", f, "text/plain")}
        upload_response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers,
            files=files,
            data={"tags": "test,auth", "folder": "/test"}
        )
    
    # Verify upload response
    assert upload_response.status_code == 200
    result = upload_response.json()
    assert "document_id" in result
    assert result["document_id"] == "doc123"

@patch('requests.post')
def test_authentication_failure(mock_post):
    """Test authentication failure with invalid credentials"""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Invalid credentials"
    mock_post.return_value = mock_response
    
    # Try to get a token with invalid credentials
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": "wrong_username",
            "password": "wrong_password"
        }
    )
    
    # Verify response
    assert response.status_code == 401
    assert "Invalid credentials" in response.text

@patch('requests.post')
@patch('requests.get')
def test_protected_endpoint_access_failure(mock_get, mock_post, mock_token_response):
    """Test failure to access protected endpoint with invalid token"""
    # Mock the token response
    mock_post.return_value = mock_token_response
    
    # Mock the protected endpoint response
    mock_me_response = MagicMock()
    mock_me_response.status_code = 401
    mock_me_response.text = "Invalid token"
    mock_get.return_value = mock_me_response
    
    # Get a token
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    
    # Verify token response
    assert response.status_code == 200
    token_data = response.json()
    
    # Try to access protected endpoint with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    # Verify response
    assert me_response.status_code == 401
    assert "Invalid token" in me_response.text