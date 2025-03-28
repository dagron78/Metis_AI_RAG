from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.db.repositories.role_repository import RoleRepository
from app.models.role import Role, RoleCreate, RoleUpdate, UserRole, UserRoleCreate
from app.models.user import User
from app.core.security import get_current_user
from app.core.permissions import has_permission, PERMISSION_MANAGE_ROLES

router = APIRouter()


@router.get("/roles", response_model=List[Role])
async def get_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all roles
    """
    # Only admins or users with manage_roles permission can list all roles
    if not current_user.is_admin and not await RoleRepository(db).user_has_permission(current_user.id, PERMISSION_MANAGE_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to list roles"
        )
    
    roles = await RoleRepository(db).get_all_roles(skip=skip, limit=limit)
    return roles


@router.post("/roles", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    current_user: User = Depends(has_permission(PERMISSION_MANAGE_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new role
    """
    try:
        created_role = await RoleRepository(db).create_role(role)
        return created_role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/roles/{role_id}", response_model=Role)
async def get_role(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a role by ID
    """
    # Only admins or users with manage_roles permission can get role details
    if not current_user.is_admin and not await RoleRepository(db).user_has_permission(current_user.id, PERMISSION_MANAGE_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view role details"
        )
    
    role = await RoleRepository(db).get_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    return role


@router.put("/roles/{role_id}", response_model=Role)
async def update_role(
    role_id: str,
    role_update: RoleUpdate,
    current_user: User = Depends(has_permission(PERMISSION_MANAGE_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a role
    """
    try:
        updated_role = await RoleRepository(db).update_role(role_id, role_update)
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        return updated_role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    current_user: User = Depends(has_permission(PERMISSION_MANAGE_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a role
    """
    # Check if role exists
    role = await RoleRepository(db).get_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Don't allow deleting the admin role
    if role.name == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the admin role"
        )
    
    # Delete the role
    deleted = await RoleRepository(db).delete_role(role_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete role"
        )
    
    return None


@router.get("/users/{user_id}/roles", response_model=List[Role])
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all roles assigned to a user
    """
    # Users can view their own roles, admins can view anyone's roles
    if not current_user.is_admin and current_user.id != user_id and not await RoleRepository(db).user_has_permission(current_user.id, PERMISSION_MANAGE_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view user roles"
        )
    
    roles = await RoleRepository(db).get_user_roles(user_id)
    return roles


@router.post("/users/{user_id}/roles", response_model=UserRole, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: str,
    role_id: str,
    current_user: User = Depends(has_permission(PERMISSION_MANAGE_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign a role to a user
    """
    try:
        user_role = await RoleRepository(db).assign_role_to_user(user_id, role_id)
        return user_role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    current_user: User = Depends(has_permission(PERMISSION_MANAGE_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a role from a user
    """
    # Check if user has the role
    role_repo = RoleRepository(db)
    roles = await role_repo.get_user_roles(user_id)
    role_ids = [role.id for role in roles]
    
    if role_id not in role_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User does not have role with ID {role_id}"
        )
    
    # Don't allow removing the admin role from the last admin user
    role = await role_repo.get_by_id(role_id)
    if role and role.name == "admin":
        # Check if this is the last admin user
        admin_users = await role_repo.get_role_users(role_id)
        if len(admin_users) == 1 and admin_users[0] == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the admin role from the last admin user"
            )
    
    # Remove the role
    removed = await role_repo.remove_role_from_user(user_id, role_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove role from user"
        )
    
    return None


@router.get("/roles/{role_id}/users", response_model=List[str])
async def get_role_users(
    role_id: str,
    current_user: User = Depends(has_permission(PERMISSION_MANAGE_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users assigned to a role
    """
    # Check if role exists
    role = await RoleRepository(db).get_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Get users with this role
    users = await RoleRepository(db).get_role_users(role_id)
    return users


@router.get("/check-permission/{permission}", response_model=bool)
async def check_user_permission(
    permission: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if the current user has a specific permission
    """
    # Admin users have all permissions
    if current_user.is_admin:
        return True
    
    # Check if user has the permission
    has_perm = await RoleRepository(db).user_has_permission(current_user.id, permission)
    return has_perm