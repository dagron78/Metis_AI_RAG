"""
Memory buffer functionality for Metis RAG
"""
import logging
import re
import time
from typing import Dict, Any, List, Optional, Union, Tuple
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
) -> Optional[Memory]:
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
    # Track if we created a session
    session_created = False
    session_gen = None
    
    try:
        # Get database session if not provided
        if db is None:
            session_gen = get_session()
            db = await anext(session_gen)
            session_created = True
            logger.debug(f"Created new session for add_to_memory_buffer, conversation_id: {conversation_id}")
        else:
            logger.debug(f"Using provided session for add_to_memory_buffer, conversation_id: {conversation_id}")
        
        # Verify conversation exists
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalars().first()
        
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found, cannot store memory")
            return None
        
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
        logger.info(f"Memory ID: {memory.id}, Conversation ID: {conversation_id}, Label: {label}")
        
        return memory
    except Exception as e:
        logger.error(f"Error adding to memory buffer: {str(e)}")
        if db and session_created:
            try:
                await db.rollback()
            except Exception as rollback_error:
                logger.warning(f"Error rolling back transaction: {str(rollback_error)}")
        raise
    finally:
        # Only close the session if we created it
        if session_created and session_gen:
            try:
                # Close the generator to trigger the finally block in get_session
                await session_gen.aclose()
                logger.debug(f"Closed session generator in add_to_memory_buffer, conversation_id: {conversation_id}")
            except Exception as e:
                logger.warning(f"Error closing session generator in add_to_memory_buffer: {str(e)}")

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
    # Track if we created a session
    session_created = False
    session_gen = None
    
    try:
        # Get database session if not provided
        if db is None:
            session_gen = get_session()
            db = await anext(session_gen)
            session_created = True
            logger.debug(f"Created new session for get_memory_buffer, conversation_id: {conversation_id}")
        else:
            logger.debug(f"Using provided session for get_memory_buffer, conversation_id: {conversation_id}")
        
        logger.debug(f"Getting memories for conversation {conversation_id}")
        
        # Build query
        query = select(Memory).where(Memory.conversation_id == conversation_id)
        
        # Add label filter if provided
        if label:
            query = query.where(Memory.label == label)
            
        logger.debug(f"Query: {query}")
        
        # Order by creation time (newest first)
        query = query.order_by(desc(Memory.created_at))
        
        # Execute query
        result = await db.execute(query)
        memories = list(result.scalars().all())
        logger.debug(f"Found {len(memories)} memories in database")
        
        # Filter by search term if provided
        if search_term and memories:
            logger.debug(f"Filtering memories by search term: {search_term}")
            
            # If search term is "what I asked you to remember" or similar, return all memories
            if re.search(r"(what|that|which|anything).*(?:ask|tell).*(?:remember|recall)", search_term, re.IGNORECASE):
                logger.debug(f"Generic recall request detected, returning all memories")
                # No filtering needed, return all memories
            else:
                # Try to match the search term against memory content
                filtered_memories = []
                
                # Check for common memory queries
                common_memory_terms = {
                    "favorite color": ["color", "favourite", "favorite", "like", "prefer", "best"],
                    "favorite food": ["food", "meal", "dish", "eat", "cuisine", "favourite", "favorite", "like", "prefer", "best"],
                    "name": ["name", "call", "called"],
                    "birthday": ["birthday", "born", "birth"],
                    "address": ["address", "live", "location", "residence"],
                    "phone": ["phone", "number", "contact", "call"],
                    "email": ["email", "mail", "contact"],
                }
                
                # Check if search term matches any common memory categories
                matched_category = None
                for category, terms in common_memory_terms.items():
                    if any(term.lower() in search_term.lower() for term in terms):
                        matched_category = category
                        logger.debug(f"Matched common memory category: {matched_category}")
                        break
                
                # If we matched a category, use those terms for searching
                if matched_category:
                    search_terms = common_memory_terms[matched_category]
                else:
                    # Otherwise use the original search terms
                    search_terms = [term for term in search_term.split() if len(term) > 3]
                
                # Search for memories matching the terms
                for memory in memories:
                    # Use more flexible matching
                    if matched_category and any(term.lower() in memory.content.lower() for term in search_terms):
                        filtered_memories.append(memory)
                        logger.debug(f"Memory matched category {matched_category}: {memory.content[:50]}...")
                    elif any(term.lower() in memory.content.lower() for term in search_term.split() if len(term) > 3):
                        filtered_memories.append(memory)
                        logger.debug(f"Memory matched search term: {memory.content[:50]}...")
                
                if filtered_memories:
                    logger.debug(f"Found {len(filtered_memories)} memories matching search term")
                    memories = filtered_memories
                else:
                    # If no matches with individual terms, return all memories
                    logger.debug(f"No specific matches found, returning all memories")
        elif search_term:
            logger.debug(f"No memories to filter with search term: {search_term}")
        
        # Limit results
        memories = memories[:limit]
        logger.info(f"Retrieved {len(memories)} memories from buffer for conversation {conversation_id}")
        
        # Log each memory for debugging
        for i, memory in enumerate(memories):
            logger.debug(f"Memory {i+1}: ID={memory.id}, Content={memory.content[:50]}..., Label={memory.label}")
        logger.info(f"Retrieved {len(memories)} memories from buffer")
        
        return memories
    except Exception as e:
        logger.error(f"Error getting memory buffer: {str(e)}")
        return []
    finally:
        # Only close the session if we created it
        if session_created and session_gen:
            try:
                # Close the generator to trigger the finally block in get_session
                await session_gen.aclose()
                logger.debug(f"Closed session generator in get_memory_buffer, conversation_id: {conversation_id}")
            except Exception as e:
                logger.warning(f"Error closing session generator in get_memory_buffer: {str(e)}")

async def process_query(
    query: str,
    user_id: str,
    conversation_id: Union[str, UUID],
    db: AsyncSession = None
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Process a query for memory commands before sending to RAG
    
    Args:
        query: User query
        user_id: User ID
        conversation_id: Conversation ID (can be string or UUID)
        db: Database session
        
    Returns:
        Tuple of (processed_query, memory_response, memory_operation)
    """
    # Track if we created a session
    session_created = False
    session_gen = None
    
    try:
        # Get database session if not provided
        if db is None:
            session_gen = get_session()
            db = await anext(session_gen)
            session_created = True
            logger.debug("Created new session for process_query")
        else:
            logger.debug("Using provided session for process_query")
        
        # Convert conversation_id to UUID if it's a string
        if isinstance(conversation_id, str):
            try:
                conversation_id = UUID(conversation_id)
                logger.info(f"Converted string conversation_id to UUID: {conversation_id}")
            except ValueError:
                logger.error(f"Invalid conversation_id format: {conversation_id}")
                # Return original query without memory processing
                return query, None, None
        
        # Convert user_id to UUID if it's a string
        user_uuid = None
        if isinstance(user_id, str):
            try:
                user_uuid = UUID(user_id)
                logger.info(f"Converted string user_id to UUID: {user_uuid}")
            except ValueError:
                # Generate a deterministic UUID based on the string
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{user_id}")
                logger.warning(f"Invalid user_id format: {user_id}, generated deterministic UUID: {user_uuid}")
                user_id = str(user_uuid)  # Update user_id to be the UUID string
        elif isinstance(user_id, UUID):
            user_uuid = user_id
            user_id = str(user_uuid)  # Ensure user_id is a string
        else:
            logger.error(f"Unexpected user_id type: {type(user_id)}")
            # Return original query without memory processing
            return query, None, None
        
        logger.info(f"Processing query for memory commands: {query[:50]}...")
        logger.info(f"User ID: {user_id}, Conversation ID: {conversation_id}")
        
        # Check for explicit memory commands
        memory_match = re.search(r"remember\s+this(?:\s+(?:phrase|name|information))?\s*:\s*(.+)", query, re.IGNORECASE)
        if memory_match:
            content = memory_match.group(1).strip()
            
            # Store in memory buffer
            memory = await add_to_memory_buffer(
                conversation_id=conversation_id,
                content=content,
                label="explicit_memory",
                db=db
            )
            
            # Check if memory was stored successfully
            if not memory:
                logger.warning(f"Failed to store explicit memory: conversation {conversation_id} not found")
                return query, "I couldn't store that in my memory due to a technical issue.", None
            
            # Create confirmation response
            memory_response = f"I've stored this in my memory: '{content}'"
            logger.info(f"Memory stored successfully: {content[:50]}...")
            
            # Remove the command from the query
            processed_query = query.replace(memory_match.group(0), "").strip()
            if not processed_query:
                processed_query = "Thank you for providing that information."
            
            return processed_query, memory_response, "store"
            
        # Always store the user's query in the memory buffer for implicit memory
        memory = await add_to_memory_buffer(
            conversation_id=conversation_id,
            content=query,
            label="implicit_memory",
            db=db
        )
        
        if memory:
            logger.info(f"Stored user query in memory buffer: {query[:50]}...")
        else:
            logger.warning(f"Failed to store user query in memory buffer: conversation {conversation_id} not found")
        
        # Check for explicit recall command with improved pattern
        recall_match = re.search(r"(?:recall|remember)(?:\s+(?:the|my|what|about))?\s*(.*)", query, re.IGNORECASE)
        
        # Check for implicit memory-related queries
        implicit_memory_match = re.search(r"(?:what is|what's|what are|tell me|do you know|do you remember) (?:my|our|the) (favorite|preferred|best|chosen|selected|liked|loved|hated|disliked|color|food|movie|book|song|hobby|interest|name|birthday|address|phone|email|contact|information|preference|choice|option|selection)", query, re.IGNORECASE)
        
        if (recall_match and not memory_match) or implicit_memory_match:  # Avoid conflict with "remember this" command
            # Get search term from either explicit or implicit match
            if recall_match:
                search_term = recall_match.group(1).strip() if recall_match.group(1) else None
                logger.info(f"Explicit recall command detected with search term: '{search_term}'")
            else:
                search_term = implicit_memory_match.group(1).strip() if implicit_memory_match.group(1) else None
                logger.info(f"Implicit memory query detected with search term: '{search_term}'")
            
            # Retrieve from memory buffer - use the same database session
            memories = await get_memory_buffer(
                conversation_id=conversation_id,
                search_term=search_term,
                db=db
            )
            
            # Log the memories for debugging
            logger.debug(f"Retrieved {len(memories)} memories for recall operation")
            for i, memory in enumerate(memories):
                logger.debug(f"Memory {i+1}: {memory.content}")
            
            if memories:
                memory_items = [f"{i+1}. {memory.content}" for i, memory in enumerate(memories)]
                memory_response = "Here's what I remember:\n" + "\n".join(memory_items)
                logger.info(f"Retrieved {len(memories)} memories for recall operation")
                
                # For implicit queries, we want to continue with the original query
                # but include the memory information in the response
                if implicit_memory_match:
                    return query, memory_response, "recall"
            else:
                memory_response = "I don't have any memories stored about that."
                logger.info("No memories found for recall operation")
            
            # For explicit recall commands, remove the command from the query
            if recall_match:
                processed_query = query.replace(recall_match.group(0), "").strip()
                if not processed_query:
                    processed_query = "Please provide the information you'd like me to recall."
                return processed_query, memory_response, "recall"
            
            # For implicit memory queries with no memories found, continue with original query
            return query, memory_response, "recall"
        
        # No memory command found
        logger.info("No memory command detected in query")
        
        return query, None, None
    
    except Exception as e:
        logger.error(f"Error processing memory commands: {str(e)}")
        return query, None, None
    finally:
        # Only close the session if we created it
        if session_created and session_gen:
            try:
                # Close the generator to trigger the finally block in get_session
                await session_gen.aclose()
                logger.debug("Closed session generator in process_query")
            except Exception as e:
                logger.warning(f"Error closing session generator in process_query: {str(e)}")

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