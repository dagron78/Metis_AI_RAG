from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, and_, select, text, update, desc
from sqlalchemy.dialects.postgresql import UUID as SQLUUID

from app.db.models import Notification as DBNotification, User as DBUser
from app.models.notification import Notification as PydanticNotification, NotificationCreate
from app.db.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[DBNotification]):
    """
    Repository for Notification model
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DBNotification)
    
    async def get_by_id(self, id: Union[str, UUID]) -> Optional[PydanticNotification]:
        """
        Get a notification by ID
        
        Args:
            id: Notification ID
            
        Returns:
            Notification if found, None otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(id, str):
            try:
                id = UUID(id)
            except ValueError:
                return None
        
        stmt = select(DBNotification).where(DBNotification.id == id)
        result = await self.session.execute(stmt)
        notification = result.scalars().first()
        
        if not notification:
            return None
        
        return self._db_notification_to_pydantic(notification)
    
    async def create_notification(self, notification_data: NotificationCreate) -> PydanticNotification:
        """
        Create a new notification
        
        Args:
            notification_data: Notification creation data
            
        Returns:
            Created notification
        """
        # Create notification
        notification = DBNotification(
            user_id=UUID(notification_data.user_id) if isinstance(notification_data.user_id, str) else notification_data.user_id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            data=notification_data.data,
            is_read=notification_data.is_read,
            created_at=datetime.utcnow()
        )
        
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        
        return self._db_notification_to_pydantic(notification)
    
    async def get_user_notifications(
        self, 
        user_id: Union[str, UUID], 
        skip: int = 0, 
        limit: int = 20,
        unread_only: bool = False
    ) -> List[PydanticNotification]:
        """
        Get notifications for a user
        
        Args:
            user_id: User ID
            skip: Number of notifications to skip
            limit: Maximum number of notifications to return
            unread_only: Whether to return only unread notifications
            
        Returns:
            List of notifications
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return []
        
        # Build query
        query = select(DBNotification).where(DBNotification.user_id == user_id)
        
        if unread_only:
            query = query.where(DBNotification.is_read == False)
        
        # Order by created_at (newest first) and apply pagination
        query = query.order_by(desc(DBNotification.created_at)).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        notifications = result.scalars().all()
        
        return [self._db_notification_to_pydantic(notification) for notification in notifications]
    
    async def mark_as_read(self, notification_id: Union[str, UUID]) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: Notification ID
            
        Returns:
            True if notification was marked as read, False otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(notification_id, str):
            try:
                notification_id = UUID(notification_id)
            except ValueError:
                return False
        
        # Get notification
        stmt = select(DBNotification).where(DBNotification.id == notification_id)
        result = await self.session.execute(stmt)
        notification = result.scalars().first()
        
        if not notification:
            return False
        
        # Mark as read
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        
        await self.session.commit()
        return True
    
    async def mark_all_as_read(self, user_id: Union[str, UUID]) -> int:
        """
        Mark all notifications for a user as read
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return 0
        
        # Get unread notifications
        stmt = select(DBNotification).where(
            and_(
                DBNotification.user_id == user_id,
                DBNotification.is_read == False
            )
        )
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()
        
        if not notifications:
            return 0
        
        # Mark all as read
        now = datetime.utcnow()
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
        
        await self.session.commit()
        return len(notifications)
    
    async def delete_notification(self, notification_id: Union[str, UUID]) -> bool:
        """
        Delete a notification
        
        Args:
            notification_id: Notification ID
            
        Returns:
            True if notification was deleted, False otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(notification_id, str):
            try:
                notification_id = UUID(notification_id)
            except ValueError:
                return False
        
        # Get notification
        stmt = select(DBNotification).where(DBNotification.id == notification_id)
        result = await self.session.execute(stmt)
        notification = result.scalars().first()
        
        if not notification:
            return False
        
        # Delete notification
        await self.session.delete(notification)
        await self.session.commit()
        
        return True
    
    async def delete_all_notifications(self, user_id: Union[str, UUID]) -> int:
        """
        Delete all notifications for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications deleted
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return 0
        
        # Get notifications
        stmt = select(DBNotification).where(DBNotification.user_id == user_id)
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()
        
        if not notifications:
            return 0
        
        # Delete all notifications
        for notification in notifications:
            await self.session.delete(notification)
        
        await self.session.commit()
        return len(notifications)
    
    async def count_unread_notifications(self, user_id: Union[str, UUID]) -> int:
        """
        Count unread notifications for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of unread notifications
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return 0
        
        # Count unread notifications
        stmt = select(func.count()).where(
            and_(
                DBNotification.user_id == user_id,
                DBNotification.is_read == False
            )
        )
        result = await self.session.execute(stmt)
        count = result.scalar()
        
        return count or 0
    
    async def create_document_shared_notification(
        self, 
        user_id: Union[str, UUID], 
        document_id: Union[str, UUID], 
        document_name: str, 
        shared_by_username: str,
        permission_level: str
    ) -> PydanticNotification:
        """
        Create a notification for a document being shared with a user
        
        Args:
            user_id: User ID
            document_id: Document ID
            document_name: Document name
            shared_by_username: Username of the user who shared the document
            permission_level: Permission level granted
            
        Returns:
            Created notification
        """
        # Create notification data
        notification_data = NotificationCreate(
            user_id=str(user_id) if isinstance(user_id, UUID) else user_id,
            type="document_shared",
            title=f"{shared_by_username} shared a document with you",
            message=f"{shared_by_username} shared '{document_name}' with you with {permission_level} permission.",
            data={
                "document_id": str(document_id) if isinstance(document_id, UUID) else document_id,
                "document_name": document_name,
                "shared_by": shared_by_username,
                "permission_level": permission_level
            },
            is_read=False
        )
        
        # Create notification
        return await self.create_notification(notification_data)
    
    def _db_notification_to_pydantic(self, db_notification: DBNotification) -> PydanticNotification:
        """
        Convert a database notification to a Pydantic notification
        
        Args:
            db_notification: Database notification
            
        Returns:
            Pydantic notification
        """
        return PydanticNotification(
            id=str(db_notification.id),
            user_id=str(db_notification.user_id),
            type=db_notification.type,
            title=db_notification.title,
            message=db_notification.message,
            data=db_notification.data,
            is_read=db_notification.is_read,
            created_at=db_notification.created_at,
            read_at=db_notification.read_at
        )