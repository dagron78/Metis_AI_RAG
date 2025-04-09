"""
Fixtures for document processing E2E tests
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timedelta

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.repositories.document import DocumentRepository
from app.db.repositories.processing_job import ProcessingJobRepository
from app.models.user import User
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.core.security import get_password_hash, create_access_token
from app.rag.vector_store import VectorStore
from app.tasks.background_tasks import process_document, update_vector_store
from app.tasks.task_manager import TaskManager

@pytest.fixture
def test_client():
    """Return a TestClient instance for API testing"""
    return TestClient(app)

@pytest.fixture
def test_db():
    """Create a test database"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create the database URL
    db_url = f"sqlite:///{db_path}"
    
    # Create the engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    # Create a session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override the get_db dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Apply the override
    app.dependency_overrides[get_db] = override_get_db
    
    # Yield the session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        os.close(db_fd)
        os.unlink(db_path)
        
        # Remove the override
        app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def test_user(test_db):
    """Create a test user in the database"""
    from app.db.repositories.user import UserRepository
    user_repo = UserRepository(test_db)
    
    # Create a test user
    hashed_password = get_password_hash("testpassword")
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    
    # Add the user to the database
    db_user = user_repo.create(user)
    
    return db_user

@pytest.fixture
def user_token(test_user):
    """Create a valid JWT token for the test user"""
    access_token = create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=30)
    )
    return access_token

@pytest.fixture
def user_headers(user_token):
    """Create authorization headers with a user token"""
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def test_uploads_dir():
    """Create a temporary directory for uploads"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_document_file():
    """Create a test document file"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, 'w') as f:
        f.write("This is a test document content.")
    
    yield path
    
    # Clean up
    os.unlink(path)

@pytest.fixture
def test_document(test_db, test_user):
    """Create a test document in the database"""
    doc_repo = DocumentRepository(test_db)
    
    # Create a test document
    document = Document(
        title="Test Document",
        filename="test.txt",
        content="This is a test document content.",
        mime_type="text/plain",
        size=30,
        user_id=test_user.id,
        is_public=True,
        status="pending",
        folder="test_folder",
        tags=["test", "document"]
    )
    
    # Add the document to the database
    db_document = doc_repo.create(document)
    
    return db_document

@pytest.fixture
def test_processing_job(test_db, test_document):
    """Create a test processing job in the database"""
    job_repo = ProcessingJobRepository(test_db)
    
    # Create a test processing job
    job = ProcessingJob(
        document_id=test_document.id,
        status="pending",
        metadata={
            "filename": test_document.filename,
            "mime_type": test_document.mime_type,
            "size": test_document.size
        }
    )
    
    # Add the job to the database
    db_job = job_repo.create(job)
    
    return db_job

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store"""
    mock = AsyncMock(spec=VectorStore)
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