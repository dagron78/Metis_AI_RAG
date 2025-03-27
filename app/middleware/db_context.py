from fastapi import Request, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from jose import jwt, JWTError

from app.db.dependencies import get_db
from app.core.config import SETTINGS

# Setup logging
logger = logging.getLogger("app.middleware.db_context")

async def extract_user_id_from_request(request: Request) -> str:
    """
    Extract the user ID from the request's Authorization header
    
    Args:
        request: FastAPI request
        
    Returns:
        User ID if found, None otherwise
    """
    # Get authorization header
    auth_header = request.headers.get("Authorization")
    auth_cookie = request.cookies.get("auth_token")
    
    # Check for auth header
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    # Check for auth cookie
    elif auth_cookie:
        token = auth_cookie
    else:
        return None
    
    try:
        # Decode token
        payload = jwt.decode(
            token,
            SETTINGS.secret_key,
            algorithms=[SETTINGS.algorithm],
            options={"verify_aud": False}  # Don't verify audience claim for now
        )
        
        # Get user ID from token
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        # Check token type
        token_type = payload.get("token_type")
        if token_type != "access":
            return None
        
        return user_id
    except JWTError as e:
        logger.warning(f"JWT validation error in DB context: {str(e)}")
        return None


async def set_db_context(db: AsyncSession, user_id: str = None):
    """
    Set the database context for Row Level Security
    
    Args:
        db: Database session
        user_id: User ID (optional, will be extracted from request if not provided)
    
    Returns:
        Database session with context set
    """
    try:
        if user_id:
            # Set the current_user_id for RLS policies
            await db.execute(text(f"SET app.current_user_id = '{user_id}'"))
        else:
            # Set to NULL if no user
            await db.execute(text("SET app.current_user_id = NULL"))
    except Exception as e:
        # Log the error but continue
        logger.error(f"Error setting database context: {e}")
        # Set to NULL if error
        await db.execute(text("SET app.current_user_id = NULL"))
    
    return db


class DBContextMiddleware:
    """
    Middleware to set database context for Row Level Security
    """
    
    async def __call__(self, request: Request, call_next):
        """
        Process the request and set the database context
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint
        
        Returns:
            Response
        """
        # Get database session
        db = await get_db()
        
        try:
            # Try to get current user ID
            user_id = await extract_user_id_from_request(request)
            if user_id:
                # Set the current_user_id for RLS policies
                await db.execute(text(f"SET app.current_user_id = '{user_id}'"))
                logger.debug(f"Set database context for user_id: {user_id}")
            else:
                # Set to NULL if no user
                await db.execute(text("SET app.current_user_id = NULL"))
                logger.debug("Set database context to NULL (no user)")
        except Exception as e:
            # Log the error but continue
            logger.error(f"Error setting database context: {e}")
            # Set to NULL if error
            await db.execute(text("SET app.current_user_id = NULL"))
        
        # Process the request
        response = await call_next(request)
        
        return response