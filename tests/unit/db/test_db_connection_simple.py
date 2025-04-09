import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

async def test_connection():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL from environment: {DATABASE_URL}")
    
    # Ensure we're using the correct URL
    if not DATABASE_URL or "asyncpg" not in DATABASE_URL:
        DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/metis_rag"
        print(f"Using hardcoded DATABASE_URL: {DATABASE_URL}")
    
    print(f"Testing connection to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            print(f"Connection successful: {result.scalar()}")
    except Exception as e:
        print(f"Connection failed: {str(e)}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())