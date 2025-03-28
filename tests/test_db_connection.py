import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

async def test_connection():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL from environment: {database_url}")
    
    # Ensure we're using the correct URL
    if not database_url or "asyncpg" not in database_url:
        database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/metis_rag"
        print(f"Using hardcoded DATABASE_URL: {database_url}")
    
    print(f"Testing connection to {database_url}")
    
    # Create engine
    engine = create_async_engine(
        database_url,
        echo=True,  # Enable SQL logging
    )
    
    # Test connection
    try:
        async with engine.begin() as conn:
            # Execute a simple query
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1"))
            print(f"Connection successful: {result.scalar()}")
    except Exception as e:
        print(f"Connection failed: {str(e)}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())