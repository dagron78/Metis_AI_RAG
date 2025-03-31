import pytest
import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def client():
    """
    Create a TestClient instance for each test.
    This ensures that dependency overrides are correctly applied.
    """
    from fastapi.testclient import TestClient  # Import INSIDE the fixture
    from app.main import app  # Import your FastAPI app

    client = TestClient(app)
    yield client

@pytest.fixture
def test_dir():
    """
    Return the directory containing test files
    """
    return Path(__file__).parent / "data"

@pytest.fixture
def temp_upload_dir(tmpdir):
    """
    Return a temporary directory for uploads
    """
    from app.core.config import UPLOAD_DIR
    original_upload_dir = UPLOAD_DIR
    
    # Temporarily override the upload directory
    import app.core.config
    app.core.config.UPLOAD_DIR = str(tmpdir)
    
    yield str(tmpdir)
    
    # Restore the original upload directory
    app.core.config.UPLOAD_DIR = original_upload_dir