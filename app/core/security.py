from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import logging
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from uuid import UUID

from app.core.config import CORS_ORIGINS, SETTINGS
from app.core.security_alerts import SecurityEvent, log_security_event

# Setup logging
logger = logging.getLogger("app.core.security")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{SETTINGS.api_v1_str}/auth/token")

# Token models
class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str

class TokenData(BaseModel):
    """Token data model for internal use"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    exp: Optional[datetime] = None
    token_type: Optional[str] = None

class RefreshToken(BaseModel):
    """Refresh token request model"""
    refresh_token: str

def setup_security(app: FastAPI) -> None:
    """
    Setup security middleware for the application
    """
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response: Response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Add Referrer-Policy to prevent leaking URL parameters to external sites
        response.headers["Referrer-Policy"] = "same-origin"
        
        # Add HSTS header for HTTPS enforcement
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Add Cache-Control for sensitive pages
        path = request.url.path
        if path in ["/login", "/register", "/forgot-password", "/reset-password"]:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Enhanced Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; "
            "img-src 'self' data:; "
            "connect-src 'self';"
            "form-action 'self';"
        )
        
        return response

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        True if the password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: The plain text password
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=SETTINGS.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SETTINGS.secret_key, algorithm=SETTINGS.algorithm)
    
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT refresh token
    """
    to_encode = data.copy()
    
    # Refresh tokens should have longer expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 7 days for refresh tokens
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SETTINGS.secret_key, algorithm=SETTINGS.algorithm)
    
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The decoded token payload
        
    Raises:
        JWTError: If the token is invalid
    """
    return jwt.decode(
        token,
        SETTINGS.secret_key,
        algorithms=[SETTINGS.algorithm],
        options={"verify_aud": False}  # Don't verify audience claim for now
    )

def verify_refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a refresh token and return the payload if valid
    
    Args:
        refresh_token: The refresh token to verify
        
    Returns:
        The decoded token payload if valid, None otherwise
    """
    try:
        # Use direct jwt.decode instead of decode_token to specify options
        payload = jwt.decode(
            refresh_token,
            SETTINGS.secret_key,
            algorithms=[SETTINGS.algorithm],
            options={"verify_aud": False}  # Don't verify audience claim for now
        )
        
        # Check if it's a refresh token
        if payload.get("token_type") != "refresh":
            logger.warning(f"Invalid token type: {payload.get('token_type', 'none')}, expected 'refresh'")
            return None
        
        # Check required claims
        if "sub" not in payload or "user_id" not in payload:
            logger.warning("Missing required claims ('sub' and 'user_id') in refresh token")
            return None
        
        return payload
    except JWTError as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user from a JWT token
    
    Args:
        token: The JWT token
        
    Returns:
        The user if the token is valid
        
    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(
            token,
            SETTINGS.secret_key,
            algorithms=[SETTINGS.algorithm],
            options={"verify_aud": False}  # Don't verify audience claim for now
        )
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        token_type: str = payload.get("token_type")
        
        # Validate token data
        if username is None or user_id is None:
            logger.warning("Missing username or user_id in token")
            raise credentials_exception
        
        # Ensure it's an access token
        if token_type != "access":
            logger.warning(f"Invalid token type: {token_type}")
            raise credentials_exception
        
        token_data = TokenData(
            username=username,
            user_id=user_id,
            exp=datetime.fromtimestamp(payload.get("exp")),
            token_type=token_type
        )
    except JWTError as e:
        logger.warning(f"JWT validation error: {str(e)}")
        raise credentials_exception
    
    # Get user from database
    from app.db.dependencies import get_user_repository
    from app.db.session import AsyncSessionLocal
    
    db = AsyncSessionLocal()
    try:
        user_repository = await get_user_repository(db)
        user = await user_repository.get_by_username(token_data.username)
        
        if user is None:
            logger.warning(f"User not found: {token_data.username}")
            raise credentials_exception
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {token_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
    finally:
        await db.close()

async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Get the current active user
    
    Args:
        current_user: The current user from the token
        
    Returns:
        The user if active
        
    Raises:
        HTTPException: If the user is inactive
    """
    # Special handling for developer mode - provide a fake user for testing
    if SETTINGS.developer_mode:
        logger.info("Developer mode: Using fake user for authentication")
        # Create a fake user object
        from app.models.user import User
        from uuid import uuid4
        fake_user = User(
            id=str(uuid4()),
            username="developer",
            email="developer@example.com",
            is_active=True,
            is_admin=True
        )
        return fake_user
        
    # Normal authentication check
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user

async def get_current_admin_user(current_user = Depends(get_current_user)):
    """
    Get the current admin user
    
    Args:
        current_user: The current user from the token
        
    Returns:
        The user if admin
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an admin user"
        )
    
    return current_user

async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)):
    """
    Get the current user from a JWT token, but return None if no valid token
    
    Args:
        token: The JWT token (optional)
        
    Returns:
        The user if the token is valid, None otherwise
    """
    if not token:
        return None
        
    try:
        # Decode token
        payload = jwt.decode(
            token,
            SETTINGS.secret_key,
            algorithms=[SETTINGS.algorithm],
            options={"verify_aud": False}  # Don't verify audience claim for now
        )
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        token_type: str = payload.get("token_type")
        
        # Validate token data
        if username is None or user_id is None or token_type != "access":
            logger.warning("Invalid token data")
            return None
            
        # Get user from database
        from app.db.dependencies import get_user_repository
        from app.db.session import AsyncSessionLocal
        
        db = AsyncSessionLocal()
        try:
            user_repository = await get_user_repository(db)
            user = await user_repository.get_by_username(username)
            
            if user is None or not user.is_active:
                logger.warning(f"User not found or inactive: {username}")
                return None
                
            return user
        finally:
            await db.close()
    except JWTError as e:
        logger.warning(f"JWT validation error in optional auth: {str(e)}")
        return None