"""
Base RAG Engine class with core functionality
"""
import logging
import re
from typing import Optional, Dict, Any
from uuid import UUID

from app.core.config import USE_RETRIEVAL_JUDGE
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.agents.retrieval_judge import RetrievalJudge
from app.rag.mem0_client import get_mem0_client
from app.cache.cache_manager import CacheManager

logger = logging.getLogger("app.rag.rag_engine_base")

class BaseRAGEngine:
    """
    Base class for RAG (Retrieval Augmented Generation) Engine with security features
    """
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        ollama_client: Optional[OllamaClient] = None,
        retrieval_judge: Optional[RetrievalJudge] = None,
        cache_manager: Optional[CacheManager] = None,
        user_id: Optional[UUID] = None
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
        self.vector_store = vector_store or VectorStore(user_id=user_id)
        self.ollama_client = ollama_client or OllamaClient()
        self.retrieval_judge = retrieval_judge if retrieval_judge is not None else (
            RetrievalJudge(ollama_client=self.ollama_client) if USE_RETRIEVAL_JUDGE else None
        )
        self.user_id = user_id  # Store the user ID for permission filtering
        
        # Initialize Mem0 client
        self.mem0_client = get_mem0_client()
        
        # Initialize cache manager
        self.cache_manager = cache_manager or CacheManager()
        
        if self.retrieval_judge:
            logger.info("Retrieval Judge is enabled")
        else:
            logger.info("Retrieval Judge is disabled")
            
        if self.mem0_client:
            logger.info("Mem0 integration is enabled")
        else:
            logger.info("Mem0 integration is disabled")
            
        # Log cache status
        cache_stats = self.cache_manager.get_all_cache_stats()
        if cache_stats.get("caching_enabled", False):
            logger.info("Caching is enabled")
        else:
            logger.info("Caching is disabled")
    
    def _is_code_related_query(self, query: str) -> bool:
        """
        Determine if a query is related to code or programming.
        
        Args:
            query: The user query
            
        Returns:
            True if the query is code-related, False otherwise
        """
        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower()
        
        # Check for explicit non-code indicators
        non_code_indicators = [
            "summary of", "explain", "what is", "definition of",
            "tell me about", "describe", "history of", "concept of",
            "brief", "overview", "introduction to", "guide to"
        ]
        
        for indicator in non_code_indicators:
            if indicator in query_lower:
                # Log the non-code indicator that was matched
                logger.debug(f"Query matched non-code indicator: '{indicator}'")
                return False
        
        # Check for code-related keywords (refined list)
        code_keywords = [
            # Programming languages (specific)
            'python', 'javascript', 'java', 'c++', 'c#', 'typescript',
            'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala',
            
            # Programming concepts (specific)
            'function', 'class', 'method', 'variable', 'algorithm',
            'loop', 'conditional', 'recursion', 'inheritance',
            
            # Development terms (specific)
            'compile', 'debug', 'syntax', 'runtime', 'exception',
            'framework', 'library', 'api', 'sdk', 'ide',
            
            # Code-specific actions
            'implement', 'code', 'program', 'develop', 'write code',
            'script', 'coding', 'programming'
        ]
        
        # Check if any code keyword is in the query with word boundaries
        for keyword in code_keywords:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_lower):
                logger.info(f"Detected code-related query, matched keyword: '{keyword}'")
                return True
        
        # Check for code patterns (unchanged)
        code_patterns = [
            r'```[\s\S]*```',  # Code blocks
            r'def\s+\w+\s*\(',  # Python function definition
            r'function\s+\w+\s*\(',  # JavaScript function definition
            r'class\s+\w+',  # Class definition
            r'import\s+\w+',  # Import statement
            r'from\s+\w+\s+import',  # Python import
            r'<\w+>.*</\w+>',  # HTML tags
            r'\w+\s*=\s*function\(',  # JavaScript function assignment
            r'const\s+\w+\s*=',  # JavaScript const declaration
            r'let\s+\w+\s*=',  # JavaScript let declaration
            r'var\s+\w+\s*=',  # JavaScript var declaration
            r'public\s+\w+\s+\w+\(',  # Java method
            r'SELECT\s+.*\s+FROM',  # SQL query
            r'CREATE\s+TABLE',  # SQL create table
            r'@app\.route',  # Flask route
            r'npm\s+install',  # npm command
            r'pip\s+install',  # pip command
            r'git\s+\w+'  # git command
        ]
        
        # Check if any code pattern is in the query
        for pattern in code_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.info(f"Detected code-related query, matched pattern: '{pattern}'")
                return True
        
        logger.info(f"Query not detected as code-related: '{query[:50]}...'")
        return False