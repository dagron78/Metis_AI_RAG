from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class RoleBase(BaseModel):
    """Base role model"""
    name: str
    description: Optional[str] = None
    permissions: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class RoleCreate(RoleBase):
    """Role creation model"""
    
    class Config:
        arbitrary_types_allowed = True

class RoleUpdate(BaseModel):
    """Role update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True

class Role(RoleBase):
    """Role model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class UserRoleBase(BaseModel):
    """Base user-role association model"""
    user_id: str
    role_id: str
    
    class Config:
        arbitrary_types_allowed = True

class UserRoleCreate(UserRoleBase):
    """User-role association creation model"""
    
    class Config:
        arbitrary_types_allowed = True

class UserRole(UserRoleBase):
    """User-role association model"""
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True