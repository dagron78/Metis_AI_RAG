from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid

class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    
    class Config:
        arbitrary_types_allowed = True

class UserCreate(UserBase):
    """User creation model"""
    password: str
    
    class Config:
        arbitrary_types_allowed = True

class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    
    class Config:
        arbitrary_types_allowed = True

class User(UserBase):
    """User model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class UserInDB(User):
    """User model with password hash (for internal use)"""
    password_hash: str
    
    class Config:
        arbitrary_types_allowed = True