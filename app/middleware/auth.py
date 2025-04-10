from fastapi import Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List, Callable, Optional, Dict, Any
from starlette.types import ASGIApp, Scope, Receive, Send
import logging
from jose import jwt, JWTError

from app.core.security_alerts import SecurityEvent, log_security_event
from app.core.config import SETTINGS

# Setup logging
logger = logging.getLogger("app.middleware.auth")

async def log_suspicious_requests(request: Request, call_next):
    """
    Middleware to log suspicious requests that might pose security risks
    """
    path = request.url.path
    query_params = request.query_params
    
    # Check for sensitive parameters in URLs
    sensitive_params = ['username', 'password', 'token', 'key', 'secret', 'api_key', 'auth']
    found_sensitive = [param for param in sensitive_params if param in query_params]
    
    if found_sensitive:
        # Collect request metadata for security analysis
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        referrer = request.headers.get("referer", "none")
        # Log security event (without logging the actual sensitive values)
        logger.warning(
            f"Security alert: Sensitive parameters ({', '.join(found_sensitive)}) "
            f"detected in URL for path: {path}. "
            f"IP: {client_ip}, "
            f"User-Agent: {user_agent}, "
            f"Referrer: {referrer}"
        )
        
        # Create and log security event
        security_event = SecurityEvent(
            event_type="sensitive_params_in_url",
            severity="medium",
            source_ip=client_ip,
            user_agent=user_agent,
            details={
                "path": path,
                "sensitive_params": found_sensitive,
                "referrer": referrer,
                "query_params": str(query_params)
            }
        )
        log_security_event(security_event)
    
    # Continue with the request
    response = await call_next(request)
    return response


class AuthMiddleware:
    """
    Middleware to check for authentication on protected routes
    
    This middleware validates JWT tokens for protected routes and API endpoints.
    It redirects unauthenticated browser requests to the login page and
    returns 401 Unauthorized for unauthenticated API requests.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        protected_routes: List[str] = None,
        api_routes: List[str] = None,
        exclude_routes: List[str] = None,
        login_url: str = "/login"
    ):
        """
        Initialize the middleware
        
        Args:
            app: The ASGI application
            protected_routes: List of routes that require authentication
            api_routes: List of API routes that require authentication
            exclude_routes: List of routes to exclude from authentication
            login_url: URL to redirect to for login
        """
        self.app = app
        self.protected_routes = protected_routes or [
            "/documents",
            "/chat",
            "/analytics",
            "/system",
            "/tasks"
        ]
        self.api_routes = api_routes or [
            "/api/documents",
            "/api/chat",
            "/api/analytics",
            "/api/system",
            "/api/tasks",
            "/api/processing",
            "/api/query"
        ]
        self.exclude_routes = exclude_routes or [
            "/login",
            "/register",
            "/api/auth/token",
            "/api/auth/refresh",
            "/api/auth/register",
            "/api/health",
            "/health",
            "/api/health/readiness",
            "/api/health/liveness",
            "/static",
            "/forgot-password",
            "/reset-password",
            # TEMPORARY: Allow document uploads without authentication
            "/api/documents/upload",
            "/api/documents/process",
            "/api/documents/actions/clear-all"
        ]
        self.login_url = login_url
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Process the request
        
        Args:
            scope: The ASGI scope
            receive: The ASGI receive function
            send: The ASGI send function
            
        Returns:
            The response from the next middleware or route handler
        """
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Check if developer mode is enabled
        if SETTINGS.developer_mode:
            logger.info("Developer mode is enabled, bypassing authentication")
            return await self.app(scope, receive, send)
            
        # Create a request object
        request = Request(scope)
        # Check if the route is protected
        path = request.url.path
        
        # Skip authentication for excluded routes
        for route in self.exclude_routes:
            if path.startswith(route):
                return await self.app(scope, receive, send)
        
        # Check if the route is protected
        is_protected = False
        for route in self.protected_routes:
            if path.startswith(route):
                is_protected = True
                break
        
        # Check if the route is an API route
        is_api = False
        for route in self.api_routes:
            if path.startswith(route):
                is_api = True
                break
        
        # If the route is not protected, continue
        if not is_protected and not is_api:
            return await self.app(scope, receive, send)
        
        # Check for authentication
        auth_header = request.headers.get("Authorization")
        auth_cookie = request.cookies.get("auth_token")
        
        # For API routes, validate JWT token
        if is_api:
            if not auth_header or not auth_header.startswith("Bearer "):
                # Log unauthorized API access attempt
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("user-agent", "unknown")
                logger.warning(
                    f"Unauthorized API access attempt: {path}, "
                    f"IP: {client_ip}, User-Agent: {user_agent}"
                )
                
                # Create a 401 response
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                await response(scope, receive, send)
                return
            
            # Extract and validate the token
            token = auth_header.split(" ")[1]
            is_valid = self._validate_jwt_token(token, request)
            
            if not is_valid:
                # Log invalid token
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("user-agent", "unknown")
                logger.warning(
                    f"Invalid token for API access: {path}, "
                    f"IP: {client_ip}, User-Agent: {user_agent}"
                )
                
                # Create a 401 response
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                await response(scope, receive, send)
                return
            
            # Continue with the request
            return await self.app(scope, receive, send)
        
        # For protected routes, check for authentication cookie or header
        if is_protected:
            # First check for auth cookie (for browser requests)
            if auth_cookie:
                is_valid = self._validate_jwt_token(auth_cookie, request)
                if is_valid:
                    # Continue with the request
                    return await self.app(scope, receive, send)
            
            # Then check for auth header (for programmatic requests)
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                is_valid = self._validate_jwt_token(token, request)
                if is_valid:
                    # Continue with the request
                    return await self.app(scope, receive, send)
            
            # If no valid authentication, redirect to login
            redirect_url = f"{self.login_url}?redirect={path}"
            response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
            await response(scope, receive, send)
            return
        
        # Continue with the request
        return await self.app(scope, receive, send)
    
    def _validate_jwt_token(self, token: str, request: Request) -> bool:
        """
        Validate a JWT token
        
        Args:
            token: The JWT token to validate
            request: The request object for logging
            
        Returns:
            True if the token is valid, False otherwise
        """
        try:
            # Decode and validate the token
            payload = jwt.decode(
                token,
                SETTINGS.secret_key,
                algorithms=[SETTINGS.algorithm],
                options={
                    "verify_signature": True,
                    "verify_aud": False  # Don't verify audience claim for now
                }
            )
            
            # Check required claims
            if "sub" not in payload or "user_id" not in payload:
                return False
            
            # Check token type
            if payload.get("token_type") != "access":
                # Log invalid token type
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("user-agent", "unknown")
                logger.warning(
                    f"Invalid token type: {payload.get('token_type', 'none')}, expected 'access'. "
                    f"IP: {client_ip}, User-Agent: {user_agent}"
                )
                
                # Create and log security event
                security_event = SecurityEvent(
                    event_type="invalid_token_type",
                    severity="medium",
                    source_ip=client_ip,
                    user_agent=user_agent,
                    details={
                        "error": "Invalid token type",
                        "expected": "access",
                        "found": payload.get("token_type", "none"),
                        "path": request.url.path
                    }
                )
                log_security_event(security_event)
                return False
            
            # Token is valid
            return True
            
        except JWTError as e:
            # Log the error
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            logger.warning(
                f"JWT validation error: {str(e)}, "
                f"IP: {client_ip}, User-Agent: {user_agent}"
            )
            
            # Create and log security event
            security_event = SecurityEvent(
                event_type="invalid_jwt",
                severity="medium",
                source_ip=client_ip,
                user_agent=user_agent,
                details={
                    "error": str(e),
                    "path": request.url.path
                }
            )
            log_security_event(security_event)
            
            return False