"""
Fixtures for core unit tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.core.config import Settings
from app.core.security import create_access_token, get_password_hash
from app.core.dependencies import get_current_user, get_current_active_user

class MockUser(BaseModel):
    """Mock user model for testing"""
    id: str
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False
    
    class Config:
        arbitrary_types_allowed = True

@pytest.fixture
def mock_settings():
    """Mock application settings"""
    mock = MagicMock(spec=Settings)
    mock.SECRET_KEY = "test_secret_key"
    mock.ALGORITHM = "HS256"
    mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock.DATABASE_URL = "sqlite:///./test.db"
    mock.REDIS_URL = "redis://localhost:6379/0"
    mock.OLLAMA_BASE_URL = "http://localhost:11434"
    mock.DEFAULT_MODEL = "llama2"
    mock.DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
    mock.ENABLE_CACHE = True
    mock.CACHE_TTL = 3600
    mock.UPLOADS_DIR = "./uploads"
    mock.CHROMA_DB_DIR = "./chroma_db"
    mock.LOG_LEVEL = "INFO"
    mock.CORS_ORIGINS = ["http://localhost:3000"]
    mock.API_V1_PREFIX = "/api/v1"
    return mock

@pytest.fixture
def mock_token_data():
    """Mock token data for testing"""
    return {
        "sub": "user123",
        "exp": 1716841200,  # 2024-05-27T12:00:00Z
        "iat": 1716837600,  # 2024-05-27T11:00:00Z
        "scope": "user"
    }

@pytest.fixture
def mock_access_token():
    """Mock access token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNzE2ODQxMjAwLCJpYXQiOjE3MTY4Mzc2MDAsInNjb3BlIjoidXNlciJ9.8HUL8cqYgXdnzVrJWWqq9UVdlrGjYBKBrQoyGwN1AAc"

@pytest.fixture
def mock_user():
    """Mock user for testing"""
    return MockUser(
        id="user123",
        username="testuser",
        email="test@example.com",
        is_active=True,
        is_admin=False
    )

@pytest.fixture
def mock_admin_user():
    """Mock admin user for testing"""
    return MockUser(
        id="admin123",
        username="adminuser",
        email="admin@example.com",
        is_active=True,
        is_admin=True
    )

@pytest.fixture
def mock_inactive_user():
    """Mock inactive user for testing"""
    return MockUser(
        id="inactive123",
        username="inactiveuser",
        email="inactive@example.com",
        is_active=False,
        is_admin=False
    )

@pytest.fixture
def mock_get_current_user():
    """Mock get_current_user dependency"""
    async def _get_current_user():
        return MockUser(
            id="user123",
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_admin=False
        )
    
    return AsyncMock(side_effect=_get_current_user)

@pytest.fixture
def mock_get_current_admin_user():
    """Mock get_current_user dependency for admin user"""
    async def _get_current_admin_user():
        return MockUser(
            id="admin123",
            username="adminuser",
            email="admin@example.com",
            is_active=True,
            is_admin=True
        )
    
    return AsyncMock(side_effect=_get_current_admin_user)

@pytest.fixture
def mock_security_functions():
    """Mock security functions"""
    mock = MagicMock()
    mock.create_access_token.return_value = "mock_access_token"
    mock.get_password_hash.return_value = "mock_hashed_password"
    mock.verify_password.return_value = True
    return mock