"""
Memory repository for managing memory operations
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.repositories.base import BaseRepository
from app.models.memory import Memory

class MemoryRepository(BaseRepository[Memory]):
    """
    Repository for Memory model
    
    This repository provides methods for managing memory operations,
    including storing and retrieving memories.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the memory repository
        
        Args:
            session: Database session
        """
        super().__init__(session, Memory)
    
    async def create_memory(self, conversation_id: UUID, content: str, label: str = "explicit_memory") -> Memory:
        """
        Create a new memory
        
        Args:
            conversation_id: Conversation ID
            content: Memory content
            label: Memory label
            
        Returns:
            Created memory
        """
        memory_data = {
            "conversation_id": conversation_id,
            "content": content,
            "label": label
        }
        
        return await self.create(memory_data)
    
    async def get_memories_by_conversation(
        self,
        conversation_id: UUID,
        label: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """
        Get memories for a conversation
        
        Args:
            conversation_id: Conversation ID
            label: Optional memory label filter
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        query = select(Memory).where(Memory.conversation_id == conversation_id)
        
        if label:
            query = query.where(Memory.label == label)
        
        query = query.order_by(desc(Memory.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_memories(
        self,
        conversation_id: UUID,
        search_term: str,
        label: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """
        Search memories by content
        
        Args:
            conversation_id: Conversation ID
            search_term: Search term
            label: Optional memory label filter
            limit: Maximum number of memories to return
            
        Returns:
            List of matching memories
        """
        # First get all memories for the conversation
        memories = await self.get_memories_by_conversation(
            conversation_id=conversation_id,
            label=label
        )
        
        # Filter by search term
        if search_term:
            search_term_lower = search_term.lower()
            filtered_memories = [
                memory for memory in memories
                if search_term_lower in memory.content.lower()
            ]
            memories = filtered_memories
        
        # Apply limit
        return memories[:limit]
    
    async def delete_memories_by_conversation(self, conversation_id: UUID) -> int:
        """
        Delete all memories for a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Number of deleted memories
        """
        query = select(Memory).where(Memory.conversation_id == conversation_id)
        result = await self.session.execute(query)
        memories = result.scalars().all()
        
        count = 0
        for memory in memories:
            await self.session.delete(memory)
            count += 1
        
        await self.session.commit()
        return count

# Factory function for dependency injection
async def get_memory_repository(session: AsyncSession) -> MemoryRepository:
    """
    Get a memory repository instance
    
    Args:
        session: Database session
        
    Returns:
        Memory repository
    """
    return MemoryRepository(session)