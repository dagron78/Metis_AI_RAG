import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.rag.rag_engine import RAGEngine
from app.models.chat import Citation

@pytest.fixture
def mock_vector_store():
    """
    Create a mock vector store
    """
    mock = AsyncMock()
    mock.search.return_value = [
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
    ]
    return mock

@pytest.fixture
def mock_ollama_client():
    """
    Create a mock Ollama client
    """
    mock = AsyncMock()
    mock.generate.return_value = {"response": "This is a test response"}
    return mock

@pytest.mark.asyncio
async def test_rag_engine_query_with_rag(mock_vector_store, mock_ollama_client):
    """
    Test RAG engine query with RAG enabled
    """
    # Arrange
    engine = RAGEngine(
        vector_store=mock_vector_store,
        ollama_client=mock_ollama_client
    )
    
    # Act
    result = await engine.query(
        query="test query",
        model="test-model",
        use_rag=True,
        stream=False
    )
    
    # Assert
    assert mock_vector_store.search.called
    assert mock_ollama_client.generate.called
    assert result["query"] == "test query"
    assert result["answer"] == "This is a test response"
    assert len(result["sources"]) == 2
    assert isinstance(result["sources"][0], Citation)

@pytest.mark.asyncio
async def test_rag_engine_query_without_rag(mock_vector_store, mock_ollama_client):
    """
    Test RAG engine query with RAG disabled
    """
    # Arrange
    engine = RAGEngine(
        vector_store=mock_vector_store,
        ollama_client=mock_ollama_client
    )
    
    # Act
    result = await engine.query(
        query="test query",
        model="test-model",
        use_rag=False,
        stream=False
    )
    
    # Assert
    assert not mock_vector_store.search.called
    assert mock_ollama_client.generate.called
    assert result["query"] == "test query"
    assert result["answer"] == "This is a test response"
    assert result["sources"] is None