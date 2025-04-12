from fastapi import Request, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio
from jose import jwt, JWTError
from starlette.types import ASGIApp, Scope, Receive, Send

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
    # Skip token validation for certain paths
    path = request.url.path.lower()
    if path.startswith("/static") or path == "/login" or path == "/favicon.ico" or path == "/register" or path.startswith("/api/auth"):
        return None
    
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
        # Only log warnings for non-public paths
        if not (path.startswith("/static") or path == "/login" or path == "/favicon.ico" or path == "/register" or path.startswith("/api/auth")):
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
    # Skip setting context for SQLite
    if SETTINGS.database_type.startswith("sqlite"):
        logger.debug("Skipping database context setting for SQLite")
        return db
        
    try:
        if user_id:
            # Set the current_user_id for RLS policies
            await db.execute(text(f"SET app.current_user_id = '{user_id}'"))
        else:
            # Set to NULL if no user - use empty string instead of NULL
            await db.execute(text("SET app.current_user_id = ''"))
    except Exception as e:
        # Log the error but continue
        logger.error(f"Error setting database context: {e}")
    
    return db


class DBContextMiddleware:
    """
    Middleware to set database context for Row Level Security
    """
    
    def __init__(self, app):
        """
        Initialize the middleware
        
        Args:
            app: The ASGI application
        """
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Process the request and set the database context
        
        Args:
            scope: The ASGI scope
            receive: The ASGI receive function
            send: The ASGI send function
            
        Returns:
            The response from the next middleware or route handler
        """
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Create a request object
        request = Request(scope)
        
        try:
            # Try to get current user ID
            user_id = await extract_user_id_from_request(request)
            
            # Get database session using anext() since get_db() is an async generator
            db_gen = get_db()
            db = await anext(db_gen)
            
            # Skip setting context for SQLite
            if not SETTINGS.database_type.startswith("sqlite"):
                try:
                    if user_id:
                        # Set the current_user_id for RLS policies
                        await db.execute(text(f"SET app.current_user_id = '{user_id}'"))
                        logger.debug(f"Set database context for user_id: {user_id}")
                    else:
                        # Set to empty string instead of NULL
                        await db.execute(text("SET app.current_user_id = ''"))
                        logger.debug("Set database context to empty string (no user)")
                except Exception as e:
                    # Log the error but continue
                    logger.error(f"Error setting database context: {e}")
            else:
                logger.debug("Skipping database context setting for SQLite")
        except Exception as e:
            logger.error(f"Error in DB context middleware: {e}")
        
        # Process the request
        return await self.app(scope, receive, send)