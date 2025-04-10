"""
Tests for the text formatting components
"""
import pytest
import re
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
    
    def test_format_code_blocks(self):
        """Test formatting code blocks"""
        formatter = CodeFormatter()
        
        # Test basic code block formatting
        text = "Here is some code:\n```python\nprint('hello')\n```"
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the code block
        assert "```python" in formatted_text
        assert "print('hello')" in formatted_text
        
        # Test code block with no language tag
        text = "Here is some code:\n```\nprint('hello')\n```"
        formatted_text = formatter.format(text)
        
        # The formatter should add a language tag
        assert re.search(r"```\w+", formatted_text) is not None


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
    
    def test_format_lists(self):
        """Test formatting lists"""
        formatter = ListFormatter()
        
        # Test unordered list formatting
        text = "Here is a list:\n- Item 1\n- Item 2\n- Item 3"
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the list items
        assert "- Item 1" in formatted_text
        assert "- Item 2" in formatted_text
        assert "- Item 3" in formatted_text
        
        # Test ordered list formatting
        text = "Here is a list:\n1. Item 1\n2. Item 2\n3. Item 3"
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the list items
        assert "1. Item 1" in formatted_text
        assert "2. Item 2" in formatted_text
        assert "3. Item 3" in formatted_text


class TestTableFormatter:
    """Tests for the TableFormatter class"""
    
    def test_can_format(self):
        """Test the can_format method"""
        formatter = TableFormatter()
        
        # Should return True for text with tables
        text_with_table = "Here is a table:\n| Header 1 | Header 2 |\n| --- | --- |\n| Cell 1 | Cell 2 |"
        assert formatter.can_format(text_with_table) is True
        
        # Should return False for text without tables
        text_without_table = "Here is some text without tables"
        assert formatter.can_format(text_without_table) is False
    
    def test_format_tables(self):
        """Test formatting tables"""
        formatter = TableFormatter()
        
        # Test basic table formatting
        text = "Here is a table:\n| Header 1 | Header 2 |\n| --- | --- |\n| Cell 1 | Cell 2 |"
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the table
        assert "| Header 1 | Header 2 |" in formatted_text
        assert "| --- | --- |" in formatted_text
        assert "| Cell 1 | Cell 2 |" in formatted_text


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
    
    def test_format_markdown(self):
        """Test formatting markdown"""
        formatter = MarkdownFormatter()
        
        # Test basic markdown formatting
        text = "# Heading\n\nThis is **bold** and *italic* text."
        formatted_text = formatter.format(text)
        
        # The formatted text should still contain the markdown elements
        assert "# Heading" in formatted_text
        assert "**bold**" in formatted_text
        assert "*italic*" in formatted_text


class TestTextFormattingMonitor:
    """Tests for the TextFormattingMonitor class"""
    
    def test_record_event(self):
        """Test recording events"""
        monitor = get_monitor()
        
        # Record an event
        monitor.record_event(
            approach=FormattingApproach.RULE_BASED,
            event=FormattingEvent.SUCCESS,
            details={"content_type": "code"}
        )
        
        # The event should be recorded in the monitor's stats
        assert monitor.stats["events"] > 0
    
    def test_record_structured_output_success(self):
        """Test recording structured output success"""
        monitor = get_monitor()
        
        # Record a structured output success
        monitor.record_structured_output_success(
            response_size=100,
            content_types=["text", "code"]
        )
        
        # The success should be recorded in the monitor's stats
        assert monitor.stats["structured_output"]["success"] > 0
    
    def test_record_structured_output_error(self):
        """Test recording structured output error"""
        monitor = get_monitor()
        
        # Record a structured output error
        monitor.record_structured_output_error(
            error_message="Invalid JSON",
            processing_stage="json_parsing"
        )
        
        # The error should be recorded in the monitor's stats
        assert monitor.stats["structured_output"]["errors"] > 0
    
    def test_record_fallback(self):
        """Test recording fallback"""
        monitor = get_monitor()
        
        # Record a fallback
        monitor.record_fallback(
            from_approach=FormattingApproach.STRUCTURED_OUTPUT,
            to_approach=FormattingApproach.BACKEND_PROCESSING,
            reason="JSON parsing error"
        )
        
        # The fallback should be recorded in the monitor's stats
        assert monitor.stats["fallbacks"] > 0