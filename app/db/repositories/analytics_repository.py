from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date, extract

from app.db.models import AnalyticsQuery, Document, Chunk, Message, Citation
from app.db.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[AnalyticsQuery]):
    """
    Repository for AnalyticsQuery model
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, AnalyticsQuery)
    
    async def log_query(self,
                 query: str, 
                 model: Optional[str] = None, 
                 use_rag: bool = True, 
                 response_time_ms: Optional[float] = None, 
                 token_count: Optional[int] = None,
                 document_id_list: Optional[List[str]] = None,  # Changed from document_ids to document_id_list
                 query_type: Optional[str] = None, 
                 successful: bool = True) -> AnalyticsQuery:
        """
        Log a query for analytics
        
        Args:
            query: Query text
            model: Model used
            use_rag: Whether RAG was used
            response_time_ms: Response time in milliseconds
            token_count: Token count
            document_id_list: List of document IDs used
            query_type: Query type (simple, complex, agentic)
            successful: Whether the query was successful
            
        Returns:
            Created analytics query
        """
        analytics_query = AnalyticsQuery(
            query=query,
            model=model,
            use_rag=use_rag,
            timestamp=datetime.utcnow(),
            response_time_ms=response_time_ms,
            token_count=token_count,
            document_id_list=document_id_list or [],  # Changed from document_ids to document_id_list
            query_type=query_type,
            successful=successful
        )
        
        self.session.add(analytics_query)
        await self.session.commit()
        await self.session.refresh(analytics_query)
        return analytics_query
    
    async def get_query_count_by_date(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get query count by date
        
        Args:
            days: Number of days to include
            
        Returns:
            List of dictionaries with date and count
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query_result = await (
            self.session.query(
                cast(AnalyticsQuery.timestamp, Date).label("date"),
                func.count(AnalyticsQuery.id).label("count")
            )
            .filter(AnalyticsQuery.timestamp >= start_date)
            .group_by(cast(AnalyticsQuery.timestamp, Date))
            .order_by(cast(AnalyticsQuery.timestamp, Date))
            .all()
        )
        
        return [{"date": str(row.date), "count": row.count} for row in query_result]
    
    async def get_average_response_time(self, days: int = 30) -> Dict[str, float]:
        """
        Get average response time
        
        Args:
            days: Number of days to include
            
        Returns:
            Dictionary with average response times
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        avg_time_overall = await (
            self.session.query(func.avg(AnalyticsQuery.response_time_ms))
            .filter(AnalyticsQuery.timestamp >= start_date)
            .scalar() or 0
        )
        
        avg_time_with_rag = await (
            self.session.query(func.avg(AnalyticsQuery.response_time_ms))
            .filter(AnalyticsQuery.timestamp >= start_date)
            .filter(AnalyticsQuery.use_rag == True)
            .scalar() or 0
        )
        
        avg_time_without_rag = await (
            self.session.query(func.avg(AnalyticsQuery.response_time_ms))
            .filter(AnalyticsQuery.timestamp >= start_date)
            .filter(AnalyticsQuery.use_rag == False)
            .scalar() or 0
        )
        
        return {
            "overall": float(avg_time_overall),
            "with_rag": float(avg_time_with_rag),
            "without_rag": float(avg_time_without_rag)
        }
    
    async def get_query_type_distribution(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get query type distribution
        
        Args:
            days: Number of days to include
            
        Returns:
            List of dictionaries with query type and count
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query_result = await (
            self.session.query(
                AnalyticsQuery.query_type,
                func.count(AnalyticsQuery.id).label("count")
            )
            .filter(AnalyticsQuery.timestamp >= start_date)
            .filter(AnalyticsQuery.query_type.isnot(None))
            .group_by(AnalyticsQuery.query_type)
            .order_by(desc("count"))
            .all()
        )
        
        return [{"query_type": row.query_type, "count": row.count} for row in query_result]
    
    async def get_model_usage_statistics(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get model usage statistics
        
        Args:
            days: Number of days to include
            
        Returns:
            List of dictionaries with model and usage statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query_result = await (
            self.session.query(
                AnalyticsQuery.model,
                func.count(AnalyticsQuery.id).label("query_count"),
                func.avg(AnalyticsQuery.response_time_ms).label("avg_response_time"),
                func.avg(AnalyticsQuery.token_count).label("avg_token_count"),
                func.sum(AnalyticsQuery.token_count).label("total_token_count")
            )
            .filter(AnalyticsQuery.timestamp >= start_date)
            .filter(AnalyticsQuery.model.isnot(None))
            .group_by(AnalyticsQuery.model)
            .order_by(desc("query_count"))
            .all()
        )
        
        return [
            {
                "model": row.model,
                "query_count": row.query_count,
                "avg_response_time": float(row.avg_response_time or 0),
                "avg_token_count": float(row.avg_token_count or 0),
                "total_token_count": row.total_token_count or 0
            }
            for row in query_result
        ]
    
    async def get_success_rate(self, days: int = 30) -> Dict[str, Any]:
        """
        Get query success rate
        
        Args:
            days: Number of days to include
            
        Returns:
            Dictionary with success rate statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total_queries = await (
            self.session.query(func.count(AnalyticsQuery.id))
            .filter(AnalyticsQuery.timestamp >= start_date)
            .scalar() or 0
        )
        
        successful_queries = await (
            self.session.query(func.count(AnalyticsQuery.id))
            .filter(AnalyticsQuery.timestamp >= start_date)
            .filter(AnalyticsQuery.successful == True)
            .scalar() or 0
        )
        
        success_rate = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": total_queries - successful_queries,
            "success_rate": success_rate
        }
    
    async def get_document_usage_statistics(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get document usage statistics
        
        Args:
            days: Number of days to include
            limit: Maximum number of documents to return
            
        Returns:
            List of dictionaries with document and usage statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # This is a more complex query that requires JSON array processing
        # For PostgreSQL, we can use the jsonb_array_elements function
        # This is a simplified version that counts documents in the document_ids array
        
        # In a real implementation, you would need to use a database-specific approach
        # to extract and count elements from the JSON array
        
        # For now, we'll return a placeholder
        return []
    
    async def get_hourly_query_distribution(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get hourly query distribution
        
        Args:
            days: Number of days to include
            
        Returns:
            List of dictionaries with hour and count
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query_result = await (
            self.session.query(
                extract('hour', AnalyticsQuery.timestamp).label("hour"),
                func.count(AnalyticsQuery.id).label("count")
            )
            .filter(AnalyticsQuery.timestamp >= start_date)
            .group_by(extract('hour', AnalyticsQuery.timestamp))
            .order_by(extract('hour', AnalyticsQuery.timestamp))
            .all()
        )
        
        return [{"hour": int(row.hour), "count": row.count} for row in query_result]