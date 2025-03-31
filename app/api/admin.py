from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserCreate, UserUpdate
from app.core.security import get_current_admin_user
from app.db.dependencies import get_db, get_user_repository
from app.db.repositories.user_repository import UserRepository

# Create router
router = APIRouter()

@router.get("/users", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users (admin only)
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        search: Search term for username or email
        current_user: Current user (admin only)
        db: Database session
        
    Returns:
        List of users
    """
    user_repository = await get_user_repository(db)
    
    if search:
        users = await user_repository.search_users(search, skip=skip, limit=limit)
    else:
        users = await user_repository.get_all_users(skip=skip, limit=limit)
    
    return users

@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a user by ID (admin only)
    
    Args:
        user_id: User ID
        current_user: Current user (admin only)
        db: Database session
        
    Returns:
        User
    """
    user_repository = await get_user_repository(db)
    user = await user_repository.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user (admin only)
    
    Args:
        user_data: User creation data
        current_user: Current user (admin only)
        db: Database session
        
    Returns:
        Created user
    """
    try:
        user_repository = await get_user_repository(db)
        user = await user_repository.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user (admin only)
    
    Args:
        user_id: User ID
        user_data: User update data
        current_user: Current user (admin only)
        db: Database session
        
    Returns:
        Updated user
    """
    try:
        user_repository = await get_user_repository(db)
        updated_user = await user_repository.update_user(user_id, user_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user (admin only)
    
    Args:
        user_id: User ID
        current_user: Current user (admin only)
        db: Database session
        
    Returns:
        Success message
    """
    # Prevent deleting yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user_repository = await get_user_repository(db)
    success = await user_repository.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}