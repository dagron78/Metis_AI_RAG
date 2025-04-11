import logging
import asyncio
import os
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db, get_document_repository
from app.db.repositories.document_repository import DocumentRepository
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.models.system import SystemStats, AgentSettings, AgentSettingsUpdate
from app.core.security import get_current_admin_user
from app.models.user import User
from app.core.config import SETTINGS
from uuid import uuid4

# Create router
router = APIRouter()

# Logger
logger = logging.getLogger("app.api.devops")

# Vector store
vector_store = VectorStore.get_instance()

# Custom dependency for DevOps endpoints
async def get_devops_admin_user():
    """
    Get the current admin user or a fake user in developer mode
    """
    if SETTINGS.developer_mode:
        logger.info("Developer mode: Using fake user for DevOps operations")
        # Create a fake user object
        fake_user = User(
            id=str(uuid4()),
            username="developer",
            email="developer@example.com",
            is_active=True,
            is_admin=True
        )
        return fake_user
    else:
        # Use the regular admin user dependency
        return await get_current_admin_user()

@router.get("/stats", response_model=SystemStats)
async def get_devops_stats(
    db: AsyncSession = Depends(get_db),
    document_repository: DocumentRepository = Depends(get_document_repository),
    current_user: User = Depends(get_devops_admin_user)
):
    """
    Get system statistics including cache stats
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
        documents = await document_repository.get_all()
        total_chunks = sum(len(doc.chunks) if hasattr(doc, 'chunks') else 0 for doc in documents)
        
        # Create response
        stats = SystemStats(
            documents_count=len(documents),
            total_chunks=total_chunks,
            vector_store_size=vector_store_stats["count"],
            available_models=model_names
        )
        
        # Add cache stats if available
        if "cache_enabled" in vector_store_stats:
            stats.cache_enabled = vector_store_stats["cache_enabled"]
            
            if stats.cache_enabled:
                stats.cache_size = vector_store_stats["cache_size"]
                stats.cache_max_size = vector_store_stats["cache_max_size"]
                stats.cache_hits = vector_store_stats["cache_hits"]
                stats.cache_misses = vector_store_stats["cache_misses"]
                stats.cache_hit_ratio = vector_store_stats["cache_hit_ratio"]
                stats.cache_ttl_seconds = vector_store_stats["cache_ttl_seconds"]
                stats.cache_persist = vector_store_stats["cache_persist"]
        
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")

@router.post("/clear-vector-store")
async def clear_vector_store(
    current_user: User = Depends(get_devops_admin_user)
):
    """
    Clear all documents from the vector store
    """
    try:
        logger.info(f"User {current_user.username} initiated vector store clearing")
        
        # Import the clear_vector_store function from the script
        from scripts.clear_vector_store import clear_vector_store_sync as clear_vs_func
        
        # Get count before deletion
        stats_before = vector_store.get_stats()
        count_before = stats_before["count"]
        
        # Run the clear function in a separate thread to avoid blocking
        await asyncio.to_thread(clear_vs_func)
        
        # Get count after deletion
        stats_after = vector_store.get_stats()
        count_after = stats_after["count"]
        
        # Calculate deleted count
        deleted_count = count_before - count_after
        
        logger.info(f"Vector store cleared successfully. Deleted {deleted_count} documents.")
        
        return {
            "status": "success",
            "message": "Vector store cleared successfully",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error clearing vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing vector store: {str(e)}")

@router.post("/clear-cache")
async def clear_cache(
    current_user: User = Depends(get_devops_admin_user)
):
    """
    Clear the vector search cache
    """
    try:
        logger.info(f"User {current_user.username} initiated cache clearing")
        
        # Get cache stats before clearing
        cache_stats_before = vector_store.get_cache_stats()
        
        # Clear the cache
        vector_store.clear_cache()
        
        # Get cache stats after clearing
        cache_stats_after = vector_store.get_cache_stats()
        
        logger.info("Vector store cache cleared successfully")
        
        return {
            "status": "success",
            "message": "Vector store cache cleared successfully",
            "cache_stats_before": cache_stats_before,
            "cache_stats_after": cache_stats_after
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.get("/agent-settings", response_model=AgentSettings)
async def get_agent_settings(
    current_user: User = Depends(get_devops_admin_user)
):
    """
    Get current RAG agent settings
    """
    try:
        logger.info(f"User {current_user.username} requested agent settings")
        
        # Create settings object with current values from config
        settings = AgentSettings(
            use_mem0=SETTINGS.use_mem0,
            use_chunking_judge=SETTINGS.use_chunking_judge,
            use_retrieval_judge=SETTINGS.use_retrieval_judge,
            use_langgraph_rag=SETTINGS.use_langgraph_rag,
            use_enhanced_langgraph_rag=SETTINGS.use_enhanced_langgraph_rag,
            
            # Default sensitivity values (these would come from config in a real implementation)
            mem0_sensitivity=int(os.getenv("MEM0_SENSITIVITY", "50")),
            chunking_judge_sensitivity=int(os.getenv("CHUNKING_JUDGE_SENSITIVITY", "50")),
            retrieval_judge_sensitivity=int(os.getenv("RETRIEVAL_JUDGE_SENSITIVITY", "50")),
            langgraph_rag_sensitivity=int(os.getenv("LANGGRAPH_RAG_SENSITIVITY", "50"))
        )
        
        return settings
    except Exception as e:
        logger.error(f"Error getting agent settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting agent settings: {str(e)}")

@router.post("/agent-settings", response_model=AgentSettings)
async def update_agent_settings(
    settings_update: AgentSettingsUpdate,
    current_user: User = Depends(get_devops_admin_user)
):
    """
    Update RAG agent settings
    """
    try:
        logger.info(f"User {current_user.username} updating agent settings: {settings_update}")
        
        # Get current settings
        current_settings = await get_agent_settings(current_user)
        
        # Update settings with new values
        updated_settings = AgentSettings(
            use_mem0=settings_update.use_mem0 if settings_update.use_mem0 is not None else current_settings.use_mem0,
            use_chunking_judge=settings_update.use_chunking_judge if settings_update.use_chunking_judge is not None else current_settings.use_chunking_judge,
            use_retrieval_judge=settings_update.use_retrieval_judge if settings_update.use_retrieval_judge is not None else current_settings.use_retrieval_judge,
            use_langgraph_rag=settings_update.use_langgraph_rag if settings_update.use_langgraph_rag is not None else current_settings.use_langgraph_rag,
            use_enhanced_langgraph_rag=settings_update.use_enhanced_langgraph_rag if settings_update.use_enhanced_langgraph_rag is not None else current_settings.use_enhanced_langgraph_rag,
            
            mem0_sensitivity=settings_update.mem0_sensitivity if settings_update.mem0_sensitivity is not None else current_settings.mem0_sensitivity,
            chunking_judge_sensitivity=settings_update.chunking_judge_sensitivity if settings_update.chunking_judge_sensitivity is not None else current_settings.chunking_judge_sensitivity,
            retrieval_judge_sensitivity=settings_update.retrieval_judge_sensitivity if settings_update.retrieval_judge_sensitivity is not None else current_settings.retrieval_judge_sensitivity,
            langgraph_rag_sensitivity=settings_update.langgraph_rag_sensitivity if settings_update.langgraph_rag_sensitivity is not None else current_settings.langgraph_rag_sensitivity
        )
        
        # In a real implementation, we would save these settings to a database or config file
        # For now, we'll just update environment variables in memory
        # Note: This is not persistent across restarts
        os.environ["USE_MEM0"] = str(updated_settings.use_mem0)
        os.environ["USE_CHUNKING_JUDGE"] = str(updated_settings.use_chunking_judge)
        os.environ["USE_RETRIEVAL_JUDGE"] = str(updated_settings.use_retrieval_judge)
        os.environ["USE_LANGGRAPH_RAG"] = str(updated_settings.use_langgraph_rag)
        os.environ["USE_ENHANCED_LANGGRAPH_RAG"] = str(updated_settings.use_enhanced_langgraph_rag)
        
        os.environ["MEM0_SENSITIVITY"] = str(updated_settings.mem0_sensitivity)
        os.environ["CHUNKING_JUDGE_SENSITIVITY"] = str(updated_settings.chunking_judge_sensitivity)
        os.environ["RETRIEVAL_JUDGE_SENSITIVITY"] = str(updated_settings.retrieval_judge_sensitivity)
        os.environ["LANGGRAPH_RAG_SENSITIVITY"] = str(updated_settings.langgraph_rag_sensitivity)
        
        # Update SETTINGS object
        SETTINGS.use_mem0 = updated_settings.use_mem0
        SETTINGS.use_chunking_judge = updated_settings.use_chunking_judge
        SETTINGS.use_retrieval_judge = updated_settings.use_retrieval_judge
        SETTINGS.use_langgraph_rag = updated_settings.use_langgraph_rag
        SETTINGS.use_enhanced_langgraph_rag = updated_settings.use_enhanced_langgraph_rag
        
        logger.info(f"Agent settings updated successfully: {updated_settings}")
        
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating agent settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating agent settings: {str(e)}")