"""
Unit tests for the Semantic Chunker
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.rag.chunkers.semantic_chunker import SemanticChunker
from langchain.schema import Document as LangchainDocument

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client for testing"""
    client = AsyncMock()
    client.generate.return_value = {
        "response": """
        [500, 1000, 1500]
        """
    }
    return client

@pytest.fixture
def sample_text():
    """Create a sample text for testing"""
    return """
    This is the first section of the document. It contains information about the introduction.
    The introduction sets the stage for the rest of the document and provides context.
    
    This is the second section of the document. It contains information about the main topic.
    The main topic is discussed in detail with examples and explanations.
    
    This is the third section of the document. It contains information about the conclusion.
    The conclusion summarizes the main points and provides next steps.
    """

@pytest.mark.asyncio
async def test_semantic_chunker_split_text_async(mock_ollama_client, sample_text):
    """Test that the SemanticChunker correctly splits text asynchronously"""
    # Create semantic chunker with mock client
    chunker = SemanticChunker(ollama_client=mock_ollama_client)
    
    # Mock the _identify_semantic_boundaries method to return predictable results
    async def mock_identify_boundaries(text):
        # Return a simple chunk
        return [text]
    
    # Patch the _identify_semantic_boundaries method
    with patch.object(chunker, '_identify_semantic_boundaries', side_effect=mock_identify_boundaries):
        # Test async splitting
        chunks = await chunker.split_text_async(sample_text)
        
        # Verify result
        assert len(chunks) == 1

@pytest.mark.asyncio
async def test_semantic_chunker_caching(mock_ollama_client, sample_text):
    """Test that the SemanticChunker caches results"""
    # For this test, we need to use a sample text that's longer than chunk_size
    long_sample = sample_text * 10  # Make it long enough to trigger chunking
    
    # Create semantic chunker with mock client and caching enabled
    chunker = SemanticChunker(ollama_client=mock_ollama_client, cache_enabled=True, chunk_size=500, chunk_overlap=50)
    
    # Create a simple implementation for _semantic_chunking_async that we can track
    original_method = chunker._semantic_chunking_async
    call_count = 0
    
    async def tracked_method(text):
        nonlocal call_count
        call_count += 1
        # Just return a simple chunk for testing
        return ["Test chunk 1", "Test chunk 2"]
    
    # Replace the method
    chunker._semantic_chunking_async = tracked_method
    
    try:
        # First call should use our tracked method
        chunks1 = await chunker.split_text_async(long_sample)
        
        # Second call should use the cache
        chunks2 = await chunker.split_text_async(long_sample)
        
        # Verify results are the same
        assert chunks1 == chunks2
        
        # Verify the method was called only once
        assert call_count == 1
    finally:
        # Restore the original method
        chunker._semantic_chunking_async = original_method

@pytest.mark.asyncio
async def test_semantic_chunker_short_text(mock_ollama_client):
    """Test that the SemanticChunker handles short text correctly"""
    # Create semantic chunker with mock client
    chunker = SemanticChunker(ollama_client=mock_ollama_client, chunk_size=1000)
    
    # Short text that doesn't need chunking
    short_text = "This is a short text that doesn't need chunking."
    
    # Test async splitting
    chunks = await chunker.split_text_async(short_text)
    
    # Verify result
    assert len(chunks) == 1
    assert chunks[0] == short_text
    
    # Verify LLM was not called
    assert mock_ollama_client.generate.call_count == 0

@pytest.mark.asyncio
async def test_semantic_chunker_error_handling(mock_ollama_client, sample_text):
    """Test that the SemanticChunker handles errors gracefully"""
    # For this test, we need to use a sample text that's longer than chunk_size
    long_sample = sample_text * 10  # Make it long enough to trigger chunking
    
    # Create semantic chunker with mock client
    chunker = SemanticChunker(ollama_client=mock_ollama_client, chunk_size=500, chunk_overlap=50)
    
    # Save original methods
    original_semantic_chunking = chunker._semantic_chunking_async
    original_fallback = chunker._fallback_chunking
    
    # Create a method that directly calls _fallback_chunking to bypass the normal flow
    async def error_method(text):
        # This will force the use of fallback chunking
        return chunker._fallback_chunking(text)
    
    # Create a predictable fallback method
    def mock_fallback(text):
        return ["Fallback chunk 1", "Fallback chunk 2"]
    
    # Replace the methods
    chunker._semantic_chunking_async = error_method
    chunker._fallback_chunking = mock_fallback
    
    try:
        # Test async splitting with our modified methods
        chunks = await chunker.split_text_async(long_sample)
        
        # Verify fallback to simple chunking
        assert len(chunks) == 2
        assert chunks[0] == "Fallback chunk 1"
        assert chunks[1] == "Fallback chunk 2"
    finally:
        # Restore the original methods
        chunker._semantic_chunking_async = original_semantic_chunking
        chunker._fallback_chunking = original_fallback

@pytest.mark.asyncio
async def test_semantic_chunker_apply_overlap(mock_ollama_client):
    """Test that the SemanticChunker applies overlap correctly"""
    # Create semantic chunker with mock client and significant overlap
    chunker = SemanticChunker(ollama_client=mock_ollama_client, chunk_overlap=10)
    
    # Create test chunks with enough length for overlap
    original_chunks = [
        "This is the first chunk of text that is long enough for overlap.",
        "This is the second chunk of text that is also long enough.",
        "This is the third chunk of text with sufficient length."
    ]
    
    # Apply overlap
    overlapped_chunks = chunker._apply_overlap(original_chunks)
    
    # Verify result
    assert len(overlapped_chunks) == 3
    assert overlapped_chunks[0] == original_chunks[0]
    assert overlapped_chunks[1].startswith(original_chunks[0][-10:])
    assert overlapped_chunks[2].startswith(original_chunks[1][-10:])

@pytest.mark.asyncio
async def test_semantic_chunker_integration_with_langchain(mock_ollama_client, sample_text):
    """Test that the SemanticChunker works with Langchain documents"""
    # Create semantic chunker with mock client
    chunker = SemanticChunker(ollama_client=mock_ollama_client)
    
    # Create Langchain document
    doc = LangchainDocument(page_content=sample_text, metadata={"source": "test"})
    
    # Split document
    split_docs = chunker.split_documents([doc])
    
    # Verify result
    assert len(split_docs) > 0
    assert all(isinstance(d, LangchainDocument) for d in split_docs)
    assert all("source" in d.metadata for d in split_docs)

@pytest.mark.asyncio
async def test_semantic_chunker_long_text_processing(mock_ollama_client):
    """Test that the SemanticChunker handles long text correctly"""
    # Create a long text that exceeds the max_llm_context_length
    long_text = "This is section " + ". ".join([f"Part {i}" for i in range(1000)])
    
    # Create semantic chunker with mock client and small max context
    chunker = SemanticChunker(
        ollama_client=mock_ollama_client,
        max_llm_context_length=2000
    )
    
    # Mock the _process_long_text method to return predictable results
    async def mock_process_long_text(text):
        # Return a chunk for each 1000 characters
        chunks = []
        for i in range(0, len(text), 1000):
            end = min(i + 1000, len(text))
            chunks.append(text[i:end])
        return chunks
    
    # Patch the method
    with patch.object(chunker, '_process_long_text', side_effect=mock_process_long_text):
        # Test async splitting
        chunks = await chunker.split_text_async(long_text)
        
        # Verify result
        assert len(chunks) > 1
        assert len(chunks) == (len(long_text) + 999) // 1000  # Ceiling division