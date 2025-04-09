import logging
import os
import platform
import psutil
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from app.models.system import SystemStats, ModelInfo, HealthCheck
from app.rag.ollama_client import OllamaClient
from app.rag.vector_store import VectorStore
from app.db.dependencies import get_db, get_document_repository
from app.db.repositories.document_repository import DocumentRepository
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.config import API_V1_STR

# Create router
router = APIRouter()

# Logger
logger = logging.getLogger("app.api.system")

# Vector store
vector_store = VectorStore()

@router.get("/stats", response_model=SystemStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    document_repository: DocumentRepository = Depends(get_document_repository)
):
    """
    Get system statistics
    """
    try:
        # Get Ollama client
        async with OllamaClient() as ollama_client:
            # Get available models
            models = await ollama_client.list_models()
            model_names = [model["name"] for model in models]
        
        # Get vector store stats
        vector_store_stats = vector_store.get_stats()
        
        # Get document count and total chunks from repository
        documents = document_repository.get_all()
        total_chunks = sum(len(doc.chunks) if hasattr(doc, 'chunks') else 0 for doc in documents)
        
        return SystemStats(
            documents_count=len(documents),
            total_chunks=total_chunks,
            vector_store_size=vector_store_stats["count"],
            available_models=model_names
        )
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")

@router.get("/models", response_model=List[ModelInfo])
async def get_models():
    """
    Get available models
    """
    try:
        # Get Ollama client
        async with OllamaClient() as ollama_client:
            # Get available models
            models = await ollama_client.list_models()
        
        # Convert to ModelInfo
        model_infos = [
            ModelInfo(
                name=model["name"],
                size=str(model.get("size")) if model.get("size") is not None else None,
                modified_at=model.get("modified_at"),
                description=model.get("description", f"Ollama model: {model['name']}")
            )
            for model in models
        ]
        
        return model_infos
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint
    """
    server_start_time = os.environ.get("SERVER_START_TIME", "unknown")
    
    try:
        # Check Ollama
        ollama_status = "healthy"
        try:
            async with OllamaClient() as ollama_client:
                await ollama_client.list_models()
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            ollama_status = "unhealthy"
        
        # Check vector DB
        vector_db_status = "healthy"
        try:
            vector_store.get_stats()
        except Exception as e:
            logger.error(f"Vector DB health check failed: {str(e)}")
            vector_db_status = "unhealthy"
        
        return HealthCheck(
            status="healthy" if ollama_status == "healthy" and vector_db_status == "healthy" else "unhealthy",
            ollama_status=ollama_status,
            vector_db_status=vector_db_status,
            api_version="v1",
            server_start_time=server_start_time
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            ollama_status="unknown",
            vector_db_status="unknown",
            api_version="v1",
            server_start_time=server_start_time
        )