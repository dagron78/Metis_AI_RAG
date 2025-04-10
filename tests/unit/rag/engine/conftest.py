"""
Fixtures for RAG engine tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

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