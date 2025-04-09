"""
Global pytest configuration.
This file ensures proper setup for all tests.
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Configure pytest-asyncio settings through fixtures
# Don't try to set asyncio_mode directly as it's part of pytest.ini configuration

@pytest.fixture
def event_loop():
    """Create an event loop for each test"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def project_root_path():
    """Return the project root path as a Path object"""
    return Path(project_root)