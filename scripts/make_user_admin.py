#!/usr/bin/env python
"""
Script to make a user an admin
"""
import asyncio
import sys
import os
from uuid import UUID

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_session
from app.db.repositories.user_repository import UserRepository
from app.models.user import UserUpdate


async def make_user_admin(username: str):
    """
    Make a user an admin
    
    Args:
        username: Username of the user to make admin
    """
    print(f"Making user '{username}' an admin...")
    
    async for session in get_session():
        # Get the user repository
        user_repo = UserRepository(session)
        
        # Get the user by username
        user = await user_repo.get_by_username(username)
        
        if not user:
            print(f"User '{username}' not found")
            return
        
        # Check if user is already an admin
        if user.is_admin:
            print(f"User '{username}' is already an admin")
            return
        
        # Update the user to make them an admin
        user_data = UserUpdate(is_admin=True)
        updated_user = await user_repo.update_user(user.id, user_data)
        
        if updated_user:
            print(f"User '{username}' is now an admin")
        else:
            print(f"Failed to update user '{username}'")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_user_admin.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(make_user_admin(username))