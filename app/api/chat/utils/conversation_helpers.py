"""
Conversation helper utilities for the chat API.

This module contains utility functions for managing conversations in the chat API.
"""

import logging
from typing import Optional, Tuple, List
from uuid import UUID

from app.models.chat import Message

# Logger
logger = logging.getLogger("app.api.chat.utils.conversation_helpers")

# Maximum number of messages to include in conversation history
MAX_HISTORY_MESSAGES = 25

async def get_or_create_conversation(
    conversation_id: Optional[str],
    conversation_repository,
    user_id: str
) -> Tuple[str, bool]:
    """
    Get an existing conversation or create a new one.
    
    Args:
        conversation_id: The ID of the conversation to get, or None to create a new one
        conversation_repository: Repository for retrieving and creating conversations
        user_id: The ID of the user
        
    Returns:
        A tuple of (conversation_id, is_new) where is_new is True if a new conversation was created
    """
    is_new = False
    
    if conversation_id:
        # Try to get existing conversation
        try:
            conversation_uuid = UUID(conversation_id)
            conversation = await conversation_repository.get_by_id(conversation_uuid)
            
            # The repository will handle permission checks based on user_id
            # If the conversation doesn't belong to the user, it will return None
            if not conversation:
                # Log this event for security monitoring
                logger.warning(
                    f"User {user_id} attempted to access conversation {conversation_id} " 
                    f"which doesn't exist or they don't have permission to access"
                )
                
                # Create new conversation if not found or not authorized
                # The repository will use its user_id context
                conversation = await conversation_repository.create_conversation(
                    metadata={"previous_attempt": str(conversation_uuid)}
                )
                conversation_id = str(conversation.id)
                is_new = True
                logger.info(f"Created new conversation {conversation_id} for user {user_id}")
        except ValueError:
            # Invalid UUID format, create new conversation
            logger.warning(f"Invalid UUID format: {conversation_id}")
            conversation = await conversation_repository.create_conversation()
            conversation_id = str(conversation.id)
            is_new = True
    else:
        # Create new conversation
        # The repository will use its user_id context
        conversation = await conversation_repository.create_conversation()
        conversation_id = str(conversation.id)
        is_new = True
        logger.info(f"Created new conversation {conversation_id} for user {user_id}")
    
    return conversation_id, is_new

async def get_conversation_history(
    conversation_id: str,
    conversation_repository,
    limit: int = MAX_HISTORY_MESSAGES
) -> List[Message]:
    """
    Get the conversation history.
    
    Args:
        conversation_id: The ID of the conversation
        conversation_repository: Repository for retrieving messages
        limit: Maximum number of messages to retrieve
        
    Returns:
        A list of messages
    """
    return await conversation_repository.get_conversation_messages(
        conversation_id=UUID(conversation_id),
        limit=limit
    )

async def add_message_to_conversation(
    conversation_id: str,
    content: str,
    role: str,
    conversation_repository
) -> Message:
    """
    Add a message to a conversation.
    
    Args:
        conversation_id: The ID of the conversation
        content: The message content
        role: The message role (user or assistant)
        conversation_repository: Repository for adding messages
        
    Returns:
        The created message
    """
    return await conversation_repository.add_message(
        conversation_id=UUID(conversation_id),
        content=content,
        role=role
    )

def format_conversation_history(messages: List[Message], max_messages: int = 10) -> str:
    """
    Format conversation history for inclusion in prompts.
    
    Args:
        messages: List of messages
        max_messages: Maximum number of messages to include
        
    Returns:
        Formatted conversation history as a string
    """
    if not messages or len(messages) <= 1:
        return ""
    
    # Get the last few messages to keep context manageable, but exclude the most recent user message
    recent_history = messages[:-1]
    if len(recent_history) > max_messages:
        recent_history = recent_history[-max_messages:]
    
    # Format the conversation history
    history_pieces = []
    for msg in recent_history:
        role_prefix = "User" if msg.role == "user" else "Assistant"
        history_pieces.append(f"{role_prefix}: {msg.content}")
    
    return "\n".join(history_pieces)