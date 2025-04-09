"""
Unit tests for the chat API endpoints
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture
def test_client():
    """Return a TestClient instance for API testing"""
    return TestClient(app)

def test_chat_query_endpoint(test_client):
    """Test the chat query endpoint"""
    # Prepare the request payload
    payload = {
        "message": "Hello, how are you?",
        "use_rag": True,
        "stream": False
    }
    
    # Make the request
    response = test_client.post("/api/chat/query", json=payload)
    
    # Assert the response
    assert response.status_code == 200
    response_data = response.json()
    assert "answer" in response_data
    assert "query" in response_data
    assert response_data["query"] == "Hello, how are you?"

def test_chat_query_without_rag(test_client):
    """Test the chat query endpoint without RAG"""
    # Prepare the request payload
    payload = {
        "message": "Hello, how are you?",
        "use_rag": False,
        "stream": False
    }
    
    # Make the request
    response = test_client.post("/api/chat/query", json=payload)
    
    # Assert the response
    assert response.status_code == 200
    response_data = response.json()
    assert "answer" in response_data
    assert "query" in response_data
    assert "sources" in response_data
    assert len(response_data["sources"]) == 0  # No sources when RAG is disabled

def test_chat_query_with_invalid_payload(test_client):
    """Test the chat query endpoint with invalid payload"""
    # Prepare an invalid request payload (missing required field)
    payload = {
        "use_rag": True,
        "stream": False
    }
    
    # Make the request
    response = test_client.post("/api/chat/query", json=payload)
    
    # Assert the response
    assert response.status_code == 422  # Unprocessable Entity

def test_chat_query_with_streaming(test_client):
    """Test the chat query endpoint with streaming enabled"""
    # Prepare the request payload
    payload = {
        "message": "Hello, how are you?",
        "use_rag": True,
        "stream": True
    }
    
    # Make the request
    response = test_client.post("/api/chat/query", json=payload)
    
    # Assert the response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    # Check that the response contains SSE events
    content = response.content.decode("utf-8")
    assert "data:" in content