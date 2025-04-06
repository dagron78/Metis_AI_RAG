# Fixed SQLAlchemy Models Code

Below is the corrected version of the `app/db/models.py` file with the metadata naming conflicts resolved:

```python
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, 
    DateTime, ForeignKey, JSON, Table, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base

# Association table for document-tag many-to-many relationship
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('added_at', DateTime, default=datetime.utcnow)
)

class Document(Base):
    """Document model for database"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # Can be null if we only store metadata
    doc_metadata = Column(JSONB, default={})  # Changed from 'metadata' to 'doc_metadata'
    folder = Column(String, ForeignKey('folders.path'), default="/")
    uploaded = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_strategy = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=document_tags, back_populates="documents")
    folder_rel = relationship("Folder", back_populates="documents")
    citations = relationship("Citation", back_populates="document")

    # Indexes
    __table_args__ = (
        Index('ix_documents_filename', filename),
        Index('ix_documents_folder', folder),
        Index('ix_documents_processing_status', processing_status),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"


class Chunk(Base):
    """Chunk model for database"""
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSONB, default={})  # Changed from 'metadata' to 'chunk_metadata'
    index = Column(Integer, nullable=False)  # Position in the document
    embedding_quality = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    citations = relationship("Citation", back_populates="chunk")

    # Indexes
    __table_args__ = (
        Index('ix_chunks_document_id', document_id),
        Index('ix_chunks_document_id_index', document_id, index),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.index})>"


class Tag(Base):
    """Tag model for database"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)

    # Relationships
    documents = relationship("Document", secondary=document_tags, back_populates="tags")

    # Indexes
    __table_args__ = (
        Index('ix_tags_name', name),
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


class Folder(Base):
    """Folder model for database"""
    __tablename__ = "folders"

    path = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    parent_path = Column(String, ForeignKey('folders.path'), nullable=True)
    document_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="folder_rel")
    subfolders = relationship("Folder", 
                             backref=relationship.backref("parent", remote_side=[path]),
                             cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_folders_parent_path', parent_path),
    )

    def __repr__(self):
        return f"<Folder(path='{self.path}', name='{self.name}')>"


class Conversation(Base):
    """Conversation model for database"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    conv_metadata = Column(JSONB, default={})  # Changed from 'metadata' to 'conv_metadata'
    message_count = Column(Integer, default=0)

    # Relationships
