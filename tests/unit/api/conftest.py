"""
Fixtures for API unit tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture
def test_client():
    """Return a TestClient instance for API testing"""
    return TestClient(app)

@pytest.fixture
def mock_auth_middleware():
    """Mock authentication middleware"""
    return MagicMock()

@pytest.fixture
def mock_db_session():
    """Mock database session for API tests"""
    mock = MagicMock()
    yield mock