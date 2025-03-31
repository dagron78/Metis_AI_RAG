"""
Integration tests for the Semantic Chunker
"""
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
import tempfile
import shutil

from app.rag.document_processor import DocumentProcessor
from app.rag.chunkers.semantic_chunker import SemanticChunker
from app.models.document import Document
from app.core.config import UPLOAD_DIR

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client for testing"""
    client = AsyncMock()
    # Mock for chunking judge
    client.generate.return_value = {
        "response": """
        {
            "strategy": "semantic",
            "parameters": {
                "chunk_size": 1000,
                "chunk_overlap": 150
            },
            "justification": "This document contains complex concepts that would benefit from semantic chunking to preserve meaning and context."
        }
        """
    }
    return client

@pytest.fixture
def mock_semantic_chunker():
    """Create a mock SemanticChunker for testing"""
    chunker = MagicMock(spec=SemanticChunker)
    
    # Mock the split_documents method
    def mock_split_documents(docs):
        # Create 3 chunks from each document
        result = []
        for doc in docs:
            content = doc.page_content
            chunk_size = len(content) // 3
            for i in range(3):
                start = i * chunk_size
                end = start + chunk_size if i < 2 else len(content)
                chunk_content = content[start:end]
                result.append(doc.__class__(
                    page_content=chunk_content,
                    metadata=doc.metadata.copy()
                ))
        return result
    
    chunker.split_documents.side_effect = mock_split_documents
    return chunker

@pytest.fixture
def sample_document():
    """Create a sample document for testing"""
    return Document(
        id="test-doc-id",
        filename="test_semantic.txt",
        content="""
        This is a complex document with multiple semantic sections.
        
        Section 1: Introduction
        This section introduces the main concepts and provides context.
        
        Section 2: Main Content
        This section contains the core information and detailed explanations.
        
        Section 3: Conclusion
        This section summarizes the key points and provides next steps.
        """
    )

@pytest.fixture
def temp_upload_dir():
    """Create a temporary upload directory for testing"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Create the document directory structure
    doc_dir = os.path.join(temp_dir, "test-doc-id")
    os.makedirs(doc_dir, exist_ok=True)
    
    # Yield the temp directory
    yield temp_dir
    
    # Clean up
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_document_processor_with_semantic_chunking(mock_ollama_client, sample_document, temp_upload_dir):
    """Test that the DocumentProcessor correctly uses semantic chunking when recommended by the Chunking Judge"""
    # Create the document file
    doc_path = os.path.join(temp_upload_dir, sample_document.id, sample_document.filename)
    os.makedirs(os.path.dirname(doc_path), exist_ok=True)
    with open(doc_path, 'w') as f:
        f.write(sample_document.content)
    
    # Patch the UPLOAD_DIR config
    with patch('app.rag.document_processor.UPLOAD_DIR', temp_upload_dir):
        # Patch the USE_CHUNKING_JUDGE config to True
        with patch('app.rag.document_processor.USE_CHUNKING_JUDGE', True):
            # Patch the OllamaClient to use our mock
            with patch('app.rag.agents.chunking_judge.OllamaClient', return_value=mock_ollama_client):
                    # Create document processor
                    processor = DocumentProcessor()
                    
                    # Process the document
                    processed_doc = await processor.process_document(sample_document)
                    
                    # Verify the document was processed with semantic chunking
                    assert processed_doc.metadata["chunking_analysis"]["strategy"] == "semantic"
                    assert len(processed_doc.chunks) > 0
                    
                    # Verify the chunking parameters
                    assert processor.chunk_size == 1000
                    assert processor.chunk_overlap == 150

@pytest.mark.asyncio
async def test_semantic_chunker_with_document_processor(mock_ollama_client, mock_semantic_chunker, sample_document, temp_upload_dir):
    """Test that the SemanticChunker integrates correctly with DocumentProcessor"""
    # Create the document file
    doc_path = os.path.join(temp_upload_dir, sample_document.id, sample_document.filename)
    os.makedirs(os.path.dirname(doc_path), exist_ok=True)
    with open(doc_path, 'w') as f:
        f.write(sample_document.content)
    
    # Patch the UPLOAD_DIR config
    with patch('app.rag.document_processor.UPLOAD_DIR', temp_upload_dir):
        # Patch the USE_CHUNKING_JUDGE config to False to use direct strategy
        with patch('app.rag.document_processor.USE_CHUNKING_JUDGE', False):
                # Create document processor with semantic chunking strategy
                processor = DocumentProcessor(chunking_strategy="semantic")
                
                # Process the document
                processed_doc = await processor.process_document(sample_document)
                
                # Verify the document was processed
                assert len(processed_doc.chunks) > 0
                
                # Verify the chunking strategy
                assert processor.chunking_strategy == "semantic"