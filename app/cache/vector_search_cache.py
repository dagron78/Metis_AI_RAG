"""
Vector search cache implementation for Metis_RAG.
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple

from app.cache.base import Cache

class VectorSearchCache(Cache[List[Dict[str, Any]]]):
    """
    Cache implementation for vector search results.
    
    This cache stores the results of vector searches to avoid redundant
    embedding generation and vector database queries.
    
    Attributes:
        Inherits all attributes from the base Cache class
    """
    
    def __init__(
        self,
        ttl: int = 3600,
        max_size: int = 1000,
        persist: bool = True,
        persist_dir: str = "data/cache"
    ):
        """
        Initialize a new vector search cache.
        
        Args:
            ttl: Time-to-live in seconds for cache entries (default: 3600)
            max_size: Maximum number of entries in the cache (default: 1000)
            persist: Whether to persist the cache to disk (default: True)
            persist_dir: Directory for cache persistence (default: "data/cache")
        """
        super().__init__(
            name="vector_search",
            ttl=ttl,
            max_size=max_size,
            persist=persist,
            persist_dir=persist_dir
        )
    
    def get_results(
        self,
        query: str,
        top_k: int,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_criteria: Optional filter criteria
            
        Returns:
            Cached search results if found, None otherwise
        """
        cache_key = self._create_cache_key(query, top_k, filter_criteria)
        return self.get(cache_key)
    
    def set_results(
        self,
        query: str,
        top_k: int,
        results: List[Dict[str, Any]],
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache search results for a query.
        
        Args:
            query: Search query
            top_k: Number of results
            results: Search results to cache
            filter_criteria: Optional filter criteria
        """
        cache_key = self._create_cache_key(query, top_k, filter_criteria)
        self.set(cache_key, results)
    
    def _create_cache_key(
        self,
        query: str,
        top_k: int,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a cache key from the search parameters.
        
        Args:
            query: Search query
            top_k: Number of results
            filter_criteria: Optional filter criteria
            
        Returns:
            Cache key string
        """
        # Normalize the query by removing extra whitespace and lowercasing
        normalized_query = " ".join(query.lower().split())
        
        # Convert filter criteria to a stable string representation
        filter_str = "none"
        if filter_criteria:
            # Sort keys to ensure consistent ordering
            filter_str = json.dumps(filter_criteria, sort_keys=True)
        
        # Create a hash of the combined parameters for a shorter key
        key_data = f"{normalized_query}:{top_k}:{filter_str}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"vsearch:{key_hash}"
    
    def invalidate_by_document_id(self, document_id: str) -> int:
        """
        Invalidate all cache entries that might contain results from a specific document.
        This is a more complex operation that requires examining the cached results.
        
        Args:
            document_id: Document ID to invalidate
            
        Returns:
            Number of cache entries invalidated
        """
        invalidated_count = 0
        keys_to_delete = []
        
        # Find all cache entries that contain the document ID
        for key, entry in list(self.cache.items()):
            results = entry["value"]
            for result in results:
                if result.get("document_id") == document_id or result.get("metadata", {}).get("document_id") == document_id:
                    keys_to_delete.append(key)
                    invalidated_count += 1
                    break
        
        # Delete the identified entries
        for key in keys_to_delete:
            self.delete(key)
        
        self.logger.info(f"Invalidated {invalidated_count} cache entries for document {document_id}")
        return invalidated_count
    
    def get_cache_stats_by_query_prefix(self, prefix: str) -> Tuple[int, int]:
        """
        Get hit/miss statistics for queries with a specific prefix.
        
        Args:
            prefix: Query prefix to filter by
            
        Returns:
            Tuple of (hits, misses) for queries with the given prefix
        """
        hits = 0
        misses = 0
        
        # This is a simplified implementation that would need to be enhanced
        # with actual tracking of per-query statistics in a real system
        
        return hits, misses