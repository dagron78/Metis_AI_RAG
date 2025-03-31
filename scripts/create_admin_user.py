import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import AsyncSessionLocal
from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserUpdate

async def create_admin_user():
    """Create an admin user or update an existing user to be an admin"""
    
    admin_username = "admin"
    admin_email = "admin@example.com"
    admin_password = "admin123"
    
    async with AsyncSessionLocal() as session:
        user_repository = UserRepository(session)
        
        # Check if admin user already exists
        admin_user = await user_repository.get_by_username(admin_username)
        
        if admin_user:
            print(f"Admin user already exists: {admin_user.username}")
            
            # Make sure the user is an admin
            if not admin_user.is_admin:
                print(f"Updating {admin_user.username} to be an admin...")
                update_data = UserUpdate(is_admin=True)
                updated_user = await user_repository.update_user(admin_user.id, update_data)
                print(f"User updated: {updated_user.username} (admin: {updated_user.is_admin})")
        else:
            print(f"Creating admin user: {admin_username}")
            
            # Create admin user
            admin_user_data = UserCreate(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                full_name="Admin User",
                is_active=True,
                is_admin=True
            )
            
            try:
                user = await user_repository.create_user(admin_user_data)
                print(f"Admin user created successfully: {user.username} (email: {user.email}, admin: {user.is_admin})")
                print(f"Username: {admin_username}")
                print(f"Password: {admin_password}")
            except ValueError as e:
                print(f"Error creating admin user: {str(e)}")
                
                # Try with a different email if the username is taken but email is different
                try:
                    existing_user = await user_repository.get_by_username(admin_username)
                    if existing_user and existing_user.email != admin_email:
                        admin_user_data.email = f"admin_{os.urandom(4).hex()}@example.com"
                        user = await user_repository.create_user(admin_user_data)
                        print(f"Admin user created with alternative email: {user.username} (email: {user.email}, admin: {user.is_admin})")
                        print(f"Username: {admin_username}")
                        print(f"Password: {admin_password}")
                except Exception as e2:
                    print(f"Error creating admin user with alternative email: {str(e2)}")

if __name__ == "__main__":
    asyncio.run(create_admin_user())