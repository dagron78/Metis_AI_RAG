"""
Enhanced LangGraph RAG chat handler.

This module contains the handler for the Enhanced LangGraph RAG chat endpoint.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.models.chat import ChatQuery, ChatResponse
from app.models.user import User
from app.rag.agents.enhanced_langgraph_rag_agent import EnhancedLangGraphRAGAgent
from app.db.dependencies import get_db, get_conversation_repository
from app.db.repositories.conversation_repository import ConversationRepository
from app.core.security import get_current_active_user
from app.core.config import DEFAULT_MODEL, USE_LANGGRAPH_RAG, USE_ENHANCED_LANGGRAPH_RAG

from app.api.chat.utils.streaming import create_event_generator, create_streaming_response
from app.api.chat.utils.error_handling import handle_chat_error
from app.api.chat.utils.conversation_helpers import (
    get_or_create_conversation,
    get_conversation_history,
    add_message_to_conversation,
    format_conversation_history
)

# Logger
logger = logging.getLogger("app.api.chat.handlers.enhanced_langgraph")

# Enhanced LangGraph RAG Agent instance (conditional on configuration)
enhanced_langgraph_rag_agent = EnhancedLangGraphRAGAgent() if USE_LANGGRAPH_RAG and USE_ENHANCED_LANGGRAPH_RAG else None

async def enhanced_langgraph_query_chat(
    query: ChatQuery,
    request: Request,
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a chat query to the Enhanced LangGraph RAG Agent and get a response
    """
    if not USE_LANGGRAPH_RAG or not USE_ENHANCED_LANGGRAPH_RAG or not enhanced_langgraph_rag_agent:
        raise HTTPException(status_code=400, detail="Enhanced LangGraph RAG Agent is not enabled")
    
    try:
        # Get or create conversation
        conversation_id, is_new = await get_or_create_conversation(
            query.conversation_id,
            conversation_repository,
            str(current_user.id)
        )
        
        # Add user message to conversation
        user_message = await add_message_to_conversation(
            conversation_id,
            query.message,
            "user",
            conversation_repository
        )
        
        # Get model name
        model = query.model or DEFAULT_MODEL
        
        # Format conversation history
        conversation_context = None
        messages = await get_conversation_history(
            conversation_id,
            conversation_repository,
            limit=6  # Get 6 messages to exclude the current one
        )
        
        if len(messages) > 1:  # Only include history if there's more than just the current message
            # Format the conversation history
            conversation_context = format_conversation_history(messages, max_messages=5)
            logger.info(f"Including conversation history with {len(messages)-1} messages")
        else:
            logger.info("No previous conversation history to include")
        
        # Extract metadata filters if provided
        metadata_filters = query.metadata_filters if hasattr(query, 'metadata_filters') else None
        
        # Query Enhanced LangGraph RAG Agent
        if query.stream:
            # For streaming, return an EventSourceResponse
            logger.info(f"Streaming response for conversation {conversation_id} using Enhanced LangGraph RAG Agent")
            
            # Get Enhanced LangGraph RAG response
            enhanced_response = await enhanced_langgraph_rag_agent.query(
                query=query.message,
                model=model,
                system_prompt=None,  # Use default system prompt
                stream=True,
                model_parameters=query.model_parameters,
                conversation_context=conversation_context,
                metadata_filters=metadata_filters,
                user_id=current_user.id,
                use_rag=query.use_rag
            )
            
            # Get sources (with safety check)
            sources = enhanced_response.get("sources", [])
            
            # Create event generator
            event_generator = create_event_generator(
                conversation_id,
                enhanced_response["stream"],
                conversation_repository,
                sources
            )
            
            # Return streaming response
            return create_streaming_response(event_generator)
        else:
            # For non-streaming, return the complete response
            logger.info(f"Generating response for conversation {conversation_id} using Enhanced LangGraph RAG Agent")
            
            # Get Enhanced LangGraph RAG response
            enhanced_response = await enhanced_langgraph_rag_agent.query(
                query=query.message,
                model=model,
                system_prompt=None,  # Use default system prompt
                stream=False,
                model_parameters=query.model_parameters,
                conversation_context=conversation_context,
                metadata_filters=metadata_filters,
                user_id=current_user.id,
                use_rag=query.use_rag
            )
            
            # Get response and sources
            response_text = enhanced_response.get("answer", "")
            sources = enhanced_response.get("sources", [])
            execution_trace = enhanced_response.get("execution_trace", [])
            
            # Add assistant message to conversation
            assistant_message = await add_message_to_conversation(
                conversation_id,
                response_text,
                "assistant",
                conversation_repository
            )
            
            # Add citations if any
            if sources:
                for source in sources:
                    await conversation_repository.add_citation(
                        message_id=assistant_message.id,
                        document_id=source.get("document_id"),
                        chunk_id=source.get("chunk_id"),
                        relevance_score=source.get("relevance_score"),
                        excerpt=source.get("excerpt", "")
                    )
            
            # Return response
            return ChatResponse(
                message=response_text,
                conversation_id=conversation_id,
                citations=sources,
                execution_trace=execution_trace
            )
    except Exception as e:
        # Handle errors
        return await handle_chat_error(e, conversation_id, conversation_repository)