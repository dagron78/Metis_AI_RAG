"""
Memory model for storing explicit memories
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class Memory(Base):
    """
    Memory model for storing explicit memories
    
    This model stores explicit memories that users want the system to remember,
    such as preferences, facts, or other information.
    """
    __tablename__ = "memories"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(PostgresUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    label = Column(String(50), nullable=False, default="explicit_memory")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="memories")
    
    def __repr__(self):
        return f"<Memory(id={self.id}, label={self.label})>"
    
    def to_dict(self):
        """Convert memory to dictionary"""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "content": self.content,
            "label": self.label,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }