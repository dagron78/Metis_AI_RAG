"""
Fixtures for document processing unit tests
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
def mock_document_processor():
    """Create a mock document processor for testing"""
    processor = MagicMock()
    processor.process_document = AsyncMock()
    return processor

@pytest.fixture
def mock_document_analysis_service():
    """Create a mock document analysis service for testing"""
    service = MagicMock()
    service.analyze_document = AsyncMock()
    return service