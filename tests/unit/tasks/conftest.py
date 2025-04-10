"""
Fixtures for background task unit tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import uuid
from datetime import datetime

from app.tasks.background_tasks import process_document, update_vector_store
from app.tasks.task_manager import TaskManager
from app.models.processing_job import ProcessingJob

@pytest.fixture
def mock_task_manager():
    """Mock task manager"""
    mock = MagicMock(spec=TaskManager)
    mock.add_task.return_value = str(uuid.uuid4())
    mock.get_task_status.return_value = {"status": "completed", "result": "Task completed successfully"}
    mock.cancel_task.return_value = True
    return mock

@pytest.fixture
def mock_process_document():
    """Mock process_document task"""
    mock = AsyncMock(spec=process_document)
    mock.return_value = {
        "status": "completed",
        "document_id": str(uuid.uuid4()),
        "chunks_created": 5,
        "processing_time": 2.5
    }
    return mock

@pytest.fixture
def mock_update_vector_store():
    """Mock update_vector_store task"""
    mock = AsyncMock(spec=update_vector_store)
    mock.return_value = {
        "status": "completed",
        "document_id": str(uuid.uuid4()),
        "chunks_added": 5,
        "processing_time": 1.5
    }
    return mock

@pytest.fixture
def sample_processing_job():
    """Create a sample processing job for testing"""
    return ProcessingJob(
        id=str(uuid.uuid4()),
        document_id=str(uuid.uuid4()),
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        error=None,
        metadata={
            "filename": "test.pdf",
            "mime_type": "application/pdf",
            "size": 1024
        }
    )

@pytest.fixture
def mock_celery_app():
    """Mock Celery app"""
    mock = MagicMock()
    mock.task.return_value = lambda func: func
    mock.send_task.return_value = MagicMock(id=str(uuid.uuid4()))
    return mock

@pytest.fixture
def mock_celery_task():
    """Mock Celery task"""
    mock = MagicMock()
    mock.delay.return_value = MagicMock(id=str(uuid.uuid4()))
    mock.apply_async.return_value = MagicMock(id=str(uuid.uuid4()))
    return mock

@pytest.fixture
def mock_document_processor():
    """Mock document processor"""
    mock = MagicMock()
    mock.process.return_value = {
        "document_id": str(uuid.uuid4()),
        "chunks_created": 5,
        "status": "processed"
    }
    return mock

@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    mock = AsyncMock()
    mock.add_document.return_value = None
    mock.search.return_value = [
        {
            "chunk_id": "chunk1",
            "content": "This is a test chunk",
            "metadata": {"document_id": "doc1"},
            "distance": 0.1
        }
    ]
    return mock