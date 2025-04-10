"""
Fixtures for permissions E2E tests
"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timedelta

from app.main import app
from app.db.session import Base
from app.db.session import get_db
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.permission import PermissionRepository
from app.models.user import User
from app.models.document import Document
from app.models.permission import Permission
from app.core.security import get_password_hash, create_access_token
from app.rag.vector_store import VectorStore

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
def test_admin_user(test_db):
    """Create a test admin user in the database"""
    user_repo = UserRepository(test_db)
    
    # Create a test admin user
    hashed_password = get_password_hash("adminpassword")
    user = User(
        username="adminuser",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True
    )
    
    # Add the user to the database
    db_user = user_repo.create(user)
    
    return db_user

@pytest.fixture
def test_user2(test_db):
    """Create a second test user in the database"""
    user_repo = UserRepository(test_db)
    
    # Create a second test user
    hashed_password = get_password_hash("testpassword2")
    user = User(
        username="testuser2",
        email="test2@example.com",
        full_name="Test User 2",
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
def admin_token(test_admin_user):
    """Create a valid JWT token for the test admin user"""
    access_token = create_access_token(
        data={"sub": test_admin_user.username},
        expires_delta=timedelta(minutes=30)
    )
    return access_token

@pytest.fixture
def user2_token(test_user2):
    """Create a valid JWT token for the second test user"""
    access_token = create_access_token(
        data={"sub": test_user2.username},
        expires_delta=timedelta(minutes=30)
    )
    return access_token

@pytest.fixture
def user_headers(user_token):
    """Create authorization headers with a user token"""
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def admin_headers(admin_token):
    """Create authorization headers with an admin token"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def user2_headers(user2_token):
    """Create authorization headers with a second user token"""
    return {"Authorization": f"Bearer {user2_token}"}

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
        is_public=False,
        status="processed",
        folder="test_folder",
        tags=["test", "document"]
    )
    
    # Add the document to the database
    db_document = doc_repo.create(document)
    
    return db_document

@pytest.fixture
def test_permission(test_db, test_document, test_user2):
    """Create a test permission in the database"""
    perm_repo = PermissionRepository(test_db)
    
    # Create a test permission
    permission = Permission(
        document_id=test_document.id,
        user_id=test_user2.id,
        permission_type="read"
    )
    
    # Add the permission to the database
    db_permission = perm_repo.create(permission)
    
    return db_permission

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store"""
    mock = AsyncMock(spec=VectorStore)
    mock.search.return_value = [
        {
            "chunk_id": "chunk1",
            "content": "This is a test chunk",
            "metadata": {"document_id": "doc1", "is_public": False, "user_id": "user1"},
            "distance": 0.1
        }
    ]
    return mock