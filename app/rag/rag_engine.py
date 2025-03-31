"""
RAG (Retrieval Augmented Generation) Engine
"""
import logging
import time
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from uuid import UUID

from app.core.config import DEFAULT_MODEL
from app.models.chat import Citation, Message
from app.rag.rag_engine_base import BaseRAGEngine
from app.rag.rag_retrieval import RetrievalMixin
from app.rag.rag_generation import GenerationMixin
from app.rag.mem0_client import store_message, get_conversation_history, store_document_interaction, get_user_preferences

logger = logging.getLogger("app.rag.rag_engine")

class RAGEngine(BaseRAGEngine, RetrievalMixin, GenerationMixin):
    """
    RAG (Retrieval Augmented Generation) Engine with security features
    
    This class combines the base RAGEngine with retrieval and generation functionality
    to provide a complete RAG solution with security features.
    """
    
    async def query(self,
                   query: str,
                   model: str = DEFAULT_MODEL,
                   use_rag: bool = True,
                   top_k: int = 10,
                   system_prompt: Optional[str] = None,
                   stream: bool = False,
                   model_parameters: Dict[str, Any] = None,
                   conversation_history: Optional[List[Message]] = None,
                   metadata_filters: Optional[Dict[str, Any]] = None,
                   user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the RAG engine with optional conversation history and metadata filtering
        
        Args:
            query: Query string
            model: Model to use
            use_rag: Whether to use RAG
            top_k: Number of results to return
            system_prompt: System prompt
            stream: Whether to stream the response
            model_parameters: Model parameters
            conversation_history: Conversation history
            metadata_filters: Metadata filters
            user_id: User ID for permission filtering
            
        Returns:
            Response dictionary
        """
        start_time = time.time()
        document_ids = []
        
        try:
            logger.info(f"RAG query: {query[:50]}...")
            
            # Get context from vector store if RAG is enabled
            context = ""
            sources = []
            
            # Generate a user_id if not provided
            if not user_id:
                user_id = f"session_{str(uuid.uuid4())[:8]}"
                logger.info(f"Generated session user_id: {user_id}")
            
            # Convert string user_id to UUID if needed
            user_uuid = None
            if user_id:
                try:
                    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
                except ValueError:
                    logger.warning(f"Invalid user_id format: {user_id}, using as string")
            
            # Integrate with Mem0 if available
            if self.mem0_client and user_id:
                # Store the user query in Mem0
                await store_message(user_id, "user", query)
                
                # Get user preferences if available
                user_prefs = await get_user_preferences(user_id)
                if user_prefs:
                    logger.info(f"Retrieved user preferences: {user_prefs}")
                    # Apply user preferences if available
                    if "preferred_model" in user_prefs and user_prefs["preferred_model"]:
                        model = user_prefs["preferred_model"]
                        logger.info(f"Using preferred model from user preferences: {model}")
            
            # Format conversation history if provided
            conversation_context = ""
            if conversation_history and len(conversation_history) > 1:  # Only include history if there's more than just the current message
                # Get the last few messages (up to 5) to keep context manageable, but exclude the most recent user message
                # which is the current query and shouldn't be treated as history
                recent_history = conversation_history[:-1]
                if len(recent_history) > 5:
                    recent_history = recent_history[-5:]
                
                # Format the conversation history
                history_pieces = []
                for msg in recent_history:
                    role_prefix = "User" if msg.role == "user" else "Assistant"
                    history_pieces.append(f"{role_prefix}: {msg.content}")
                
                conversation_context = "\n".join(history_pieces)
                logger.info(f"Including conversation history with {len(recent_history)} messages")
            elif self.mem0_client and user_id:
                # Try to get conversation history from Mem0 if not provided
                mem0_history = await get_conversation_history(user_id, limit=5)
                if mem0_history:
                    # Format the conversation history from Mem0
                    history_pieces = []
                    for msg in mem0_history:
                        role_prefix = "User" if msg["role"] == "user" else "Assistant"
                        history_pieces.append(f"{role_prefix}: {msg['content']}")
                    
                    conversation_context = "\n".join(history_pieces)
                    logger.info(f"Including conversation history from Mem0 with {len(mem0_history)} messages")
                else:
                    logger.info("No previous conversation history found in Mem0")
            else:
                logger.info("No previous conversation history to include")
            
            if use_rag:
                # Use enhanced retrieval if Retrieval Judge is enabled
                if self.retrieval_judge:
                    logger.info("Using enhanced retrieval with Retrieval Judge")
                    context, sources, document_ids = await self._enhanced_retrieval(
                        query=query,
                        conversation_context=conversation_context,
                        top_k=top_k,
                        metadata_filters=metadata_filters,
                        user_id=user_uuid  # Pass user_id for permission filtering
                    )
                else:
                    # Use standard retrieval
                    logger.info("Using standard retrieval (Retrieval Judge disabled)")
                    # Check if there are any documents in the vector store
                    stats = self.vector_store.get_stats()
                    if stats["count"] == 0:
                        logger.warning("RAG is enabled but no documents are available in the vector store")
                        # Leave context empty to indicate no documents
                        context = ""
                    else:
                        # Combine the current query with conversation context for better retrieval
                        search_query = query
                        if conversation_context:
                            # For retrieval, we focus more on the current query but include
                            # some context from the conversation to improve relevance
                            search_query = f"{query} {conversation_context[-200:]}"
                        
                        # Log the search query
                        logger.info(f"Searching with query: {search_query[:100]}...")
                        
                        # Use a higher fixed value for top_k to get more potential matches, then filter by relevance
                        search_results = await self.vector_store.search(
                            query=search_query,
                            top_k=15,  # Fixed value to retrieve more chunks
                            filter_criteria=metadata_filters,
                            user_id=user_uuid  # Pass user_id for permission filtering
                        )
                        
                        if search_results:
                            # Process search results and format context
                            context_pieces = []
                            relevant_results = []
                            
                            # Set a relevance threshold - only include chunks with relevance score above this
                            relevance_threshold = 0.4  # Lower threshold to ensure we include more relevant chunks
                            
                            for i, result in enumerate(search_results):
                                # Skip results with None content
                                if "content" not in result or result["content"] is None:
                                    logger.warning(f"Skipping result {i+1} due to missing or None content")
                                    continue
                                    
                                # Extract metadata for better context
                                metadata = result["metadata"]
                                filename = metadata.get("filename", "Unknown")
                                tags = metadata.get("tags", [])
                                folder = metadata.get("folder", "/")
                                
                                # Calculate relevance score (lower distance = higher relevance)
                                relevance_score = 1.0 - (result["distance"] if result["distance"] is not None else 0)
                                
                                # Log the relevance score for debugging
                                logger.debug(f"Chunk {i+1} relevance score: {relevance_score:.4f}")
                                
                                # Only include chunks that are sufficiently relevant
                                if relevance_score >= relevance_threshold:
                                    # Format the context piece with metadata
                                    context_piece = f"[{len(relevant_results)+1}] Source: {filename}, Tags: {tags}, Folder: {folder}\n\n{result['content']}"
                                    context_pieces.append(context_piece)
                                    
                                    # Track the source for citation
                                    doc_id = metadata["document_id"]
                                    document_ids.append(doc_id)
                                    
                                    source_info = {
                                        "document_id": doc_id,
                                        "chunk_id": result["chunk_id"],
                                        "relevance_score": relevance_score,
                                        "excerpt": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                                        "filename": filename,
                                        "tags": tags,
                                        "folder": folder
                                    }
                                    
                                    sources.append(source_info)
                                    
                                    # Store document interaction in Mem0 if available
                                    if self.mem0_client and user_id:
                                        await store_document_interaction(
                                            human_id=user_id,
                                            document_id=doc_id,
                                            interaction_type="retrieval",
                                            data={
                                                "query": query,
                                                "chunk_id": result["chunk_id"],
                                                "relevance_score": relevance_score,
                                                "filename": filename
                                            }
                                        )
                                    
                                    relevant_results.append(result)
                                else:
                                    logger.info(f"Skipping chunk {i+1} with low relevance score: {relevance_score:.4f}")
                            
                            # Join all context pieces
                            context = "\n\n".join(context_pieces)
                            
                            # Log how many chunks were filtered out due to low relevance
                            logger.info(f"Using {len(relevant_results)} of {len(search_results)} chunks after relevance filtering")
                            
                            # Log the total context length
                            logger.info(f"Total context length: {len(context)} characters")
                            
                            # Check if we have enough relevant context
                            if len(relevant_results) == 0:
                                logger.warning("No sufficiently relevant documents found for the query")
                                context = ""
                            elif len(context.strip()) < 50:  # Very short context might not be useful
                                logger.warning("Context is too short to be useful")
                                context = ""
                        else:
                            logger.warning("No relevant documents found for the query")
                            context = ""
            
            # Determine retrieval state based on the context
            retrieval_state = "success"
            if not use_rag:
                retrieval_state = "no_documents"
            elif not context or context.startswith("Note:"):
                # If context is empty or starts with a note, it means no relevant documents were found
                retrieval_state = "no_documents"
                # Reset context to empty string if it was a note
                if context and context.startswith("Note:"):
                    context = ""
            elif len(sources) == 0:
                # If no sources were found but context exists, it's low relevance
                retrieval_state = "low_relevance"
            
            logger.info(f"Determined retrieval state: {retrieval_state}")
            
            # Create system prompt and user prompt if not provided
            if not system_prompt:
                if self._is_code_related_query(query):
                    # For code queries, use the existing system prompt
                    system_prompt = self._create_system_prompt(query)
                    # Create a simple user prompt for code queries
                    full_prompt = f"User Question: {query}"
                else:
                    # For non-code queries, use the PromptManager
                    system_prompt, full_prompt = self._create_full_prompt(
                        query,
                        context,
                        conversation_context,
                        retrieval_state
                    )
            else:
                # If system prompt is provided, still use PromptManager for user prompt
                _, full_prompt = self._create_full_prompt(
                    query,
                    context,
                    conversation_context,
                    retrieval_state
                )
            
            # Log the prompt and system prompt for debugging
            logger.debug(f"System prompt: {system_prompt[:200]}...")
            logger.debug(f"Full prompt: {full_prompt[:200]}...")
            
            # Generate response
            if stream:
                # For streaming, just return the stream response
                logger.info(f"Generating streaming response with model: {model}")
                
                # Create a wrapper for the stream that applies text normalization
                stream_response = self._generate_streaming_response(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    model_parameters=model_parameters or {}
                )
                
                # Record analytics asynchronously
                response_time_ms = (time.time() - start_time) * 1000
                logger.info(f"Response time: {response_time_ms:.2f}ms")
                
                # Use await instead of async for with the coroutine
                await self._record_analytics(
                    query=query,
                    model=model,
                    use_rag=use_rag,
                    response_time_ms=response_time_ms,
                    document_ids=document_ids,
                    token_count=len(query.split())  # Approximate token count
                )
                
                return {
                    "query": query,
                    "stream": stream_response,
                    "sources": [Citation(**source) for source in sources] if sources else []
                }
            else:
                # For non-streaming, check cache first
                logger.info(f"Generating non-streaming response with model: {model}")
                
                # Get cached or generate new response
                response = await self._get_cached_or_generate_response(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    model_parameters=model_parameters or {}
                )
                
                # Calculate response time
                response_time_ms = (time.time() - start_time) * 1000
                logger.info(f"Response time: {response_time_ms:.2f}ms")
                
                # Process response text
                response_text = self._process_response_text(response)
                
                logger.info(f"Response length: {len(response_text)} characters")
                
                # Log a preview of the response
                if response_text:
                    logger.debug(f"Response preview: {response_text[:100]}...")
                
                # Store assistant response in Mem0 if available
                if self.mem0_client and user_id:
                    await store_message(user_id, "assistant", response_text)
                    logger.info(f"Stored assistant response in Mem0 for user {user_id}")
                
                # Record analytics asynchronously
                await self._record_analytics(
                    query=query,
                    model=model,
                    use_rag=use_rag,
                    response_time_ms=response_time_ms,
                    document_ids=document_ids,
                    token_count=len(query.split()) + len(response_text.split())  # Approximate token count
                )
                
                return {
                    "query": query,
                    "answer": response_text,
                    "sources": [Citation(**source) for source in sources] if sources else []
                }
        except Exception as e:
            logger.error(f"Error querying RAG engine: {str(e)}")
            raise
