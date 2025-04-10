"""
Fixtures for API and database integration tests
"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.main import app
from app.db.session import Base
from app.db.session import get_session, Base

# Create mock functions for get_db and get_async_db
async def get_async_db():
    """Mock for get_async_db"""
    from unittest.mock import AsyncMock
    from sqlalchemy.ext.asyncio import AsyncSession
    db = AsyncMock(spec=AsyncSession)
    yield db

def get_db():
    """Mock for get_db"""
    from unittest.mock import MagicMock
    from sqlalchemy.orm import Session
    db = MagicMock(spec=Session)
    yield db
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.conversation_repository import ConversationRepository
from app.core.dependencies import get_current_user, get_current_active_user

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
def test_client(test_db):
    """Return a TestClient instance for API testing"""
    return TestClient(app)

@pytest.fixture
def mock_current_user():
    """Mock the current user dependency"""
    mock_user = MagicMock()
    mock_user.id = "user123"
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.is_admin = False
    
    # Override the get_current_user dependency
    def override_get_current_user():
        return mock_user
    
    # Apply the override
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    
    yield mock_user
    
    # Remove the override
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_active_user, None)

@pytest.fixture
def mock_admin_user():
    """Mock the current admin user dependency"""
    mock_user = MagicMock()
    mock_user.id = "admin123"
    mock_user.username = "adminuser"
    mock_user.email = "admin@example.com"
    mock_user.is_active = True
    mock_user.is_admin = True
    
    # Override the get_current_user dependency
    def override_get_current_user():
        return mock_user
    
    # Apply the override
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    
    yield mock_user
    
    # Remove the override
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_active_user, None)

@pytest.fixture
def document_repository(test_db):
    """Create a document repository with the test database"""
    return DocumentRepository(test_db)

@pytest.fixture
def user_repository(test_db):
    """Create a user repository with the test database"""
    return UserRepository(test_db)

@pytest.fixture
def conversation_repository(test_db):
    """Create a conversation repository with the test database"""
    return ConversationRepository(test_db)