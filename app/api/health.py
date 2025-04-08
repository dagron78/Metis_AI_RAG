import logging
import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.dependencies import get_db
from app.db.session import engine
from app.rag.vector_store import VectorStore
from app.core.config import SETTINGS

# Server start time (used for detecting restarts)
SERVER_START_TIME = str(int(time.time()))

# Create router
router = APIRouter()

# Logger
logger = logging.getLogger("app.api.health")

@router.get("/")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint
    
    Returns:
        Health status of the application and its dependencies
    """
    try:
        # Check database connection
        db_status = "healthy"
        db_error = None
        try:
            # Execute a simple query to check database connection
            result = await db.execute(text("SELECT 1"))
            await result.fetchall()
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)
            logger.error(f"Database health check failed: {str(e)}")
        
        # Check vector store
        vector_store_status = "healthy"
        vector_store_error = None
        try:
            vector_store = VectorStore()
            stats = vector_store.get_stats()
        except Exception as e:
            vector_store_status = "unhealthy"
            vector_store_error = str(e)
            logger.error(f"Vector store health check failed: {str(e)}")
        
        # Check Mem0 if enabled
        mem0_status = "disabled"
        mem0_error = None
        if SETTINGS.use_mem0:
            try:
                from app.rag.mem0_client import get_mem0_client
                mem0_client = get_mem0_client()
                if mem0_client:
                    mem0_status = "healthy"
                else:
                    mem0_status = "unhealthy"
                    mem0_error = "Failed to initialize Mem0 client"
            except Exception as e:
                mem0_status = "unhealthy"
                mem0_error = str(e)
                logger.error(f"Mem0 health check failed: {str(e)}")
        
        # Check Ollama
        ollama_status = "healthy"
        ollama_error = None
        try:
            from app.rag.ollama_client import OllamaClient
            ollama_client = OllamaClient()
            # Just initialize the client, don't make an actual request
            # to avoid unnecessary load on the Ollama service
        except Exception as e:
            ollama_status = "unhealthy"
            ollama_error = str(e)
            logger.error(f"Ollama health check failed: {str(e)}")
        
        # Overall status is healthy only if all critical components are healthy
        overall_status = "healthy"
        if db_status != "healthy" or vector_store_status != "healthy":
            overall_status = "unhealthy"
        
        # Get client session ID if provided
        client_session_id = request.headers.get('X-Client-Session', None)
        
        # Build response
        response = {
            "status": overall_status,
            "version": SETTINGS.version,
            "server_start_time": SERVER_START_TIME,
            "components": {
                "database": {
                    "status": db_status,
                    "error": db_error
                },
                "vector_store": {
                    "status": vector_store_status,
                    "error": vector_store_error
                },
                "mem0": {
                    "status": mem0_status,
                    "error": mem0_error
                },
                "ollama": {
                    "status": ollama_status,
                    "error": ollama_error
                }
            }
        }
        
        # Include client session ID in response if provided
        if client_session_id:
            response["client_session_id"] = client_session_id
        
        # Log health check result
        logger.info(f"Health check: {overall_status}")
        
        return response
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/readiness")
async def readiness_check():
    """
    Readiness check endpoint
    
    This endpoint checks if the application is ready to accept traffic.
    It's a lightweight check that doesn't verify all dependencies.
    
    Returns:
        Readiness status
    """
    return {"status": "ready"}

@router.get("/liveness")
async def liveness_check():
    """
    Liveness check endpoint
    
    This endpoint checks if the application is alive.
    It's a very lightweight check that doesn't verify any dependencies.
    
    Returns:
        Liveness status
    """
    return {"status": "alive"}