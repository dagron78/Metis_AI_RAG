import logging
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Depends, Response, Query, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import (
    ChatQuery,
    ChatResponse,
    Conversation,
    Message,
    Citation
)
from app.rag.rag_engine import RAGEngine
from app.rag.agents.langgraph_rag_agent import LangGraphRAGAgent
from app.rag.agents.enhanced_langgraph_rag_agent import EnhancedLangGraphRAGAgent
from app.utils.text_utils import extract_citations
from app.core.config import DEFAULT_MODEL, USE_LANGGRAPH_RAG, USE_ENHANCED_LANGGRAPH_RAG
from app.db.dependencies import get_db, get_conversation_repository
from app.db.repositories.conversation_repository import ConversationRepository

# Create router
router = APIRouter()

# Logger
logger = logging.getLogger("app.api.chat")

# RAG engine instance
rag_engine = RAGEngine()

# LangGraph RAG Agent instances (conditional on configuration)
langgraph_rag_agent = LangGraphRAGAgent() if USE_LANGGRAPH_RAG else None
enhanced_langgraph_rag_agent = EnhancedLangGraphRAGAgent() if USE_LANGGRAPH_RAG and USE_ENHANCED_LANGGRAPH_RAG else None

if USE_LANGGRAPH_RAG:
    logger.info("LangGraph RAG Agent is enabled")
    if USE_ENHANCED_LANGGRAPH_RAG:
        logger.info("Enhanced LangGraph RAG Agent is enabled")
    else:
        logger.info("Enhanced LangGraph RAG Agent is disabled")
else:
    logger.info("LangGraph RAG Agents are disabled")

# Maximum number of messages to include in conversation history
MAX_HISTORY_MESSAGES = 25

@router.post("/query", response_model=ChatResponse)
async def query_chat(
    query: ChatQuery, 
    request: Request,
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
):
    """
    Send a chat query and get a response
    """
    try:
        # Get or create conversation
        conversation_id = query.conversation_id
        user_id = query.user_id
        
        if conversation_id:
            # Try to get existing conversation
            try:
                conversation_uuid = UUID(conversation_id)
                conversation = conversation_repository.get_by_id(conversation_uuid)
                if not conversation:
                    # Create new conversation if not found
                    conversation = conversation_repository.create_conversation(user_id=user_id)
                    conversation_id = str(conversation.id)
                elif user_id and not conversation.user_id:
                    # Update user_id if provided and not already set
                    conversation = conversation_repository.update_conversation(
                        conversation_id=conversation_uuid,
                        user_id=user_id
                    )
            except ValueError:
                # Invalid UUID format, create new conversation
                conversation = conversation_repository.create_conversation(user_id=user_id)
                conversation_id = str(conversation.id)
        else:
            # Create new conversation
            conversation = conversation_repository.create_conversation(user_id=user_id)
            conversation_id = str(conversation.id)
        
        # Add user message to conversation
        user_message = conversation_repository.add_message(
            conversation_id=UUID(conversation_id),
            content=query.message,
            role="user"
        )
        
        # Get model name
        model = query.model or DEFAULT_MODEL
        
        # Query RAG engine
        if query.stream:
            # For streaming, return an EventSourceResponse
            logger.info(f"Streaming response for conversation {conversation_id}")
            
            async def event_generator():
                full_response = ""
                
                # Get conversation history
                conversation_messages = conversation_repository.get_conversation_messages(
                    conversation_id=UUID(conversation_id),
                    limit=MAX_HISTORY_MESSAGES
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
                    user_id=conversation.user_id
                )
                
                # Get sources (with safety check)
                sources = rag_response.get("sources")
                if sources is None:
                    logger.warning("No sources returned from RAG engine")
                    sources = []
                
                # Stream the response
                async for token in rag_response["stream"]:
                    full_response += token
                    yield token
                
                # Add assistant message to conversation
                assistant_message = conversation_repository.add_message(
                    conversation_id=UUID(conversation_id),
                    content=full_response,
                    role="assistant"
                )
                
                # Add citations if any
                if sources:
                    for source in sources:
                        conversation_repository.add_citation(
                            message_id=assistant_message.id,
                            document_id=UUID(source.get("document_id")) if source.get("document_id") else None,
                            chunk_id=UUID(source.get("chunk_id")) if source.get("chunk_id") else None,
                            relevance_score=source.get("relevance_score"),
                            excerpt=source.get("excerpt", "")
                        )
            
            return EventSourceResponse(event_generator())
        else:
            # For non-streaming, return the complete response
            logger.info(f"Generating response for conversation {conversation_id}")
            
            # Get conversation history
            conversation_messages = conversation_repository.get_conversation_messages(
                conversation_id=UUID(conversation_id),
                limit=MAX_HISTORY_MESSAGES
            )
            
            # Extract metadata filters if provided
            metadata_filters = query.metadata_filters if hasattr(query, 'metadata_filters') else None
            
            # Get RAG response
            rag_response = await rag_engine.query(
                query=query.message,
                model=model,
                use_rag=query.use_rag,
                stream=False,
                model_parameters=query.model_parameters,
                conversation_history=conversation_messages,
                metadata_filters=metadata_filters,
                user_id=conversation.user_id
            )
            
            # Get response and sources
            response_text = rag_response.get("answer", "")
            sources = rag_response.get("sources")
            if sources is None:
                logger.warning("No sources returned from RAG engine")
                sources = []
            
            # Add assistant message to conversation
            assistant_message = conversation_repository.add_message(
                conversation_id=UUID(conversation_id),
                content=response_text,
                role="assistant"
            )
            
            # Add citations if any
            if sources:
                for source in sources:
                    conversation_repository.add_citation(
                        message_id=assistant_message.id,
                        document_id=UUID(source.get("document_id")) if source.get("document_id") else None,
                        chunk_id=UUID(source.get("chunk_id")) if source.get("chunk_id") else None,
                        relevance_score=source.get("relevance_score"),
                        excerpt=source.get("excerpt", "")
                    )
            
            # Return response
            return ChatResponse(
                message=response_text,
                conversation_id=conversation_id,
                citations=sources
            )
    except Exception as e:
        logger.error(f"Error generating chat response: {str(e)}")
        
        # Create a user-friendly error message
        error_message = "Sorry, there was an error processing your request."
        
        # Check if it's a future date query
        if "conversation_id" in locals() and conversation_id:
            try:
                conversation_uuid = UUID(conversation_id)
                conversation = conversation_repository.get_by_id(conversation_uuid)
                if conversation:
                    # Get the last user message
                    last_message = conversation_repository.get_last_user_message(conversation_uuid)
                    if last_message:
                        user_query = last_message.content.lower()
                        
                        # Check for future year patterns
                        import re
                        current_year = 2025  # Hardcoded for now, could use datetime.now().year
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
            conversation_id=conversation_id if "conversation_id" in locals() else None,
            citations=None
        )

@router.get("/history")
async def get_history(
    conversation_id: UUID,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
):
    """
    Get conversation history with pagination
    """
    conversation = conversation_repository.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    # Get messages with pagination
    messages = conversation_repository.get_conversation_messages(
        conversation_id=conversation_id,
        skip=skip,
        limit=limit
    )
    
    # Get total message count
    total_messages = conversation.message_count
    
    return {
        "id": str(conversation.id),
        "user_id": conversation.user_id,
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

@router.post("/save")
async def save_conversation(
    conversation_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
):
    """
    Save a conversation (mark as saved in metadata)
    """
    conversation = conversation_repository.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    # Update metadata to mark as saved
    metadata = conversation.metadata or {}
    metadata["saved"] = True
    
    # Update conversation
    updated_conversation = conversation_repository.update_conversation(
        conversation_id=conversation_id,
        metadata=metadata
    )
    
    return {"success": True, "message": f"Conversation {conversation_id} saved"}

@router.delete("/clear")
async def clear_conversation(
    request: Request,
    conversation_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
):
    """
    Clear a conversation or all conversations
    """
    if conversation_id:
        conversation = conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        # Delete specific conversation
        conversation_repository.delete(conversation_id)
        return {"success": True, "message": f"Conversation {conversation_id} cleared"}
    else:
        # Delete all conversations
        # Note: This is a dangerous operation and might need additional authorization
        # In a real application, you might want to limit this to admin users
        conversation_repository.delete_all()
        return {"success": True, "message": "All conversations cleared"}

@router.post("/langgraph_rag", response_model=ChatResponse)
async def langgraph_query_chat(
    query: ChatQuery,
    request: Request,
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
):
    """
    Send a chat query to the LangGraph RAG Agent and get a response
    """
    if not USE_LANGGRAPH_RAG or not langgraph_rag_agent:
        raise HTTPException(status_code=400, detail="LangGraph RAG Agent is not enabled")
    
    try:
        # Get or create conversation
        conversation_id = query.conversation_id
        user_id = query.user_id
        
        if conversation_id:
            # Try to get existing conversation
            try:
                conversation_uuid = UUID(conversation_id)
                conversation = conversation_repository.get_by_id(conversation_uuid)
                if not conversation:
                    # Create new conversation if not found
                    conversation = conversation_repository.create_conversation(user_id=user_id)
                    conversation_id = str(conversation.id)
                elif user_id and not conversation.user_id:
                    # Update user_id if provided and not already set
                    conversation = conversation_repository.update_conversation(
                        conversation_id=conversation_uuid,
                        user_id=user_id
                    )
            except ValueError:
                # Invalid UUID format, create new conversation
                conversation = conversation_repository.create_conversation(user_id=user_id)
                conversation_id = str(conversation.id)
        else:
            # Create new conversation
            conversation = conversation_repository.create_conversation(user_id=user_id)
            conversation_id = str(conversation.id)
        
        # Add user message to conversation
        user_message = conversation_repository.add_message(
            conversation_id=UUID(conversation_id),
            content=query.message,
            role="user"
        )
        
        # Get model name
        model = query.model or DEFAULT_MODEL
        
        # Format conversation history
        conversation_context = None
        messages = conversation_repository.get_conversation_messages(
            conversation_id=UUID(conversation_id),
            limit=6  # Get 6 messages to exclude the current one
        )
        
        if len(messages) > 1:  # Only include history if there's more than just the current message
            # Get the last few messages (up to 5) to keep context manageable, but exclude the most recent user message
            recent_history = messages[:-1]
            if len(recent_history) > 5:
                recent_history = recent_history[-5:]
            
            # Format the conversation history
            history_pieces = []
            for msg in recent_history:
                role_prefix = "User" if msg.role == "user" else "Assistant"
                history_pieces.append(f"{role_prefix}: {msg.content}")
            
            conversation_context = "\n".join(history_pieces)
            logger.info(f"Including conversation history with {len(recent_history)} messages")
        else:
            logger.info("No previous conversation history to include")
        
        # Extract metadata filters if provided
        metadata_filters = query.metadata_filters if hasattr(query, 'metadata_filters') else None
        
        # Query LangGraph RAG Agent
        if query.stream:
            # For streaming, return an EventSourceResponse
            logger.info(f"Streaming response for conversation {conversation_id} using LangGraph RAG Agent")
            
            async def event_generator():
                full_response = ""
                
                # Get LangGraph RAG response
                langgraph_response = await langgraph_rag_agent.query(
                    query=query.message,
                    model=model,
                    system_prompt=None,  # Use default system prompt
                    stream=True,
                    model_parameters=query.model_parameters,
                    conversation_context=conversation_context,
                    metadata_filters=metadata_filters,
                    user_id=user_id,
                    use_rag=query.use_rag
                )
                
                # Get sources (with safety check)
                sources = langgraph_response.get("sources")
                if sources is None:
                    logger.warning("No sources returned from LangGraph RAG Agent")
                    sources = []
                
                # Stream the response
                async for token in langgraph_response["stream"]:
                    full_response += token
                    yield token
                
                # Add assistant message to conversation
                assistant_message = conversation_repository.add_message(
                    conversation_id=UUID(conversation_id),
                    content=full_response,
                    role="assistant"
                )
                
                # Add citations if any
                if sources:
                    for source in sources:
                        conversation_repository.add_citation(
                            message_id=assistant_message.id,
                            document_id=UUID(source.get("document_id")) if source.get("document_id") else None,
                            chunk_id=UUID(source.get("chunk_id")) if source.get("chunk_id") else None,
                            relevance_score=source.get("relevance_score"),
                            excerpt=source.get("excerpt", "")
                        )
            
            return EventSourceResponse(event_generator())
        else:
            # For non-streaming, return the complete response
            logger.info(f"Generating response for conversation {conversation_id} using LangGraph RAG Agent")
            
            # Get LangGraph RAG response
            langgraph_response = await langgraph_rag_agent.query(
                query=query.message,
                model=model,
                system_prompt=None,  # Use default system prompt
                stream=False,
                model_parameters=query.model_parameters,
                conversation_context=conversation_context,
                metadata_filters=metadata_filters,
                user_id=user_id,
                use_rag=query.use_rag
            )
            
            # Get response and sources
            response_text = langgraph_response.get("answer", "")
            sources = langgraph_response.get("sources")
            if sources is None:
                logger.warning("No sources returned from LangGraph RAG Agent")
                sources = []
            
            # Add assistant message to conversation
            assistant_message = conversation_repository.add_message(
                conversation_id=UUID(conversation_id),
                content=response_text,
                role="assistant"
            )
            
            # Add citations if any
            if sources:
                for source in sources:
                    conversation_repository.add_citation(
                        message_id=assistant_message.id,
                        document_id=UUID(source.get("document_id")) if source.get("document_id") else None,
                        chunk_id=UUID(source.get("chunk_id")) if source.get("chunk_id") else None,
                        relevance_score=source.get("relevance_score"),
                        excerpt=source.get("excerpt", "")
                    )
            
            # Return response
            return ChatResponse(
                message=response_text,
                conversation_id=conversation_id,
                citations=sources
            )
    except Exception as e:
        logger.error(f"Error generating chat response with LangGraph RAG Agent: {str(e)}")
        
        # Create a user-friendly error message
        error_message = "Sorry, there was an error processing your request with the LangGraph RAG Agent."
        
        # Return a 200 response with the error message instead of raising an exception
        return ChatResponse(
            message=error_message,
            conversation_id=conversation_id if "conversation_id" in locals() else None,
            citations=None
        )

@router.post("/enhanced_langgraph_query", response_model=ChatResponse)
async def enhanced_langgraph_query_chat(
    query: ChatQuery,
    request: Request,
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
):
    """
    Send a chat query to the Enhanced LangGraph RAG Agent and get a response
    
    This endpoint uses the enhanced LangGraph RAG agent that integrates:
    - QueryPlanner for creating execution plans
    - PlanExecutor for executing multi-step plans
    - Retrieval Judge for query refinement and context optimization
    """
    if not USE_LANGGRAPH_RAG or not USE_ENHANCED_LANGGRAPH_RAG or not enhanced_langgraph_rag_agent:
        raise HTTPException(status_code=400, detail="Enhanced LangGraph RAG Agent is not enabled")
    
    try:
        # Get or create conversation
        conversation_id = query.conversation_id
        user_id = query.user_id
        
        if conversation_id:
            # Try to get existing conversation
            try:
                conversation_uuid = UUID(conversation_id)
                conversation = conversation_repository.get_by_id(conversation_uuid)
                if not conversation:
                    # Create new conversation if not found
                    conversation = conversation_repository.create_conversation(user_id=user_id)
                    conversation_id = str(conversation.id)
                elif user_id and not conversation.user_id:
                    # Update user_id if provided and not already set
                    conversation = conversation_repository.update_conversation(
                        conversation_id=conversation_uuid,
                        user_id=user_id
                    )
            except ValueError:
                # Invalid UUID format, create new conversation
                conversation = conversation_repository.create_conversation(user_id=user_id)
                conversation_id = str(conversation.id)
        else:
            # Create new conversation
            conversation = conversation_repository.create_conversation(user_id=user_id)
            conversation_id = str(conversation.id)
        
        # Add user message to conversation
        user_message = conversation_repository.add_message(
            conversation_id=UUID(conversation_id),
            content=query.message,
            role="user"
        )
        
        # Get model name
        model = query.model or DEFAULT_MODEL
        
        # Format conversation history
        conversation_context = None
        messages = conversation_repository.get_conversation_messages(
            conversation_id=UUID(conversation_id),
            limit=6  # Get 6 messages to exclude the current one
        )
        
        if len(messages) > 1:  # Only include history if there's more than just the current message
            # Get the last few messages (up to 5) to keep context manageable, but exclude the most recent user message
            recent_history = messages[:-1]
            if len(recent_history) > 5:
                recent_history = recent_history[-5:]
            
            # Format the conversation history
            history_pieces = []
            for msg in recent_history:
                role_prefix = "User" if msg.role == "user" else "Assistant"
                history_pieces.append(f"{role_prefix}: {msg.content}")
            
            conversation_context = "\n".join(history_pieces)
            logger.info(f"Including conversation history with {len(recent_history)} messages")
        else:
            logger.info("No previous conversation history to include")
        
        # Extract metadata filters if provided
        metadata_filters = query.metadata_filters if hasattr(query, 'metadata_filters') else None
        
        # Query Enhanced LangGraph RAG Agent
        if query.stream:
            # For streaming, return an EventSourceResponse
            logger.info(f"Streaming response for conversation {conversation_id} using Enhanced LangGraph RAG Agent")
            
            async def event_generator():
                full_response = ""
                
                # Get Enhanced LangGraph RAG response
                enhanced_response = await enhanced_langgraph_rag_agent.query(
                    query=query.message,
                    model=model,
                    system_prompt=None,  # Use default system prompt
                    stream=True,
                    model_parameters=query.model_parameters,
                    conversation_context=conversation_context,
                    metadata_filters=metadata_filters,
                    user_id=user_id,
                    use_rag=query.use_rag
                )
                
                # Get sources (with safety check)
                sources = enhanced_response.get("sources")
                if sources is None:
                    logger.warning("No sources returned from Enhanced LangGraph RAG Agent")
                    sources = []
                
                # Stream the response
                async for token in enhanced_response["stream"]:
                    full_response += token
                    yield token
                
                # Add assistant message to conversation
                assistant_message = conversation_repository.add_message(
                    conversation_id=UUID(conversation_id),
                    content=full_response,
                    role="assistant"
                )
                
                # Add citations if any
                if sources:
                    for source in sources:
                        conversation_repository.add_citation(
                            message_id=assistant_message.id,
                            document_id=UUID(source.get("document_id")) if source.get("document_id") else None,
                            chunk_id=UUID(source.get("chunk_id")) if source.get("chunk_id") else None,
                            relevance_score=source.get("relevance_score"),
                            excerpt=source.get("excerpt", "")
                        )
            
            return EventSourceResponse(event_generator())
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
                user_id=user_id,
                use_rag=query.use_rag
            )
            
            # Get response and sources
            response_text = enhanced_response.get("answer", "")
            sources = enhanced_response.get("sources")
            execution_trace = enhanced_response.get("execution_trace")
            
            if sources is None:
                logger.warning("No sources returned from Enhanced LangGraph RAG Agent")
                sources = []
            
            # Add assistant message to conversation
            assistant_message = conversation_repository.add_message(
                conversation_id=UUID(conversation_id),
                content=response_text,
                role="assistant"
            )
            
            # Add citations if any
            if sources:
                for source in sources:
                    conversation_repository.add_citation(
                        message_id=assistant_message.id,
                        document_id=UUID(source.get("document_id")) if source.get("document_id") else None,
                        chunk_id=UUID(source.get("chunk_id")) if source.get("chunk_id") else None,
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
        logger.error(f"Error generating chat response with Enhanced LangGraph RAG Agent: {str(e)}")
        
        # Create a user-friendly error message
        error_message = "Sorry, there was an error processing your request with the Enhanced LangGraph RAG Agent."
        
        # Return a 200 response with the error message instead of raising an exception
        return ChatResponse(
            message=error_message,
            conversation_id=conversation_id if "conversation_id" in locals() else None,
            citations=None
        )

@router.get("/list")
async def list_conversations(
    request: Request,
    user_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
):
    """
    List conversations with optional filtering by user_id and pagination
    """
    # Get conversations with pagination
    conversations = conversation_repository.get_conversations(
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    
    # Get total count
    total_count = conversation_repository.count_conversations(user_id=user_id)
    
    return {
        "conversations": [
            {
                "id": str(conv.id),
                "user_id": conv.user_id,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": conv.message_count,
                "metadata": conv.metadata
            }
            for conv in conversations
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total_count
        }
    }