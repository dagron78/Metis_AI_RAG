import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import AsyncSessionLocal
from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate

async def create_custom_test_user():
    """Create a custom test user with specific credentials"""
    
    # Define the custom test user credentials
    username = "metistest"
    password = "metistest123"
    email = "metistest@example.com"
    full_name = "Metis Test User"
    
    async with AsyncSessionLocal() as session:
        # Check if the user already exists
        user_repository = UserRepository(session)
        users = await user_repository.get_all_users()
        
        existing_user = next((user for user in users if user.username == username), None)
        
        if existing_user:
            print(f"User '{username}' already exists.")
            return
        
        # Create the custom test user
        test_user = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            is_active=True,
            is_admin=True
        )
        
        try:
            user = await user_repository.create_user(test_user)
            print(f"Custom test user created successfully:")
            print(f"  - Username: {user.username}")
            print(f"  - Password: {password}")
            print(f"  - Email: {user.email}")
            print(f"  - Full Name: {full_name}")
            print(f"  - Admin: {user.is_admin}")
            
            # Save credentials to .clinerules-code file
            with open('.clinerules-code', 'a') as f:
                f.write("\n\n# Metis RAG Test User Credentials\n")
                f.write(f"# Username: {username}\n")
                f.write(f"# Password: {password}\n")
                f.write(f"# Email: {email}\n")
                f.write(f"# Full Name: {full_name}\n")
                f.write(f"# Admin: True\n")
            
            print("\nCredentials saved to .clinerules-code file.")
            
        except Exception as e:
            print(f"Error creating custom test user: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_custom_test_user())