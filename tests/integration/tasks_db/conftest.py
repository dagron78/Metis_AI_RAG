"""
Fixtures for tasks and database integration tests
"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base
from app.db.session import get_db
from app.db.repositories.document import DocumentRepository
from app.db.repositories.processing_job import ProcessingJobRepository
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.tasks.background_tasks import process_document, update_vector_store
from app.tasks.task_manager import TaskManager

@pytest.fixture
def test_db():
    """Create a test database"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create the database URL
    db_url = f"sqlite:///{db_path}"
    
    # Create the engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    # Create a session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Yield the session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        os.close(db_fd)
        os.unlink(db_path)

@pytest.fixture
def document_repository(test_db):
    """Create a document repository with the test database"""
    return DocumentRepository(test_db)

@pytest.fixture
def processing_job_repository(test_db):
    """Create a processing job repository with the test database"""
    return ProcessingJobRepository(test_db)

@pytest.fixture
def sample_document():
    """Create a sample document for testing"""
    return Document(
        id=str(uuid.uuid4()),
        title="Test Document",
        filename="test.pdf",
        content="This is a test document content.",
        mime_type="application/pdf",
        size=1024,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id=str(uuid.uuid4()),
        is_public=True,
        status="pending",
        folder="test_folder",
        tags=["test", "document"]
    )

@pytest.fixture
def sample_processing_job(sample_document):
    """Create a sample processing job for testing"""
    return ProcessingJob(
        id=str(uuid.uuid4()),
        document_id=sample_document.id,
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        error=None,
        metadata={
            "filename": sample_document.filename,
            "mime_type": sample_document.mime_type,
            "size": sample_document.size
        }
    )

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
def mock_celery_app():
    """Mock Celery app"""
    mock = MagicMock()
    mock.task.return_value = lambda func: func
    mock.send_task.return_value = MagicMock(id=str(uuid.uuid4()))
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