"""
System prompts package for Metis RAG.

This package contains various system prompts used by the RAG engine
to guide the behavior of the language model for different types of queries.
"""

from app.rag.system_prompts.code_generation import (
    CODE_GENERATION_SYSTEM_PROMPT,
    PYTHON_CODE_GENERATION_PROMPT,
    JAVASCRIPT_CODE_GENERATION_PROMPT,
    STRUCTURED_CODE_OUTPUT_PROMPT
)

# Note: RAG_SYSTEM_PROMPT and conversation templates have been moved to the PromptManager

__all__ = [
    'CODE_GENERATION_SYSTEM_PROMPT',
    'PYTHON_CODE_GENERATION_PROMPT',
    'JAVASCRIPT_CODE_GENERATION_PROMPT',
    'STRUCTURED_CODE_OUTPUT_PROMPT'
]