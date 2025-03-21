from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, select, delete

from app.db.models import Conversation, Message, Citation, Document, Chunk
from app.db.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation model
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Conversation)
    
    async def create_conversation(self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """
        Create a new conversation
        
        Args:
            user_id: User ID
            metadata: Conversation metadata
            
        Returns:
            Created conversation
        """
        # Initialize metadata if None
        meta = metadata or {}
        
        # Add user_id to metadata if provided
        if user_id:
            meta["user_id"] = user_id
            
        conversation = Conversation(
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            conv_metadata=meta,  # Changed to conv_metadata
            message_count=0
        )
        
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation
    
    async def add_message(self,
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
        conversation = await self.get_by_id(conversation_id)
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
        await self.session.flush()  # Flush to get the message ID
        
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
        
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def get_conversation_with_messages(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Get a conversation with its messages
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation with messages if found, None otherwise
        """
        stmt = select(Conversation).filter(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_message(self, message_id: int) -> Optional[Message]:
        """
        Get a message by ID
        
        Args:
            message_id: Message ID
            
        Returns:
            Message if found, None otherwise
        """
        stmt = select(Message).filter(Message.id == message_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_message_with_citations(self, message_id: int) -> Optional[Message]:
        """
        Get a message with its citations
        
        Args:
            message_id: Message ID
            
        Returns:
            Message with citations if found, None otherwise
        """
        stmt = select(Message).filter(Message.id == message_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_recent_conversations(self, limit: int = 10) -> List[Conversation]:
        """
        Get recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of recent conversations
        """
        stmt = select(Conversation).order_by(
            Conversation.updated_at.desc()
        ).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def search_conversations(self, query: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
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
        message_subquery = select(Message.conversation_id).filter(
            Message.content.ilike(f"%{query}%")
        ).distinct().subquery()
        
        # Get conversations with matching messages
        stmt = select(Conversation).join(
            message_subquery, Conversation.id == message_subquery.c.conversation_id
        ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_conversation(self, conversation_id: UUID, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Conversation]:
        """
        Update a conversation
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            metadata: New metadata
            
        Returns:
            Updated conversation if found, None otherwise
        """
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return None
        
        # Update metadata if provided
        if metadata or user_id:
            # Get current metadata
            current_metadata = conversation.conv_metadata or {}
            
            # Add user_id to metadata if provided
            if user_id:
                current_metadata["user_id"] = user_id
                
            # Merge new metadata if provided
            if metadata:
                current_metadata = {**current_metadata, **metadata}
                
            # Update conversation metadata
            conversation.conv_metadata = current_metadata
            
        # Update timestamp
        conversation.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation
        
    async def update_conversation_metadata(self, conversation_id: UUID, metadata: Dict[str, Any]) -> Optional[Conversation]:
        """
        Update conversation metadata
        
        Args:
            conversation_id: Conversation ID
            metadata: New metadata
            
        Returns:
            Updated conversation if found, None otherwise
        """
        return await self.update_conversation(conversation_id=conversation_id, metadata=metadata)
    
    async def delete_conversation_with_messages(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation and all its messages
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if conversation was deleted, False otherwise
        """
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return False
        
        # Delete all messages (cascade will delete citations)
        stmt = delete(Message).where(Message.conversation_id == conversation_id)
        await self.session.execute(stmt)
        
        # Delete conversation
        await self.session.delete(conversation)
        await self.session.commit()
        return True
    
    async def get_conversation_messages(self,
                                  conversation_id: UUID,
                                  skip: int = 0,
                                  limit: int = 100) -> List[Message]:
        """
        Get messages for a conversation with pagination
        
        Args:
            conversation_id: Conversation ID
            skip: Number of messages to skip
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        stmt = select(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.timestamp.asc()
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_last_user_message(self, conversation_id: UUID) -> Optional[Message]:
        """
        Get the last user message in a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Last user message if found, None otherwise
        """
        stmt = select(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == "user"
        ).order_by(
            Message.timestamp.desc()
        ).limit(1)
        
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_conversations(self,
                          user_id: Optional[str] = None,
                          skip: int = 0,
                          limit: int = 100) -> List[Conversation]:
        """
        Get conversations with optional filtering by user_id and pagination
        
        Args:
            user_id: User ID to filter by
            skip: Number of conversations to skip
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        if user_id:
            # Filter by user_id in metadata
            stmt = select(Conversation).filter(
                Conversation.conv_metadata['user_id'].astext == user_id
            ).order_by(
                Conversation.updated_at.desc()
            ).offset(skip).limit(limit)
        else:
            # Get all conversations
            stmt = select(Conversation).order_by(
                Conversation.updated_at.desc()
            ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def count_conversations(self, user_id: Optional[str] = None) -> int:
        """
        Count conversations with optional filtering by user_id
        
        Args:
            user_id: User ID to filter by
            
        Returns:
            Number of conversations
        """
        if user_id:
            # Filter by user_id in metadata
            stmt = select(func.count()).select_from(Conversation).filter(
                Conversation.conv_metadata['user_id'].astext == user_id
            )
        else:
            # Count all conversations
            stmt = select(func.count()).select_from(Conversation)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def add_citation(self,
                     message_id: int,
                     document_id: Optional[UUID] = None,
                     chunk_id: Optional[UUID] = None,
                     relevance_score: Optional[float] = None,
                     excerpt: Optional[str] = None,
                     character_range_start: Optional[int] = None,
                     character_range_end: Optional[int] = None) -> Optional[Citation]:
        """
        Add a citation to a message
        
        Args:
            message_id: Message ID
            document_id: Document ID
            chunk_id: Chunk ID
            relevance_score: Relevance score
            excerpt: Excerpt from the document
            character_range_start: Start of character range
            character_range_end: End of character range
            
        Returns:
            Created citation if message found, None otherwise
        """
        # Create citation
        citation = Citation(
            message_id=message_id,
            document_id=document_id,
            chunk_id=chunk_id,
            relevance_score=relevance_score,
            excerpt=excerpt,
            character_range_start=character_range_start,
            character_range_end=character_range_end
        )
        
        self.session.add(citation)
        await self.session.commit()
        await self.session.refresh(citation)
        return citation
    
    async def get_conversation_statistics(self) -> Dict[str, Any]:
        """
        Get conversation statistics
        
        Returns:
            Dictionary with statistics
        """
        # Get total conversations
        stmt_conversations = select(func.count(Conversation.id))
        result_conversations = await self.session.execute(stmt_conversations)
        total_conversations = result_conversations.scalar()
        
        # Get total messages
        stmt_messages = select(func.count(Message.id))
        result_messages = await self.session.execute(stmt_messages)
        total_messages = result_messages.scalar()
        
        # Get average messages per conversation
        stmt_avg = select(func.avg(Conversation.message_count))
        result_avg = await self.session.execute(stmt_avg)
        avg_messages_per_conversation = result_avg.scalar() or 0
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": float(avg_messages_per_conversation)
        }