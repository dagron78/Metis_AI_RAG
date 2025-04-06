"""
Conversation model for storing chat conversations
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Float, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class Conversation(Base):
    """
    Conversation model for storing chat conversations
    
    This model stores chat conversations between users and the system,
    including messages, metadata, and associated memories.
    """
    __tablename__ = "conversations"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    conv_metadata = Column(JSON, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"
    
    def to_dict(self):
        """Convert conversation to dictionary"""
        return {
            "id": str(self.id),
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.conv_metadata
        }
    
    @property
    def user_id(self) -> Optional[str]:
        """Get user ID from metadata"""
        if self.conv_metadata and "user_id" in self.conv_metadata:
            return self.conv_metadata["user_id"]
        return None

class Message(Base):
    """
    Message model for storing chat messages
    
    This model stores individual messages within a conversation,
    including the content, role, and associated citations.
    """
    __tablename__ = "messages"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(PostgresUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    token_count = Column(Integer, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role})>"
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "content": self.content,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "token_count": self.token_count,
            "citations": [citation.to_dict() for citation in self.citations] if self.citations else []
        }

class Citation(Base):
    """
    Citation model for storing document citations
    
    This model stores citations to documents or chunks that were used
    to generate a response.
    """
    __tablename__ = "citations"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(PostgresUUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    document_id = Column(PostgresUUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    chunk_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    relevance_score = Column(Float, nullable=True)
    excerpt = Column(Text, nullable=True)
    
    # Relationships
    message = relationship("Message", back_populates="citations")
    document = relationship("Document", back_populates="citations")
    
    def __repr__(self):
        return f"<Citation(id={self.id}, document_id={self.document_id})>"
    
    def to_dict(self):
        """Convert citation to dictionary"""
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "document_id": str(self.document_id) if self.document_id else None,
            "chunk_id": str(self.chunk_id) if self.chunk_id else None,
            "relevance_score": self.relevance_score,
            "excerpt": self.excerpt
        }