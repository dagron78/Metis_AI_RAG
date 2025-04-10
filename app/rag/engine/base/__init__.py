"""
RAG Engine Base Package

This package contains base classes and mixins for the RAG Engine.
"""

# Import and export base classes and mixins
from app.rag.engine.base.base_engine import BaseEngine
from app.rag.engine.base.vector_store_mixin import VectorStoreMixin
from app.rag.engine.base.ollama_mixin import OllamaMixin
from app.rag.engine.base.cache_mixin import CacheMixin
from app.rag.engine.base.security_mixin import SecurityMixin

__all__ = [
    'BaseEngine',
    'VectorStoreMixin',
    'OllamaMixin',
    'CacheMixin',
    'SecurityMixin'
]