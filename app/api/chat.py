import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Response
from sse_starlette.sse import EventSourceResponse

from app.models.chat import (
    ChatQuery,
    ChatResponse,
    Conversation,
    Message,
    Citation
)
from app.rag.rag_engine import RAGEngine
from app.rag.agents.langgraph_rag_agent import LangGraphRAGAgent
from app.utils.text_utils import extract_citations
from app.core.config import DEFAULT_MODEL, USE_LANGGRAPH_RAG

# Create router
router = APIRouter()

# In-memory conversation store (replace with database in production)
conversations: Dict[str, Conversation] = {}

# Logger
logger = logging.getLogger("app.api.chat")

# RAG engine instance
rag_engine = RAGEngine()

# LangGraph RAG Agent instance
langgraph_rag_agent = LangGraphRAGAgent() if USE_LANGGRAPH_RAG else None
if USE_LANGGRAPH_RAG:
    logger.info("LangGraph RAG Agent is enabled")
else:
    logger.info("LangGraph RAG Agent is disabled")

# Maximum number of messages to include in conversation history
MAX_HISTORY_MESSAGES = 25

@router.post("/query", response_model=ChatResponse)
async def query_chat(query: ChatQuery):
    """
    Send a chat query and get a response
    """
    try:
        # Get or create conversation
        conversation_id = query.conversation_id
        if conversation_id and conversation_id in conversations:
            conversation = conversations[conversation_id]
        else:
            conversation = Conversation()
            conversations[conversation.id] = conversation
            conversation_id = conversation.id
        
        # Add user message to conversation
        user_message = Message(content=query.message, role="user")
        conversation.add_message(user_message)
        
        # Get model name
        model = query.model or DEFAULT_MODEL
        
        # Query RAG engine
        if query.stream:
            # For streaming, return an EventSourceResponse
            logger.info(f"Streaming response for conversation {conversation_id}")
            
            async def event_generator():
                full_response = ""
                
                # Get conversation history
                conversation_history = conversation.messages[-MAX_HISTORY_MESSAGES:] if len(conversation.messages) > 0 else []
                
                # Extract metadata filters if provided
                metadata_filters = query.metadata_filters if hasattr(query, 'metadata_filters') else None
                
                # Get RAG response
                rag_response = await rag_engine.query(
                    query=query.message,
                    model=model,
                    use_rag=query.use_rag,
                    stream=True,
                    model_parameters=query.model_parameters,
                    conversation_history=conversation_history,
                    metadata_filters=metadata_filters
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
                assistant_message = Message(
                    content=full_response,
                    role="assistant",
                    citations=sources
                )
                conversation.add_message(assistant_message)
            
            return EventSourceResponse(event_generator())
        else:
            # For non-streaming, return the complete response
            logger.info(f"Generating response for conversation {conversation_id}")
            
            # Get conversation history
            conversation_history = conversation.messages[-MAX_HISTORY_MESSAGES:] if len(conversation.messages) > 0 else []
            
            # Extract metadata filters if provided
            metadata_filters = query.metadata_filters if hasattr(query, 'metadata_filters') else None
            
            # Get RAG response
            rag_response = await rag_engine.query(
                query=query.message,
                model=model,
                use_rag=query.use_rag,
                stream=False,
                model_parameters=query.model_parameters,
                conversation_history=conversation_history,
                metadata_filters=metadata_filters
            )
            
            # Get response and sources
            response_text = rag_response.get("answer", "")
            sources = rag_response.get("sources")
            if sources is None:
                logger.warning("No sources returned from RAG engine")
                sources = []
            
            # Add assistant message to conversation
            assistant_message = Message(
                content=response_text,
                role="assistant",
                citations=sources
            )
            conversation.add_message(assistant_message)
            
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
        if "conversation_id" in locals() and conversation_id in conversations:
            conversation = conversations[conversation_id]
            if conversation.messages and conversation.messages[-1].role == "user":
                user_query = conversation.messages[-1].content.lower()
                
                # Check for future year patterns
                import re
                current_year = 2025  # Hardcoded for now, could use datetime.now().year
                year_match = re.search(r'\b(20\d\d|19\d\d)\b', user_query)
                
                if year_match and int(year_match.group(1)) > current_year:
                    error_message = f"I cannot provide information about events in {year_match.group(1)} as it's in the future. The current year is {current_year}."
                elif re.search(r'what will happen|what is going to happen|predict the future|future events|in the future', user_query):
                    error_message = "I cannot predict future events or provide information about what will happen in the future."
        
        # Return a 200 response with the error message instead of raising an exception
        # This allows the frontend to display the message properly
        return ChatResponse(
            message=error_message,
            conversation_id=conversation_id if "conversation_id" in locals() else None,
            citations=None
        )

@router.get("/history")
async def get_history(conversation_id: str):
    """
    Get conversation history
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    return conversations[conversation_id]

@router.post("/save")
async def save_conversation(conversation_id: str):
    """
    Save a conversation
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    # In a real application, this would save to a database
    # For now, we just return success
    return {"success": True, "message": f"Conversation {conversation_id} saved"}

@router.delete("/clear")
async def clear_conversation(conversation_id: Optional[str] = None):
    """
    Clear a conversation or all conversations
    """
    if conversation_id:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        # Clear specific conversation
        del conversations[conversation_id]
        return {"success": True, "message": f"Conversation {conversation_id} cleared"}
    else:
        # Clear all conversations
        conversations.clear()
        return {"success": True, "message": "All conversations cleared"}

@router.post("/langgraph_query", response_model=ChatResponse)
async def langgraph_query_chat(query: ChatQuery):
    """
    Send a chat query to the LangGraph RAG Agent and get a response
    """
    if not USE_LANGGRAPH_RAG or not langgraph_rag_agent:
        raise HTTPException(status_code=400, detail="LangGraph RAG Agent is not enabled")
    
    try:
        # Get or create conversation
        conversation_id = query.conversation_id
        if conversation_id and conversation_id in conversations:
            conversation = conversations[conversation_id]
        else:
            conversation = Conversation()
            conversations[conversation.id] = conversation
            conversation_id = conversation.id
        
        # Add user message to conversation
        user_message = Message(content=query.message, role="user")
        conversation.add_message(user_message)
        
        # Get model name
        model = query.model or DEFAULT_MODEL
        
        # Format conversation history
        conversation_context = None
        if len(conversation.messages) > 1:  # Only include history if there's more than just the current message
            # Get the last few messages (up to 5) to keep context manageable, but exclude the most recent user message
            recent_history = conversation.messages[:-1]
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
                    metadata_filters=metadata_filters
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
                assistant_message = Message(
                    content=full_response,
                    role="assistant",
                    citations=sources
                )
                conversation.add_message(assistant_message)
            
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
                metadata_filters=metadata_filters
            )
            
            # Get response and sources
            response_text = langgraph_response.get("answer", "")
            sources = langgraph_response.get("sources")
            if sources is None:
                logger.warning("No sources returned from LangGraph RAG Agent")
                sources = []
            
            # Add assistant message to conversation
            assistant_message = Message(
                content=response_text,
                role="assistant",
                citations=sources
            )
            conversation.add_message(assistant_message)
            
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