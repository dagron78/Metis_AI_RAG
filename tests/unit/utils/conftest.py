"""
Fixtures for utility unit tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import tempfile
import os

from app.utils.file_handler import FileHandler
from app.utils.security import get_password_hash, verify_password
from app.utils.text_processor import normalize_text, format_code_blocks

@pytest.fixture
def sample_text():
    """Sample text for testing text processing utilities"""
    return """
    This is a sample text with some formatting.
    
    ```python
    def hello_world():
        print("Hello, world!")
    ```
    
    And here's a list:
    * Item 1
    * Item 2
    * Item 3
    
    And a table:
    | Column 1 | Column 2 |
    |----------|----------|
    | Value 1  | Value 2  |
    | Value 3  | Value 4  |
    """

@pytest.fixture
def sample_code():
    """Sample code for testing code formatting utilities"""
    return """
    ```python
    def hello_world():
        print("Hello, world!")
        
        # This is a comment
        for i in range(10):
            print(i)
    ```
    """

@pytest.fixture
def sample_markdown():
    """Sample markdown for testing markdown formatting utilities"""
    return """
    # Heading 1
    
    ## Heading 2
    
    This is a paragraph with **bold** and *italic* text.
    
    * List item 1
    * List item 2
    * List item 3
    
    1. Numbered item 1
    2. Numbered item 2
    3. Numbered item 3
    
    > This is a blockquote
    
    [Link text](https://example.com)
    
    ![Image alt text](https://example.com/image.jpg)
    
    ```python
    def hello_world():
        print("Hello, world!")
    ```
    
    | Column 1 | Column 2 |
    |----------|----------|
    | Value 1  | Value 2  |
    | Value 3  | Value 4  |
    """

@pytest.fixture
def temp_file():
    """Create a temporary file for testing file handling utilities"""
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as f:
        f.write("This is a test file content.")
    yield path
    os.unlink(path)

@pytest.fixture
def mock_file_handler():
    """Mock file handler"""
    mock = MagicMock(spec=FileHandler)
    mock.save_file.return_value = "test_file.txt"
    mock.get_file.return_value = b"This is a test file content."
    mock.delete_file.return_value = True
    return mock

@pytest.fixture
def mock_text_processor():
    """Mock text processor"""
    mock = MagicMock()
    mock.normalize_text.return_value = "normalized text"
    mock.format_code_blocks.return_value = "formatted code blocks"
    return mock

@pytest.fixture
def mock_security_utils():
    """Mock security utilities"""
    mock = MagicMock()
    mock.get_password_hash.return_value = "hashed_password"
    mock.verify_password.return_value = True
    return mock

@pytest.fixture
def mock_csv_json_handler():
    """Mock CSV/JSON handler"""
    mock = MagicMock()
    mock.csv_to_json.return_value = [{"column1": "value1", "column2": "value2"}]
    mock.json_to_csv.return_value = "column1,column2\nvalue1,value2"
    return mock