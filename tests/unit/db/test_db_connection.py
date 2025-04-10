import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

async def test_connection():
    # Load environment variables from .env file in the project root
    env_path = os.path.join(project_root, ".env")
    load_dotenv(env_path)
    
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