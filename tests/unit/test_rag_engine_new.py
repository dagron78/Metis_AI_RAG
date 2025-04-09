"""
Tests for the new modular RAG engine
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.rag.engine.rag_engine import RAGEngine
from app.models.chat import Citation

@pytest.fixture
def mock_retrieval_component():
    """Create a mock retrieval component"""
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
def mock_generation_component():
    """Create a mock generation component"""
    mock = AsyncMock()
    mock.generate.return_value = ("This is a test response", {})
    return mock

@pytest.fixture
def mock_memory_component():
    """Create a mock memory component"""
    mock = AsyncMock()
    mock.process_memory_operations.return_value = ("test query", None, "query")
    mock.cleanup_memory.return_value = None
    return mock

@pytest.fixture
def mock_context_builder():
    """Create a mock context builder"""
    mock = AsyncMock()
    mock.build_context.return_value = "This is a test context"
    return mock

@pytest.fixture
def rag_engine(mock_retrieval_component, mock_generation_component, mock_memory_component, mock_context_builder):
    """Create a RAG engine with mocked components"""
    engine = RAGEngine(
        vector_store=AsyncMock(),
        ollama_client=AsyncMock()
    )
    
    # Replace the components with mocks
    engine.retrieval_component = mock_retrieval_component
    engine.generation_component = mock_generation_component
    engine.memory_component = mock_memory_component
    engine.context_builder = mock_context_builder
    
    return engine

@pytest.mark.asyncio
async def test_rag_engine_query_with_rag(rag_engine, mock_retrieval_component, mock_generation_component):
    """Test RAG engine query with RAG enabled"""
    # Act
    result = await rag_engine.query(
        query="test query",
        model="test-model",
        use_rag=True,
        stream=False
    )
    
    # Assert
    assert mock_retrieval_component.retrieve.called
    assert mock_generation_component.generate.called
    assert result["query"] == "test query"
    assert result["answer"] == "This is a test response"

@pytest.mark.asyncio
async def test_rag_engine_query_without_rag(rag_engine, mock_retrieval_component, mock_generation_component):
    """Test RAG engine query with RAG disabled"""
    # Act
    result = await rag_engine.query(
        query="test query",
        model="test-model",
        use_rag=False,
        stream=False
    )
    
    # Assert
    assert not mock_retrieval_component.retrieve.called
    assert mock_generation_component.generate.called
    assert result["query"] == "test query"
    assert result["answer"] == "This is a test response"