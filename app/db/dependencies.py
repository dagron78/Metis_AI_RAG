from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import AsyncSessionLocal
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.rag.document_processor import DocumentProcessor
from app.core.config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP


# Async dependency for database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    """
    Get a document repository
    
    Args:
        db: Database session
        
    Returns:
        Document repository
    """
    return DocumentRepository(db)


def get_conversation_repository(db: AsyncSession = Depends(get_db)) -> ConversationRepository:
    """
    Get a conversation repository
    
    Args:
        db: Database session
        
    Returns:
        Conversation repository
    """
    return ConversationRepository(db)


def get_analytics_repository(db: AsyncSession = Depends(get_db)) -> AnalyticsRepository:
    """
    Get an analytics repository
    
    Args:
        db: Database session
        
    Returns:
        Analytics repository
    """
    return AnalyticsRepository(db)


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