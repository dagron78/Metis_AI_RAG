"""
Unit tests for the chat API endpoints
"""
import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

from app.main import app
from app.core.config import SETTINGS
from app.core.security import get_current_user, get_current_active_user

@pytest.fixture
def test_client():
    """Return a TestClient instance for API testing"""
    return TestClient(app)

@pytest.fixture
def mock_current_user():
    """Mock the current user dependency"""
    # Create a mock user
    mock_user = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "is_admin": False
    }
    
    # Override the get_current_user dependency
    async def override_get_current_user():
        return mock_user
    
    # Apply the override
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    
    yield mock_user
    
    # Remove the override
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_active_user, None)

@pytest.fixture
def auth_headers():
    """Create authorization headers with a valid token"""
    # Create a token that expires in 30 minutes
    expiration = datetime.utcnow() + timedelta(minutes=30)
    payload = {
        "sub": "testuser",
        "user_id": "user123",  # Add user_id field
        "exp": expiration,
        "iat": datetime.utcnow(),
        "token_type": "access"  # Add token_type field
    }
    token = jwt.encode(payload, SETTINGS.secret_key, algorithm=SETTINGS.algorithm)
    return {"Authorization": f"Bearer {token}"}

def test_chat_query_endpoint(test_client, mock_current_user, auth_headers):
    """Test the chat query endpoint"""
    # Prepare the request payload
    payload = {
        "message": "Hello, how are you?",
        "use_rag": True,
        "stream": False
    }
    
    # Make the request with authentication
    response = test_client.post("/api/chat/query", json=payload, headers=auth_headers)
    
    # Assert the response
    assert response.status_code == 200
    response_data = response.json()
    assert "answer" in response_data
    assert "query" in response_data
    assert response_data["query"] == "Hello, how are you?"

def test_chat_query_without_rag(test_client, mock_current_user, auth_headers):
    """Test the chat query endpoint without RAG"""
    # Prepare the request payload
    payload = {
        "message": "Hello, how are you?",
        "use_rag": False,
        "stream": False
    }
    
    # Make the request with authentication
    response = test_client.post("/api/chat/query", json=payload, headers=auth_headers)
    
    # Assert the response
    assert response.status_code == 200
    response_data = response.json()
    assert "answer" in response_data
    assert "query" in response_data
    assert "sources" in response_data
    assert len(response_data["sources"]) == 0  # No sources when RAG is disabled

def test_chat_query_with_invalid_payload(test_client, mock_current_user, auth_headers):
    """Test the chat query endpoint with invalid payload"""
    # Prepare an invalid request payload (missing required field)
    payload = {
        "use_rag": True,
        "stream": False
    }
    
    # Make the request with authentication
    response = test_client.post("/api/chat/query", json=payload, headers=auth_headers)
    
    # Assert the response
    assert response.status_code == 422  # Unprocessable Entity

def test_chat_query_with_streaming(test_client, mock_current_user, auth_headers):
    """Test the chat query endpoint with streaming enabled"""
    # Prepare the request payload
    payload = {
        "message": "Hello, how are you?",
        "use_rag": True,
        "stream": True
    }
    
    # Make the request with authentication
    response = test_client.post("/api/chat/query", json=payload, headers=auth_headers)
    
    # Assert the response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    # Check that the response contains SSE events
    content = response.content.decode("utf-8")
    assert "data:" in content