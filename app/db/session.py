import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from app.core.config import DATABASE_URL, DATABASE_POOL_SIZE, DATABASE_MAX_OVERFLOW

logger = logging.getLogger("app.db.session")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread safety
db_session = scoped_session(SessionLocal)

# Base class for SQLAlchemy models
Base = declarative_base()

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Ensures that sessions are properly closed and rolled back on exceptions.
    
    Usage:
        with get_db_session() as session:
            # Use session for database operations
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()

def init_db():
    """
    Initialize the database by creating all tables.
    This should be called during application startup.
    """
    logger.info("Initializing database")
    Base.metadata.create_all(bind=engine)