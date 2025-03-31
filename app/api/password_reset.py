from datetime import datetime, timedelta
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, EmailStr

from app.db.dependencies import get_db, get_user_repository
from app.db.repositories.user_repository import UserRepository
from app.core.config import SETTINGS
from app.core.email import send_email

# Create router
router = APIRouter()

# Models
class PasswordResetRequest(BaseModel):
    """
    Password reset request model
    """
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """
    Password reset confirmation model
    """
    token: str
    password: str
    confirm_password: str

class PasswordResetToken(BaseModel):
    """
    Password reset token model
    """
    id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    is_used: bool = False

# Endpoints
@router.post("/request-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request_data: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset
    
    Args:
        request_data: Password reset request data
        request: Request object
        db: Database session
        
    Returns:
        Success message
    """
    # Get user by email
    user_repository = await get_user_repository(db)
    user = await user_repository.get_by_email(request_data.email)
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    # Generate token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Store token in database
    try:
        # Use raw SQL to insert the token with text() function
        query = text("""
        INSERT INTO password_reset_tokens (id, user_id, token, created_at, expires_at, is_used)
        VALUES (:id, :user_id, :token, :created_at, :expires_at, :is_used)
        """)
        values = {
            "id": str(uuid.uuid4()),
            "user_id": str(user.id),
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_used": False
        }
        
        await db.execute(query, values)
        await db.commit()
    except Exception as e:
        print(f"Error storing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing request"
        )
    
    # Generate reset link
    base_url = str(request.base_url).rstrip('/')
    reset_link = f"{base_url}/reset-password?token={token}"
    
    # Send email
    try:
        # In a real application, this would send an actual email
        # For now, we'll just print the reset link to the console
        print(f"Password reset link for {user.email}: {reset_link}")
        
        # Uncomment this to send a real email
        # subject = "Password Reset Request"
        # body = f"""
        # Hello {user.username},
        # 
        # You have requested to reset your password. Please click the link below to reset your password:
        # 
        # {reset_link}
        # 
        # This link will expire in 24 hours.
        # 
        # If you did not request this, please ignore this email.
        # 
        # Regards,
        # The Metis RAG Team
        # """
        # await send_email(user.email, subject, body)
    except Exception as e:
        print(f"Error sending email: {str(e)}")
    
    return {"message": "If your email is registered, you will receive a password reset link"}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using a token
    
    Args:
        reset_data: Password reset confirmation data
        db: Database session
        
    Returns:
        Success message
    """
    # Validate passwords match
    if reset_data.password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Validate password length
    if len(reset_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Get token from database
    try:
        query = text("""
        SELECT id, user_id, token, created_at, expires_at, is_used
        FROM password_reset_tokens
        WHERE token = :token
        """)
        result = await db.execute(query, {"token": reset_data.token})
        token_row = result.fetchone()
        
        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )
        
        # Convert to model
        token_data = PasswordResetToken(
            id=token_row[0],
            user_id=token_row[1],
            token=token_row[2],
            created_at=token_row[3],
            expires_at=token_row[4],
            is_used=token_row[5]
        )
    except Exception as e:
        print(f"Error retrieving token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing request"
        )
    
    # Check if token is valid
    if token_data.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has already been used"
        )
    
    # Check if token is expired
    if token_data.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )
    
    # Update user password
    user_repository = await get_user_repository(db)
    user = await user_repository.get_by_id(token_data.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update password
    await user_repository.update_user(user.id, {"password": reset_data.password})
    
    # Mark token as used
    try:
        query = text("""
        UPDATE password_reset_tokens
        SET is_used = true
        WHERE id = :id
        """)
        await db.execute(query, {"id": token_data.id})
        await db.commit()
    except Exception as e:
        print(f"Error updating token: {str(e)}")
    
    return {"message": "Password reset successfully"}