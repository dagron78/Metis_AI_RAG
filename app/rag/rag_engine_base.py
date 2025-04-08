"""
Base RAG Engine class with core functionality

@deprecated This file is deprecated and will be removed in a future version.
Please use the new modular structure in app/rag/engine/base/ instead.
"""
import logging
import warnings
from typing import Optional
from uuid import UUID

from app.rag.engine.base import BaseEngine as ModularBaseEngine

# Show deprecation warning
warnings.warn(
    "DEPRECATION WARNING: app/rag/rag_engine_base.py is deprecated and will be removed in a future version. "
    "Please use the new modular structure in app/rag/engine/base/ instead.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger("app.rag.rag_engine_base")

class BaseRAGEngine:
    """
    Base class for RAG (Retrieval Augmented Generation) Engine with security features
    
    @deprecated This class is deprecated and will be removed in a future version.
    Please use app.rag.engine.base.BaseEngine instead.
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
            "DEPRECATION WARNING: app/rag/rag_engine_base.py is deprecated and will be removed in a future version. "
            "Please use the new modular structure in app/rag/engine/base/ instead."
        )
        
        # Initialize the modular base engine
        self._engine = ModularBaseEngine(
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
        
        logger.info("BaseRAGEngine initialized (legacy wrapper)")
    
    def _is_code_related_query(self, query: str) -> bool:
        """
        Determine if a query is related to code or programming.
        
        @deprecated This method is deprecated and will be removed in a future version.
        
        Args:
            query: The user query
            
        Returns:
            True if the query is code-related, False otherwise
        """
        # Log deprecation warning
        logger.warning(
            "DEPRECATION WARNING: _is_code_related_query method is deprecated and will be removed in a future version. "
            "Please use the base engine in the new modular structure instead."
        )
        
        # Delegate to the modular engine
        return self._engine._is_code_related_query(query)