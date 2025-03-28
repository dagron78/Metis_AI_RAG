"""
System prompts package for Metis RAG.

This package contains various system prompts used by the RAG engine
to guide the behavior of the language model for different types of queries.
"""

from app.rag.system_prompts.code_generation import (
    CODE_GENERATION_SYSTEM_PROMPT,
    PYTHON_CODE_GENERATION_PROMPT,
    JAVASCRIPT_CODE_GENERATION_PROMPT
)
from app.rag.system_prompts.rag import (
    RAG_SYSTEM_PROMPT
)
from app.rag.system_prompts.conversation import (
    CONVERSATION_WITH_CONTEXT_PROMPT,
    NEW_QUERY_WITH_CONTEXT_PROMPT
)

__all__ = [
    'CODE_GENERATION_SYSTEM_PROMPT',
    'PYTHON_CODE_GENERATION_PROMPT',
    'JAVASCRIPT_CODE_GENERATION_PROMPT',
    'RAG_SYSTEM_PROMPT',
    'CONVERSATION_WITH_CONTEXT_PROMPT',
    'NEW_QUERY_WITH_CONTEXT_PROMPT'
]