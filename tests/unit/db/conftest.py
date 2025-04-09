"""
Fixtures for database unit tests
"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.db.base import Base
from app.db.session import get_db, get_async_db

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
    
    # Yield the session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        os.close(db_fd)
        os.unlink(db_path)

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    mock = MagicMock(spec=Session)
    yield mock

@pytest.fixture
def mock_async_db_session():
    """Mock async database session"""
    mock = AsyncMock(spec=AsyncSession)
    yield mock

@pytest.fixture
def override_get_db(mock_db_session):
    """Override the get_db dependency"""
    def _get_db():
        try:
            yield mock_db_session
        finally:
            mock_db_session.close.return_value = None
    
    return _get_db

@pytest.fixture
def override_get_async_db(mock_async_db_session):
    """Override the get_async_db dependency"""
    async def _get_async_db():
        try:
            yield mock_async_db_session
        finally:
            await mock_async_db_session.close()
    
    return _get_async_db