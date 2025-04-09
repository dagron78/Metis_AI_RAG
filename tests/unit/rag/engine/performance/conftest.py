"""
Fixtures for RAG engine performance unit tests
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def event_loop():
    """Create an event loop for each test"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_rag_engine():
    """Create a mock RAG engine for testing"""
    engine = MagicMock()
    engine.query = AsyncMock()
    return engine