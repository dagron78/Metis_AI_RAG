"""
Standard RAG chat handler.

This module contains the handler for the standard RAG chat endpoint.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import JSONResponse

from app.models.chat import ChatQuery, ChatResponse
from app.models.user import User
from app.rag.engine.rag_engine import RAGEngine
from app.db.dependencies import get_db, get_conversation_repository
from app.db.repositories.conversation_repository import ConversationRepository
from app.core.security import get_current_active_user
from app.core.config import DEFAULT_MODEL

from app.api.chat.utils.streaming import create_event_generator, create_streaming_response
from app.api.chat.utils.error_handling import handle_chat_error
from app.api.chat.utils.conversation_helpers import (
    get_or_create_conversation,
    get_conversation_history,
    add_message_to_conversation,
    MAX_HISTORY_MESSAGES
)

# Logger
logger = logging.getLogger("app.api.chat.handlers.standard")

# RAG engine instance
rag_engine = RAGEngine()

async def query_chat(
    query: ChatQuery,
    request: Request,
    debug_raw: bool = Query(False, description="Include raw LLM output in response for debugging"),
    raw_ollama_response: bool = Query(False, description="If true, return the raw response from Ollama, bypassing backend processing"),
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a chat query and get a response
    """
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
        
        # Query RAG engine
        if query.stream:
            # For streaming, return an EventSourceResponse
            logger.info(f"Streaming response for conversation {conversation_id}")
            
            # Get conversation history
            conversation_messages = await get_conversation_history(
                conversation_id,
                conversation_repository,
                MAX_HISTORY_MESSAGES
            )
            
            # Extract metadata filters if provided
            metadata_filters = query.metadata_filters if hasattr(query, 'metadata_filters') else None
            
            # Get RAG response
            rag_response = await rag_engine.query(
                query=query.message,
                model=model,
                use_rag=query.use_rag,
                stream=True,
                model_parameters=query.model_parameters,
                conversation_history=conversation_messages,
                metadata_filters=metadata_filters,
                user_id=current_user.id,
                conversation_id=conversation_id  # Explicitly pass conversation_id
            )
            
            # Get sources (with safety check)
            sources = rag_response.get("sources")
            if sources is None:
                logger.warning("No sources returned from RAG engine")
                sources = []
            
            # Create event generator
            event_generator = create_event_generator(
                conversation_id,
                rag_response["stream"],
                conversation_repository,
                sources
            )
            
            # Return streaming response
            return create_streaming_response(event_generator)
        else:
            # For non-streaming, return the complete response
            logger.info(f"Generating response for conversation {conversation_id}")
            
            # Get conversation history
            conversation_messages = await get_conversation_history(
                conversation_id,
                conversation_repository,
                MAX_HISTORY_MESSAGES
            )
            
            # Extract metadata filters if provided
            metadata_filters = query.metadata_filters if hasattr(query, 'metadata_filters') else None
            
            # Get RAG response
            # Create a warnings list to track non-critical issues
            warnings = []
            
            try:
                # Get RAG response - this is the core functionality
                rag_response = await rag_engine.query(
                    query=query.message,
                    model=model,
                    use_rag=query.use_rag,
                    stream=False,
                    model_parameters=query.model_parameters,
                    conversation_history=conversation_messages,
                    metadata_filters=metadata_filters,
                    user_id=current_user.id,
                    conversation_id=conversation_id,  # Explicitly pass conversation_id
                    capture_raw_output=debug_raw,  # Pass the debug flag to capture raw output
                    return_raw_ollama=raw_ollama_response  # Pass the raw Ollama response flag
                )
                
                # If raw_ollama_response is true, return the raw output directly
                if raw_ollama_response and "raw_output" in rag_response:
                    return JSONResponse(content={"raw_output": rag_response.get("raw_output", "Error: Raw output not captured.")})
                
                # Get response and sources
                response_text = rag_response.get("answer", "")
                sources = rag_response.get("sources")
                if sources is None:
                    logger.warning("No sources returned from RAG engine")
                    sources = []
                    warnings.append("No sources were returned for this query")
            except Exception as e:
                # If the core RAG functionality fails, we need to re-raise the exception
                logger.error(f"Critical error in RAG engine: {str(e)}")
                raise
            
            # Post-processing steps - these should not prevent returning a response
            # even if they fail
            
            # Step 1: Add assistant message to conversation
            try:
                assistant_message = await add_message_to_conversation(
                    conversation_id,
                    response_text,
                    "assistant",
                    conversation_repository
                )
            except Exception as e:
                logger.error(f"Error adding assistant message to conversation: {str(e)}")
                warnings.append("Failed to save this message to conversation history")
                # Create a dummy message ID for citations if needed
                assistant_message = type('obj', (object,), {'id': UUID('00000000-0000-0000-0000-000000000000')})
            
            # Step 2: Add citations if any
            if sources:
                try:
                    for source in sources:
                        await conversation_repository.add_citation(
                            message_id=assistant_message.id,
                            document_id=UUID(source.document_id) if hasattr(source, "document_id") else None,
                            chunk_id=UUID(source.chunk_id) if hasattr(source, "chunk_id") else None,
                            relevance_score=source.relevance_score if hasattr(source, "relevance_score") else None,
                            excerpt=source.excerpt if hasattr(source, "excerpt") else ""
                        )
                except Exception as e:
                    logger.error(f"Error adding citations to message: {str(e)}")
                    warnings.append("Failed to save citation information")
            
            # Get raw Ollama output if available and debug mode is enabled
            raw_ollama_output = rag_response.get("raw_ollama_output") if debug_raw else None
            
            # Log the final API response text for comparison
            query_id = conversation_id
            logger.debug(f"FINAL API RESPONSE TEXT (Query ID: {query_id}):\n```\n{response_text}\n```")
            
            # Return response with any warnings and raw output if requested
            return ChatResponse(
                message=response_text,
                conversation_id=conversation_id,
                citations=sources,
                warnings=warnings if warnings else None,
                raw_ollama_output=raw_ollama_output
            )
    except Exception as e:
        # Handle errors
        return await handle_chat_error(e, conversation_id, conversation_repository)