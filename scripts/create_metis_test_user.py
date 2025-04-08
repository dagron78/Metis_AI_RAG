import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import AsyncSessionLocal
from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate

async def create_metis_test_user():
    """Create a specific test user for Metis RAG testing"""
    
    async with AsyncSessionLocal() as session:
        # Check if the user already exists
        user_repository = UserRepository(session)
        
        try:
            # Try to get the user by username
            existing_user = await user_repository.get_user_by_username("metistest")
            
            if existing_user:
                print(f"User 'metistest' already exists (email: {existing_user.email}, admin: {existing_user.is_admin})")
                return
        except Exception:
            # User doesn't exist, continue with creation
            pass
            
        print("Creating metistest user...")
        
        # Create the test user with specific credentials
        test_user = UserCreate(
            username="metistest",
            email="metistest@example.com",
            password="metistest123",
            full_name="Metis Test User",
            is_active=True,
            is_admin=True
        )
        
        try:
            user = await user_repository.create_user(test_user)
            print(f"Test user created successfully: {user.username} (email: {user.email}, admin: {user.is_admin})")
        except Exception as e:
            print(f"Error creating test user: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_metis_test_user())