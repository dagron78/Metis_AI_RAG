import logging
import os
import time
from fastapi import FastAPI, Request, status

# Set server start time for client connection verification
os.environ["SERVER_START_TIME"] = str(int(time.time()))
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import API_V1_STR, PROJECT_NAME, SETTINGS
from app.core.security import setup_security
from app.core.logging import setup_logging
from app.core.rate_limit import setup_rate_limiting, ip_ban_middleware
from app.core.security_alerts import SecurityEvent, log_security_event
from app.middleware.auth import log_suspicious_requests, AuthMiddleware
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.system import router as system_router
from app.api.analytics import router as analytics_router
from app.api.processing import router as processing_router
from app.api.query_analysis import router as query_analysis_router
from app.api.tasks import router as tasks_router
from app.api.auth import router as auth_router
from app.api.password_reset import router as password_reset_router
from app.api.admin import router as admin_router
from app.api.roles import router as roles_router
from app.api.document_sharing import router as document_sharing_router
from app.api.notifications import router as notifications_router
from app.api.organizations import router as organizations_router
from app.api.schema import router as schema_router
from app.api.text_formatting_dashboard import router as text_formatting_dashboard_router
from app.api.health import router as health_router
from app.db.session import init_db, get_session
from app.rag.tool_initializer import initialize_tools

# Setup logging
setup_logging()
logger = logging.getLogger("app.main")

# Create FastAPI app
app = FastAPI(
    title=PROJECT_NAME,
    description="Metis RAG API with JWT Authentication",
    version=SETTINGS.version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add security middleware to log suspicious requests
app.middleware("http")(log_suspicious_requests)

# Add IP ban middleware only if rate limiting is enabled
if SETTINGS.rate_limiting_enabled:
    app.middleware("http")(ip_ban_middleware)

# Setup security
setup_security(app)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Add database context middleware for Row Level Security
from app.middleware.db_context import DBContextMiddleware
app.add_middleware(DBContextMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(chat_router, prefix=f"{API_V1_STR}/chat", tags=["chat"])
app.include_router(documents_router, prefix=f"{API_V1_STR}/documents", tags=["documents"])
app.include_router(system_router, prefix=f"{API_V1_STR}/system", tags=["system"])
app.include_router(analytics_router, prefix=f"{API_V1_STR}/analytics", tags=["analytics"])
app.include_router(processing_router, prefix=f"{API_V1_STR}/processing", tags=["processing"])
app.include_router(query_analysis_router, prefix=f"{API_V1_STR}/query", tags=["query"])
app.include_router(tasks_router, prefix=f"{API_V1_STR}/tasks", tags=["tasks"])
app.include_router(auth_router, prefix=f"{API_V1_STR}/auth", tags=["auth"])
app.include_router(password_reset_router, prefix=f"{API_V1_STR}/password-reset", tags=["password-reset"])
app.include_router(admin_router, prefix=f"{API_V1_STR}/admin", tags=["admin"])
app.include_router(roles_router, prefix=f"{API_V1_STR}/roles", tags=["roles"])
app.include_router(document_sharing_router, prefix=f"{API_V1_STR}/sharing", tags=["sharing"])
app.include_router(notifications_router, prefix=f"{API_V1_STR}/notifications", tags=["notifications"])
app.include_router(organizations_router, prefix=f"{API_V1_STR}/organizations", tags=["organizations"])
app.include_router(schema_router, tags=["schema"])  # Schema router has its own prefix
app.include_router(text_formatting_dashboard_router, prefix=f"{API_V1_STR}", tags=["text-formatting"])
app.include_router(health_router, prefix=f"{API_V1_STR}/health", tags=["health"])

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Root endpoint that returns the main HTML page
    """
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    """
    Documents management page
    """
    return templates.TemplateResponse("documents.html", {"request": request})

@app.get("/system", response_class=HTMLResponse)
async def system_page(request: Request):
    """
    System management page
    """
    return templates.TemplateResponse("system.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """
    Analytics dashboard page
    """
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """
    Background tasks management page
    """
    return templates.TemplateResponse("tasks.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """
    Admin page
    """
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/schema", response_class=HTMLResponse)
async def schema_page(request: Request):
    """
    Database schema viewer page
    """
    return templates.TemplateResponse("schema.html", {"request": request})

@app.get("/text-formatting-dashboard", response_class=HTMLResponse)
async def text_formatting_dashboard_page(request: Request):
    """
    Text formatting dashboard page
    """
    return templates.TemplateResponse("text_formatting_dashboard.html", {"request": request})

@app.get("/test-models", response_class=HTMLResponse)
async def test_models_page(request: Request):
    """
    Test models page for debugging
    """
    return templates.TemplateResponse("test_models.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Login page
    """
    # Check for credentials in URL params (security vulnerability)
    params = request.query_params
    has_credentials = "username" in params or "password" in params
    
    if has_credentials:
        # Log security event (without logging the actual credentials)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        logger.warning(
            f"Security alert: Credentials detected in URL parameters. "
            f"IP: {client_host}, "
            f"User-Agent: {user_agent}"
        )
        
        # Create and log security event
        security_event = SecurityEvent(
            event_type="credentials_in_url",
            severity="high",
            source_ip=client_host,
            username=params.get("username", "unknown"),
            user_agent=user_agent,
            details={
                "path": request.url.path,
                "query_params": str(request.url.query),
                "has_username": "username" in params,
                "has_password": "password" in params
            }
        )
        log_security_event(security_event)
        
        # Get redirect param if it exists
        redirect_param = params.get("redirect", "")
        # Create clean URL (without credentials)
        clean_url = "/login" + (f"?redirect={redirect_param}" if redirect_param else "")
        
        # Redirect to clean URL with warning flag
        return RedirectResponse(
            url=clean_url + ("&" if redirect_param else "?") + "security_warning=credentials_in_url",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    # Normal login page rendering
    return templates.TemplateResponse("login.html", {
        "request": request,
        "security_warning": params.get("security_warning", "")
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Registration page
    """
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """
    Forgot password page
    """
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """
    Reset password page
    """
    token = request.query_params.get("token", "")
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@app.on_event("startup")
async def startup_event():
    """
    Actions to run on application startup
    """
    logger.info("Starting up Metis RAG application")
    
    # Print out the SECRET_KEY for debugging
    logger.info(f"Using SECRET_KEY: {SETTINGS.secret_key[:5]}...")
    
    # Initialize database
    try:
        logger.info("Initializing database connection")
        await init_db()
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    
    # Initialize rate limiting if enabled
    if SETTINGS.rate_limiting_enabled:
        try:
            logger.info("Initializing rate limiting")
            rate_limiting_success = await setup_rate_limiting()
            if rate_limiting_success:
                logger.info("Rate limiting initialized successfully")
            else:
                logger.warning("Rate limiting initialization failed, continuing without rate limiting")
        except Exception as e:
            logger.error(f"Error initializing rate limiting: {str(e)}")
    
    # Initialize tools
    try:
        logger.info("Initializing tools")
        initialize_tools()
        logger.info("Tools initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing tools: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to run on application shutdown
    """
    logger.info("Shutting down Metis RAG application")