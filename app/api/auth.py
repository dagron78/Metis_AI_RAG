from datetime import timedelta, datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import uuid

from app.models.user import User, UserCreate, UserUpdate
from app.core.security import (
    create_access_token, create_refresh_token, verify_refresh_token,
    get_current_user, get_current_active_user, get_current_admin_user,
    Token, RefreshToken
)
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
    Get an access token and refresh token for a user
    
    This endpoint authenticates a user with username and password,
    and returns JWT access and refresh tokens if successful.
    
    Args:
        request: The FastAPI request object
        form_data: The OAuth2 password request form data
        db: The database session
        rate_limiter: Optional rate limiter dependency
        
    Returns:
        A Token object containing the access token, refresh token, and expiration
        
    Raises:
        HTTPException: If authentication fails
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
    
    # Update user's last login time
    await user_repository.update_user(user.id, {"last_login": datetime.utcnow()})
    
    # Create tokens with additional claims
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "aud": SETTINGS.jwt_audience,
        "iss": SETTINGS.jwt_issuer,
        "jti": str(uuid.uuid4())  # Unique token ID
    }
    
    # Create access token
    access_token_expires = timedelta(minutes=SETTINGS.access_token_expire_minutes)
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_expires = timedelta(days=SETTINGS.refresh_token_expire_days)
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": SETTINGS.access_token_expire_minutes * 60,  # in seconds
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    request: Request,
    refresh_token_data: RefreshToken,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh an access token using a refresh token
    
    This endpoint validates a refresh token and issues a new access token
    if the refresh token is valid.
    
    Args:
        request: The FastAPI request object
        refresh_token_data: The refresh token data
        db: The database session
        
    Returns:
        A Token object containing the new access token and expiration
        
    Raises:
        HTTPException: If the refresh token is invalid
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Verify refresh token
    payload = verify_refresh_token(refresh_token_data.refresh_token)
    if not payload:
        # Log failed refresh attempt
        logger.warning(f"Failed token refresh attempt, IP: {client_ip}, User-Agent: {user_agent}")
        
        # Create and log security event
        security_event = SecurityEvent(
            event_type="failed_token_refresh",
            severity="medium",
            source_ip=client_ip,
            user_agent=user_agent,
            details={"reason": "Invalid refresh token"}
        )
        log_security_event(security_event)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user information from payload
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists
    user_repository = await get_user_repository(db)
    user = await user_repository.get_by_username(username)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful token refresh
    logger.info(f"Successful token refresh for user: {username}, IP: {client_ip}")
    
    # Create and log security event for successful token refresh
    security_event = SecurityEvent(
        event_type="successful_token_refresh",
        severity="low",
        source_ip=client_ip,
        username=username,
        user_agent=user_agent
    )
    log_security_event(security_event)
    
    # Update user's last login time
    await user_repository.update_user(user.id, {"last_login": datetime.utcnow()})
    
    # Create new token with the same claims as the refresh token
    # but with a new JTI (JWT ID)
    token_data = {
        "sub": username,
        "user_id": user_id,
        "aud": payload.get("aud", SETTINGS.jwt_audience),
        "iss": payload.get("iss", SETTINGS.jwt_issuer),
        "jti": str(uuid.uuid4())  # New unique token ID
    }
    
    # Create new access token
    access_token_expires = timedelta(minutes=SETTINGS.access_token_expire_minutes)
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": SETTINGS.access_token_expire_minutes * 60,  # in seconds
        "refresh_token": refresh_token_data.refresh_token  # Return the same refresh token
    }

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