"""
RAG (Retrieval Augmented Generation) Engine
"""
import logging
import time
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import DEFAULT_MODEL
from app.models.chat import Citation, Message
from app.rag.rag_engine_base import BaseRAGEngine
from app.rag.rag_retrieval import RetrievalMixin
from app.rag.rag_generation import GenerationMixin
from app.rag.mem0_client import store_message, get_conversation_history, store_document_interaction, get_user_preferences
from app.rag.memory_buffer import process_query, get_conversation_context

logger = logging.getLogger("app.rag.rag_engine")

class RAGEngine(BaseRAGEngine, RetrievalMixin, GenerationMixin):
    """
    RAG (Retrieval Augmented Generation) Engine with security features
    
    This class combines the base RAGEngine with retrieval and generation functionality
    to provide a complete RAG solution with security features.
    """
    
    def __init__(
        self,
        vector_store=None,
        ollama_client=None,
        retrieval_judge=None,
        cache_manager=None,
        user_id=None
    ):
        """
        Initialize the RAG engine
        
        Args:
            vector_store: Vector store instance
            ollama_client: Ollama client instance
            retrieval_judge: Retrieval judge instance
            cache_manager: Cache manager instance
            user_id: User ID for permission filtering
        """
        # Initialize BaseRAGEngine
        BaseRAGEngine.__init__(
            self,
            vector_store=vector_store,
            ollama_client=ollama_client,
            retrieval_judge=retrieval_judge,
            cache_manager=cache_manager,
            user_id=user_id
        )
        
        # Initialize GenerationMixin
        GenerationMixin.__init__(self)
        
        logger.info("RAGEngine initialized with PromptManager")
    
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
                   user_id: Optional[str] = None,
                   conversation_id: Optional[str] = None,
                   db: AsyncSession = None,  # Add db parameter
                   capture_raw_output: bool = False,  # Add parameter to capture raw output
                   return_raw_ollama: bool = False,  # Add parameter to return raw Ollama output
                   **kwargs) -> Dict[str, Any]:
        """
        Query the RAG engine with optional conversation history and metadata filtering
        
        Args:
            query: Query string
            model: Model to use
            use_rag: Whether to use RAG
            conversation_id: Conversation ID for memory operations
            top_k: Number of results to return
            system_prompt: System prompt
            stream: Whether to stream the response
            model_parameters: Model parameters
            conversation_history: Conversation history
            metadata_filters: Metadata filters
            user_id: User ID for permission filtering
            db: Database session to use for memory operations
            capture_raw_output: Whether to capture and include raw Ollama output in the response
            return_raw_ollama: Whether to return only the raw Ollama output, bypassing processing
            
        Returns:
            Response dictionary
        """
        start_time = time.time()
        document_ids = []
        
        try:
            # Start timing the entire query process
            start_time = time.time()
            logger.info(f"RAG query: {query[:50]}...")
            
            # Create a timing dictionary to track performance
            timings = {}
            
            # Get context from vector store if RAG is enabled
            context = ""
            sources = []
            
            # Function to record timing for a step
            def record_timing(step_name):
                current_time = time.time()
                elapsed = current_time - start_time
                step_time = elapsed - sum(timings.values())
                timings[step_name] = step_time
                logger.info(f"Step '{step_name}' completed in {step_time:.2f}s (total elapsed: {elapsed:.2f}s)")
            
            # Only extract conversation_id from conversation_history if not already provided
            if not conversation_id and conversation_history and len(conversation_history) > 0:
                # Assuming the first message has the conversation_id
                conversation_id = getattr(conversation_history[0], 'conversation_id', None)
                if conversation_id:
                    logger.info(f"Using conversation_id from history: {conversation_id}")
            
            # Use the user_id from the conversation if provided
            if not user_id and conversation_id:
                # Generate a consistent user_id based on the conversation_id
                # Use UUID5 to ensure deterministic generation
                user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"conversation-{conversation_id}"))
                logger.info(f"Using consistent user_id from conversation: {user_id}")
            elif not user_id:
                # If no user_id and no conversation_id, generate a new one
                # Always use UUID4 for anonymous users
                user_id = str(uuid.uuid4())
                logger.info(f"Generated new user_id: {user_id}")
            else:
                # User ID was provided - ensure it's a valid UUID
                logger.info(f"Using provided user_id: {user_id}")
            
            # Always ensure user_id is a valid UUID
            user_uuid = None
            if isinstance(user_id, UUID):
                # Already a UUID object
                user_uuid = user_id
            elif isinstance(user_id, str):
                # Check for special case "system" user ID
                if user_id == "system" or user_id.startswith("session_"):
                    # Replace with a deterministic UUID based on the string
                    old_user_id = user_id
                    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"fixed-{user_id}")
                    user_id = str(user_uuid)
                    logger.warning(f"Replaced invalid user_id format: {old_user_id} with UUID: {user_id}")
                else:
                    try:
                        # Try to convert string to UUID
                        user_uuid = UUID(user_id)
                    except ValueError:
                        # If it's not a valid UUID string, generate a deterministic UUID
                        # This ensures the same string always maps to the same UUID
                        old_user_id = user_id
                        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{user_id}")
                        user_id = str(user_uuid)
                        logger.warning(f"Converting non-UUID user_id format: {old_user_id} to deterministic UUID: {user_id}")
            else:
                # If it's neither a UUID nor a string, log an error and use a default UUID
                logger.error(f"Unexpected user_id type: {type(user_id)}, using default UUID")
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "default-user")
                user_id = str(user_uuid)
                
            # Validate the final user_id to ensure it's a valid UUID
            try:
                # This will raise ValueError if not a valid UUID
                UUID(user_id)
            except ValueError:
                # If somehow we still have an invalid UUID, generate a new one
                logger.error(f"Final user_id validation failed: {user_id}, generating new UUID")
                user_uuid = uuid.uuid4()
                user_id = str(user_uuid)
            
            # Process memory commands if user_id is provided
            processed_query = query
            memory_response = None
            memory_operation = None
            # Log conversation ID for debugging
            if conversation_id:
                # Always use the provided conversation_id
                self.conversation_id = conversation_id
                logger.info(f"Using provided conversation_id: {conversation_id}")
            else:
                # Try to get conversation_id from kwargs if provided
                if 'conversation_id' in kwargs:
                    conversation_id = kwargs.get('conversation_id')
                    if conversation_id:
                        logger.info(f"Using conversation_id from kwargs: {conversation_id}")
                        self.conversation_id = conversation_id
                
                # If still no conversation_id, this is a warning condition
                # The API should always create a conversation and pass its ID
                if not conversation_id:
                    logger.warning("No conversation_id provided, this may cause issues with memory operations")
            
            # Record timing for user ID and conversation ID processing
            record_timing("id_processing")
            
            if user_id and conversation_id:
                processed_query, memory_response, memory_operation = await process_query(
                    query=query,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    db=db  # Pass the provided session
                )
                
                # If it's a recall operation with a response, evaluate whether to return immediately
                if memory_operation == "recall" and memory_response:
                    # Check if this is a pure memory recall or if it should be augmented with LLM
                    if "Here's what I remember:" in memory_response and len(memory_response.split('\n')) <= 2:
                        # This is likely just returning minimal information, augment with LLM
                        logger.info(f"Memory recall contains minimal information, augmenting with LLM")
                        # Continue with normal processing but include memory in context
                        if not context:
                            context = f"User previously mentioned: {memory_response}"
                        else:
                            context = f"User previously mentioned: {memory_response}\n\n{context}"
                    else:
                        # This is a substantial memory recall, return directly
                        logger.info(f"Substantial memory recall detected, returning directly")
                        return {
                            "query": query,
                            "answer": memory_response,
                            "sources": []
                        }
            
            # Use the processed query for RAG
            query = processed_query
            
            # Record timing for memory processing
            record_timing("memory_processing")
            
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
                # Get the last few messages (up to 10) to keep context manageable, but exclude the most recent user message
                # which is the current query and shouldn't be treated as history
                recent_history = conversation_history[:-1]
                if len(recent_history) > 10:
                    recent_history = recent_history[-10:]
                
                # Format the conversation history
                history_pieces = []
                for msg in recent_history:
                    role_prefix = "User" if msg.role == "user" else "Assistant"
                    history_pieces.append(f"{role_prefix}: {msg.content}")
                    # Log each message for debugging
                    logger.debug(f"History message - Role: {msg.role}, Content: {msg.content[:50]}...")
                
                conversation_context = "\n".join(history_pieces)
                logger.info(f"Including conversation history with {len(recent_history)} messages")
                logger.debug(f"Conversation context: {conversation_context[:200]}...")
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
            
            # Record timing for conversation history processing
            record_timing("conversation_history")
            
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
            
            # Record timing for retrieval process
            record_timing("retrieval")
            
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
            
            # Record timing for retrieval state determination
            record_timing("retrieval_state")
            
            # Create system prompt and user prompt if not provided
            if not system_prompt:
                if self._is_code_related_query(query):
                    # For code queries, use the structured output system prompt
                    system_prompt = self._create_system_prompt(query)
                    # Create a simple user prompt for code queries
                    full_prompt = f"User Question: {query}"
                    
                    # Import the FormattedResponse model for the schema
                    from app.models.structured_output import FormattedResponse
                    
                    # Set the format parameter for structured output
                    if not model_parameters:
                        model_parameters = {}
                    
                    # Add the format schema to the model parameters
                    model_parameters["format"] = FormattedResponse.model_json_schema()
                    
                    # Set temperature to 0 for more deterministic output
                    model_parameters["temperature"] = 0.0
                    
                    logger.info("Using structured output format for code-related query")
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
            
            # Record timing for prompt creation
            record_timing("prompt_creation")
            
            # Generate response
            if stream:
                # For streaming, return the stream generator directly
                logger.info(f"Generating streaming response with model: {model}")
                
                # Handle memory operations for streaming responses
                if memory_operation == "recall" and memory_response:
                    # For recall operations, we've already returned early
                    # This code should not be reached
                    pass
                elif memory_operation == "store" and memory_response:
                    # For store operations, we need to modify the prompt to include the memory confirmation
                    full_prompt = f"{full_prompt}\n\nAlso, include this confirmation in your response: {memory_response}"
                
                # Use the simplified streaming response method
                stream_response = self._generate_streaming_response(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    model_parameters=model_parameters or {}
                )
                
                # Record timing for response generation
                record_timing("response_generation")
                
                # Record analytics asynchronously
                response_time_ms = (time.time() - start_time) * 1000
                logger.info(f"Response time: {response_time_ms:.2f}ms")
                
                # Use await instead of async for with the coroutine
                await self._record_analytics(
                    query=query,
                    model=model,
                    use_rag=use_rag,
                    response_time_ms=response_time_ms,
                    document_id_list=document_ids,  # Changed from document_ids to document_id_list
                    token_count=len(query.split())  # Approximate token count
                )
                # Perform memory cleanup to reduce memory usage
                await self._cleanup_memory()
                
                # Log timing summary
                logger.info(f"Timing summary: {', '.join([f'{k}: {v:.2f}s' for k, v in timings.items()])}")
                logger.info(f"Total processing time: {(time.time() - start_time):.2f}s")
                
                
                return {
                    "query": query,
                    "stream": stream_response,
                    "sources": [Citation(**source) for source in sources] if sources else []
                }
            else:
                # For non-streaming, generate the complete response
                logger.info(f"Generating non-streaming response with model: {model}")
                
                # Use the simplified complete response method
                response = await self.generate_complete_response(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    model_parameters=model_parameters or {}
                )
                
                # Record timing for response generation
                record_timing("response_generation")
                
                # Calculate response time
                response_time_ms = (time.time() - start_time) * 1000
                logger.info(f"Response time: {response_time_ms:.2f}ms")
                
                # Capture the raw Ollama output if requested
                raw_ollama_output = None
                if (capture_raw_output or return_raw_ollama) and "response" in response:
                    raw_ollama_output = response.get("response", "")
                    
                    # If return_raw_ollama is true, return only the raw output
                    if return_raw_ollama:
                        logger.info("Returning RAW Ollama output as requested")
                        return {"raw_output": raw_ollama_output}
                
                # Process response text with optional normalization
                response_text = self._process_response_text(response)
                
                logger.info(f"Response length: {len(response_text)} characters")
                
                # Log a preview of the response
                if response_text:
                    logger.debug(f"Response preview: {response_text[:100]}...")
                
                # Handle memory operations in the response
                if memory_operation == "store" and memory_response:
                    # If we stored a memory, append the confirmation to the response
                    response_text = f"{response_text}\n\n{memory_response}"
                
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
                    document_id_list=document_ids,  # Changed from document_ids to document_id_list
                    token_count=len(query.split()) + len(response_text.split())  # Approximate token count
                )
                # Perform memory cleanup to reduce memory usage
                await self._cleanup_memory()
                
                # Log timing summary
                logger.info(f"Timing summary: {', '.join([f'{k}: {v:.2f}s' for k, v in timings.items()])}")
                logger.info(f"Total processing time: {(time.time() - start_time):.2f}s")
                
                
                return {
                    "query": query,
                    "answer": response_text,
                    "sources": [Citation(**source) for source in sources] if sources else [],
                    "raw_ollama_output": raw_ollama_output if capture_raw_output else None,
                    "raw_output": raw_ollama_output if return_raw_ollama else None
                }
        except Exception as e:
            logger.error(f"Error querying RAG engine: {str(e)}")
            raise
            
    async def _cleanup_memory(self) -> None:
        """
        Perform memory cleanup to reduce memory usage
        """
        try:
            # Import necessary modules
            import gc
            import psutil
            import sys
            
            # Get current memory usage before cleanup
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            
            # Force garbage collection with more aggressive settings
            gc.collect(2)  # Full collection with the highest generation
            
            # Clear any cached data
            if hasattr(self, '_context_cache'):
                self._context_cache = {}
            
            # Clear any large temporary variables
            context = None
            sources = None
            
            # Clear any other large objects that might be in memory
            if hasattr(self, '_last_query_data'):
                self._last_query_data = None
                
            if hasattr(self, '_last_response'):
                self._last_response = None
            
            # Get memory usage after cleanup
            memory_after = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            memory_freed = memory_before - memory_after
            
            # Log memory usage statistics
            logger.info(f"Memory cleanup performed: {memory_freed:.2f} MB freed")
            logger.info(f"Current memory usage: {memory_after:.2f} MB")
            
            # Check if memory usage is still high
            memory_percent = process.memory_percent()
            if memory_percent > 80.0:
                # More aggressive cleanup if memory usage is still high
                logger.warning(f"Memory usage still high after cleanup: {memory_percent:.1f}%")
                
                # Clear more caches
                if hasattr(self.vector_store, 'clear_cache'):
                    self.vector_store.clear_cache()
                
                # Clear Python's internal caches
                sys.intern.clear()  # Clear string interning cache
                
                # Run garbage collection again
                gc.collect(2)
                
                # Log memory usage after aggressive cleanup
                memory_after_aggressive = process.memory_info().rss / (1024 * 1024)
                logger.info(f"Memory after aggressive cleanup: {memory_after_aggressive:.2f} MB")
            
        except Exception as e:
            logger.warning(f"Error during memory cleanup: {str(e)}")
