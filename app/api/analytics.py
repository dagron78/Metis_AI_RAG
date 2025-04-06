import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
import json

from app.db.dependencies import get_db, get_analytics_repository, get_document_repository
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.db.repositories.document_repository import DocumentRepository

# Create router
router = APIRouter()

# Logger
logger = logging.getLogger("app.api.analytics")

@router.post("/record_query")
async def record_query(
    query_data: Dict[str, Any],
    db: Session = Depends(get_db),
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Record a query for analytics
    """
    try:
        # Add timestamp if not provided
        if "timestamp" not in query_data:
            query_data["timestamp"] = datetime.now().isoformat()
        
        # Create analytics query record
        analytics_query = analytics_repository.log_query(
            query=query_data.get("query", ""),
            model=query_data.get("model", ""),
            use_rag=query_data.get("use_rag", False),
            response_time_ms=query_data.get("response_time_ms", 0),
            token_count=query_data.get("token_count", 0),
            document_ids=query_data.get("document_ids", []),
            query_type=query_data.get("query_type", "standard"),
            successful=query_data.get("successful", True)
        )
        
        return {"success": True, "message": "Query recorded for analytics", "id": analytics_query.id}
    except Exception as e:
        logger.error(f"Error recording query analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recording query analytics: {str(e)}")

@router.get("/query_stats")
async def get_query_stats(
    time_period: Optional[str] = Query("all", description="Time period for stats (all, day, week, month)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Get query statistics with pagination
    """
    try:
        # Get cutoff date based on time period
        cutoff_date = get_cutoff_date(time_period)
        
        # Get query stats from repository
        stats = analytics_repository.get_query_stats(cutoff_date)
        
        # Get most common queries
        most_common_queries = analytics_repository.get_most_common_queries(
            cutoff_date=cutoff_date,
            limit=10
        )
        
        # Get recent queries with pagination
        recent_queries = analytics_repository.get_recent_queries(
            cutoff_date=cutoff_date,
            skip=skip,
            limit=10  # Always get the 10 most recent
        )
        
        # Format the response
        return {
            "query_count": stats.get("query_count", 0),
            "avg_response_time_ms": stats.get("avg_response_time_ms", 0),
            "avg_token_count": stats.get("avg_token_count", 0),
            "rag_usage_percent": stats.get("rag_usage_percent", 0),
            "most_common_queries": [
                {"query": q.query, "count": q.count}
                for q in most_common_queries
            ],
            "recent_queries": [
                {
                    "id": q.id,
                    "query": q.query,
                    "model": q.model,
                    "use_rag": q.use_rag,
                    "timestamp": q.timestamp.isoformat() if q.timestamp else None,
                    "response_time_ms": q.response_time_ms,
                    "token_count": q.token_count,
                    "document_ids": q.document_ids,
                    "query_type": q.query_type,
                    "successful": q.successful
                }
                for q in recent_queries
            ],
            "time_period": time_period,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": stats.get("query_count", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error getting query stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting query stats: {str(e)}")

@router.get("/document_usage")
async def get_document_usage(
    time_period: Optional[str] = Query("all", description="Time period for stats (all, day, week, month)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository),
    document_repository: DocumentRepository = Depends(get_document_repository)
):
    """
    Get document usage statistics with pagination
    """
    try:
        # Get cutoff date based on time period
        cutoff_date = get_cutoff_date(time_period)
        
        # Get document usage stats from repository
        document_usage = analytics_repository.get_document_usage_stats(
            cutoff_date=cutoff_date,
            skip=skip,
            limit=limit
        )
        
        # Get total document count
        document_count = analytics_repository.count_documents_used(cutoff_date)
        
        # Enrich with document metadata
        enriched_usage = []
        for usage in document_usage:
            try:
                # Get document info
                document = document_repository.get_by_id(UUID(usage.document_id))
                
                # Add document info to usage stats
                enriched_usage.append({
                    "id": usage.document_id,
                    "usage_count": usage.usage_count,
                    "last_used": usage.last_used.isoformat() if usage.last_used else None,
                    "filename": document.filename if document else "Unknown",
                    "folder": document.folder if document else "Unknown"
                })
            except Exception as doc_error:
                logger.error(f"Error enriching document usage: {str(doc_error)}")
                # Include basic usage stats without document info
                enriched_usage.append({
                    "id": usage.document_id,
                    "usage_count": usage.usage_count,
                    "last_used": usage.last_used.isoformat() if usage.last_used else None,
                    "filename": "Unknown",
                    "folder": "Unknown"
                })
        
        return {
            "document_count": document_count,
            "most_used": enriched_usage,
            "time_period": time_period,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": document_count
            }
        }
    except Exception as e:
        logger.error(f"Error getting document usage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document usage stats: {str(e)}")

@router.get("/system_stats")
async def get_system_stats(
    db: Session = Depends(get_db),
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository),
    document_repository: DocumentRepository = Depends(get_document_repository)
):
    """
    Get system statistics
    """
    try:
        from app.rag.vector_store import VectorStore
        
        # Get vector store stats
        vector_store = VectorStore()
        vector_stats = vector_store.get_stats()
        
        # Get query stats
        query_count = analytics_repository.count_queries()
        
        # Get document stats
        document_count = document_repository.count()
        
        # Get additional stats
        rag_query_count = analytics_repository.count_rag_queries()
        avg_response_time = analytics_repository.get_avg_response_time()
        
        return {
            "vector_store": vector_stats,
            "query_count": query_count,
            "document_count": document_count,
            "rag_query_count": rag_query_count,
            "rag_usage_percent": (rag_query_count / query_count * 100) if query_count > 0 else 0,
            "avg_response_time_ms": avg_response_time,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")

@router.get("/model_performance")
async def get_model_performance(
    time_period: Optional[str] = Query("all", description="Time period for stats (all, day, week, month)"),
    db: Session = Depends(get_db),
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Get model performance statistics
    """
    try:
        # Get cutoff date based on time period
        cutoff_date = get_cutoff_date(time_period)
        
        # Get model performance stats from repository
        model_stats = analytics_repository.get_model_performance_stats(cutoff_date)
        
        return {
            "models": [
                {
                    "model": stat.model,
                    "query_count": stat.query_count,
                    "avg_response_time_ms": stat.avg_response_time_ms,
                    "avg_token_count": stat.avg_token_count,
                    "success_rate": stat.success_rate
                }
                for stat in model_stats
            ],
            "time_period": time_period
        }
    except Exception as e:
        logger.error(f"Error getting model performance stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model performance stats: {str(e)}")

@router.get("/query_types")
async def get_query_types(
    time_period: Optional[str] = Query("all", description="Time period for stats (all, day, week, month)"),
    db: Session = Depends(get_db),
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository)
):
    """
    Get query type statistics
    """
    try:
        # Get cutoff date based on time period
        cutoff_date = get_cutoff_date(time_period)
        
        # Get query type stats from repository
        query_type_stats = analytics_repository.get_query_type_stats(cutoff_date)
        
        return {
            "query_types": [
                {
                    "query_type": stat.query_type,
                    "query_count": stat.query_count,
                    "avg_response_time_ms": stat.avg_response_time_ms,
                    "success_rate": stat.success_rate
                }
                for stat in query_type_stats
            ],
            "time_period": time_period
        }
    except Exception as e:
        logger.error(f"Error getting query type stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting query type stats: {str(e)}")

def get_cutoff_date(time_period):
    """
    Get cutoff date for time period
    """
    now = datetime.now()
    
    if time_period == "day":
        return now - timedelta(days=1)
    elif time_period == "week":
        return now - timedelta(days=7)
    elif time_period == "month":
        return now - timedelta(days=30)
    else:
        # Default to all time
        return now - timedelta(days=365 * 10)  # 10 years ago