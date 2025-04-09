"""
Tests for the new modular text formatting components
"""
import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.text_formatting.formatters.code_formatter import CodeFormatter
from app.utils.text_formatting.formatters.list_formatter import ListFormatter
from app.utils.text_formatting.formatters.table_formatter import TableFormatter
from app.utils.text_formatting.formatters.markdown_formatter import MarkdownFormatter
from app.utils.text_formatting.monitor import get_monitor, FormattingApproach, FormattingEvent

class TestCodeFormatter:
    """Tests for the CodeFormatter class"""
    
    def test_can_format(self):
        """Test the can_format method"""
        formatter = CodeFormatter()
        
        # Should return True for text with code blocks
        text_with_code = "Here is some code:\n```python\nprint('hello')\n```"
        assert formatter.can_format(text_with_code) is True
        
        # Should return False for text without code blocks
        text_without_code = "Here is some text without code blocks"
        assert formatter.can_format(text_without_code) is False
    
    def test_format(self):
        """Test the format method"""
        formatter = CodeFormatter()
        
        # Test basic code block formatting
        text = "Here is some code:\n```python\nprint('hello')\n```"
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the code block
        assert "```python" in formatted_text
        assert "print('hello')" in formatted_text

class TestListFormatter:
    """Tests for the ListFormatter class"""
    
    def test_can_format(self):
        """Test the can_format method"""
        formatter = ListFormatter()
        
        # Should return True for text with lists
        text_with_list = "Here is a list:\n- Item 1\n- Item 2\n- Item 3"
        assert formatter.can_format(text_with_list) is True
        
        # Should return False for text without lists
        text_without_list = "Here is some text without lists"
        assert formatter.can_format(text_without_list) is False
    
    def test_format(self):
        """Test the format method"""
        formatter = ListFormatter()
        
        # Test unordered list formatting
        text = "Here is a list:\n- Item 1\n- Item 2\n- Item 3"
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the list items
        assert "Item 1" in formatted_text
        assert "Item 2" in formatted_text
        assert "Item 3" in formatted_text

class TestTableFormatter:
    """Tests for the TableFormatter class"""
    
    def test_can_format(self):
        """Test the can_format method"""
        formatter = TableFormatter()
        
        # Should return True for text with tables
        text_with_table = "| Header 1 | Header 2 |\n| --- | --- |\n| Cell 1 | Cell 2 |\n"
        assert formatter.can_format(text_with_table) is True
        
        # Should return False for text without tables
        text_without_table = "Here is some text without tables"
        assert formatter.can_format(text_without_table) is False
    
    def test_format(self):
        """Test the format method"""
        formatter = TableFormatter()
        
        # Test basic table formatting
        text = "| Header 1 | Header 2 |\n| --- | --- |\n| Cell 1 | Cell 2 |\n"
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the table headers and cells
        assert "Header 1" in formatted_text
        assert "Header 2" in formatted_text
        assert "Cell 1" in formatted_text
        assert "Cell 2" in formatted_text

class TestMarkdownFormatter:
    """Tests for the MarkdownFormatter class"""
    
    def test_can_format(self):
        """Test the can_format method"""
        formatter = MarkdownFormatter()
        
        # Should return True for text with markdown elements
        text_with_markdown = "# Heading\n\nThis is **bold** and *italic* text."
        assert formatter.can_format(text_with_markdown) is True
        
        # Should also return True for plain text (as it can be treated as markdown)
        text_without_markdown = "Here is some plain text"
        assert formatter.can_format(text_without_markdown) is True
    
    def test_format(self):
        """Test the format method"""
        formatter = MarkdownFormatter()
        
        # Test basic markdown formatting
        text = "# Heading\n\nThis is **bold** and *italic* text."
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the markdown elements
        assert "Heading" in formatted_text
        assert "bold" in formatted_text
        assert "italic" in formatted_text

class TestTextFormattingMonitor:
    """Tests for the TextFormattingMonitor class"""
    
    def test_record_event(self):
        """Test recording events"""
        monitor = get_monitor()
        
        # Record an event
        monitor.record_event(
            approach=FormattingApproach.STRUCTURED_OUTPUT,
            event=FormattingEvent.SUCCESS,
            details={"content_type": "code"}
        )
        
        # The event should be recorded (no assertion, just checking it doesn't error)
        assert True