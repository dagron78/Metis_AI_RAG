"""
Fixtures for middleware unit tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request, Response
from jose import jwt
from datetime import datetime, timedelta

from app.middleware.jwt_bearer import JWTBearer
from app.middleware.auth import AuthMiddleware
from fastapi import HTTPException

# Create mock class for missing middleware components
class JWTAuthenticationMiddleware:
    """Mock class for JWT authentication middleware"""
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        pass

class RateLimiterMiddleware:
    """Mock class for rate limiter middleware"""
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        pass

class RequestLoggingMiddleware:
    """Mock class for request logging middleware"""
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        pass

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
def mock_jwt_bearer():
    """Mock JWT bearer authentication"""
    mock = MagicMock(spec=JWTBearer)
    mock.__call__.return_value = {"sub": "user123", "scope": "user"}
    return mock

@pytest.fixture
def mock_jwt_authentication_middleware():
    """Mock JWT authentication middleware"""
    mock = MagicMock(spec=JWTAuthenticationMiddleware)
    mock.__call__.return_value = AsyncMock()
    return mock

@pytest.fixture
def mock_rate_limiter_middleware():
    """Mock rate limiter middleware"""
    mock = MagicMock(spec=RateLimiterMiddleware)
    mock.__call__.return_value = AsyncMock()
    return mock

@pytest.fixture
def mock_request_logging_middleware():
    """Mock request logging middleware"""
    mock = MagicMock(spec=RequestLoggingMiddleware)
    mock.__call__.return_value = AsyncMock()
    return mock

@pytest.fixture
def mock_user_db():
    """Mock user database for authentication testing"""
    mock = MagicMock()
    mock.get_user_by_id.return_value = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "is_admin": False
    }
    return mock