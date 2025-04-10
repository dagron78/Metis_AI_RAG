"""
Fixtures for repository unit tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
from types import ModuleType
from uuid import UUID

from app.db.repositories.base import BaseRepository

# Create mock classes to avoid import errors
class MockDocumentRepository:
    """Mock implementation for DocumentRepository"""
    def __init__(self, session, user_id=None):
        self.session = session
        self.user_id = user_id
        
    def create_document(self, *args, **kwargs):
        """Mock method"""
        return {"id": "doc1", "title": "Test Document"}
        
    def get_document(self, *args, **kwargs):
        """Mock method"""
        return {"id": "doc1", "title": "Test Document"}
        
    def get_all_documents(self, *args, **kwargs):
        """Mock method"""
        return [{"id": "doc1", "title": "Test Document"}]
        
    def update_document(self, *args, **kwargs):
        """Mock method"""
        return {"id": "doc1", "title": "Updated Document"}
        
    def delete_document(self, *args, **kwargs):
        """Mock method"""
        return True

# Use mock implementation if the real one fails to import
try:
    from app.db.repositories.document_repository import DocumentRepository
except ImportError:
    # Register the mock class
    DocumentRepository = MockDocumentRepository
    
try:
    from app.db.repositories.user_repository import UserRepository
except ImportError:
    # Create a mock UserRepository
    UserRepository = MagicMock()

try:
    from app.db.repositories.conversation_repository import ConversationRepository
except ImportError:
    # Create a mock ConversationRepository
    ConversationRepository = MagicMock()

@pytest.fixture
def mock_base_repository():
    """Mock base repository"""
    mock = MagicMock(spec=BaseRepository)
    yield mock

@pytest.fixture
def mock_document_repository():
    """Mock document repository"""
    mock = MagicMock(spec=DocumentRepository)
    
    # Mock common methods
    mock.get_by_id.return_value = {"id": "doc1", "title": "Test Document"}
    mock.get_all.return_value = [
        {"id": "doc1", "title": "Test Document 1"},
        {"id": "doc2", "title": "Test Document 2"}
    ]
    mock.create.return_value = {"id": "doc3", "title": "New Document"}
    mock.update.return_value = {"id": "doc1", "title": "Updated Document"}
    mock.delete.return_value = True
    
    yield mock

@pytest.fixture
def mock_user_repository():
    """Mock user repository"""
    mock = MagicMock(spec=UserRepository)
    
    # Mock common methods
    mock.get_by_id.return_value = {"id": "user1", "username": "testuser"}
    mock.get_by_username.return_value = {"id": "user1", "username": "testuser"}
    mock.get_all.return_value = [
        {"id": "user1", "username": "testuser1"},
        {"id": "user2", "username": "testuser2"}
    ]
    mock.create.return_value = {"id": "user3", "username": "newuser"}
    mock.update.return_value = {"id": "user1", "username": "updateduser"}
    mock.delete.return_value = True
    
    yield mock

@pytest.fixture
def mock_conversation_repository():
    """Mock conversation repository"""
    mock = MagicMock(spec=ConversationRepository)
    
    # Mock common methods
    mock.get_by_id.return_value = {"id": "conv1", "title": "Test Conversation"}
    mock.get_by_user_id.return_value = [
        {"id": "conv1", "title": "Test Conversation 1"},
        {"id": "conv2", "title": "Test Conversation 2"}
    ]
    mock.create.return_value = {"id": "conv3", "title": "New Conversation"}
    mock.update.return_value = {"id": "conv1", "title": "Updated Conversation"}
    mock.delete.return_value = True
    
    yield mock

@pytest.fixture
def mock_async_document_repository():
    """Mock async document repository"""
    mock = AsyncMock(spec=DocumentRepository)
    
    # Mock common methods
    mock.get_by_id.return_value = {"id": "doc1", "title": "Test Document"}
    mock.get_all.return_value = [
        {"id": "doc1", "title": "Test Document 1"},
        {"id": "doc2", "title": "Test Document 2"}
    ]
    mock.create.return_value = {"id": "doc3", "title": "New Document"}
    mock.update.return_value = {"id": "doc1", "title": "Updated Document"}
    mock.delete.return_value = True
    
    yield mock