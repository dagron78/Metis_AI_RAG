"""
Fixtures for RAG and database integration tests
"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock
import uuid
from datetime import datetime

from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.engine.rag_engine import RAGEngine
from app.db.repositories.document_repository import DocumentRepository
from app.models.document import Document
from app.db.models import Chunk as DocumentChunk  # Using Chunk from db.models as DocumentChunk for compatibility

@pytest.fixture
def test_vector_store():
    """Create a test vector store with a temporary directory"""
    # Create a temporary directory for the vector store
    temp_dir = tempfile.mkdtemp()
    
    # Create the vector store
    vector_store = VectorStore(
        persist_directory=temp_dir,
        embedding_model="nomic-embed-text",
        enable_cache=False
    )
    
    yield vector_store
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client"""
    mock = AsyncMock(spec=OllamaClient)
    
    # Mock generate method
    mock.generate.return_value = {"response": "This is a test response"}
    
    # Mock create_embedding method
    mock.create_embedding.return_value = [0.1] * 384  # 384-dimensional embedding
    
    return mock

@pytest.fixture
def test_rag_engine(test_vector_store, mock_ollama_client):
    """Create a test RAG engine"""
    engine = RAGEngine(
        vector_store=test_vector_store,
        ollama_client=mock_ollama_client
    )
    
    return engine

@pytest.fixture
def sample_document():
    """Create a sample document for testing"""
    return Document(
        id=str(uuid.uuid4()),
        title="Test Document",
        filename="test.pdf",
        content="This is a test document content.",
        mime_type="application/pdf",
        size=1024,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id=str(uuid.uuid4()),
        is_public=True,
        status="processed",
        folder="test_folder",
        tags=["test", "document"],
        chunks=[
            DocumentChunk(
                id=str(uuid.uuid4()),
                content="This is chunk 1",
                metadata={"index": 0},
                embedding=[0.1, 0.2, 0.3]
            ),
            DocumentChunk(
                id=str(uuid.uuid4()),
                content="This is chunk 2",
                metadata={"index": 1},
                embedding=[0.4, 0.5, 0.6]
            )
        ]
    )

@pytest.fixture
def mock_document_repository():
    """Mock document repository"""
    mock = MagicMock(spec=DocumentRepository)
    
    # Mock get_by_id method
    mock.get_by_id.return_value = Document(
        id="doc1",
        title="Test Document",
        filename="test.pdf",
        content="This is a test document content.",
        mime_type="application/pdf",
        size=1024,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id="user1",
        is_public=True,
        status="processed",
        folder="test_folder",
        tags=["test", "document"],
        chunks=[
            DocumentChunk(
                id="chunk1",
                content="This is chunk 1",
                metadata={"index": 0},
                embedding=[0.1, 0.2, 0.3]
            ),
            DocumentChunk(
                id="chunk2",
                content="This is chunk 2",
                metadata={"index": 1},
                embedding=[0.4, 0.5, 0.6]
            )
        ]
    )
    
    # Mock get_all method
    mock.get_all.return_value = [
        Document(
            id="doc1",
            title="Test Document 1",
            filename="test1.pdf",
            content="This is test document 1 content.",
            mime_type="application/pdf",
            size=1024,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id="user1",
            is_public=True,
            status="processed",
            folder="test_folder",
            tags=["test", "document"],
            chunks=[]
        ),
        Document(
            id="doc2",
            title="Test Document 2",
            filename="test2.pdf",
            content="This is test document 2 content.",
            mime_type="application/pdf",
            size=2048,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id="user1",
            is_public=False,
            status="processed",
            folder="test_folder",
            tags=["test", "document"],
            chunks=[]
        )
    ]
    
    return mock