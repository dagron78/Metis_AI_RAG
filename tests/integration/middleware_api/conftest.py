"""
Fixtures for middleware and API integration tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import Request, Response
import jwt
from datetime import datetime, timedelta

from app.main import app
from app.middleware.authentication import JWTBearer, JWTAuthenticationMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.core.dependencies import get_current_user, get_current_active_user

@pytest.fixture
def test_client():
    """Return a TestClient instance for API testing"""
    return TestClient(app)

@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing"""
    payload = {
        "sub": "user123",
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iat": datetime.utcnow(),
        "scope": "user"
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")

@pytest.fixture
def expired_token():
    """Create an expired JWT token for testing"""
    payload = {
        "sub": "user123",
        "exp": datetime.utcnow() - timedelta(minutes=15),
        "iat": datetime.utcnow() - timedelta(minutes=30),
        "scope": "user"
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")

@pytest.fixture
def admin_token():
    """Create a valid JWT token for admin user testing"""
    payload = {
        "sub": "admin123",
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iat": datetime.utcnow(),
        "scope": "admin"
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")

@pytest.fixture
def auth_headers(valid_token):
    """Create authorization headers with a valid token"""
    return {"Authorization": f"Bearer {valid_token}"}

@pytest.fixture
def admin_headers(admin_token):
    """Create authorization headers with an admin token"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def expired_headers(expired_token):
    """Create authorization headers with an expired token"""
    return {"Authorization": f"Bearer {expired_token}"}

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
def mock_request():
    """Mock FastAPI request"""
    mock = MagicMock(spec=Request)
    mock.headers = {"Authorization": "Bearer test_token"}
    mock.cookies = {}
    mock.client = MagicMock(host="127.0.0.1")
    mock.method = "GET"
    mock.url = MagicMock(path="/api/test")
    return mock

@pytest.fixture
def mock_response():
    """Mock FastAPI response"""
    mock = MagicMock(spec=Response)
    mock.status_code = 200
    mock.headers = {}
    return mock

@pytest.fixture
def mock_call_next():
    """Mock call_next function for middleware testing"""
    async def _call_next(request):
        return mock_response()
    
    return AsyncMock(side_effect=_call_next)