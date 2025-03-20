"""
Adapter functions to convert between Pydantic and SQLAlchemy models.

This module provides functions to convert between Pydantic models (used in the API and domain layers)
and SQLAlchemy models (used in the database layer). This separation allows for clean domain models
while maintaining efficient database operations.
"""
import uuid
from typing import List, Optional, Union, Dict, Any
from uuid import UUID

from app.models import document as pydantic_models
from app.db import models as db_models
from app.core.config import DATABASE_TYPE

def to_str_id(id_value: Union[str, UUID, None]) -> Optional[str]:
    """
    Convert ID to string format.
    
    Args:
        id_value: ID value (can be string, UUID, or None)
        
    Returns:
        String representation of the ID, or None if input is None
    """
    if id_value is None:
        return None
    return str(id_value)

def to_uuid_or_str(id_value: Union[str, UUID, None]) -> Optional[Union[str, UUID]]:
    """
    Convert ID to appropriate type based on database.
    For PostgreSQL: UUID
    For SQLite: string
    
    Args:
        id_value: ID value (can be string, UUID, or None)
        
    Returns:
        UUID for PostgreSQL, string for other databases, or None if input is None
    """
    if id_value is None:
        return None
        
    if DATABASE_TYPE == 'postgresql':
        if isinstance(id_value, UUID):
            return id_value
        try:
            return UUID(id_value)
        except ValueError:
            # If the string is not a valid UUID format, return it as is
            return id_value
    else:
        return to_str_id(id_value)

def pydantic_document_to_sqlalchemy(doc: pydantic_models.Document) -> db_models.Document:
    """
    Convert Pydantic Document to SQLAlchemy Document.
    
    Args:
        doc: Pydantic Document model
        
    Returns:
        SQLAlchemy Document model
    """
    # Handle UUID conversion based on database type
    doc_id = to_uuid_or_str(doc.id)
    
    # Create SQLAlchemy Document
    sqlalchemy_doc = db_models.Document(
        id=doc_id,
        filename=doc.filename,
        content=doc.content,
        doc_metadata=doc.metadata,  # Note the attribute name change
        folder=doc.folder,
        uploaded=doc.uploaded,
        processing_status=doc.metadata.get("processing_status", "pending"),
        processing_strategy=doc.metadata.get("processing_strategy", None),
        file_size=doc.metadata.get("file_size", None),
        file_type=doc.metadata.get("file_type", None),
        last_accessed=doc.metadata.get("last_accessed", doc.uploaded)
    )
    
    # Convert chunks if available
    if hasattr(doc, 'chunks') and doc.chunks:
        sqlalchemy_doc.chunks = [
            pydantic_chunk_to_sqlalchemy(chunk, doc_id) 
            for chunk in doc.chunks
        ]
    
    return sqlalchemy_doc

def sqlalchemy_document_to_pydantic(doc: db_models.Document) -> pydantic_models.Document:
    """
    Convert SQLAlchemy Document to Pydantic Document.
    
    Args:
        doc: SQLAlchemy Document model
        
    Returns:
        Pydantic Document model
    """
    pydantic_doc = pydantic_models.Document(
        id=to_str_id(doc.id),
        filename=doc.filename,
        content=doc.content,
        metadata=doc.doc_metadata,  # Note the attribute name change
        folder=doc.folder,
        uploaded=doc.uploaded
    )
    
    # Convert chunks if available
    if hasattr(doc, 'chunks') and doc.chunks:
        pydantic_doc.chunks = [
            sqlalchemy_chunk_to_pydantic(chunk) 
            for chunk in doc.chunks
        ]
    
    # Convert tags if available
    if hasattr(doc, 'tags') and doc.tags:
        pydantic_doc.tags = [tag.name for tag in doc.tags]
    
    return pydantic_doc

def pydantic_chunk_to_sqlalchemy(chunk: pydantic_models.Chunk, document_id: Union[str, UUID]) -> db_models.Chunk:
    """
    Convert Pydantic Chunk to SQLAlchemy Chunk.
    
    Args:
        chunk: Pydantic Chunk model
        document_id: ID of the parent document
        
    Returns:
        SQLAlchemy Chunk model
    """
    # Handle UUID conversion based on database type
    chunk_id = to_uuid_or_str(chunk.id)
    doc_id = to_uuid_or_str(document_id)
    
    # Extract index from metadata or default to 0
    index = chunk.metadata.get('index', 0) if chunk.metadata else 0
    
    sqlalchemy_chunk = db_models.Chunk(
        id=chunk_id,
        document_id=doc_id,
        content=chunk.content,
        chunk_metadata=chunk.metadata,  # Note the attribute name change
        index=index,
        embedding_quality=chunk.metadata.get('embedding_quality', None) if chunk.metadata else None
    )
    return sqlalchemy_chunk

def sqlalchemy_chunk_to_pydantic(chunk: db_models.Chunk) -> pydantic_models.Chunk:
    """
    Convert SQLAlchemy Chunk to Pydantic Chunk.
    
    Args:
        chunk: SQLAlchemy Chunk model
        
    Returns:
        Pydantic Chunk model
    """
    pydantic_chunk = pydantic_models.Chunk(
        id=to_str_id(chunk.id),
        content=chunk.content,
        metadata=chunk.chunk_metadata  # Note the attribute name change
    )
    
    # Add embedding if available
    if hasattr(chunk, 'embedding') and chunk.embedding:
        pydantic_chunk.embedding = chunk.embedding
    
    return pydantic_chunk

def is_sqlalchemy_model(obj: Any) -> bool:
    """
    Check if an object is a SQLAlchemy model.
    
    Args:
        obj: Object to check
        
    Returns:
        True if the object is a SQLAlchemy model, False otherwise
    """
    return hasattr(obj, '_sa_instance_state')

def is_pydantic_model(obj: Any) -> bool:
    """
    Check if an object is a Pydantic model.
    
    Args:
        obj: Object to check
        
    Returns:
        True if the object is a Pydantic model, False otherwise
    """
    return hasattr(obj, '__fields__')