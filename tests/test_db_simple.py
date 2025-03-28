import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def test_db_connection():
    print("Testing database connection...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            print(f"Connection successful: {result.scalar()}")
    except Exception as e:
        print(f"Connection failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_db_connection())