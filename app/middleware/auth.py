from fastapi import Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List, Callable, Optional, Dict, Any
from starlette.types import ASGIApp, Scope, Receive, Send

class AuthMiddleware:
    """
    Middleware to check for authentication on protected routes
    """
    
    def __init__(
        self,
        app: ASGIApp,
        protected_routes: List[str] = None,
        api_routes: List[str] = None,
        exclude_routes: List[str] = None,
        login_url: str = "/login"
    ):
        self.app = app
        """
        Initialize the middleware
        
        Args:
            protected_routes: List of routes that require authentication
            api_routes: List of API routes that require authentication
            exclude_routes: List of routes to exclude from authentication
            login_url: URL to redirect to for login
        """
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
            "/api/auth/register",
            "/api/health",
            "/health",
            "/static"
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
        
        # For API routes, return 401 if not authenticated
        if is_api:
            if not auth_header or not auth_header.startswith("Bearer "):
                # Create a 401 response
                from starlette.responses import JSONResponse
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                await response(scope, receive, send)
                return
            
            # Continue with the request
            return await self.app(scope, receive, send)
        
        # For protected routes, redirect to login if not authenticated
        if is_protected:
            # Check for authentication cookie or header
            # For browser routes, we'll check for a cookie in the future
            # For now, we'll just redirect to login
            # In a real implementation, you would check for a valid token
            
            # Redirect to login with the current path as the redirect parameter
            redirect_url = f"{self.login_url}?redirect={path}"
            response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
            await response(scope, receive, send)
            return
        
        # Continue with the request
        return await self.app(scope, receive, send)