from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.db.repositories.notification_repository import NotificationRepository
from app.models.notification import Notification
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter()


@router.get("/notifications", response_model=List[Notification])
async def get_notifications(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notifications for the current user
    
    Args:
        skip: Number of notifications to skip
        limit: Maximum number of notifications to return
        unread_only: Whether to return only unread notifications
        
    Returns:
        List of notifications
    """
    notification_repo = NotificationRepository(db)
    notifications = await notification_repo.get_user_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    return notifications


@router.get("/notifications/count", response_model=int)
async def count_unread_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Count unread notifications for the current user
    
    Returns:
        Number of unread notifications
    """
    notification_repo = NotificationRepository(db)
    count = await notification_repo.count_unread_notifications(current_user.id)
    
    return count


@router.get("/notifications/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a notification by ID
    
    Args:
        notification_id: Notification ID
        
    Returns:
        Notification if found
    """
    notification_repo = NotificationRepository(db)
    notification = await notification_repo.get_by_id(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )
    
    # Check if notification belongs to the current user
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this notification"
        )
    
    return notification


@router.post("/notifications/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read
    
    Args:
        notification_id: Notification ID
        
    Returns:
        Updated notification
    """
    notification_repo = NotificationRepository(db)
    
    # Get notification
    notification = await notification_repo.get_by_id(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )
    
    # Check if notification belongs to the current user
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this notification"
        )
    
    # Mark as read
    success = await notification_repo.mark_as_read(notification_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )
    
    # Get updated notification
    updated_notification = await notification_repo.get_by_id(notification_id)
    return updated_notification


@router.post("/notifications/read-all", response_model=int)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all notifications for the current user as read
    
    Returns:
        Number of notifications marked as read
    """
    notification_repo = NotificationRepository(db)
    count = await notification_repo.mark_all_as_read(current_user.id)
    
    return count


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a notification
    
    Args:
        notification_id: Notification ID
    """
    notification_repo = NotificationRepository(db)
    
    # Get notification
    notification = await notification_repo.get_by_id(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )
    
    # Check if notification belongs to the current user
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this notification"
        )
    
    # Delete notification
    success = await notification_repo.delete_notification(notification_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )
    
    return None


@router.delete("/notifications", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all notifications for the current user
    """
    notification_repo = NotificationRepository(db)
    await notification_repo.delete_all_notifications(current_user.id)
    
    return None