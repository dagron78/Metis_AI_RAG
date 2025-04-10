"""
Fixtures for text formatting tests
"""
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def sample_text_with_code():
    """Sample text with code blocks"""
    return """Here is some code:

```python
def hello_world():
    print("Hello, world!")
    
hello_world()
```

And here's a JavaScript example:

```javascript
function helloWorld() {
    console.log("Hello, world!");
}

helloWorld();
```"""

@pytest.fixture
def sample_text_with_lists():
    """Sample text with lists"""
    return """Here is a list:
- Item 1
- Item 2
- Item 3

And here's a numbered list:
1. First item
2. Second item
3. Third item"""

@pytest.fixture
def sample_text_with_tables():
    """Sample text with tables"""
    return """Here is a table:

| Header 1 | Header 2 | Header 3 |
| -------- | -------- | -------- |
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |"""

@pytest.fixture
def sample_markdown_text():
    """Sample markdown text"""
    return """# Heading 1

## Heading 2

This is a paragraph with **bold** and *italic* text.

> This is a blockquote

- List item 1
- List item 2
  - Nested item
  - Another nested item
- List item 3"""

@pytest.fixture
def mock_formatting_monitor():
    """Mock formatting monitor"""
    mock = MagicMock()
    return mock