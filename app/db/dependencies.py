from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from uuid import UUID

from app.db.session import get_session
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.password_reset_repository import PasswordResetRepository
from app.rag.document_processor import DocumentProcessor
from app.core.config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from app.core.security import get_current_user_optional
from app.models.user import User


# Async dependency for database session
get_db = get_session


async def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    """
    Get a document repository
    
    Args:
        db: Database session
        
    Returns:
        Document repository
    """
    return DocumentRepository(db)

async def get_conversation_repository(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> ConversationRepository:
    """
    Get a conversation repository with user context
    
    Args:
        db: Database session
        current_user: Current user (optional)
        
    Returns:
        Conversation repository with user context
    """
    user_id = current_user.id if current_user else None
    return ConversationRepository(db, user_id=user_id)

async def get_analytics_repository(db: AsyncSession = Depends(get_db)) -> AnalyticsRepository:
    """
    Get an analytics repository
    
    Args:
        db: Database session
        
    Returns:
        Analytics repository
    """
    return AnalyticsRepository(db)


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Get a user repository
    
    Args:
        db: Database session
        
    Returns:
        User repository
    """
    return UserRepository(db)


async def get_password_reset_repository(db: AsyncSession = Depends(get_db)) -> PasswordResetRepository:
    """
    Get a password reset repository
    
    Args:
        db: Database session
        
    Returns:
        Password reset repository
    """
    return PasswordResetRepository(db)


def get_document_processor(
    upload_dir: str = UPLOAD_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    chunking_strategy: str = "recursive",
    llm_provider = None
) -> DocumentProcessor:
    """
    Get a document processor with the specified parameters
    
    Args:
        upload_dir: Upload directory
        chunk_size: Chunk size
        chunk_overlap: Chunk overlap
        chunking_strategy: Chunking strategy
        llm_provider: LLM provider
        
    Returns:
        Document processor
    """
    return DocumentProcessor(
        upload_dir=upload_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=chunking_strategy,
        llm_provider=llm_provider
    )