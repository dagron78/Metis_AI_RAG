"""
RAG (Retrieval Augmented Generation) Engine

@deprecated This file is deprecated and will be removed in a future version.
Please use the new modular structure in app/rag/engine/ instead.
"""
import logging
import warnings
from typing import Dict, Any, Optional, List, AsyncGenerator
from uuid import UUID

from app.core.config import DEFAULT_MODEL
from app.models.chat import Citation, Message
from app.rag.engine.rag_engine import RAGEngine as ModularRAGEngine

# Show deprecation warning
warnings.warn(
    "DEPRECATION WARNING: app/rag/rag_engine.py is deprecated and will be removed in a future version. "
    "Please use the new modular structure in app/rag/engine/ instead.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger("app.rag.rag_engine")

class RAGEngine:
    """
    RAG (Retrieval Augmented Generation) Engine with security features
    
    @deprecated This class is deprecated and will be removed in a future version.
    Please use app.rag.engine.rag_engine.RAGEngine instead.
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
        # Log deprecation warning
        logger.warning(
            "DEPRECATION WARNING: app/rag/rag_engine.py is deprecated and will be removed in a future version. "
            "Please use the new modular structure in app/rag/engine/ instead."
        )
        
        # Initialize the modular RAG engine
        self._engine = ModularRAGEngine(
            vector_store=vector_store,
            ollama_client=ollama_client,
            retrieval_judge=retrieval_judge,
            cache_manager=cache_manager,
            user_id=user_id
        )
        
        # Copy attributes from the modular engine
        self.vector_store = self._engine.vector_store
        self.ollama_client = self._engine.ollama_client
        self.retrieval_judge = self._engine.retrieval_judge
        self.user_id = self._engine.user_id
        self.mem0_client = self._engine.mem0_client
        self.cache_manager = self._engine.cache_manager
        self.conversation_id = None
        
        logger.info("RAGEngine initialized (legacy wrapper)")
    
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
        # Store conversation ID for backward compatibility
        self.conversation_id = conversation_id
        
        # Delegate to the modular engine
        return await self._engine.query(
            query=query,
            model=model,
            use_rag=use_rag,
            top_k=top_k,
            system_prompt=system_prompt,
            stream=stream,
            model_parameters=model_parameters,
            conversation_history=conversation_history,
            metadata_filters=metadata_filters,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db,
            capture_raw_output=capture_raw_output,
            return_raw_ollama=return_raw_ollama,
            **kwargs
        )
    
    async def _enhanced_retrieval(self,
                                 query: str,
                                 conversation_context: str = "",
                                 top_k: int = 10,
                                 metadata_filters: Optional[Dict[str, Any]] = None,
                                 user_id: Optional[UUID] = None) -> tuple:
        """
        Enhanced retrieval using the Retrieval Judge with permission filtering
        
        @deprecated This method is deprecated and will be removed in a future version.
        
        Args:
            query: The user query
            conversation_context: Optional conversation history context
            top_k: Number of chunks to retrieve
            metadata_filters: Optional filters for retrieval
            user_id: User ID for permission filtering
            
        Returns:
            Tuple of (context, sources, document_ids)
        """
        # Log deprecation warning
        logger.warning(
            "DEPRECATION WARNING: _enhanced_retrieval method is deprecated and will be removed in a future version. "
            "Please use the retrieval component in the new modular structure instead."
        )
        
        # Convert user_id to string if it's a UUID
        user_id_str = str(user_id) if user_id else None
        
        # Use the retrieval component
        documents, retrieval_state = await self._engine.retrieval_component.retrieve(
            query=query,
            top_k=top_k,
            metadata_filters=metadata_filters,
            user_id=user_id
        )
        
        # Build context
        context, sources = await self._engine.context_builder.build_context(
            documents=documents,
            query=query
        )
        
        # Extract document IDs
        document_ids = [source.get("document_id") for source in sources]
        
        return context, sources, document_ids
    
    async def _cleanup_memory(self) -> None:
        """
        Perform memory cleanup to reduce memory usage
        
        @deprecated This method is deprecated and will be removed in a future version.
        """
        # Log deprecation warning
        logger.warning(
            "DEPRECATION WARNING: _cleanup_memory method is deprecated and will be removed in a future version. "
            "Please use the memory component in the new modular structure instead."
        )
        
        # Delegate to the memory component
        await self._engine.memory_component.cleanup_memory()
