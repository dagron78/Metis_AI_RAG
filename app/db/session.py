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
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """
    Initialize the database by creating all tables.
    This should be called during application startup.
    """
    logger.info("Initializing database")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)