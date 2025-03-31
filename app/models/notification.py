from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class NotificationBase(BaseModel):
    """Base notification model"""
    type: str  # e.g., 'document_shared', 'mention', 'system'
    title: str
    message: str
    data: Dict[str, Any] = {}
    is_read: bool = False
    
    class Config:
        arbitrary_types_allowed = True

class NotificationCreate(NotificationBase):
    """Notification creation model"""
    user_id: str
    
    class Config:
        arbitrary_types_allowed = True

class Notification(NotificationBase):
    """Notification model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    read_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True