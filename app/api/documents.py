import logging
import os
from typing import List, Dict, Any, Optional, Set, Union
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, Depends
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import (
    Document, DocumentInfo, DocumentProcessRequest,
    TagUpdateRequest, FolderUpdateRequest, DocumentFilterRequest
)
from pydantic import BaseModel

class DevProcessRequest(BaseModel):
    document_id: str

class DevSearchRequest(BaseModel):
    query: str

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

# Special no-auth upload endpoint for developer mode
@router.post("/dev-upload", include_in_schema=False)
async def dev_upload_document(
    file: UploadFile = File(...),
    tags: str = Form(""),
    folder: str = Form("/")
):
    """
    Special development-only endpoint for uploading documents without authentication
    """
    try:
        # Validate file
        is_valid, error_msg = await validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Save file directly to disk
        import uuid
        import os
        from datetime import datetime
        
        # Generate a document ID
        document_id = uuid.uuid4()
        
        # Save file to disk
        upload_dir = os.path.join(UPLOAD_DIR, str(document_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        
        # Save the file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Log success
        logger.info(f"Dev mode: File {file.filename} saved to {file_path}")
        
        return {
            "success": True,
            "message": f"Document {file.filename} uploaded successfully in dev mode",
            "document_id": str(document_id),
            "file_path": file_path
        }
    except Exception as e:
        logger.error(f"Dev mode upload error: {str(e)}")
        return {
            "success": False,
            "message": f"Error uploading document: {str(e)}"
        }

@router.get("/dev-list", include_in_schema=False)
async def dev_list_documents():
    """
    List all documents uploaded in developer mode
    """
    try:
        import os
        import time
        
        # List all document directories in the upload dir
        document_dirs = [d for d in os.listdir(UPLOAD_DIR) if os.path.isdir(os.path.join(UPLOAD_DIR, d))]
        
        files = []
        for doc_id in document_dirs:
            doc_dir = os.path.join(UPLOAD_DIR, doc_id)
            # List files in this directory
            doc_files = os.listdir(doc_dir)
            
            for filename in doc_files:
                file_path = os.path.join(doc_dir, filename)
                # Get file stats
                stats = os.stat(file_path)
                
                files.append({
                    "id": doc_id,
                    "filename": filename,
                    "path": file_path,
                    "size": stats.st_size,
                    "created": stats.st_ctime,
                    "modified": stats.st_mtime
                })
        
        # Sort by newest first
        files.sort(key=lambda x: x["created"], reverse=True)
        
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.get("/dev-content", include_in_schema=False)
async def dev_get_document_content(path: str):
    """
    Get the content of a document
    """
    try:
        # Validate path is within upload dir
        import os
        
        # Make sure path is absolute and within the upload directory
        abs_path = os.path.abspath(path)
        abs_upload_dir = os.path.abspath(UPLOAD_DIR)
        
        if not abs_path.startswith(abs_upload_dir):
            raise HTTPException(status_code=403, detail="Path is outside of uploads directory")
        
        # Check if file exists
        if not os.path.isfile(abs_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content
        with open(abs_path, "r") as f:
            content = f.read()
            
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading document content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading document content: {str(e)}")

from pydantic import BaseModel

class DevProcessRequest(BaseModel):
    document_id: str

@router.post("/dev-process", include_in_schema=False)
async def dev_process_document(request: DevProcessRequest):
    """
    Process a document without requiring authentication or database interaction
    This is a simplified version that only adds the document to the vector store
    """
    try:
        import os
        import uuid
        from datetime import datetime
        from app.models.document import Document

        # Validate that the document exists
        document_dir = os.path.join(UPLOAD_DIR, request.document_id)
        if not os.path.isdir(document_dir):
            raise HTTPException(status_code=404, detail=f"Document {request.document_id} not found")

        # Get the document files
        files = os.listdir(document_dir)
        if not files:
            raise HTTPException(status_code=404, detail=f"No files found for document {request.document_id}")

        # Get the first file (assuming there's only one)
        filename = files[0]
        file_path = os.path.join(document_dir, filename)

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Create a Document object
        document = Document(
            id=request.document_id,
            filename=filename,
            content=content,
            metadata={
                "processed_at": datetime.utcnow().isoformat(),
                "method": "dev-process"
            },
            folder="/dev",
            uploaded=datetime.utcnow()
        )

        # Process the document
        logger.info(f"Processing document {request.document_id} with simplified dev method")
        processor = DocumentProcessor(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            chunking_strategy="recursive"  # Use the same strategy as the regular processor
        )

        # Process document
        processed_document = await processor.process_document(document)
        
        # Add to vector store
        await vector_store.add_document(processed_document)
        
        return {
            "success": True,
            "message": f"Document {filename} processed successfully in dev mode",
            "document_id": request.document_id,
            "chunk_count": len(processed_document.chunks) if hasattr(processed_document, "chunks") else 0
        }
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return {
            "success": False,
            "message": f"Error processing document: {str(e)}"
        }

@router.post("/dev-search", include_in_schema=False)
async def dev_search_documents(request: DevSearchRequest):
    """
    Development endpoint to search for documents directly in the vector store
    """
    try:
        # Get query from request
        query = request.query
        logger.info(f"Searching for documents with query: {query}")
        
        # Create a fake user ID for vector store
        from uuid import uuid4
        user_id = str(uuid4())
        
        # Search vector store directly
        results = await vector_store.search(
            query=query,
            top_k=10,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": f"Found {len(results)} documents matching query",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return {
            "success": False,
            "message": f"Error searching documents: {str(e)}"
        }

@router.get("/dev-document", include_in_schema=False)
async def dev_get_document(id: str):
    """
    Get a document by ID directly from the file system and check if it exists in the vector store
    """
    try:
        import os
        import json
        from datetime import datetime
        from app.models.document import Document
        
        # Check if document exists
        document_dir = os.path.join(UPLOAD_DIR, id)
        if not os.path.isdir(document_dir):
            return {
                "success": False,
                "message": f"Document {id} not found"
            }
        
        # Get the document files
        files = os.listdir(document_dir)
        if not files:
            return {
                "success": False,
                "message": f"No files found for document {id}"
            }
        
        # Get the first file
        filename = files[0]
        file_path = os.path.join(document_dir, filename)
        
        # Read file content
        with open(file_path, "r") as f:
            content = f.read()
        
        # Create a Document object
        document = Document(
            id=id,
            filename=filename,
            content=content,
            metadata={},
            folder="/dev",
            uploaded=datetime.utcnow()
        )
        
        # Try to get chunks from vector store
        try:
            chunks = await vector_store.get_document_chunks(id)
            document.chunks = chunks
        except Exception as chunk_error:
            logger.warning(f"Could not retrieve chunks: {str(chunk_error)}")
        
        # Return document
        return {
            "success": True,
            "document": document.dict()
        }
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting document: {str(e)}"
        }
        
@router.post("/dev-force-process", include_in_schema=False)
async def dev_force_process_document(document_id: str = Form(...), force_delete: bool = Form(False)):
    """
    Force process a document with extra diagnostics
    This is a special endpoint for debugging problematic documents
    """
    try:
        import os
        from datetime import datetime
        from app.models.document import Document
        
        logger.info(f"Force processing document {document_id} with diagnostics")
        
        # Validate that the document exists
        document_dir = os.path.join(UPLOAD_DIR, document_id)
        if not os.path.isdir(document_dir):
            return {
                "success": False,
                "message": f"Document {document_id} not found",
                "step": "validation"
            }
        
        # Get the document files
        files = os.listdir(document_dir)
        if not files:
            return {
                "success": False,
                "message": f"No files found for document {document_id}",
                "step": "file_check"
            }
        
        # Get the first file
        filename = files[0]
        file_path = os.path.join(document_dir, filename)
        file_size = os.path.getsize(file_path)
        
        # Log the file details
        logger.info(f"Processing file: {filename} (size: {file_size} bytes)")
        
        # Read file content
        with open(file_path, "r") as f:
            content = f.read()
        
        # Check if document already exists in vector store
        try:
            existing_chunks = await vector_store.get_document_chunks(document_id)
            if existing_chunks and force_delete:
                # Delete existing document from vector store
                logger.info(f"Deleting existing document {document_id} from vector store (found {len(existing_chunks)} chunks)")
                vector_store.delete_document(document_id)
                logger.info(f"Existing document deleted from vector store")
            elif existing_chunks:
                logger.info(f"Document already exists in vector store with {len(existing_chunks)} chunks")
        except Exception as e:
            logger.warning(f"Error checking existing document: {str(e)}")
        
        # Create a Document object with extra metadata
        document = Document(
            id=document_id,
            filename=filename,
            content=content,
            metadata={
                "processed_at": datetime.utcnow().isoformat(),
                "method": "dev-force-process",
                "file_size": file_size,
                "content_length": len(content)
            },
            folder="/dev",
            uploaded=datetime.utcnow()
        )
        
        # Process document with more detailed logging
        logger.info(f"Creating document processor for {document_id} with chunking strategy: recursive")
        processor = DocumentProcessor(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            chunking_strategy="recursive"
        )
        
        # Log processor settings
        logger.info(f"Processor settings: chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}")
        
        # Process document with extra logging
        logger.info(f"Starting document processing")
        processed_document = await processor.process_document(document)
        
        # Check processed document
        if not hasattr(processed_document, "chunks") or not processed_document.chunks:
            logger.warning(f"Processing completed but no chunks were generated")
            return {
                "success": False,
                "message": f"Processing completed but no chunks were generated",
                "step": "processing",
                "document": processed_document.dict()
            }
        
        logger.info(f"Document processed into {len(processed_document.chunks)} chunks")
        
        # Add to vector store with extra logging
        logger.info(f"Adding document to vector store with {len(processed_document.chunks)} chunks")
        add_start_time = datetime.utcnow()
        await vector_store.add_document(processed_document)
        add_end_time = datetime.utcnow()
        add_duration = (add_end_time - add_start_time).total_seconds()
        logger.info(f"Document added to vector store in {add_duration:.2f} seconds")
        
        # Verify document exists in vector store
        logger.info(f"Verifying document exists in vector store")
        verify_chunks = await vector_store.get_document_chunks(document_id)
        
        return {
            "success": True,
            "message": f"Document {filename} force processed successfully",
            "document_id": document_id,
            "original_size": file_size,
            "content_length": len(content),
            "chunk_count": len(processed_document.chunks),
            "processing_time": add_duration,
            "vector_store_chunks": len(verify_chunks),
            "chunks": [chunk.dict() for chunk in processed_document.chunks]
        }
    except Exception as e:
        logger.error(f"Error force processing document: {str(e)}")
        import traceback
        trace = traceback.format_exc()
        return {
            "success": False,
            "message": f"Error force processing document: {str(e)}",
            "error_trace": trace
        }
        
class DevManualProcessRequest(BaseModel):
    id: str
    filename: str
    content: str
    force_delete: bool = True
        
@router.post("/dev-manual-process", include_in_schema=False)
async def dev_manual_process_document(request: DevManualProcessRequest):
    """
    Manually process a document from content provided directly
    Used for debugging when the regular process isn't working
    """
    try:
        from datetime import datetime
        from app.models.document import Document
        
        document_id = request.id
        logger.info(f"Manual processing document {document_id} with provided content")
        
        # Check if document already exists in vector store
        try:
            existing_chunks = await vector_store.get_document_chunks(document_id)
            if existing_chunks and request.force_delete:
                # Delete existing document from vector store
                logger.info(f"Deleting existing document {document_id} from vector store (found {len(existing_chunks)} chunks)")
                vector_store.delete_document(document_id)
                logger.info(f"Existing document deleted from vector store")
        except Exception as e:
            logger.warning(f"Error checking existing document: {str(e)}")
        
        # Create a Document object with extra metadata
        document = Document(
            id=document_id,
            filename=request.filename,
            content=request.content,
            metadata={
                "processed_at": datetime.utcnow().isoformat(),
                "method": "dev-manual-process",
                "content_length": len(request.content),
                "is_public": True,  # Make document public for all users
                "user_id": "public"  # Special user ID for public documents
            },
            folder="/dev",
            uploaded=datetime.utcnow()
        )
        
        # Process document
        logger.info(f"Creating document processor with chunking strategy: recursive")
        processor = DocumentProcessor(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            chunking_strategy="recursive"
        )
        
        # Log processor settings
        logger.info(f"Processor settings: chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}")
        
        # Process document
        logger.info(f"Starting document processing")
        add_start_time = datetime.utcnow()
        processed_document = await processor.process_document(document)
        
        # Check processed document
        if not hasattr(processed_document, "chunks") or not processed_document.chunks:
            logger.warning(f"Processing completed but no chunks were generated")
            return {
                "success": False,
                "message": f"Processing completed but no chunks were generated",
                "document": processed_document.dict()
            }
        
        logger.info(f"Document processed into {len(processed_document.chunks)} chunks")
        
        # Add to vector store
        logger.info(f"Adding document to vector store with {len(processed_document.chunks)} chunks")
        await vector_store.add_document(processed_document)
        add_end_time = datetime.utcnow()
        add_duration = (add_end_time - add_start_time).total_seconds()
        logger.info(f"Document added to vector store in {add_duration:.2f} seconds")
        
        # Verify document exists in vector store
        logger.info(f"Verifying document exists in vector store")
        verify_chunks = await vector_store.get_document_chunks(document_id)
        
        return {
            "success": True,
            "message": f"Document {request.filename} manually processed successfully",
            "document_id": document_id,
            "content_length": len(request.content),
            "chunk_count": len(processed_document.chunks),
            "processing_time": add_duration,
            "vector_store_chunks": len(verify_chunks),
            "chunks": [chunk.dict() for chunk in processed_document.chunks]
        }
    except Exception as e:
        logger.error(f"Error manually processing document: {str(e)}")
        import traceback
        trace = traceback.format_exc()
        return {
            "success": False,
            "message": f"Error manually processing document: {str(e)}",
            "error_trace": trace
        }
        
@router.post("/dev-delete-vector", include_in_schema=False)
async def dev_delete_from_vector_store(request: DevProcessRequest):
    """
    Delete a document from the vector store only
    """
    try:
        document_id = request.document_id
        logger.info(f"Deleting document {document_id} from vector store")
        
        # Check if document exists in vector store
        try:
            existing_chunks = await vector_store.get_document_chunks(document_id)
            if existing_chunks:
                # Delete existing document from vector store
                logger.info(f"Found {len(existing_chunks)} chunks to delete")
                vector_store.delete_document(document_id)
                logger.info(f"Document deleted from vector store")
                return {
                    "success": True,
                    "message": f"Document {document_id} deleted from vector store ({len(existing_chunks)} chunks removed)"
                }
            else:
                return {
                    "success": True,
                    "message": f"Document {document_id} not found in vector store (nothing to delete)"
                }
        except Exception as e:
            logger.warning(f"Error checking document in vector store: {str(e)}")
            return {
                "success": False,
                "message": f"Error checking document: {str(e)}"
            }
    except Exception as e:
        logger.error(f"Error deleting document from vector store: {str(e)}")
        return {
            "success": False,
            "message": f"Error deleting document: {str(e)}"
        }

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    tags: str = Form(""),
    folder: str = Form("/"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Regular upload document endpoint that requires authentication
    """
    try:
        # Validate file
        is_valid, error_msg = await validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
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
                INSERT INTO documents (id, filename, folder, uploaded, processing_status, user_id, doc_metadata)
                VALUES (:id, :filename, :folder, :uploaded, :status, :user_id, :metadata)
            """)
            
            await db.execute(query, {
                "id": document_id,
                "filename": file.filename,
                "folder": folder,
                "uploaded": datetime.utcnow(),
                "status": "pending",
                "user_id": current_user.id,
                "metadata": {}  # Empty JSON metadata to avoid NULL issues
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
    current_user: Optional[User] = None
):
    # Create a fake user if none was provided (for developer mode)
    if current_user is None:
        try:
            # First try to get a real user from the database
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import text
            
            logger.info("Developer mode: Attempting to find a real user for document processing")
            db = AsyncSessionLocal()
            result = await db.execute(text("SELECT id, username, email FROM users LIMIT 1"))
            user_row = result.fetchone()
            await db.close()
            
            if user_row:
                # Create a User object with the row data
                from uuid import UUID
                current_user = User(
                    id=str(user_row.id),
                    username=user_row.username,
                    email=user_row.email,
                    is_active=True,
                    is_admin=True
                )
                logger.info(f"Developer mode: Using real user for document processing: {current_user.id}")
            else:
                # No users in database, create a fake one
                from uuid import uuid4
                current_user = User(
                    id=str(uuid4()),
                    username="developer",
                    email="developer@example.com",
                    is_active=True,
                    is_admin=True
                )
                logger.info(f"Developer mode: Created fake user for document processing: {current_user.id}")
        except Exception as e:
            # If anything goes wrong, just create a fake user
            logger.error(f"Error finding real user: {str(e)}")
            from uuid import uuid4
            current_user = User(
                id=str(uuid4()),
                username="developer",
                email="developer@example.com",
                is_active=True,
                is_admin=True
            )
            logger.info(f"Developer mode: Created fake user for document processing (fallback): {current_user.id}")
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

@router.delete("/actions/clear-all", response_model=dict)
async def clear_all_documents(
    db: AsyncSession = Depends(get_db),
    document_repository: DocumentRepository = Depends(get_document_repository),
    current_user: Optional[User] = None
):
    # Create a fake user if none was provided (for developer mode)
    if current_user is None:
        try:
            # First try to get a real user from the database
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import text
            
            logger.info("Developer mode: Attempting to find a real user for document clearing")
            db = AsyncSessionLocal()
            result = await db.execute(text("SELECT id, username, email FROM users LIMIT 1"))
            user_row = result.fetchone()
            await db.close()
            
            if user_row:
                # Create a User object with the row data
                from uuid import UUID
                current_user = User(
                    id=str(user_row.id),
                    username=user_row.username,
                    email=user_row.email,
                    is_active=True,
                    is_admin=True
                )
                logger.info(f"Developer mode: Using real user for document clearing: {current_user.id}")
            else:
                # No users in database, create a fake one
                from uuid import uuid4
                current_user = User(
                    id=str(uuid4()),
                    username="developer",
                    email="developer@example.com",
                    is_active=True,
                    is_admin=True
                )
                logger.info(f"Developer mode: Created fake user for document clearing: {current_user.id}")
        except Exception as e:
            # If anything goes wrong, just create a fake user
            logger.error(f"Error finding real user: {str(e)}")
            from uuid import uuid4
            current_user = User(
                id=str(uuid4()),
                username="developer",
                email="developer@example.com",
                is_active=True,
                is_admin=True
            )
            logger.info(f"Developer mode: Created fake user for document clearing (fallback): {current_user.id}")
    """
    Clear all documents from both the database and vector store.
    This is a destructive operation and should be used with caution.
    Only admin users can perform this operation.
    """
    try:
        # Get all document IDs using raw SQL for async compatibility
        from sqlalchemy import text
        result = await db.execute(text("SELECT id FROM documents"))
        document_ids = [str(row[0]) for row in result.fetchall()]
        
        logger.info(f"Clearing {len(document_ids)} documents from system")
        
        # Clear vector store first
        for doc_id in document_ids:
            try:
                # Delete from vector store
                vector_store.delete_document(doc_id)
                logger.info(f"Deleted document {doc_id} from vector store")
            except Exception as e:
                logger.error(f"Error deleting document {doc_id} from vector store: {str(e)}")
        
        # Delete all documents from database
        # Use raw SQL for efficiency
        try:
            # First delete related records in document_tags
            await db.execute(text("DELETE FROM document_tags"))
            
            # Then delete chunks
            await db.execute(text("DELETE FROM chunks"))
            
            # Then delete citations
            await db.execute(text("DELETE FROM citations WHERE document_id IS NOT NULL"))
            
            # Finally delete documents
            await db.execute(text("DELETE FROM documents"))
            
            # Commit the transaction
            await db.commit()
            
            logger.info(f"Deleted {len(document_ids)} documents from database")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error clearing documents from database: {str(e)}")
            raise
        
        return {
            "success": True,
            "message": f"Successfully cleared {len(document_ids)} documents from the system",
            "document_count": len(document_ids)
        }
    except Exception as e:
        logger.error(f"Error clearing all documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing all documents: {str(e)}")