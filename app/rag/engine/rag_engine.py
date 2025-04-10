"""
RAG Engine

This module provides the RAGEngine class that combines all components
to provide a complete RAG solution.
"""
import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple, Union, AsyncGenerator
from uuid import UUID

from app.core.config import DEFAULT_MODEL
from app.models.chat import Citation, Message
from app.rag.engine.base.base_engine import BaseEngine
from app.rag.engine.base.vector_store_mixin import VectorStoreMixin
from app.rag.engine.base.ollama_mixin import OllamaMixin
from app.rag.engine.base.cache_mixin import CacheMixin
from app.rag.engine.base.security_mixin import SecurityMixin
from app.rag.engine.components.retrieval import RetrievalComponent
from app.rag.engine.components.generation import GenerationComponent
from app.rag.engine.components.memory import MemoryComponent
from app.rag.engine.components.context_builder import ContextBuilder
from app.rag.engine.utils.timing import TimingStats, async_timing_context
from app.rag.engine.utils.error_handler import RAGError, handle_rag_error

logger = logging.getLogger("app.rag.engine.rag_engine")

class RAGEngine(BaseEngine, VectorStoreMixin, OllamaMixin, CacheMixin, SecurityMixin):
    """
    RAG (Retrieval Augmented Generation) Engine
    
    This class combines all components to provide a complete RAG solution,
    including retrieval, generation, memory, and security features.
    """
    
    def __init__(
        self,
        vector_store=None,
        ollama_client=None,
        retrieval_judge=None,
        cache_manager=None,
        user_id=None,
        db=None
    ):
        """
        Initialize the RAG engine
        
        Args:
            vector_store: Vector store instance
            ollama_client: Ollama client instance
            retrieval_judge: Retrieval judge instance
            cache_manager: Cache manager instance
            user_id: User ID for permission filtering
            db: Database session for memory operations
        """
        # Initialize base classes
        BaseEngine.__init__(
            self,
            vector_store=vector_store,
            ollama_client=ollama_client,
            retrieval_judge=retrieval_judge,
            cache_manager=cache_manager,
            user_id=user_id
        )
        
        # Initialize components
        self.retrieval_component = RetrievalComponent(
            vector_store=self.vector_store,
            retrieval_judge=self.retrieval_judge
        )
        
        self.generation_component = GenerationComponent(
            ollama_client=self.ollama_client,
            cache_manager=self.cache_manager
        )
        
        self.memory_component = MemoryComponent(
            mem0_client=self.mem0_client,
            db=db
        )
        
        self.context_builder = ContextBuilder()
        
        # Initialize timing stats
        self.timing_stats = TimingStats()
        
        # Initialize state
        self.conversation_id = None
        
        logger.info("RAGEngine initialized with all components")
    
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
                   db = None,
                   capture_raw_output: bool = False,
                   return_raw_ollama: bool = False,
                   **kwargs) -> Dict[str, Any]:
        """
        Query the RAG engine
        
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
            conversation_id: Conversation ID for memory operations
            db: Database session for memory operations
            capture_raw_output: Whether to capture raw output
            return_raw_ollama: Whether to return raw Ollama output
            
        Returns:
            Response dictionary
        """
        self.timing_stats.start("total")
        
        try:
            # Start timing the entire query process
            logger.info(f"RAG query: {query[:50]}...")
            
            # Process user ID
            effective_user_id = await self._process_user_id(user_id)
            
            # Process conversation ID
            effective_conversation_id = await self._process_conversation_id(conversation_id, conversation_history)
            self.conversation_id = effective_conversation_id
            
            # Record timing for ID processing
            self.timing_stats.record_timing("id_processing", self.timing_stats.stop("id_processing") if "id_processing" in self.timing_stats.timings else 0.1)
            
            # Process memory operations
            async with async_timing_context("memory_processing", self.timing_stats):
                processed_query, memory_response, memory_operation = await self.memory_component.process_memory_operations(
                    query=query,
                    user_id=effective_user_id,
                    conversation_id=effective_conversation_id
                )
                
                # If it's a recall operation with a response, evaluate whether to return immediately
                if memory_operation == "recall" and memory_response:
                    # Check if this is a pure memory recall or if it should be augmented with LLM
                    if "Here's what I remember:" in memory_response and len(memory_response.split('\n')) <= 2:
                        # This is likely just returning minimal information, augment with LLM
                        logger.info(f"Memory recall contains minimal information, augmenting with LLM")
                        # Continue with normal processing but include memory in context
                        context = f"User previously mentioned: {memory_response}"
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
            
            # Format conversation history
            async with async_timing_context("conversation_history", self.timing_stats):
                conversation_context = await self._format_conversation_history(conversation_history)
            
            # Get context from vector store if RAG is enabled
            context = ""
            sources = []
            document_ids = []
            retrieval_state = "no_documents"
            
            if use_rag:
                async with async_timing_context("retrieval", self.timing_stats):
                    # Retrieve documents
                    documents, retrieval_state = await self.retrieval_component.retrieve(
                        query=query,
                        top_k=top_k,
                        metadata_filters=metadata_filters,
                        user_id=UUID(effective_user_id) if effective_user_id else None
                    )
                    
                    # Build context
                    if documents:
                        context, sources = await self.context_builder.build_context(
                            documents=documents,
                            query=query
                        )
                        
                        # Extract document IDs
                        document_ids = [source.get("document_id") for source in sources]
            
            # Generate response
            async with async_timing_context("response_generation", self.timing_stats):
                # Handle memory operations in the prompt
                if memory_operation == "store" and memory_response:
                    # For store operations, we need to modify the prompt to include the memory confirmation
                    if not system_prompt:
                        system_prompt = f"Include this confirmation in your response: {memory_response}"
                    else:
                        system_prompt += f"\n\nAlso, include this confirmation in your response: {memory_response}"
                
                if stream:
                    # For streaming, return the stream generator
                    stream_response = await self.generation_component.generate(
                        query=query,
                        context=context,
                        conversation_context=conversation_context,
                        model=model,
                        system_prompt=system_prompt,
                        model_parameters=model_parameters,
                        retrieval_state=retrieval_state,
                        stream=True
                    )
                    
                    # Record analytics asynchronously
                    response_time_ms = (time.time() - self.timing_stats.total_start_time) * 1000
                    await self._record_analytics(
                        query=query,
                        model=model,
                        use_rag=use_rag,
                        response_time_ms=response_time_ms,
                        document_id_list=document_ids,
                        token_count=len(query.split())
                    )
                    
                    # Perform memory cleanup to reduce memory usage
                    await self.memory_component.cleanup_memory()
                    
                    # Log timing summary
                    self.timing_stats.stop("total")
                    logger.info(f"Total processing time: {self.timing_stats.get_timing('total'):.2f}s")
                    self.timing_stats.log_summary()
                    
                    return {
                        "query": query,
                        "stream": stream_response,
                        "sources": [Citation(**source) for source in sources] if sources else []
                    }
                else:
                    # For non-streaming, generate the complete response
                    response = await self.generation_component.generate(
                        query=query,
                        context=context,
                        conversation_context=conversation_context,
                        model=model,
                        system_prompt=system_prompt,
                        model_parameters=model_parameters,
                        retrieval_state=retrieval_state,
                        stream=False
                    )
                    
                    # Get response text
                    response_text = response.get("content", "")
                    
                    # Capture the raw Ollama output if requested
                    raw_ollama_output = None
                    if (capture_raw_output or return_raw_ollama) and "raw_response" in response:
                        raw_ollama_output = response.get("raw_response", {}).get("response", "")
                        
                        # If return_raw_ollama is true, return only the raw output
                        if return_raw_ollama:
                            logger.info("Returning RAW Ollama output as requested")
                            return {"raw_output": raw_ollama_output}
                    
                    # Handle memory operations in the response
                    if memory_operation == "store" and memory_response:
                        # If we stored a memory, append the confirmation to the response
                        response_text = f"{response_text}\n\n{memory_response}"
                    
                    # Store assistant response in memory
                    if effective_user_id and effective_conversation_id:
                        await self.memory_component.store_message(
                            role="assistant",
                            content=response_text,
                            user_id=effective_user_id,
                            conversation_id=effective_conversation_id
                        )
                    
                    # Record analytics asynchronously
                    response_time_ms = (time.time() - self.timing_stats.total_start_time) * 1000
                    await self._record_analytics(
                        query=query,
                        model=model,
                        use_rag=use_rag,
                        response_time_ms=response_time_ms,
                        document_id_list=document_ids,
                        token_count=len(query.split()) + len(response_text.split())
                    )
                    
                    # Perform memory cleanup to reduce memory usage
                    await self.memory_component.cleanup_memory()
                    
                    # Log timing summary
                    self.timing_stats.stop("total")
                    logger.info(f"Total processing time: {self.timing_stats.get_timing('total'):.2f}s")
                    self.timing_stats.log_summary()
                    
                    return {
                        "query": query,
                        "answer": response_text,
                        "sources": [Citation(**source) for source in sources] if sources else [],
                        "raw_ollama_output": raw_ollama_output if capture_raw_output else None,
                        "raw_output": raw_ollama_output if return_raw_ollama else None
                    }
        
        except Exception as e:
            self.timing_stats.stop("total")
            logger.error(f"Error querying RAG engine: {str(e)}")
            return handle_rag_error(e, "Error processing your query")
    
    async def _process_user_id(self, user_id: Optional[str] = None) -> Optional[str]:
        """
        Process and validate user ID
        
        Args:
            user_id: User ID
            
        Returns:
            Processed user ID
        """
        self.timing_stats.start("id_processing")
        
        # Use the provided user_id or fall back to the instance's user_id
        effective_user_id = user_id or (str(self.user_id) if self.user_id else None)
        
        # If no user ID is provided, generate a new one
        if not effective_user_id:
            # Generate a new UUID
            effective_user_id = str(uuid.uuid4())
            logger.info(f"Generated new user_id: {effective_user_id}")
        else:
            logger.info(f"Using provided user_id: {effective_user_id}")
        
        # Always ensure user_id is a valid UUID
        try:
            # This will raise ValueError if not a valid UUID
            UUID(effective_user_id)
        except ValueError:
            # If it's not a valid UUID string, generate a deterministic UUID
            old_user_id = effective_user_id
            effective_user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{effective_user_id}"))
            logger.warning(f"Converting non-UUID user_id format: {old_user_id} to deterministic UUID: {effective_user_id}")
        
        return effective_user_id
    
    async def _process_conversation_id(self, 
                                      conversation_id: Optional[str] = None, 
                                      conversation_history: Optional[List[Message]] = None) -> Optional[str]:
        """
        Process and validate conversation ID
        
        Args:
            conversation_id: Conversation ID
            conversation_history: Conversation history
            
        Returns:
            Processed conversation ID
        """
        # Use provided conversation_id
        if conversation_id:
            logger.info(f"Using provided conversation_id: {conversation_id}")
            return conversation_id
        
        # Extract from conversation history if available
        if not conversation_id and conversation_history and len(conversation_history) > 0:
            # Assuming the first message has the conversation_id
            extracted_id = getattr(conversation_history[0], 'conversation_id', None)
            if extracted_id:
                logger.info(f"Using conversation_id from history: {extracted_id}")
                return extracted_id
        
        # Generate a new conversation ID
        new_id = str(uuid.uuid4())
        logger.info(f"Generated new conversation_id: {new_id}")
        return new_id
    
    async def _format_conversation_history(self, conversation_history: Optional[List[Message]] = None) -> str:
        """
        Format conversation history
        
        Args:
            conversation_history: Conversation history
            
        Returns:
            Formatted conversation history
        """
        if not conversation_history or len(conversation_history) <= 1:
            return ""
        
        # Convert conversation history to list of dictionaries
        messages = []
        for msg in conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if hasattr(msg, 'created_at') else None
            })
        
        # Build conversation context
        conversation_context = await self.context_builder.build_conversation_context(messages)
        
        return conversation_context