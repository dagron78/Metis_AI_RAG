"""
Fixtures for model unit tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
import uuid

from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.processing_job import ProcessingJob

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
        status="processed",
        folder="test_folder",
        tags=["test", "document"],
        chunks=[
            DocumentChunk(
                id=str(uuid.uuid4()),
                content="This is chunk 1",
                metadata={"index": 0},
                embedding=[0.1, 0.2, 0.3]
            ),
            DocumentChunk(
                id=str(uuid.uuid4()),
                content="This is chunk 2",
                metadata={"index": 1},
                embedding=[0.4, 0.5, 0.6]
            )
        ]
    )

@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing"""
    return Conversation(
        id=str(uuid.uuid4()),
        title="Test Conversation",
        user_id=str(uuid.uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        messages=[
            Message(
                id=str(uuid.uuid4()),
                role="user",
                content="Hello, this is a test message",
                created_at=datetime.now()
            ),
            Message(
                id=str(uuid.uuid4()),
                role="assistant",
                content="Hello, I am an AI assistant",
                created_at=datetime.now()
            )
        ]
    )

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
def mock_document_analysis_service():
    """Mock document analysis service"""
    mock = MagicMock()
    mock.analyze_document.return_value = {
        "entities": ["entity1", "entity2"],
        "summary": "This is a test document summary.",
        "topics": ["topic1", "topic2"],
        "sentiment": "positive"
    }
    return mock