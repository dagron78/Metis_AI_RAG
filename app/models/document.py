from typing import List, Dict, Optional, Any, Set
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class Chunk(BaseModel):
    """Document chunk model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None

    class Config:
        arbitrary_types_allowed = True


class Document(BaseModel):
    """Document model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content: str
    chunks: List[Chunk] = []
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    folder: str = "/"  # Root folder by default
    uploaded: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class DocumentInfo(BaseModel):
    """Document information (without content)"""
    id: str
    filename: str
    chunk_count: int
    metadata: Dict[str, Any]
    tags: List[str]
    folder: str
    uploaded: datetime

    class Config:
        arbitrary_types_allowed = True


class DocumentProcessRequest(BaseModel):
    """Document processing request"""
    document_ids: List[str]
    force_reprocess: bool = False
    chunking_strategy: Optional[str] = "recursive"
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True


class TagUpdateRequest(BaseModel):
    """Request to update document tags"""
    tags: List[str]

    class Config:
        arbitrary_types_allowed = True


class FolderUpdateRequest(BaseModel):
    """Request to update document folder"""
    folder: str

    class Config:
        arbitrary_types_allowed = True


class DocumentFilterRequest(BaseModel):
    """Request to filter documents"""
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True