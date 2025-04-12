import logging
import os
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, Depends
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import (
    Document, DocumentInfo, DocumentProcessRequest,
    TagUpdateRequest, FolderUpdateRequest, DocumentFilterRequest
)
from app.db.models import Document as DBDocument
from app.rag.document_processor import DocumentProcessor
from app.rag.vector_store import VectorStore
from app.utils.file_utils import validate_file, save_upload_file, delete_document_files
from app.core.config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from app.db.dependencies import get_db
from app.db.repositories.basic_document_repository import BasicDocumentRepository
from sqlalchemy.ext.asyncio import AsyncSession

# Create a custom dependency for document repository that works in developer mode
async def get_dev_document_repository(db: AsyncSession = Depends(get_db)):
    """
    Get a document repository instance for developer mode
    This repository allows all operations without authentication
    """
    # Create a system user ID for developer mode
    from uuid import uuid4
    dev_user_id = uuid4()
    
    # Create repository with the developer user ID
    repo = BasicDocumentRepository(db, user_id=dev_user_id)
    
    return repo

# Create router
router = APIRouter()

# Logger
logger = logging.getLogger("app.api.basic_documents")

# Vector store
vector_store = VectorStore()

# Create document processor function with session
async def get_document_processor(db: AsyncSession = Depends(get_db)):
    """Get a document processor instance with the current database session"""
    return DocumentProcessor(session=db)

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tags: str = Form(""),
    folder: str = Form("/"),
    document_repository: BasicDocumentRepository = Depends(get_dev_document_repository),
    document_processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Upload a document without authentication (for developer mode)
    """
    try:
        # Validate file
        is_valid, error_message = await validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # Validate folder
        if not folder.startswith("/"):
            folder = "/" + folder
        
        # Create document with the correct field names
        document = await document_repository.create_document(
            filename=file.filename,
            content="",  # Add empty content to satisfy the model validation
            metadata={},  # We'll update this after saving the file
            tags=tag_list,
            folder=folder,
            is_public=True  # Make document public so it can be accessed without authentication
        )
        
        # Get the document ID from the database
        document_id = str(document.id)
        
        # Save file using the database document ID
        file_path = await save_upload_file(file, document_id)
        
        # Update document metadata with file path
        document.doc_metadata = {
            "file_path": file_path, 
            "content_type": file.content_type
        }
        await document_repository.session.commit()
        
        # Process document in background
        background_tasks.add_task(
            document_processor.process_document,
            document
        )
        
        return {"id": document_id, "filename": file.filename, "status": "uploaded"}
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.get("/list")
async def list_documents(
    document_repository: BasicDocumentRepository = Depends(get_dev_document_repository)
):
    """
    List all documents without authentication (for developer mode)
    """
    try:
        documents = await document_repository.get_all_documents()
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    document_repository: BasicDocumentRepository = Depends(get_dev_document_repository)
):
    """
    Get a document by ID without authentication (for developer mode)
    """
    try:
        document = await document_repository.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    document_repository: BasicDocumentRepository = Depends(get_dev_document_repository)
):
    """
    Delete a document by ID without authentication (for developer mode)
    """
    try:
        document = await document_repository.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Try to delete document from vector store first
        try:
            await vector_store.delete_document(str(document_id))
            logger.info(f"Document {document_id} deleted from vector store")
        except Exception as vs_error:
            logger.error(f"Error deleting document from vector store: {str(vs_error)}")
            # Continue with deletion even if vector store deletion fails
        
        # Delete document files
        try:
            if document.doc_metadata and "file_path" in document.doc_metadata:
                delete_document_files(document.doc_metadata["file_path"])
                logger.info(f"Document files deleted for {document_id}")
        except Exception as file_error:
            logger.error(f"Error deleting document files: {str(file_error)}")
            # Continue with deletion even if file deletion fails
        
        # Delete document from database
        success = await document_repository.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete document from database")
        
        logger.info(f"Document {document_id} successfully deleted")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.put("/{document_id}/tags")
async def update_document_tags(
    document_id: UUID,
    request: TagUpdateRequest,
    document_repository: BasicDocumentRepository = Depends(get_dev_document_repository)
):
    """
    Update document tags without authentication (for developer mode)
    """
    try:
        document = await document_repository.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update tags
        await document_repository.update_document_tags(document_id, request.tags)
        
        return {"status": "updated", "tags": request.tags}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document tags: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document tags: {str(e)}")

@router.put("/{document_id}/folder")
async def update_document_folder(
    document_id: UUID,
    request: FolderUpdateRequest,
    document_repository: BasicDocumentRepository = Depends(get_dev_document_repository)
):
    """
    Update document folder without authentication (for developer mode)
    """
    try:
        document = await document_repository.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Validate folder
        folder = request.folder
        if not folder.startswith("/"):
            folder = "/" + folder
        
        # Update folder
        await document_repository.update_document_folder(document_id, folder)
        
        return {"status": "updated", "folder": folder}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document folder: {str(e)}")

@router.post("/{document_id}/process")
async def process_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    document_repository: BasicDocumentRepository = Depends(get_dev_document_repository),
    document_processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Process a document by ID without authentication (for developer mode)
    This will chunk the document and add it to the vector store
    """
    try:
        document = await document_repository.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update processing status to "processing"
        document.processing_status = "processing"
        await document_repository.session.commit()
        
        # Process document in background
        background_tasks.add_task(
            document_processor.process_document,
            document
        )
        
        return {"status": "processing", "message": f"Document {document_id} is being processed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/stats", name="get_vector_store_statistics")
async def get_vector_store_statistics():
    """
    Get statistics about the vector store
    """
    try:
        # Get vector store statistics
        stats = await vector_store.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting vector store statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting vector store statistics: {str(e)}")