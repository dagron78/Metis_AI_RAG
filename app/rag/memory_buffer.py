"""
Memory buffer functionality for Metis RAG
"""
import logging
import re
import time
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.memory import Memory
from app.db.models import Conversation

logger = logging.getLogger("app.rag.memory_buffer")

async def add_to_memory_buffer(
    conversation_id: UUID,
    content: str,
    label: str = "explicit_memory",
    db: AsyncSession = None
) -> Memory:
    """
    Add content to the memory buffer
    
    Args:
        conversation_id: Conversation ID
        content: Content to store
        label: Memory label
        db: Database session
        
    Returns:
        Created memory object
    """
    try:
        # Get database session if not provided
        if db is None:
            db = await anext(get_db())
        
        # Create memory object
        memory = Memory(
            conversation_id=conversation_id,
            content=content,
            label=label,
            created_at=datetime.now()
        )
        
        # Add to database
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        
        logger.info(f"Added memory to buffer: {content[:50]}...")
        
        return memory
    except Exception as e:
        logger.error(f"Error adding to memory buffer: {str(e)}")
        if db:
            await db.rollback()
        raise

async def get_memory_buffer(
    conversation_id: UUID,
    search_term: Optional[str] = None,
    label: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = None
) -> List[Memory]:
    """
    Get memories from the buffer
    
    Args:
        conversation_id: Conversation ID
        search_term: Optional search term
        label: Optional memory label
        limit: Maximum number of memories to return
        db: Database session
        
    Returns:
        List of memory objects
    """
    try:
        # Get database session if not provided
        if db is None:
            db = await anext(get_session())
        
        # Build query
        query = select(Memory).where(Memory.conversation_id == conversation_id)
        
        # Add label filter if provided
        if label:
            query = query.where(Memory.label == label)
        
        # Order by creation time (newest first)
        query = query.order_by(desc(Memory.created_at))
        
        # Execute query
        result = await db.execute(query)
        memories = result.scalars().all()
        
        # Filter by search term if provided
        if search_term and memories:
            filtered_memories = []
            for memory in memories:
                if search_term.lower() in memory.content.lower():
                    filtered_memories.append(memory)
            memories = filtered_memories
        
        # Limit results
        memories = memories[:limit]
        
        logger.info(f"Retrieved {len(memories)} memories from buffer")
        
        return memories
    except Exception as e:
        logger.error(f"Error getting memory buffer: {str(e)}")
        return []

async def process_query(
    query: str,
    user_id: str,
    conversation_id: UUID,
    db: AsyncSession = None
) -> tuple[str, Optional[str], Optional[str]]:
    """
    Process a query for memory commands before sending to RAG
    
    Args:
        query: User query
        user_id: User ID
        conversation_id: Conversation ID
        db: Database session
        
    Returns:
        Tuple of (processed_query, memory_response, memory_operation)
    """
    # Get database session if not provided
    if db is None:
        db = await anext(get_session())
    
    # Check for memory commands
    memory_match = re.search(r"remember\s+this(?:\s+(?:phrase|name|information))?\s*:\s*(.+)", query, re.IGNORECASE)
    if memory_match:
        content = memory_match.group(1).strip()
        
        # Store in memory buffer
        await add_to_memory_buffer(
            conversation_id=conversation_id,
            content=content,
            label="explicit_memory",
            db=db
        )
        
        # Create confirmation response
        memory_response = f"I've stored this in my memory: '{content}'"
        
        # Remove the command from the query
        processed_query = query.replace(memory_match.group(0), "").strip()
        if not processed_query:
            processed_query = "Thank you for providing that information."
        
        return processed_query, memory_response, "store"
    
    # Check for recall command
    recall_match = re.search(r"(?:recall|remember)(?:\s+(?:the|my))?\s*(?:(.+))?", query, re.IGNORECASE)
    if recall_match and not memory_match:  # Avoid conflict with "remember this" command
        search_term = recall_match.group(1).strip() if recall_match.group(1) else None
        
        # Retrieve from memory buffer
        memories = await get_memory_buffer(
            conversation_id=conversation_id,
            search_term=search_term,
            db=db
        )
        
        if memories:
            memory_items = [f"{i+1}. {memory.content}" for i, memory in enumerate(memories)]
            memory_response = "Here's what I remember:\n" + "\n".join(memory_items)
        else:
            memory_response = "I don't have any memories stored about that."
        
        # Remove the command from the query
        processed_query = query.replace(recall_match.group(0), "").strip()
        if not processed_query:
            processed_query = "Please provide the information you'd like me to recall."
        
        return processed_query, memory_response, "recall"
    
    # No memory command found
    return query, None, None

async def get_conversation_context(
    conversation_history: Optional[List[Any]] = None,
    max_tokens: int = 4000
) -> str:
    """
    Get the full conversation context up to the specified token limit
    
    Args:
        conversation_history: List of conversation messages
        max_tokens: Maximum number of tokens to include
        
    Returns:
        Formatted conversation context string
    """
    if not conversation_history:
        return ""
    
    # Calculate tokens for each message
    message_tokens = []
    for msg in conversation_history:
        # Estimate token count if not already calculated
        token_count = getattr(msg, 'token_count', None) or len(msg.content.split())
        message_tokens.append({
            "role": msg.role,
            "content": msg.content,
            "tokens": token_count
        })
    
    # Apply smart context window management
    formatted_messages = []
    total_tokens = 0
    
    # First, include messages with memory operations
    memory_messages = [m for m in message_tokens if contains_memory_operation(m["content"])]
    for msg in memory_messages:
        if total_tokens + msg["tokens"] <= max_tokens:
            formatted_messages.append(msg)
            total_tokens += msg["tokens"]
    
    # Then include the most recent messages
    recent_messages = [m for m in reversed(message_tokens) if m not in formatted_messages]
    for msg in recent_messages:
        if total_tokens + msg["tokens"] <= max_tokens:
            formatted_messages.insert(0, msg)  # Insert at beginning to maintain order
            total_tokens += msg["tokens"]
        else:
            break
    
    # Sort messages by original order
    formatted_messages.sort(key=lambda m: message_tokens.index(m))
    
    # Format the conversation history
    history_pieces = []
    for msg in formatted_messages:
        role_prefix = "User" if msg["role"] == "user" else "Assistant"
        history_pieces.append(f"{role_prefix}: {msg['content']}")
    
    return "\n".join(history_pieces)

def contains_memory_operation(content: str) -> bool:
    """
    Check if a message contains a memory operation
    
    Args:
        content: Message content
        
    Returns:
        True if the message contains a memory operation
    """
    memory_patterns = [
        r"remember\s+this",
        r"(?:recall|remember)(?:\s+(?:the|my))?"
    ]
    
    for pattern in memory_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    return False