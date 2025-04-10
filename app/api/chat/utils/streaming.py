"""
Streaming utilities for the chat API.

This module contains utility functions for streaming responses in the chat API.
"""

import logging
from typing import AsyncGenerator, Dict, Any
from sse_starlette.sse import EventSourceResponse
from uuid import UUID

# Logger
logger = logging.getLogger("app.api.chat.utils.streaming")

async def create_event_generator(
    conversation_id: str,
    stream_generator: AsyncGenerator[str, None],
    conversation_repository,
    sources: list = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Create an event generator for streaming responses.
    
    Args:
        conversation_id: The ID of the conversation
        stream_generator: The generator that yields tokens
        conversation_repository: Repository for storing messages
        sources: List of sources for citations
        
    Returns:
        An async generator that yields events for SSE
    """
    full_response = ""
    
    # First, send the conversation ID as a separate event with a specific event type
    yield {"event": "conversation_id", "data": conversation_id}
    
    # Stream the response
    async for token in stream_generator:
        full_response += token
        yield token
    
    # Add assistant message to conversation
    assistant_message = await conversation_repository.add_message(
        conversation_id=UUID(conversation_id),
        content=full_response,
        role="assistant"
    )
    
    # Add citations if any
    if sources:
        for source in sources:
            await conversation_repository.add_citation(
                message_id=assistant_message.id,
                document_id=UUID(source.document_id) if hasattr(source, "document_id") else None,
                chunk_id=UUID(source.chunk_id) if hasattr(source, "chunk_id") else None,
                relevance_score=source.relevance_score if hasattr(source, "relevance_score") else None,
                excerpt=source.excerpt if hasattr(source, "excerpt") else ""
            )

def create_streaming_response(event_generator: AsyncGenerator) -> EventSourceResponse:
    """
    Create a streaming response from an event generator.
    
    Args:
        event_generator: The generator that yields events
        
    Returns:
        An EventSourceResponse
    """
    return EventSourceResponse(event_generator)