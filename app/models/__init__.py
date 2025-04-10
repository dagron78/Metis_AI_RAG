"""
Models for the application
"""
import sys

# Keep track of imported models to prevent duplicate imports
_imported_models = set()

def import_models():
    """
    Import all models to ensure they're registered with SQLAlchemy
    This prevents duplicate table definitions when models are imported
    from different paths
    """
    # Skip if already imported
    if 'MODELS_IMPORTED' in globals():
        return
    
    # Import all models
    from app.models.chat import Citation, Message, Conversation, ChatQuery, ChatResponse
    from app.models.document import Chunk, Document, DocumentInfo, DocumentProcessRequest
    from app.models.memory import Memory
    from app.models.system import SystemStats, ModelInfo, HealthCheck
    
    # Mark as imported
    global MODELS_IMPORTED
    MODELS_IMPORTED = True

# Auto-import models when the package is imported
import_models()

# Re-export models for backward compatibility
from app.models.chat import Citation, Message, Conversation, ChatQuery, ChatResponse
from app.models.document import Chunk, Document, DocumentInfo, DocumentProcessRequest
from app.models.system import SystemStats, ModelInfo, HealthCheck