from typing import Generator
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.analytics_repository import AnalyticsRepository


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_document_repository(db: Session) -> DocumentRepository:
    """
    Get a document repository
    
    Args:
        db: Database session
        
    Returns:
        Document repository
    """
    return DocumentRepository(db)


def get_conversation_repository(db: Session) -> ConversationRepository:
    """
    Get a conversation repository
    
    Args:
        db: Database session
        
    Returns:
        Conversation repository
    """
    return ConversationRepository(db)


def get_analytics_repository(db: Session) -> AnalyticsRepository:
    """
    Get an analytics repository
    
    Args:
        db: Database session
        
    Returns:
        Analytics repository
    """
    return AnalyticsRepository(db)