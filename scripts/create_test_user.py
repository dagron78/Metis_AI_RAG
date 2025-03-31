import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import AsyncSessionLocal
from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate

async def create_test_user():
    """Check if there are any users in the database and create a test user if needed"""
    
    async with AsyncSessionLocal() as session:
        # Check if there are any users
        user_repository = UserRepository(session)
        users = await user_repository.get_all_users()
        
        if users:
            print(f"Found {len(users)} users in the database:")
            for user in users:
                print(f"  - {user.username} (email: {user.email}, admin: {user.is_admin})")
        else:
            print("No users found in the database. Creating a test user...")
            
            # Create a test user
            test_user = UserCreate(
                username="testuser",
                email="test@example.com",
                password="password123",
                full_name="Test User",
                is_active=True,
                is_admin=True
            )
            
            try:
                user = await user_repository.create_user(test_user)
                print(f"Test user created successfully: {user.username} (email: {user.email}, admin: {user.is_admin})")
            except Exception as e:
                print(f"Error creating test user: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_test_user())