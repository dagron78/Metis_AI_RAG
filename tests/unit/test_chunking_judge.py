"""
Unit tests for the Chunking Judge
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.rag.agents.chunking_judge import ChunkingJudge
from app.models.document import Document

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client for testing"""
    client = AsyncMock()
    client.generate.return_value = {
        "response": """
        {
            "strategy": "markdown",
            "parameters": {
                "chunk_size": 800,
                "chunk_overlap": 100
            },
            "justification": "This is a structured markdown document with clear headers."
        }
        """
    }
    return client

@pytest.fixture
def markdown_document():
    """Create a test markdown document"""
    return Document(
        id="test-id",
        filename="test.md",
        content="""# Header 1
This is content under header 1.

## Header 2
This is content under header 2.

### Header 3
This is content under header 3.
"""
    )

@pytest.fixture
def text_document():
    """Create a test text document"""
    return Document(
        id="test-id-2",
        filename="test.txt",
        content="""This is a plain text document.
It has multiple paragraphs but no clear structure.

This is the second paragraph.
It continues for a few lines.
"""
    )

@pytest.mark.asyncio
async def test_chunking_judge_markdown_analysis(mock_ollama_client, markdown_document):
    """Test that the Chunking Judge correctly analyzes a markdown document"""
    # Create chunking judge with mock client
    judge = ChunkingJudge(ollama_client=mock_ollama_client)
    
    # Test analysis
    result = await judge.analyze_document(markdown_document)
    
    # Verify result
    assert result["strategy"] == "markdown"
    assert result["parameters"]["chunk_size"] == 800
    assert result["parameters"]["chunk_overlap"] == 100
    assert "justification" in result
    
    # Verify prompt creation
    call_args = mock_ollama_client.generate.call_args[1]
    assert "document analysis expert" in call_args["prompt"].lower()
    assert "test.md" in call_args["prompt"]
    assert "Header 1" in call_args["prompt"]
    assert "Header 2" in call_args["prompt"]

@pytest.mark.asyncio
async def test_chunking_judge_text_analysis(mock_ollama_client, text_document):
    """Test that the Chunking Judge correctly analyzes a text document"""
    # Override the mock response for text document
    mock_ollama_client.generate.return_value = {
        "response": """
        {
            "strategy": "recursive",
            "parameters": {
                "chunk_size": 1000,
                "chunk_overlap": 150
            },
            "justification": "This is a plain text document with paragraphs."
        }
        """
    }
    
    # Create chunking judge with mock client
    judge = ChunkingJudge(ollama_client=mock_ollama_client)
    
    # Test analysis
    result = await judge.analyze_document(text_document)
    
    # Verify result
    assert result["strategy"] == "recursive"
    assert result["parameters"]["chunk_size"] == 1000
    assert result["parameters"]["chunk_overlap"] == 150
    assert "justification" in result
    
    # Verify prompt creation
    call_args = mock_ollama_client.generate.call_args[1]
    assert "document analysis expert" in call_args["prompt"].lower()
    assert "test.txt" in call_args["prompt"]
    assert "plain text document" in call_args["prompt"]

@pytest.mark.asyncio
async def test_chunking_judge_error_handling(mock_ollama_client, markdown_document):
    """Test that the Chunking Judge handles errors gracefully"""
    # Make the mock client return an invalid JSON response
    mock_ollama_client.generate.return_value = {
        "response": "This is not valid JSON"
    }
    
    # Create chunking judge with mock client
    judge = ChunkingJudge(ollama_client=mock_ollama_client)
    
    # Test analysis
    result = await judge.analyze_document(markdown_document)
    
    # Verify fallback to default values
    assert result["strategy"] == "recursive"
    assert result["parameters"]["chunk_size"] == 500
    assert result["parameters"]["chunk_overlap"] == 50
    assert "Failed to parse" in result["justification"]

@pytest.mark.asyncio
async def test_chunking_judge_invalid_strategy(mock_ollama_client, markdown_document):
    """Test that the Chunking Judge handles invalid strategies gracefully"""
    # Make the mock client return an invalid strategy
    mock_ollama_client.generate.return_value = {
        "response": """
        {
            "strategy": "invalid_strategy",
            "parameters": {
                "chunk_size": 800,
                "chunk_overlap": 100
            },
            "justification": "This is an invalid strategy."
        }
        """
    }
    
    # Create chunking judge with mock client
    judge = ChunkingJudge(ollama_client=mock_ollama_client)
    
    # Test analysis
    result = await judge.analyze_document(markdown_document)
    
    # Verify fallback to recursive strategy
    assert result["strategy"] == "recursive"
    assert result["parameters"]["chunk_size"] == 800
    assert result["parameters"]["chunk_overlap"] == 100

@pytest.mark.asyncio
async def test_extract_representative_sample_markdown():
    """Test the _extract_representative_sample method with markdown content"""
    judge = ChunkingJudge(ollama_client=AsyncMock())
    
    # Create a long markdown document
    long_content = "# Header 1\n\n" + "Content under header 1.\n" * 100
    long_content += "\n## Header 2\n\n" + "Content under header 2.\n" * 100
    long_content += "\n### Header 3\n\n" + "Content under header 3.\n" * 100
    
    # Extract sample
    sample = judge._extract_representative_sample(long_content, "test.md", max_length=1000)
    
    # Verify sample contains headers and some content
    assert "# Header 1" in sample
    assert "## Header 2" in sample
    assert "### Header 3" in sample
    assert "Content under header" in sample
    assert len(sample) <= 1000 + 100  # Allow for some buffer

@pytest.mark.asyncio
async def test_extract_representative_sample_text():
    """Test the _extract_representative_sample method with text content"""
    judge = ChunkingJudge(ollama_client=AsyncMock())
    
    # Create a long text document
    long_content = "This is the beginning of the document.\n" * 50
    long_content += "This is the middle of the document.\n" * 50
    long_content += "This is the end of the document.\n" * 50
    
    # Extract sample
    sample = judge._extract_representative_sample(long_content, "test.txt", max_length=1000)
    
    # Verify sample contains beginning, middle, and end
    assert "beginning of the document" in sample
    assert "middle of the document" in sample
    assert "end of the document" in sample
    assert len(sample) <= 1000 + 100  # Allow for some buffer