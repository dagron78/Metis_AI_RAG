"""
Fixtures for RAG component tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store"""
    mock = AsyncMock()
    mock.retrieve.return_value = (
        [
            {
                "chunk_id": "chunk1",
                "content": "This is a test chunk",
                "metadata": {"document_id": "doc1"},
                "distance": 0.1
            },
            {
                "chunk_id": "chunk2",
                "content": "This is another test chunk",
                "metadata": {"document_id": "doc1"},
                "distance": 0.2
            }
        ],
        "success"
    )
    return mock

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client"""
    mock = AsyncMock()
    mock.generate.return_value = {"response": "This is a test response"}
    return mock