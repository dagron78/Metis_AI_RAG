"""
Memory-related handlers.

This module contains handlers for memory-related endpoints.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.db.dependencies import get_db, get_conversation_repository
from app.db.repositories.conversation_repository import ConversationRepository
from app.core.security import get_current_active_user
from app.rag.mem0_client import get_memory_diagnostics, get_conversation_history

# Logger
logger = logging.getLogger("app.api.chat.handlers.memory")

async def memory_diagnostics(
    request: Request,
    human_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get memory diagnostics for a user
    
    This endpoint is primarily for debugging and development purposes.
    It provides information about what the system remembers about a user.
    """
    # Only allow admin users to access this endpoint
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin users can access memory diagnostics")
    
    # Use the provided human_id or the current user's ID
    target_id = human_id or str(current_user.id)
    
    try:
        # Get memory diagnostics from Mem0
        memory_data = await get_memory_diagnostics(target_id)
        
        # Get conversation history from Mem0
        conversation_history = await get_conversation_history(target_id, limit=10)
        
        # Get conversation statistics from the database
        db_stats = await conversation_repository.get_conversation_statistics()
        
        # Combine all data
        result = {
            "user_id": target_id,
            "memory": memory_data,
            "recent_conversations": conversation_history,
            "database_statistics": db_stats
        }
        
        return result
    except Exception as e:
        logger.error(f"Error getting memory diagnostics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting memory diagnostics: {str(e)}")