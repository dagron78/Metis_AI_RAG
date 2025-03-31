#!/usr/bin/env python3
"""
Script to create default roles in the database.
This script creates the basic roles (admin, editor, viewer) with their respective permissions.
"""

import asyncio
import sys
import os
import logging
from uuid import UUID
from sqlalchemy import select

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import AsyncSessionLocal, init_db
from app.db.models import Role, UserRole, User
from app.db.repositories.role_repository import RoleRepository
from app.models.role import RoleCreate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define default roles and their permissions
DEFAULT_ROLES = [
    {
        "name": "admin",
        "description": "Administrator with full access to all features",
        "permissions": {
            "read": True,
            "write": True,
            "delete": True,
            "share": True,
            "manage_users": True,
            "manage_roles": True,
            "manage_system": True
        }
    },
    {
        "name": "editor",
        "description": "Editor with access to create and edit documents",
        "permissions": {
            "read": True,
            "write": True,
            "delete": True,
            "share": True,
            "manage_users": False,
            "manage_roles": False,
            "manage_system": False
        }
    },
    {
        "name": "viewer",
        "description": "Viewer with read-only access to documents",
        "permissions": {
            "read": True,
            "write": False,
            "delete": False,
            "share": False,
            "manage_users": False,
            "manage_roles": False,
            "manage_system": False
        }
    }
]


async def create_default_roles():
    """Create default roles in the database"""
    logger.info("Initializing database connection...")
    await init_db()
    
    async with AsyncSessionLocal() as session:
        role_repo = RoleRepository(session)
        
        for role_data in DEFAULT_ROLES:
            # Check if role already exists
            existing_role = await role_repo.get_by_name(role_data["name"])
            
            if existing_role:
                logger.info(f"Role '{role_data['name']}' already exists, updating permissions...")
                # Update existing role
                await role_repo.update_role(
                    existing_role.id,
                    {
                        "description": role_data["description"],
                        "permissions": role_data["permissions"]
                    }
                )
            else:
                logger.info(f"Creating role '{role_data['name']}'...")
                # Create new role
                role_create = RoleCreate(
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"]
                )
                await role_repo.create_role(role_create)
        
        logger.info("Default roles created/updated successfully")
        
        # Assign admin role to admin users
        logger.info("Assigning admin role to admin users...")
        
        # Get admin role
        admin_role = await role_repo.get_by_name("admin")
        if not admin_role:
            logger.error("Admin role not found, cannot assign to users")
            return
        
        # Get all admin users
        stmt = select(User).where(User.is_admin == True)
        admin_users = await session.execute(stmt)
        admin_users = admin_users.scalars().all()
        
        if not admin_users:
            logger.warning("No admin users found in the database")
            return
        
        # Assign admin role to each admin user
        for user in admin_users:
            logger.info(f"Assigning admin role to user '{user.username}'...")
            try:
                await role_repo.assign_role_to_user(str(user.id), admin_role.id)
                logger.info(f"Admin role assigned to user '{user.username}' successfully")
            except ValueError as e:
                # This might happen if the user already has the role
                logger.info(f"Note: {str(e)}")
        
        logger.info("Admin role assignment completed")


if __name__ == "__main__":
    asyncio.run(create_default_roles())