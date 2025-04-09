"""
Unit tests for the DocumentRepository
"""
import pytest
import logging
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.document import DocumentRepository
from app.models.document import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_create_document(mock_async_db_session):
    """Test creating a document using the DocumentRepository"""
    # Create a document repository with the mock session
    document_repository = DocumentRepository(mock_async_db_session)
    
    # Create a document
    document_data = {
        "filename": "test_document.txt",
        "content": "This is a test document.",
        "metadata": {"source": "test"},
        "tags": ["test", "sample"],
        "folder": "/"
    }
    
    # Mock the create method to return a document
    mock_async_db_session.add.return_value = None
    mock_async_db_session.commit.return_value = None
    mock_async_db_session.refresh.return_value = None
    
    # Call the create method
    document = await document_repository.create_document(**document_data)
    
    # Assert that the document was created with the correct attributes
    assert document is not None
    assert document.filename == document_data["filename"]
    assert document.content == document_data["content"]
    assert document.metadata == document_data["metadata"]
    assert document.tags == document_data["tags"]
    assert document.folder == document_data["folder"]
    
    # Assert that the session methods were called
    mock_async_db_session.add.assert_called_once()
    mock_async_db_session.commit.assert_called_once()
    mock_async_db_session.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_document_by_id(mock_async_db_session, sample_document):
    """Test getting a document by ID"""
    # Create a document repository with the mock session
    document_repository = DocumentRepository(mock_async_db_session)
    
    # Mock the get method to return a document
    mock_async_db_session.get.return_value = sample_document
    
    # Call the get_by_id method
    document = await document_repository.get_document_by_id(sample_document.id)
    
    # Assert that the document was retrieved
    assert document is not None
    assert document.id == sample_document.id
    assert document.filename == sample_document.filename
    
    # Assert that the session method was called
    mock_async_db_session.get.assert_called_once()

@pytest.mark.asyncio
async def test_get_documents_by_user(mock_async_db_session, sample_document):
    """Test getting documents by user ID"""
    # Create a document repository with the mock session
    document_repository = DocumentRepository(mock_async_db_session)
    
    # Mock the execute method to return a result with documents
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_document]
    mock_async_db_session.execute.return_value = mock_result
    
    # Call the get_documents_by_user method
    documents = await document_repository.get_documents_by_user(sample_document.user_id)
    
    # Assert that the documents were retrieved
    assert documents is not None
    assert len(documents) == 1
    assert documents[0].id == sample_document.id
    
    # Assert that the session method was called
    mock_async_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_update_document(mock_async_db_session, sample_document):
    """Test updating a document"""
    # Create a document repository with the mock session
    document_repository = DocumentRepository(mock_async_db_session)
    
    # Mock the get method to return a document
    mock_async_db_session.get.return_value = sample_document
    
    # Call the update_document method
    updated_document = await document_repository.update_document(
        sample_document.id,
        title="Updated Title",
        tags=["updated", "test"]
    )
    
    # Assert that the document was updated
    assert updated_document is not None
    assert updated_document.title == "Updated Title"
    assert updated_document.tags == ["updated", "test"]
    
    # Assert that the session methods were called
    mock_async_db_session.get.assert_called_once()
    mock_async_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_document(mock_async_db_session, sample_document):
    """Test deleting a document"""
    # Create a document repository with the mock session
    document_repository = DocumentRepository(mock_async_db_session)
    
    # Mock the get method to return a document
    mock_async_db_session.get.return_value = sample_document
    
    # Call the delete_document method
    result = await document_repository.delete_document(sample_document.id)
    
    # Assert that the document was deleted
    assert result is True
    
    # Assert that the session methods were called
    mock_async_db_session.get.assert_called_once()
    mock_async_db_session.delete.assert_called_once()
    mock_async_db_session.commit.assert_called_once()