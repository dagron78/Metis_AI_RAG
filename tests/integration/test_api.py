import pytest
from fastapi.testclient import TestClient
import os
import tempfile
from io import BytesIO
import uuid
from unittest.mock import AsyncMock

from app.main import app
from app.models.chat import ChatQuery
from app.models.document import DocumentProcessRequest
# Import necessary components for dependency injection and mocking
from app.rag.agents.langgraph_rag_agent import LangGraphRAGAgent
from app.rag.ollama_client import OllamaClient
from app.rag.vector_store import VectorStore

# --- Fixture for TestClient ---
@pytest.fixture
def client():
    """
    Create a TestClient instance for each test.
    This ensures that dependency overrides are correctly applied.
    """
    with TestClient(app) as c:  # Use 'with' statement for proper cleanup
        yield c


# --- Helper function for dependency injection ---
async def get_langgraph_rag_agent():
    """Dependency for injecting the LangGraphRAGAgent"""
    # In a real application, you'd create the agent here with proper dependencies
    # For testing, we'll override this with a mocked version
    return LangGraphRAGAgent()


def test_health_check(client: TestClient):  # Use the fixture
    """
    Test the health check endpoint
    """
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # Note: This might fail in CI if Ollama is not available

def test_chat_query_without_context(client: TestClient): # Use the fixture
    """
    Test chat query without RAG context
    """
    # Arrange
    query = ChatQuery(
        message="Hello, world!",
        use_rag=False,
        stream=False
    )

    # Act
    response = client.post("/api/chat/query", json=query.dict())

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "conversation_id" in data

@pytest.mark.asyncio
async def test_langgraph_rag_chat_endpoint(client: TestClient): # Use the fixture
    """
    Test the LangGraph RAG Agent query endpoint
    """
    # Arrange: Create a mock query
    query = ChatQuery(
        message="What are the key features of the Metis RAG system?",
        use_rag=True,
        stream=False
    )

    # Mock dependencies (OllamaClient and VectorStore)
    mock_ollama_client = AsyncMock(spec=OllamaClient)
    mock_vector_store = AsyncMock(spec=VectorStore)

    # Configure mock responses (adjust as needed for your test case)
    mock_ollama_client.generate.return_value = {"response": "This is a mock LLM response."}
    mock_vector_store.search.return_value = [
        {
            "chunk_id": "chunk1",
            "content": "Metis RAG features include document management...",
            "metadata": {"document_id": "doc1", "filename": "test.txt"},
            "distance": 0.1
        }
    ]

    # Create an instance of the LangGraphRAGAgent with mocked dependencies
    mock_rag_agent = LangGraphRAGAgent(
        ollama_client=mock_ollama_client,
        vector_store=mock_vector_store
    )

    # Patch the global langgraph_rag_agent in app/api/chat.py
    import app.api.chat
    original_agent = app.api.chat.langgraph_rag_agent
    app.api.chat.langgraph_rag_agent = mock_rag_agent

    try:
        # Act: Send the request to the correct endpoint
        response = client.post("/api/chat/langgraph_query", json=query.dict())  # Using the endpoint defined in app/api/chat.py

        # Assert: Check the response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "conversation_id" in data
        assert "citations" in data

        # Assert that the mocked methods were called
        mock_ollama_client.generate.assert_called()
        mock_vector_store.search.assert_called()
    finally:
        # Restore the original agent (IMPORTANT for other tests)
        app.api.chat.langgraph_rag_agent = original_agent

# Ollama is running, so we can run this test
def test_document_upload_and_process(client: TestClient): # Use the fixture
    """
    Test document upload and processing
    """
    # Arrange
    test_content = b"This is a test document for RAG testing."
    test_file = BytesIO(test_content)
    test_file.name = "test.txt"

    # Act - Upload
    upload_response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", test_file, "text/plain")}
    )

    # Assert - Upload
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["success"] is True
    assert "document_id" in upload_data
    document_id = upload_data["document_id"]

    # Act - Process
    process_request = DocumentProcessRequest(document_ids=[document_id])
    process_response = client.post(
        "/api/documents/process",
        json=process_request.dict()
    )

    # Assert - Process
    assert process_response.status_code == 200
    process_data = process_response.json()
    assert process_data["success"] is True

    # Act - Get Document (to check chunk count)
    get_response = client.get(f"/api/documents/{document_id}")
    assert get_response.status_code == 200
    document = get_response.json()
    assert "chunks" in document
    assert len(document["chunks"]) > 0  # Check that chunks were created

    # Act - List Documents
    list_response = client.get("/api/documents/list")

    # Assert - List Documents
    assert list_response.status_code == 200
    documents = list_response.json()
    assert len(documents) >= 1
    found = any(doc["id"] == document_id for doc in documents)
    assert found is True

    # Act - Delete
    delete_response = client.delete(f"/api/documents/{document_id}")

    # Assert - Delete
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["success"] is True