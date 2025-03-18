import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import API_V1_STR, PROJECT_NAME
from app.core.security import setup_security
from app.core.logging import setup_logging
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.system import router as system_router
from app.api.analytics import router as analytics_router
from app.api.processing import router as processing_router
from app.db.session import init_db, db_session

# Setup logging
setup_logging()
logger = logging.getLogger("app.main")

# Create FastAPI app
app = FastAPI(title=PROJECT_NAME)

# Setup security
setup_security(app)

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

@app.get("/test-models", response_class=HTMLResponse)
async def test_models_page(request: Request):
    """
    Test models page for debugging
    """
    return templates.TemplateResponse("test_models.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    """
    Actions to run on application startup
    """
    logger.info("Starting up Metis RAG application")
    
    # Initialize database
    try:
        logger.info("Initializing database connection")
        init_db()
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to run on application shutdown
    """
    logger.info("Shutting down Metis RAG application")
    
    # Close database session
    db_session.remove()