from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class OrganizationBase(BaseModel):
    """Base organization model"""
    name: str
    description: Optional[str] = None
    settings: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class OrganizationCreate(OrganizationBase):
    """Organization creation model"""
    
    class Config:
        arbitrary_types_allowed = True

class OrganizationUpdate(BaseModel):
    """Organization update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True

class Organization(OrganizationBase):
    """Organization model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class OrganizationMemberBase(BaseModel):
    """Base organization member model"""
    organization_id: str
    user_id: str
    role: str  # 'owner', 'admin', 'member'
    
    class Config:
        arbitrary_types_allowed = True

class OrganizationMemberCreate(OrganizationMemberBase):
    """Organization member creation model"""
    
    class Config:
        arbitrary_types_allowed = True

class OrganizationMember(OrganizationMemberBase):
    """Organization member model"""
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True