from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import logging

from app.core.config import SETTINGS
from app.core.security_alerts import SecurityEvent, log_security_event

# Setup logging
logger = logging.getLogger("app.middleware.jwt_bearer")

class JWTBearer(HTTPBearer):
    """
    JWT Bearer token authentication dependency for FastAPI routes
    
    This class extends HTTPBearer to provide JWT token validation.
    It can be used as a dependency in FastAPI route functions.
    """
    
    def __init__(self, auto_error: bool = True):
        """
        Initialize the JWT Bearer authentication
        
        Args:
            auto_error: Whether to automatically raise an HTTPException on authentication failure
        """
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> dict:
        """
        Validate the JWT token from the Authorization header
        
        Args:
            request: The FastAPI request object
            
        Returns:
            The decoded JWT payload if valid
            
        Raises:
            HTTPException: If the token is invalid or missing
        """
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        if credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication scheme. Use Bearer token.",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        # Validate the token
        payload = self.verify_jwt(credentials.credentials, request)
        return payload
    
    def verify_jwt(self, token: str, request: Request) -> dict:
        """
        Verify the JWT token and return the payload
        
        Args:
            token: The JWT token to verify
            request: The FastAPI request object
            
        Returns:
            The decoded JWT payload if valid
            
        Raises:
            HTTPException: If the token is invalid
        """
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                SETTINGS.secret_key,
                algorithms=[SETTINGS.algorithm],
                options={
                    "verify_signature": True,
                    "verify_aud": False  # Match the same options used in security.py
                }
            )
            
            # Check if token has required claims
            if "sub" not in payload or "user_id" not in payload:
                self._log_invalid_token(request, token, "Missing required claims")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Verify token type is "access"
            if payload.get("token_type") != "access":
                self._log_invalid_token(request, token, "Invalid token type")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            return payload
            
        except JWTError as e:
            self._log_invalid_token(request, token, str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def _log_invalid_token(self, request: Request, token: str, reason: str):
        """
        Log an invalid token attempt
        
        Args:
            request: The FastAPI request object
            token: The invalid token
            reason: The reason the token is invalid
        """
        # Get request metadata
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log the event
        logger.warning(
            f"Invalid token detected. Reason: {reason}. "
            f"IP: {client_ip}, User-Agent: {user_agent}"
        )
        
        # Create and log security event
        security_event = SecurityEvent(
            event_type="invalid_token",
            severity="medium",
            source_ip=client_ip,
            user_agent=user_agent,
            details={
                "reason": reason,
                "path": request.url.path,
                # Don't log the full token for security reasons
                "token_prefix": token[:10] + "..." if len(token) > 10 else token
            }
        )
        log_security_event(security_event)