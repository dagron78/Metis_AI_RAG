"""
RAG Engine Utilities Package

This package contains utility functions for the RAG Engine.
"""

# Import and export utility functions
from app.rag.engine.utils.query_processor import (
    process_query,
    analyze_query_complexity,
    extract_keywords
)

from app.rag.engine.utils.timing import (
    time_operation,
    async_time_operation,
    timing_context,
    async_timing_context,
    get_performance_stats,
    TimingStats
)

from app.rag.engine.utils.relevance import (
    calculate_relevance_score,
    rank_documents,
    evaluate_retrieval_quality
)

from app.rag.engine.utils.error_handler import (
    handle_rag_error,
    format_user_facing_error,
    log_error_with_context,
    create_error_response,
    safe_execute,
    safe_execute_async,
    get_error_context,
    RAGError,
    RetrievalError,
    GenerationError,
    MemoryError,
    SecurityError,
    ValidationError,
    ConfigurationError
)

__all__ = [
    # Query processor
    'process_query',
    'analyze_query_complexity',
    'extract_keywords',
    
    # Timing
    'time_operation',
    'async_time_operation',
    'timing_context',
    'async_timing_context',
    'get_performance_stats',
    'TimingStats',
    
    # Relevance
    'calculate_relevance_score',
    'rank_documents',
    'evaluate_retrieval_quality',
    
    # Error handler
    'handle_rag_error',
    'format_user_facing_error',
    'log_error_with_context',
    'create_error_response',
    'safe_execute',
    'safe_execute_async',
    'get_error_context',
    'RAGError',
    'RetrievalError',
    'GenerationError',
    'MemoryError',
    'SecurityError',
    'ValidationError',
    'ConfigurationError'
]