import logging
import os
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, Depends
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import (
    Document, DocumentInfo, DocumentProcessRequest,
    TagUpdateRequest, FolderUpdateRequest, DocumentFilterRequest
)
from app.models.user import User
from app.db.models import Document as DBDocument
from app.rag.document_processor import DocumentProcessor
from app.rag.vector_store import VectorStore
from app.utils.file_utils import validate_file, save_upload_file, delete_document_files
from app.core.config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from app.db.dependencies import get_db, get_document_repository
from app.db.repositories.document_repository import DocumentRepository
from app.core.security import get_current_active_user

# Create router
router = APIRouter()

# Logger
logger = logging.getLogger("app.api.documents")

# Document processor
document_processor = DocumentProcessor()

# Vector store
vector_store = VectorStore()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    tags: str = Form(""),
    folder: str = Form("/"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a document
    """
    try:
        # Validate file
        if not validate_file(file):
            raise HTTPException(status_code=400, detail=f"File type not allowed: {file.filename}")
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # Validate folder
        if not folder.startswith("/"):
            folder = "/" + folder
        
        # Create a simple document record with minimal information
        import uuid
        from datetime import datetime
        
        # Generate a document ID
        document_id = uuid.uuid4()
        
        # Save file to disk first
        file_path = await save_upload_file(file, str(document_id))
        
        # Create a simple document record in the database
        # We'll use raw SQL to avoid async/sync issues
        from sqlalchemy import text
        from app.db.session import AsyncSessionLocal
        
        db = AsyncSessionLocal()
        try:
            # Create document record
            query = text("""
                INSERT INTO documents (id, filename, folder, uploaded, processing_status, user_id)
                VALUES (:id, :filename, :folder, :uploaded, :status, :user_id)
            """)
            
            await db.execute(query, {
                "id": document_id,
                "filename": file.filename,
                "folder": folder,
                "uploaded": datetime.utcnow(),
                "status": "pending",
                "user_id": current_user.id
            })
            
            # Add tags if provided
            for tag_name in tag_list:
                # Check if tag exists
                tag_query = text("SELECT id FROM tags WHERE name = :name")
                tag_result = await db.execute(tag_query, {"name": tag_name})
                tag_row = tag_result.fetchone()
                
                if tag_row:
                    tag_id = tag_row[0]
                    # Update usage count
                    await db.execute(
                        text("UPDATE tags SET usage_count = usage_count + 1 WHERE id = :id"),
                        {"id": tag_id}
                    )
                else:
                    # Create new tag
                    tag_insert = text("""
                        INSERT INTO tags (name, created_at, usage_count)
                        VALUES (:name, :created_at, 1)
                        RETURNING id
                    """)
                    tag_result = await db.execute(
                        tag_insert,
                        {"name": tag_name, "created_at": datetime.utcnow()}
                    )
                    tag_id = tag_result.fetchone()[0]
                
                # Link tag to document
                await db.execute(
                    text("INSERT INTO document_tags (document_id, tag_id) VALUES (:doc_id, :tag_id)"),
                    {"doc_id": document_id, "tag_id": tag_id}
                )
            
            # Commit transaction
            await db.commit()
            
            return {
                "success": True,
                "message": f"Document {file.filename} uploaded successfully",
                "document_id": str(document_id)
            }
        except Exception as e:
            await db.rollback()
            raise e
        finally:
            await db.close()
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")
@router.get("/list", response_model=List[DocumentInfo])
async def list_documents(
    tags: Optional[List[str]] = Query(None),
    folder: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all documents with optional filtering and pagination
    """
    try:
        # Use raw SQL query with text function
        sql_query = """
        SELECT id, filename, content, doc_metadata, folder, uploaded, processing_status,
               processing_strategy, file_size, file_type, last_accessed
        FROM documents
        """
        
        # Add folder and user_id filters
        where_clauses = ["user_id = :user_id"]
        params = {"user_id": current_user.id}
        if folder:
            where_clauses.append("folder = :folder")
            params["folder"] = folder
        
        # Add WHERE clause if needed
        if where_clauses:
            sql_query += " WHERE " + " AND ".join(where_clauses)
        
        # Add pagination
        sql_query += " LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
        
        # Execute query
        result = await db.execute(text(sql_query), params)
        rows = result.fetchall()
        
        # Convert rows to DocumentInfo objects
        document_infos = []
        for row in rows:
            # Create DocumentInfo object
            doc_info = DocumentInfo(
                id=str(row.id),
                filename=row.filename,
                chunk_count=0,  # We don't have chunk information in this query
                metadata=row.doc_metadata or {},
                tags=[],  # We'll need to fetch tags separately if needed
                folder=row.folder,
                uploaded=row.uploaded
            )
            document_infos.append(doc_info)
        
        return document_infos
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.post("/filter", response_model=List[DocumentInfo])
async def filter_documents(
    filter_request: DocumentFilterRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Filter documents by tags, folder, and metadata with pagination
    """
    try:
        # Use raw SQL query with text function
        sql_query = """
        SELECT id, filename, content, doc_metadata, folder, uploaded, processing_status,
               processing_strategy, file_size, file_type, last_accessed
        FROM documents
        """
        
        # Add folder and user_id filters
        where_clauses = ["user_id = :user_id"]
        params = {"user_id": current_user.id}
        if filter_request.folder:
            where_clauses.append("folder = :folder")
            params["folder"] = filter_request.folder
        
        # Add search query filter if provided
        search_query = filter_request.query if hasattr(filter_request, 'query') else ""
        if search_query:
            where_clauses.append("(filename ILIKE :search_query OR content ILIKE :search_query)")
            params["search_query"] = f"%{search_query}%"
        
        # Add WHERE clause if needed
        if where_clauses:
            sql_query += " WHERE " + " AND ".join(where_clauses)
        
        # Add pagination
        sql_query += " LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
        
        # Execute query
        result = await db.execute(text(sql_query), params)
        rows = result.fetchall()
        
        # Convert rows to DocumentInfo objects
        document_infos = []
        for row in rows:
            # Create DocumentInfo object
            doc_info = DocumentInfo(
                id=str(row.id),
                filename=row.filename,
                chunk_count=0,  # We don't have chunk information in this query
                metadata=row.doc_metadata or {},
                tags=[],  # We'll need to fetch tags separately if needed
                folder=row.folder,
                uploaded=row.uploaded
            )
            document_infos.append(doc_info)
        
        # Convert documents to DocumentInfo
        document_infos = [
            DocumentInfo(
                id=str(doc.id),
                filename=doc.filename,
                chunk_count=len(doc.chunks) if hasattr(doc, 'chunks') else 0,
                metadata=doc.metadata or {},
                tags=[tag.name for tag in doc.tags] if hasattr(doc, 'tags') else [],
                folder=doc.folder,
                uploaded=doc.uploaded
            )
            for doc in documents
        ]
        
        return document_infos
    except Exception as e:
        logger.error(f"Error filtering documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error filtering documents: {str(e)}")

@router.get("/tags")
async def get_all_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all tags used by the current user
    """
    try:
        # Query tags used by the current user
        query = text("""
            SELECT DISTINCT t.name
            FROM tags t
            JOIN document_tags dt ON t.id = dt.tag_id
            JOIN documents d ON dt.document_id = d.id
            WHERE d.user_id = :user_id
            ORDER BY t.name
        """)
        result = await db.execute(query, {"user_id": current_user.id})
        tags = result.all()
        return {"tags": [tag[0] for tag in tags]}
    except Exception as e:
        logger.error(f"Error getting tags: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting tags: {str(e)}")

@router.get("/folders")
async def get_all_folders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all folders used by the current user
    """
    try:
        # Query folders used by the current user
        query = text("""
            SELECT DISTINCT d.folder
            FROM documents d
            WHERE d.user_id = :user_id
            ORDER BY d.folder
        """)
        result = await db.execute(query, {"user_id": current_user.id})
        folders = result.all()
        return {"folders": [folder[0] for folder in folders]}
    except Exception as e:
        logger.error(f"Error getting folders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting folders: {str(e)}")

@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    document_repository: DocumentRepository = Depends(get_document_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a document by ID
    """
    document = await document_repository.get_document_with_chunks(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    # Check if the document belongs to the current user
    if str(document.user_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")
    
    # Update last accessed timestamp
    await document_repository.update_document(
        document_id=document_id,
        metadata={"last_accessed": "now"}  # This will be converted to a timestamp in the repository
    )
    
    return document

@router.put("/{document_id}/tags")
async def update_document_tags(
    document_id: UUID,
    tag_request: TagUpdateRequest,
    db: AsyncSession = Depends(get_db),
    document_repository: DocumentRepository = Depends(get_document_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update document tags
    """
    document = await document_repository.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    # Check if the document belongs to the current user
    if str(document.user_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this document")
    
    try:
        # Update document tags in database
        updated_document = await document_repository.update_document_tags(document_id, tag_request.tags)
        
        # Update vector store metadata - convert tags list to string for ChromaDB
        await vector_store.update_document_metadata(
            str(document_id),
            {
                "tags": ",".join(tag_request.tags) if tag_request.tags else "",
                "tags_list": tag_request.tags  # Keep original list for internal use
            }
        )
        
        return {
            "success": True,
            "message": f"Tags updated for document {document_id}",
            "tags": tag_request.tags
        }
    except Exception as e:
        logger.error(f"Error updating document tags: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document tags: {str(e)}")

@router.put("/{document_id}/folder")
async def update_document_folder(
    document_id: UUID,
    folder_request: FolderUpdateRequest,
    db: AsyncSession = Depends(get_db),
    document_repository: DocumentRepository = Depends(get_document_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update document folder
    """
    document = await document_repository.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    # Check if the document belongs to the current user
    if str(document.user_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this document")
    
    try:
        # Validate folder
        folder = folder_request.folder
        if not folder.startswith("/"):
            folder = "/" + folder
        
        # Update document folder in database
        updated_document = await document_repository.update_document(
            document_id=document_id,
            folder=folder
        )
        
        # Update vector store metadata
        await vector_store.update_document_metadata(
            str(document_id),
            {"folder": folder}
        )
        
        return {
            "success": True,
            "message": f"Folder updated for document {document_id}",
            "folder": folder
        }
    except Exception as e:
        logger.error(f"Error updating document folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating document folder: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    document_repository: DocumentRepository = Depends(get_document_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a document
    """
    document = await document_repository.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    # Check if the document belongs to the current user
    if str(document.user_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    try:
        # Delete from vector store
        await vector_store.delete_document(str(document_id))
        
        # Delete document files
        delete_document_files(str(document_id))
        
        # Delete from database
        await document_repository.delete(document_id)
        
        return {"success": True, "message": f"Document {document_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

async def process_document_background(
    document_ids: List[UUID],
    force_reprocess: bool = False,
    chunking_strategy: str = "recursive",
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
):
    """
    Background task to process documents with configurable chunking strategy
    """
    # Create a new session for the background task
    from app.db.session import AsyncSessionLocal
    db = AsyncSessionLocal()
    
    try:
        # Create a document processor with the specified parameters
        processor = DocumentProcessor(
            chunk_size=chunk_size or CHUNK_SIZE,
            chunk_overlap=chunk_overlap or CHUNK_OVERLAP,
            chunking_strategy=chunking_strategy
        )
        
        for document_id in document_ids:
            try:
                # Get document using raw SQL
                from sqlalchemy import text
                query = text("""
                    SELECT id, filename, content, doc_metadata, folder, uploaded, processing_status
                    FROM documents WHERE id = :id
                """)
                result = await db.execute(query, {"id": document_id})
                doc_row = result.fetchone()
                
                if not doc_row:
                    logger.warning(f"Document {document_id} not found, skipping processing")
                    continue
                
                # Update processing status
                update_query = text("""
                    UPDATE documents
                    SET processing_status = :status, processing_strategy = :strategy
                    WHERE id = :id
                """)
                await db.execute(
                    update_query,
                    {
                        "id": document_id,
                        "status": "processing",
                        "strategy": chunking_strategy
                    }
                )
                await db.commit()
                
                # Create a document object for processing
                from app.models.document import Document
                document = Document(
                    id=str(doc_row.id),
                    filename=doc_row.filename,
                    content=doc_row.content or "",
                    metadata=doc_row.doc_metadata or {},
                    folder=doc_row.folder,
                    uploaded=doc_row.uploaded
                )
                
                # Process document with the configured processor
                processed_document = await processor.process_document(document)
                
                # Add to vector store
                await vector_store.add_document(processed_document)
                
                # Update processing status to completed
                await db.execute(
                    update_query,
                    {
                        "id": document_id,
                        "status": "completed",
                        "strategy": chunking_strategy
                    }
                )
                await db.commit()
                
                logger.info(f"Document {document_id} processed successfully with {chunking_strategy} chunking strategy")
            except Exception as e:
                # Update processing status to failed
                await db.execute(
                    update_query,
                    {
                        "id": document_id,
                        "status": "failed",
                        "strategy": chunking_strategy
                    }
                )
                await db.commit()
                logger.error(f"Error processing document {document_id}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in background processing task: {str(e)}")
    finally:
        await db.close()

@router.post("/process")
async def process_documents(
    request: DocumentProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Process documents with configurable chunking strategy
    """
    try:
        # Convert string IDs to UUID
        document_ids = [UUID(doc_id) for doc_id in request.document_ids]
        
        # Create a new session for validation
        from app.db.session import AsyncSessionLocal
        db = AsyncSessionLocal()
        
        try:
            # Validate document IDs using raw SQL
            for doc_id in document_ids:
                # Check if document exists and belongs to the current user
                from sqlalchemy import text
                query = text("SELECT id FROM documents WHERE id = :id AND user_id = :user_id")
                result = await db.execute(query, {"id": doc_id, "user_id": current_user.id})
                if not result.fetchone():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Document {doc_id} not found or not authorized to access"
                    )
            
            # Log chunking strategy
            logger.info(f"Processing documents with chunking strategy: {request.chunking_strategy}")
            
            # Add the background task
            background_tasks.add_task(
                process_document_background,
                document_ids,
                request.force_reprocess,
                request.chunking_strategy,
                request.chunk_size,
                request.chunk_overlap
            )
            
            return {
                "success": True,
                "message": f"Processing started for {len(request.document_ids)} documents"
            }
        finally:
            await db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")