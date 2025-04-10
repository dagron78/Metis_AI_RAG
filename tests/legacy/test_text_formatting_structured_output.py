"""
Test the structured output approach for text formatting
"""
import pytest
import json
import re
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.structured_output import FormattedResponse, CodeBlock, TextBlock
from app.rag.rag_engine import RAGEngine
from app.rag.system_prompts import STRUCTURED_CODE_OUTPUT_PROMPT
from app.rag.rag_generation import GenerationMixin


@pytest.fixture
def mock_rag_engine():
    """Create a mock RAG engine for testing"""
    engine = MagicMock(spec=RAGEngine)
    engine._is_code_related_query = MagicMock(return_value=True)
    engine._create_system_prompt = MagicMock(return_value=STRUCTURED_CODE_OUTPUT_PROMPT)
    engine.ollama_client = AsyncMock()
    engine.cache_manager = MagicMock()
    engine.cache_manager.llm_response_cache.get_response = MagicMock(return_value=None)
    engine._record_analytics = AsyncMock()
    engine._cleanup_memory = AsyncMock()
    return engine


@pytest.mark.asyncio
async def test_text_formatting_detection():
    """Test that text formatting queries are detected correctly"""
    # Create a RAG engine
    engine = RAGEngine()
    
    # Test text formatting queries
    formatting_queries = [
        "How do I format text properly?",
        "Help me with paragraph structure in my document",
        "I need to preserve paragraphs in my text",
        "How to format code blocks in markdown",
        "What's the best way to use structured output for text?"
    ]
    
    for query in formatting_queries:
        assert engine._is_code_related_query(query), f"Failed to detect text formatting query: {query}"
    
    # Test non-formatting queries
    non_formatting_queries = [
        "What is the capital of France?",
        "Tell me about quantum physics",
        "How do I make a cake?",
        "What's the weather like today?"
    ]
    
    for query in non_formatting_queries:
        assert not engine._is_code_related_query(query), f"Incorrectly detected as text formatting query: {query}"


@pytest.mark.asyncio
async def test_text_formatting_structured_output():
    """Test structured output processing for text formatting"""
    # Create a sample JSON response with text blocks
    json_response = json.dumps({
        "text": "This is a sample text with multiple paragraphs.\n\nThis is the second paragraph.",
        "code_blocks": [],
        "text_blocks": [
            {
                "content": "Text Formatting Example",
                "format_type": "heading"
            },
            {
                "content": "This is a sample text with proper paragraph structure.",
                "format_type": "paragraph"
            },
            {
                "content": "This is the second paragraph that should be separated from the first.",
                "format_type": "paragraph"
            },
            {
                "content": "This is a list item",
                "format_type": "list_item"
            },
            {
                "content": "This is another list item",
                "format_type": "list_item"
            }
        ],
        "preserve_paragraphs": True
    })
    
    # Create a mock response object
    mock_response = {"response": json_response}
    
    # Create an instance of GenerationMixin
    mixin = GenerationMixin()
    
    # Process the response
    processed_text = mixin._process_response_text(mock_response)
    
    # Verify that the heading is properly formatted
    assert "## Text Formatting Example" in processed_text
    
    # Verify that paragraphs are properly separated
    assert "This is a sample text with proper paragraph structure." in processed_text
    assert "This is the second paragraph that should be separated from the first." in processed_text
    
    # Verify that list items are properly formatted
    assert "- This is a list item" in processed_text
    assert "- This is another list item" in processed_text
    
    # Count the number of paragraphs (separated by double newlines)
    paragraphs = re.split(r'\n\n+', processed_text)
    assert len(paragraphs) >= 4, f"Expected at least 4 paragraphs, got {len(paragraphs)}"


@pytest.mark.asyncio
async def test_mixed_content_structured_output():
    """Test structured output processing for mixed content (text and code)"""
    # Create a sample JSON response with text blocks and code blocks
    json_response = json.dumps({
        "text": "This is a sample text with code blocks.\n\nHere's a Python example: {CODE_BLOCK_0}",
        "code_blocks": [
            {
                "language": "python",
                "code": "def hello():\n    print('Hello, world!')"
            }
        ],
        "text_blocks": [
            {
                "content": "Mixed Content Example",
                "format_type": "heading"
            },
            {
                "content": "This is a sample text with proper paragraph structure.",
                "format_type": "paragraph"
            },
            {
                "content": "Here's a Python example: {CODE_BLOCK_0}",
                "format_type": "paragraph"
            },
            {
                "content": "The function above prints a greeting message.",
                "format_type": "paragraph"
            }
        ],
        "preserve_paragraphs": True
    })
    
    # Create a mock response object
    mock_response = {"response": json_response}
    
    # Create an instance of GenerationMixin
    mixin = GenerationMixin()
    
    # Process the response
    processed_text = mixin._process_response_text(mock_response)
    
    # Verify that the heading is properly formatted
    assert "## Mixed Content Example" in processed_text
    
    # Verify that the code block was properly formatted
    assert "```python" in processed_text
    assert "def hello():" in processed_text
    assert "```" in processed_text
    
    # Verify that the placeholder was replaced
    assert "{CODE_BLOCK_0}" not in processed_text
    
    # Verify that paragraphs are properly separated
    assert "This is a sample text with proper paragraph structure." in processed_text
    assert "The function above prints a greeting message." in processed_text
    
    # Count the number of paragraphs (separated by double newlines)
    paragraphs = re.split(r'\n\n+', processed_text)
    assert len(paragraphs) >= 4, f"Expected at least 4 paragraphs, got {len(paragraphs)}"


@pytest.mark.asyncio
async def test_fallback_to_text_field():
    """Test fallback to text field when text_blocks is not provided"""
    # Create a sample JSON response without text blocks
    json_response = json.dumps({
        "text": "This is a sample text with multiple paragraphs.\n\nThis is the second paragraph.\n\nHere's a Python example: {CODE_BLOCK_0}",
        "code_blocks": [
            {
                "language": "python",
                "code": "def hello():\n    print('Hello, world!')"
            }
        ],
        "preserve_paragraphs": True
    })
    
    # Create a mock response object
    mock_response = {"response": json_response}
    
    # Create an instance of GenerationMixin
    mixin = GenerationMixin()
    
    # Process the response
    processed_text = mixin._process_response_text(mock_response)
    
    # Verify that the text content is present
    assert "This is a sample text with multiple paragraphs." in processed_text
    assert "This is the second paragraph." in processed_text
    
    # Verify that the code block was properly formatted
    assert "```python" in processed_text
    assert "def hello():" in processed_text
    assert "```" in processed_text
    
    # Verify that the placeholder was replaced
    assert "{CODE_BLOCK_0}" not in processed_text
    
    # Count the number of paragraphs (separated by double newlines)
    paragraphs = re.split(r'\n\n+', processed_text)
    assert len(paragraphs) >= 3, f"Expected at least 3 paragraphs, got {len(paragraphs)}"


if __name__ == "__main__":
    pytest.main(["-xvs", "test_text_formatting_structured_output.py"])