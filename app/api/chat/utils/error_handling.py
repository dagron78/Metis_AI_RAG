"""
Error handling utilities for the chat API.

This module contains utility functions for handling errors in the chat API.
"""

import logging
import re
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.chat import ChatResponse

# Logger
logger = logging.getLogger("app.api.chat.utils.error_handling")

async def handle_chat_error(
    e: Exception,
    conversation_id: Optional[str] = None,
    conversation_repository = None
) -> ChatResponse:
    """
    Handle errors in chat API endpoints.
    
    Args:
        e: The exception that was raised
        conversation_id: The ID of the conversation
        conversation_repository: Repository for retrieving messages
        
    Returns:
        A ChatResponse with an error message
    """
    logger.error(f"Error generating chat response: {str(e)}")
    
    # Create a user-friendly error message
    error_message = "Sorry, there was an error processing your request."
    
    # Check if it's a future date query
    if conversation_id and conversation_repository:
        try:
            conversation_uuid = UUID(conversation_id)
            conversation = await conversation_repository.get_by_id(conversation_uuid)
            if conversation:
                # Get the last user message
                last_message = await conversation_repository.get_last_user_message(conversation_uuid)
                if last_message:
                    user_query = last_message.content.lower()
                    
                    # Check for future year patterns
                    current_year = datetime.now().year
                    year_match = re.search(r'\b(20\d\d|19\d\d)\b', user_query)
                    
                    if year_match and int(year_match.group(1)) > current_year:
                        error_message = f"I cannot provide information about events in {year_match.group(1)} as it's in the future. The current year is {current_year}."
                    elif re.search(r'what will happen|what is going to happen|predict the future|future events|in the future', user_query):
                        error_message = "I cannot predict future events or provide information about what will happen in the future."
        except (ValueError, Exception) as e:
            logger.error(f"Error checking for future date query: {str(e)}")
    
    # Return a 200 response with the error message instead of raising an exception
    # This allows the frontend to display the message properly
    return ChatResponse(
        message=error_message,
        conversation_id=conversation_id,
        citations=None
    )

def create_error_response(message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        message: The error message
        conversation_id: The ID of the conversation
        
    Returns:
        A dictionary with the error response
    """
    return {
        "error": True,
        "message": message,
        "conversation_id": conversation_id
    }