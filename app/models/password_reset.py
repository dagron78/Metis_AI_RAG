from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: str

class PasswordResetToken(BaseModel):
    """Password reset token model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    is_used: bool = False

class PasswordReset(BaseModel):
    """Password reset model"""
    token: str
    password: str
    confirm_password: str