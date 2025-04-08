"""
Conversation management handlers.

This module contains handlers for conversation management endpoints.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.db.dependencies import get_db, get_conversation_repository
from app.db.repositories.conversation_repository import ConversationRepository
from app.core.security import get_current_active_user

# Logger
logger = logging.getLogger("app.api.chat.handlers.conversation")

async def get_history(
    conversation_id: UUID,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get conversation history with pagination
    """
    # The repository will handle permission checks based on user_id
    conversation = await conversation_repository.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found or you don't have permission to access it")
    
    # Note: The repository's get_by_id method already checks permissions
    # If the conversation doesn't belong to the user, it will return None
    
    # Get messages with pagination
    messages = await conversation_repository.get_conversation_messages(
        conversation_id=conversation_id,
        skip=skip,
        limit=limit
    )
    
    # Get total message count
    total_messages = conversation.message_count
    
    return {
        "id": str(conversation.id),
        "user_id": str(current_user.id),  # Always return the current user's ID
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": messages,
        "total_messages": total_messages,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total_messages
        }
    }

async def save_conversation(
    conversation_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Save a conversation (mark as saved in metadata)
    """
    # The repository will handle permission checks based on user_id
    conversation = await conversation_repository.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    # Note: The repository's get_by_id method already checks permissions
    # If the conversation doesn't belong to the user, it will return None
    
    # Update metadata to mark as saved
    metadata = conversation.conv_metadata or {}
    metadata["saved"] = True
    
    # Update conversation
    updated_conversation = await conversation_repository.update_conversation(
        conversation_id=conversation_id,
        metadata=metadata
    )
    
    return {"success": True, "message": f"Conversation {conversation_id} saved"}

async def clear_conversation(
    request: Request,
    conversation_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear a conversation from the UI (does not delete from database)
    This endpoint is used by the frontend to clear the chat display
    """
    # Simply return success - the actual clearing happens in the frontend
    if conversation_id:
        return {"success": True, "message": f"Conversation {conversation_id} cleared from display"}
    else:
        return {"success": True, "message": "All conversations cleared from display"}

async def list_conversations(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    saved_only: bool = Query(False, description="Only return saved conversations"),
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    List conversations for the current user
    """
    # Get conversations
    conversations = await conversation_repository.get_conversations(
        skip=skip,
        limit=limit
    )
    
    # Filter saved conversations if requested
    if saved_only:
        conversations = [
            conv for conv in conversations 
            if conv.conv_metadata and conv.conv_metadata.get("saved", False)
        ]
    
    # Get total count
    total_count = await conversation_repository.count_conversations()
    
    # Format response
    result = []
    for conv in conversations:
        # Get the first few messages for preview
        messages = await conversation_repository.get_conversation_messages(
            conversation_id=conv.id,
            limit=2
        )
        
        # Create preview from first message
        preview = ""
        if messages and len(messages) > 0:
            preview = messages[0].content[:100] + "..." if len(messages[0].content) > 100 else messages[0].content
        
        result.append({
            "id": str(conv.id),
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": conv.message_count,
            "preview": preview,
            "saved": conv.conv_metadata.get("saved", False) if conv.conv_metadata else False
        })
    
    return {
        "conversations": result,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total_count
        }
    }