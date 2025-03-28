from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, select, delete

from app.db.models import Conversation, Message, Citation, Document, Chunk
from app.db.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation model with user context and permission handling
    """
    
    def __init__(self, session: Session, user_id: Optional[UUID] = None):
        super().__init__(session, Conversation)
        self.user_id = user_id
    
    async def create_conversation(self, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """
        Create a new conversation
        
        Args:
            metadata: Conversation metadata
            
        Returns:
            Created conversation
        """
        # Initialize metadata if None
        meta = metadata or {}
        
        conversation = Conversation(
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            conv_metadata=meta,  # Changed to conv_metadata
            message_count=0,
            user_id=self.user_id  # Set user_id directly from context
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
        
        # Check if user has permission to add messages to this conversation
        if not self._can_modify_conversation(conversation):
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
        conversation = result.scalars().first()
        
        # Check if user has permission to view this conversation
        if conversation and not self._can_view_conversation(conversation):
            return None
        
        return conversation
    
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
        message = result.scalars().first()
        
        # Check if user has permission to view this message
        if message:
            conversation = await self.get_by_id(message.conversation_id)
            if not conversation or not self._can_view_conversation(conversation):
                return None
        
        return message
    
    async def get_message_with_citations(self, message_id: int) -> Optional[Message]:
        """
        Get a message with its citations
        
        Args:
            message_id: Message ID
            
        Returns:
            Message with citations if found, None otherwise
        """
        # Reuse get_message which already has permission checking
        return await self.get_message(message_id)
    
    async def get_recent_conversations(self, limit: int = 10) -> List[Conversation]:
        """
        Get recent conversations for the current user
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of recent conversations
        """
        # Filter by user_id if available
        if self.user_id:
            stmt = select(Conversation).filter(
                Conversation.user_id == self.user_id
            ).order_by(
                Conversation.updated_at.desc()
            ).limit(limit)
        else:
            # Return empty list if no user context
            return []
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def search_conversations(self, query: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """
        Search conversations by message content for the current user
        
        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching conversations
        """
        # Return empty list if no user context
        if not self.user_id:
            return []
        
        # Find messages matching the query
        message_subquery = select(Message.conversation_id).join(
            Conversation, Conversation.id == Message.conversation_id
        ).filter(
            Message.content.ilike(f"%{query}%"),
            Conversation.user_id == self.user_id  # Filter by user_id
        ).distinct().subquery()
        
        # Get conversations with matching messages
        stmt = select(Conversation).join(
            message_subquery, Conversation.id == message_subquery.c.conversation_id
        ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_conversation(self, conversation_id: UUID, metadata: Optional[Dict[str, Any]] = None) -> Optional[Conversation]:
        """
        Update a conversation
        
        Args:
            conversation_id: Conversation ID
            metadata: New metadata
            
        Returns:
            Updated conversation if found, None otherwise
        """
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return None
        
        # Check if user has permission to modify this conversation
        if not self._can_modify_conversation(conversation):
            return None
        
        # Update metadata if provided
        if metadata:
            # Get current metadata
            current_metadata = conversation.conv_metadata or {}
            
            # Merge new metadata
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
        
        # Check if user has permission to delete this conversation
        if not self._can_delete_conversation(conversation):
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
        # Check if user has permission to view this conversation
        conversation = await self.get_by_id(conversation_id)
        if not conversation or not self._can_view_conversation(conversation):
            return []
        
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
        # Check if user has permission to view this conversation
        conversation = await self.get_by_id(conversation_id)
        if not conversation or not self._can_view_conversation(conversation):
            return None
        
        stmt = select(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == "user"
        ).order_by(
            Message.timestamp.desc()
        ).limit(1)
        
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_conversations(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """
        Get conversations for the current user with pagination
        
        Args:
            skip: Number of conversations to skip
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        # Return empty list if no user context
        if not self.user_id:
            return []
        
        # Filter by user_id
        stmt = select(Conversation).filter(
            Conversation.user_id == self.user_id
        ).order_by(
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def count_conversations(self) -> int:
        """
        Count conversations for the current user
        
        Returns:
            Number of conversations
        """
        # Return 0 if no user context
        if not self.user_id:
            return 0
        
        # Filter by user_id
        stmt = select(func.count()).select_from(Conversation).filter(
            Conversation.user_id == self.user_id
        )
        
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
        # Check if user has permission to modify this message
        message = await self.get_message(message_id)
        if not message:
            return None
        
        conversation = await self.get_by_id(message.conversation_id)
        if not conversation or not self._can_modify_conversation(conversation):
            return None
        
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
        Get conversation statistics for the current user
        
        Returns:
            Dictionary with statistics
        """
        # Return empty stats if no user context
        if not self.user_id:
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "avg_messages_per_conversation": 0.0
            }
        
        # Get total conversations for this user
        stmt_conversations = select(func.count(Conversation.id)).filter(
            Conversation.user_id == self.user_id
        )
        result_conversations = await self.session.execute(stmt_conversations)
        total_conversations = result_conversations.scalar() or 0
        
        # Get total messages for this user's conversations
        stmt_messages = select(func.count(Message.id)).join(
            Conversation, Conversation.id == Message.conversation_id
        ).filter(
            Conversation.user_id == self.user_id
        )
        result_messages = await self.session.execute(stmt_messages)
        total_messages = result_messages.scalar() or 0
        
        # Get average messages per conversation
        avg_messages_per_conversation = 0.0
        if total_conversations > 0:
            avg_messages_per_conversation = total_messages / total_conversations
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": float(avg_messages_per_conversation)
        }
    
    def _can_view_conversation(self, conversation: Conversation) -> bool:
        """
        Check if the current user can view a conversation
        
        Args:
            conversation: Conversation to check
            
        Returns:
            True if user can view the conversation, False otherwise
        """
        # If no user context, no access
        if not self.user_id:
            return False
        
        # User can view their own conversations
        return conversation.user_id == self.user_id
    
    def _can_modify_conversation(self, conversation: Conversation) -> bool:
        """
        Check if the current user can modify a conversation
        
        Args:
            conversation: Conversation to check
            
        Returns:
            True if user can modify the conversation, False otherwise
        """
        # Same as view permissions for now - only owner can modify
        return self._can_view_conversation(conversation)
    
    def _can_delete_conversation(self, conversation: Conversation) -> bool:
        """
        Check if the current user can delete a conversation
        
        Args:
            conversation: Conversation to check
            
        Returns:
            True if user can delete the conversation, False otherwise
        """
        # Same as modify permissions - only owner can delete
        return self._can_modify_conversation(conversation)