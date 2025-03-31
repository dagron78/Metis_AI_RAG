#!/usr/bin/env python3
"""
Create a test user for authentication testing

This script creates a test user with a known password directly in the database,
bypassing the API to ensure we have a valid user for testing.
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import uuid

# Add the project root to the Python path
sys.path.append('.')

from app.db.session import AsyncSessionLocal, init_db
from app.db.models import User
from app.core.security import get_password_hash

async def create_test_user():
    """Create a test user in the database"""
    # Initialize the database
    await init_db()
    
    # Create a session
    async with AsyncSessionLocal() as session:
        # Check if the test user already exists
        result = await session.execute(select(User).where(User.username == 'testuser'))
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"Test user already exists with ID: {existing_user.id}")
            print(f"Updating password...")
            
            # Update the password
            existing_user.password_hash = get_password_hash("Test@password123")
            await session.commit()
            
            print(f"Password updated for user: {existing_user.username}")
            return
        
        # Create a new test user
        test_user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="testuser@example.com",
            password_hash=get_password_hash("Test@password123"),
            full_name="Test User",
            is_active=True,
            is_admin=False,
            created_at=datetime.utcnow()
        )
        
        # Add the user to the database
        session.add(test_user)
        await session.commit()
        
        print(f"Test user created with ID: {test_user.id}")
        print(f"Username: {test_user.username}")
        print(f"Password: Test@password123")

if __name__ == "__main__":
    asyncio.run(create_test_user())