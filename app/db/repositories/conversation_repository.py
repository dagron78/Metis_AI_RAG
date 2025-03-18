from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.db.models import Conversation, Message, Citation, Document, Chunk
from app.db.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation model
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Conversation)
    
    def create_conversation(self, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """
        Create a new conversation
        
        Args:
            metadata: Conversation metadata
            
        Returns:
            Created conversation
        """
        conversation = Conversation(
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {},
            message_count=0
        )
        
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation
    
    def add_message(self, 
                   conversation_id: UUID, 
                   content: str, 
                   role: str, 
                   citations: Optional[List[Dict[str, Any]]] = None,
                   token_count: Optional[int] = None) -> Optional[Message]:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user, assistant, system)
            citations: List of citation data
            token_count: Message token count
            
        Returns:
            Created message if conversation found, None otherwise
        """
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None
        
        # Create message
        message = Message(
            conversation_id=conversation_id,
            content=content,
            role=role,
            timestamp=datetime.utcnow(),
            token_count=token_count
        )
        
        self.session.add(message)
        self.session.flush()  # Flush to get the message ID
        
        # Add citations if provided
        if citations:
            for citation_data in citations:
                citation = Citation(
                    message_id=message.id,
                    document_id=citation_data.get("document_id"),
                    chunk_id=citation_data.get("chunk_id"),
                    relevance_score=citation_data.get("relevance_score"),
                    excerpt=citation_data.get("excerpt"),
                    character_range_start=citation_data.get("character_range_start"),
                    character_range_end=citation_data.get("character_range_end")
                )
                self.session.add(citation)
        
        # Update conversation
        conversation.message_count += 1
        conversation.updated_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(message)
        return message
    
    def get_conversation_with_messages(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Get a conversation with its messages
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation with messages if found, None otherwise
        """
        return self.session.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def get_message(self, message_id: int) -> Optional[Message]:
        """
        Get a message by ID
        
        Args:
            message_id: Message ID
            
        Returns:
            Message if found, None otherwise
        """
        return self.session.query(Message).filter(Message.id == message_id).first()
    
    def get_message_with_citations(self, message_id: int) -> Optional[Message]:
        """
        Get a message with its citations
        
        Args:
            message_id: Message ID
            
        Returns:
            Message with citations if found, None otherwise
        """
        return self.session.query(Message).filter(Message.id == message_id).first()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Conversation]:
        """
        Get recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of recent conversations
        """
        return self.session.query(Conversation).order_by(
            Conversation.updated_at.desc()
        ).limit(limit).all()
    
    def search_conversations(self, query: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """
        Search conversations by message content
        
        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching conversations
        """
        # Find messages matching the query
        message_subquery = (
            self.session.query(Message.conversation_id)
            .filter(Message.content.ilike(f"%{query}%"))
            .distinct()
            .subquery()
        )
        
        # Get conversations with matching messages
        return self.session.query(Conversation).join(
            message_subquery, Conversation.id == message_subquery.c.conversation_id
        ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    def update_conversation_metadata(self, conversation_id: UUID, metadata: Dict[str, Any]) -> Optional[Conversation]:
        """
        Update conversation metadata
        
        Args:
            conversation_id: Conversation ID
            metadata: New metadata
            
        Returns:
            Updated conversation if found, None otherwise
        """
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None
        
        # Merge metadata instead of replacing
        conversation.metadata = {**conversation.metadata, **metadata}
        conversation.updated_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(conversation)
        return conversation
    
    def delete_conversation_with_messages(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation and all its messages
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if conversation was deleted, False otherwise
        """
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return False
        
        # Delete all messages (cascade will delete citations)
        self.session.query(Message).filter(Message.conversation_id == conversation_id).delete()
        
        # Delete conversation
        self.session.delete(conversation)
        self.session.commit()
        return True
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """
        Get conversation statistics
        
        Returns:
            Dictionary with statistics
        """
        total_conversations = self.session.query(func.count(Conversation.id)).scalar()
        total_messages = self.session.query(func.count(Message.id)).scalar()
        avg_messages_per_conversation = (
            self.session.query(func.avg(Conversation.message_count)).scalar() or 0
        )
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": float(avg_messages_per_conversation)
        }