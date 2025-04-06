"""
Database session management
"""
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import SETTINGS

logger = logging.getLogger("app.db.session")

# Create SQLAlchemy base
Base = declarative_base()

# Create async engine with connection pooling
print(f"DATABASE_URL in session.py: {SETTINGS.database_url}")  # Debug print
if SETTINGS.database_type.startswith("sqlite"):
    # SQLite doesn't support pool_size and max_overflow
    engine = create_async_engine(
        SETTINGS.database_url,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,  # Verify connections before using them
    )
else:
    engine = create_async_engine(
        SETTINGS.database_url,
        echo=False,  # Set to True for SQL query logging
        pool_size=SETTINGS.database_pool_size,
        max_overflow=SETTINGS.database_max_overflow,
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,   # Recycle connections after 1 hour
        # Use a specific execution option to handle async operations
        execution_options={
            "isolation_level": "READ COMMITTED"
        }
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    future=True,
    class_=AsyncSession
)
# Create a function to get a session
async def get_session():
    """
    Get a database session.
    
    This is an async generator that yields a session and handles proper cleanup.
    The session is automatically closed when the generator is closed.
    
    Yields:
        AsyncSession: Database session
    """
    # Create a new session
    session = AsyncSessionLocal()
    
    # Track if we've yielded the session
    session_yielded = False
    
    try:
        # Yield the session to the caller
        session_yielded = True
        yield session
    except Exception as e:
        # Log the error
        logger.error(f"Session error: {str(e)}")
        
        # Ensure transaction is rolled back on error
        if session_yielded:
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.warning(f"Error rolling back session: {str(rollback_error)}")
        
        # Re-raise the exception
        raise
    finally:
        # Clean up the session
        if session_yielded:
            try:
                # Check if the session is in a transaction
                if session.in_transaction():
                    # Roll back any active transaction
                    await session.rollback()
                
                # Close the session to return connections to the pool
                await session.close()
                
                # Force garbage collection to clean up any lingering references
                import gc
                gc.collect()
            except Exception as e:
                logger.warning(f"Error during session cleanup: {str(e)}")

async def init_db():
    """
    Initialize the database by creating all tables.
    This should be called during application startup.
    """
    logger.info("Initializing database")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)