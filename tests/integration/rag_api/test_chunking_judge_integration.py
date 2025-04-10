"""
Integration tests for the Chunking Judge with DocumentProcessor
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
import tempfile
import shutil

from app.rag.document_processor import DocumentProcessor
from app.rag.agents.chunking_judge import ChunkingJudge
from app.models.document import Document
from app.core.config import UPLOAD_DIR

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
def test_document():
    """Create a test document for processing"""
    return Document(
        id="test-integration-id",
        filename="test_integration.md",
        content="""# Test Document

This is a test document for integration testing.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""
    )

@pytest.fixture
def setup_document_directory(test_document):
    """Set up a temporary directory for the test document"""
    # Create document directory
    doc_dir = os.path.join(UPLOAD_DIR, test_document.id)
    os.makedirs(doc_dir, exist_ok=True)
    
    # Write document content to file
    doc_path = os.path.join(doc_dir, test_document.filename)
    with open(doc_path, 'w') as f:
        f.write(test_document.content)
    
    yield
    
    # Clean up
    if os.path.exists(doc_dir):
        shutil.rmtree(doc_dir)

@pytest.mark.asyncio
@patch('app.core.config.USE_CHUNKING_JUDGE', True)
async def test_document_processor_with_chunking_judge(mock_ollama_client, test_document, setup_document_directory):
    """Test that the DocumentProcessor correctly uses the Chunking Judge"""
    # Patch the ChunkingJudge to use our mock
    with patch('app.rag.agents.chunking_judge.ChunkingJudge', return_value=ChunkingJudge(ollama_client=mock_ollama_client)):
        # Create document processor
        processor = DocumentProcessor()
        
        # Process document
        processed_doc = await processor.process_document(test_document)
        
        # Verify chunking analysis was added to metadata
        assert "chunking_analysis" in processed_doc.metadata
        assert processed_doc.metadata["chunking_analysis"]["strategy"] == "markdown"
        assert processed_doc.metadata["chunking_analysis"]["parameters"]["chunk_size"] == 800
        assert processed_doc.metadata["chunking_analysis"]["parameters"]["chunk_overlap"] == 100
        
        # Verify chunks were created
        assert len(processed_doc.chunks) > 0

@pytest.mark.asyncio
@patch('app.core.config.USE_CHUNKING_JUDGE', False)
async def test_document_processor_without_chunking_judge(test_document, setup_document_directory):
    """Test that the DocumentProcessor works correctly when Chunking Judge is disabled"""
    # Create document processor
    processor = DocumentProcessor()
    
    # Process document
    processed_doc = await processor.process_document(test_document)
    
    # Verify chunking analysis was not added to metadata
    assert "chunking_analysis" not in processed_doc.metadata
    
    # Verify chunks were created
    assert len(processed_doc.chunks) > 0