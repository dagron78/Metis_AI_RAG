"""
Fixtures for chat E2E tests
"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.repositories.user import UserRepository
from app.db.repositories.conversation import ConversationRepository
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.core.security import get_password_hash, create_access_token
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.engine.rag_engine import RAGEngine
from app.rag.agents.langgraph_rag_agent import LangGraphRAGAgent

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
def test_conversation(test_db, test_user):
    """Create a test conversation in the database"""
    conv_repo = ConversationRepository(test_db)
    
    # Create a test conversation
    conversation = Conversation(
        title="Test Conversation",
        user_id=test_user.id,
        messages=[
            Message(
                role="user",
                content="Hello, this is a test message"
            ),
            Message(
                role="assistant",
                content="Hello, I am an AI assistant"
            )
        ]
    )
    
    # Add the conversation to the database
    db_conversation = conv_repo.create(conversation)
    
    return db_conversation

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store"""
    mock = AsyncMock(spec=VectorStore)
    mock.search.return_value = [
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
    ]
    return mock

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client"""
    mock = AsyncMock(spec=OllamaClient)
    
    # Mock generate method
    async def mock_generate(prompt, model=None, system_prompt=None, stream=False, parameters=None):
        if stream:
            # For streaming, return an async generator
            async def mock_stream():
                for token in ["This", " is", " a", " mock", " response", "."]:
                    yield token
            return mock_stream()
        else:
            # For non-streaming, return a dict with the response
            return {"response": "This is a mock response."}
    
    mock.generate.side_effect = mock_generate
    
    # Mock create_embedding method
    mock.create_embedding.return_value = [0.1] * 384  # 384-dimensional embedding
    
    return mock

@pytest.fixture
def mock_rag_engine(mock_vector_store, mock_ollama_client):
    """Create a mock RAG engine"""
    engine = MagicMock(spec=RAGEngine)
    
    # Mock query method
    async def mock_query(query, model=None, use_rag=True, stream=False, filter_criteria=None, user_id=None):
        return {
            "query": query,
            "answer": "This is a mock response.",
            "sources": [
                {
                    "chunk_id": "chunk1",
                    "content": "This is a test chunk",
                    "metadata": {"document_id": "doc1"},
                    "distance": 0.1
                }
            ] if use_rag else []
        }
    
    engine.query.side_effect = mock_query
    
    return engine