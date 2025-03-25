from datetime import timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.user import User, UserCreate, UserUpdate
from app.core.security import create_access_token, get_current_user, get_current_active_user, get_current_admin_user, Token
from app.core.config import SETTINGS
from app.core.rate_limit import login_rate_limit
from app.core.security_alerts import SecurityEvent, log_security_event
from app.db.dependencies import get_db, get_user_repository
from app.db.repositories.user_repository import UserRepository

# Setup logging
logger = logging.getLogger("app.api.auth")

# Create router
router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    rate_limiter: None = Depends(login_rate_limit) if SETTINGS.rate_limiting_enabled else None
):
    """
    Get an access token for a user
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Log login attempt
    logger.info(f"Login attempt for user: {form_data.username}, IP: {client_ip}, User-Agent: {user_agent}")
    
    user_repository = await get_user_repository(db)
    user = await user_repository.authenticate_user(form_data.username, form_data.password)
    if not user:
        # Log failed login attempt
        logger.warning(f"Failed login attempt for user: {form_data.username}, IP: {client_ip}, User-Agent: {user_agent}")
        
        # Create and log security event
        security_event = SecurityEvent(
            event_type="failed_login",
            severity="medium",
            source_ip=client_ip,
            username=form_data.username,
            user_agent=user_agent,
            details={"reason": "Incorrect username or password"}
        )
        log_security_event(security_event)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful login
    logger.info(f"Successful login for user: {form_data.username}, IP: {client_ip}")
    
    # Create and log security event for successful login
    security_event = SecurityEvent(
        event_type="successful_login",
        severity="low",
        source_ip=client_ip,
        username=form_data.username,
        user_agent=user_agent
    )
    log_security_event(security_event)
    
    # Create access token
    access_token_expires = timedelta(minutes=SETTINGS.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
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

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user
    """
    try:
        user_repository = await get_user_repository(db)
        updated_user = await user_repository.update_user(current_user.id, user_data)
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/users", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users (admin only)
    """
    user_repository = await get_user_repository(db)
    users = await user_repository.get_all_users(skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a user by ID (admin only or self)
    """
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_repository = await get_user_repository(db)
    user = await user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user