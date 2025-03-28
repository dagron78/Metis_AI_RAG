from typing import List, Optional, Union, Dict, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.db.repositories.role_repository import RoleRepository
from app.core.security import get_current_user
from app.models.user import User


class RoleChecker:
    """
    Role-based permission checker
    """
    
    def __init__(self, required_roles: List[str] = None, required_permissions: List[str] = None):
        """
        Initialize the role checker
        
        Args:
            required_roles: List of required role names (any one is sufficient)
            required_permissions: List of required permissions (any one is sufficient)
        """
        self.required_roles = required_roles or []
        self.required_permissions = required_permissions or []
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """
        Check if the user has the required roles or permissions
        
        Args:
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            Current user if they have the required roles or permissions
            
        Raises:
            HTTPException: If the user doesn't have the required roles or permissions
        """
        # Admin users bypass all permission checks
        if current_user.is_admin:
            return current_user
        
        # If no roles or permissions are required, allow access
        if not self.required_roles and not self.required_permissions:
            return current_user
        
        # Check roles and permissions
        role_repo = RoleRepository(db)
        
        # Check if user has any of the required roles
        for role_name in self.required_roles:
            if await role_repo.user_has_role(current_user.id, role_name):
                return current_user
        
        # Check if user has any of the required permissions
        for permission in self.required_permissions:
            if await role_repo.user_has_permission(current_user.id, permission):
                return current_user
        
        # If we get here, the user doesn't have the required roles or permissions
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )


# Convenience functions for common permission checks

def has_role(role_name: str):
    """
    Check if the user has a specific role
    
    Args:
        role_name: Role name
        
    Returns:
        RoleChecker dependency
    """
    return RoleChecker(required_roles=[role_name])


def has_permission(permission: str):
    """
    Check if the user has a specific permission
    
    Args:
        permission: Permission name
        
    Returns:
        RoleChecker dependency
    """
    return RoleChecker(required_permissions=[permission])


def has_any_role(roles: List[str]):
    """
    Check if the user has any of the specified roles
    
    Args:
        roles: List of role names
        
    Returns:
        RoleChecker dependency
    """
    return RoleChecker(required_roles=roles)


def has_any_permission(permissions: List[str]):
    """
    Check if the user has any of the specified permissions
    
    Args:
        permissions: List of permission names
        
    Returns:
        RoleChecker dependency
    """
    return RoleChecker(required_permissions=permissions)


def has_role_or_permission(role_name: str, permission: str):
    """
    Check if the user has a specific role or permission
    
    Args:
        role_name: Role name
        permission: Permission name
        
    Returns:
        RoleChecker dependency
    """
    return RoleChecker(required_roles=[role_name], required_permissions=[permission])


# Common role names
ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"

# Common permission names
PERMISSION_READ = "read"
PERMISSION_WRITE = "write"
PERMISSION_DELETE = "delete"
PERMISSION_SHARE = "share"
PERMISSION_MANAGE_USERS = "manage_users"
PERMISSION_MANAGE_ROLES = "manage_roles"