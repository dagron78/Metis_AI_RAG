#!/usr/bin/env python3
"""
Unit tests to verify authentication with the Metis RAG API.
This module tests both direct API calls and the TestClient approach.
"""

import os
import sys
import logging
import pytest
import requests
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_authentication")

# Import app and authentication helper
from app.main import app
from tests.utils.test_auth_helper import (
    configure_test_client,
    verify_authentication,
    authenticate_with_session
)

@pytest.fixture
def base_url():
    """Return the base URL for API tests"""
    return "http://localhost:8000"

@pytest.fixture
def mock_session():
    """Mock requests.Session for testing"""
    session = MagicMock()
    return session

@pytest.fixture
def mock_token_response():
    """Mock a successful token response"""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "access_token": "mock_access_token",
        "token_type": "bearer",
        "expires_in": 3600
    }
    return response

@pytest.fixture
def mock_documents_response():
    """Mock a successful documents response"""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "documents": []
    }
    return response

@pytest.fixture
def mock_failed_auth_response():
    """Mock a failed authentication response"""
    response = MagicMock()
    response.status_code = 401
    response.text = "Invalid credentials"
    return response

@patch('requests.Session')
def test_direct_api_authentication_success(mock_session_class, base_url, mock_token_response, mock_documents_response):
    """Test successful authentication using direct API calls"""
    # Setup mock session
    session = MagicMock()
    mock_session_class.return_value = session
    session.post.return_value = mock_token_response
    session.get.return_value = mock_documents_response
    
    # Call the function under test with patched session
    with patch('tests.utils.test_auth_helper.requests.Session', return_value=session):
        test_session, token = authenticate_with_session(base_url, "testuser", "testpassword")
    
    # Verify the results
    assert token is not None
    assert token == "mock_access_token"
    
    # Verify the session was used correctly
    session.post.assert_called_with(
        f"{base_url}/api/auth/token",
        data={
            "username": "testuser",
            "password": "testpassword",
            "grant_type": "password"
        }
    )
    
    # Test accessing a protected endpoint
    response = test_session.get(f"{base_url}/api/documents")
    assert response.status_code == 200

@patch('requests.Session')
def test_direct_api_authentication_failure(mock_session_class, base_url, mock_failed_auth_response):
    """Test failed authentication using direct API calls"""
    # Setup mock session
    session = MagicMock()
    mock_session_class.return_value = session
    session.post.return_value = mock_failed_auth_response
    
    # Call the function under test with patched session
    with patch('tests.utils.test_auth_helper.requests.Session', return_value=session):
        test_session, token = authenticate_with_session(base_url, "testuser", "wrongpassword")
    
    # Verify the results
    assert token is None
    
    # Verify the session was used correctly
    session.post.assert_called_with(
        f"{base_url}/api/auth/token",
        data={
            "username": "testuser",
            "password": "wrongpassword",
            "grant_type": "password"
        }
    )

def test_testclient_authentication_success(monkeypatch):
    """Test successful authentication using TestClient"""
    # Create a mock TestClient
    mock_client = MagicMock()
    
    # Mock the login response
    mock_login_response = MagicMock()
    mock_login_response.status_code = 200
    mock_login_response.json.return_value = {
        "access_token": "mock_access_token",
        "token_type": "bearer",
        "expires_in": 3600
    }
    
    # Mock the documents response
    mock_documents_response = MagicMock()
    mock_documents_response.status_code = 200
    mock_documents_response.json.return_value = {
        "documents": []
    }
    
    # Mock the me response for verify_authentication
    mock_me_response = MagicMock()
    mock_me_response.status_code = 200
    mock_me_response.json.return_value = {
        "username": "testuser",
        "email": "testuser@example.com"
    }
    
    # Configure the mock client's post and get methods
    mock_client.post.return_value = mock_login_response
    mock_client.get.side_effect = [mock_me_response, mock_documents_response]
    
    # Patch the TestClient constructor
    monkeypatch.setattr('fastapi.testclient.TestClient', lambda app: mock_client)
    
    # Call the function under test
    client = configure_test_client(app, "testuser", "testpassword")
    
    # Verify authentication
    is_authenticated = verify_authentication(client)
    assert is_authenticated is True
    
    # Test accessing a protected endpoint
    response = client.get("/api/documents")
    assert response.status_code == 200
    
    # Verify the client was used correctly
    mock_client.post.assert_called_with(
        "/api/auth/token",
        data={
            "username": "testuser",
            "password": "testpassword",
            "grant_type": "password"
        }
    )
    
    # Verify the Authorization header was set
    assert "Authorization" in mock_client.headers
    assert mock_client.headers["Authorization"] == "Bearer mock_access_token"

def test_testclient_authentication_failure(monkeypatch):
    """Test failed authentication using TestClient"""
    # Create a mock TestClient
    mock_client = MagicMock()
    
    # Mock the login response
    mock_login_response = MagicMock()
    mock_login_response.status_code = 401
    mock_login_response.text = "Invalid credentials"
    
    # Configure the mock client's post method
    mock_client.post.return_value = mock_login_response
    
    # Patch the TestClient constructor
    monkeypatch.setattr('fastapi.testclient.TestClient', lambda app: mock_client)
    
    # Call the function under test
    client = configure_test_client(app, "testuser", "wrongpassword")
    
    # Verify the client was used correctly
    mock_client.post.assert_called_with(
        "/api/auth/token",
        data={
            "username": "testuser",
            "password": "wrongpassword",
            "grant_type": "password"
        }
    )
    
    # Verify the Authorization header was not set
    assert "Authorization" not in mock_client.headers