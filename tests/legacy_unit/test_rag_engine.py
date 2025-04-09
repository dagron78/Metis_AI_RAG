import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.rag.engine.rag_engine import RAGEngine
from app.models.chat import Citation

@pytest.fixture
def mock_retrieval_component():
    """
    Create a mock retrieval component
    """
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
    """
    Create a mock generation component
    """
    mock = AsyncMock()
    mock.generate.return_value = ("This is a test response", {})
    return mock

@pytest.fixture
def mock_memory_component():
    """
    Create a mock memory component
    """
    mock = AsyncMock()
    mock.process_memory_operations.return_value = ("test query", None, "query")
    mock.cleanup_memory.return_value = None
    return mock

@pytest.fixture
def mock_context_builder():
    """
    Create a mock context builder
    """
    mock = AsyncMock()
    mock.build_context.return_value = "This is a test context"
    return mock

@pytest.mark.asyncio
async def test_rag_engine_query_with_rag():
    """
    Test RAG engine query with RAG enabled
    """
    # Arrange
    with patch('app.rag.engine.components.retrieval.RetrievalComponent') as mock_retrieval_class, \
         patch('app.rag.engine.components.generation.GenerationComponent') as mock_generation_class, \
         patch('app.rag.engine.components.memory.MemoryComponent') as mock_memory_class, \
         patch('app.rag.engine.components.context_builder.ContextBuilder') as mock_context_builder_class:
        
        # Create mock components
        mock_retrieval = AsyncMock()
        mock_retrieval.retrieve.return_value = (
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
        
        mock_generation = AsyncMock()
        mock_generation.generate.return_value = ("This is a test response", {})
        
        mock_memory = AsyncMock()
        mock_memory.process_memory_operations.return_value = ("test query", None, "query")
        mock_memory.cleanup_memory.return_value = None
        
        mock_context = AsyncMock()
        mock_context.build_context.return_value = "This is a test context"
        
        # Configure the mock classes to return our mock instances
        mock_retrieval_class.return_value = mock_retrieval
        mock_generation_class.return_value = mock_generation
        mock_memory_class.return_value = mock_memory
        mock_context_builder_class.return_value = mock_context
        
        # Create the engine
        engine = RAGEngine(
            vector_store=AsyncMock(),
            ollama_client=AsyncMock()
        )
        
        # Act
        result = await engine.query(
            query="test query",
            model="test-model",
            use_rag=True,
            stream=False
        )
        
        # Assert
        assert mock_retrieval.retrieve.called
        assert mock_generation.generate.called
        assert result["query"] == "test query"
        assert result["answer"] == "This is a test response"
        assert len(result["sources"]) == 2
        assert isinstance(result["sources"][0], Citation)

@pytest.mark.asyncio
async def test_rag_engine_query_without_rag():
    """
    Test RAG engine query with RAG disabled
    """
    # Arrange
    with patch('app.rag.engine.components.retrieval.RetrievalComponent') as mock_retrieval_class, \
         patch('app.rag.engine.components.generation.GenerationComponent') as mock_generation_class, \
         patch('app.rag.engine.components.memory.MemoryComponent') as mock_memory_class, \
         patch('app.rag.engine.components.context_builder.ContextBuilder') as mock_context_builder_class:
        
        # Create mock components
        mock_retrieval = AsyncMock()
        mock_retrieval.retrieve.return_value = ([], "no_documents")
        
        mock_generation = AsyncMock()
        mock_generation.generate.return_value = ("This is a test response", {})
        
        mock_memory = AsyncMock()
        mock_memory.process_memory_operations.return_value = ("test query", None, "query")
        mock_memory.cleanup_memory.return_value = None
        
        mock_context = AsyncMock()
        mock_context.build_context.return_value = "This is a test context"
        
        # Configure the mock classes to return our mock instances
        mock_retrieval_class.return_value = mock_retrieval
        mock_generation_class.return_value = mock_generation
        mock_memory_class.return_value = mock_memory
        mock_context_builder_class.return_value = mock_context
        
        # Create the engine
        engine = RAGEngine(
            vector_store=AsyncMock(),
            ollama_client=AsyncMock()
        )
        
        # Act
        result = await engine.query(
            query="test query",
            model="test-model",
            use_rag=False,
            stream=False
        )
        
        # Assert
        assert not mock_retrieval.retrieve.called
        assert mock_generation.generate.called
        assert result["query"] == "test query"
        assert result["answer"] == "This is a test response"
        assert result["sources"] == []