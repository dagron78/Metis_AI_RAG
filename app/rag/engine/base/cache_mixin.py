"""
Cache Mixin for RAG Engine

This module provides the CacheMixin class that adds caching
functionality to the RAG Engine.
"""
import logging
import json
import hashlib
from typing import Dict, Any, Optional, Union, List

logger = logging.getLogger("app.rag.engine.base.cache_mixin")

class CacheMixin:
    """
    Mixin class that adds caching functionality to the RAG Engine
    
    This mixin provides methods for interacting with the cache manager,
    including getting and setting cached responses, and managing cache settings.
    """
    
    def get_cached_response(self,
                           key: str,
                           namespace: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get a cached response
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            Cached response or None if not found
        """
        try:
            # Get cached response
            cached_response = self.cache_manager.get(key, namespace)
            
            if cached_response:
                logger.info(f"Cache hit for key: {key[:20]}... in namespace: {namespace}")
                return cached_response
            else:
                logger.info(f"Cache miss for key: {key[:20]}... in namespace: {namespace}")
                return None
        except Exception as e:
            logger.error(f"Error getting cached response: {str(e)}")
            return None
    
    def set_cached_response(self,
                           key: str,
                           value: Dict[str, Any],
                           namespace: str = "default",
                           ttl: Optional[int] = None) -> bool:
        """
        Set a cached response
        
        Args:
            key: Cache key
            value: Value to cache
            namespace: Cache namespace
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Set cached response
            self.cache_manager.set(key, value, namespace, ttl)
            
            logger.info(f"Cached response for key: {key[:20]}... in namespace: {namespace}")
            return True
        except Exception as e:
            logger.error(f"Error setting cached response: {str(e)}")
            return False
    
    def delete_cached_response(self,
                              key: str,
                              namespace: str = "default") -> bool:
        """
        Delete a cached response
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete cached response
            self.cache_manager.delete(key, namespace)
            
            logger.info(f"Deleted cached response for key: {key[:20]}... in namespace: {namespace}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cached response: {str(e)}")
            return False
    
    def clear_cache(self, namespace: Optional[str] = None) -> bool:
        """
        Clear the cache
        
        Args:
            namespace: Cache namespace to clear (if None, clears all namespaces)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear cache
            if namespace:
                self.cache_manager.clear_namespace(namespace)
                logger.info(f"Cleared cache for namespace: {namespace}")
            else:
                self.cache_manager.clear_all()
                logger.info("Cleared all caches")
            
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary of cache statistics
        """
        try:
            # Get cache statistics
            stats = self.cache_manager.get_all_cache_stats()
            
            logger.info(f"Cache stats: {stats}")
            
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {"error": str(e)}
    
    def generate_cache_key(self,
                          data: Union[str, Dict[str, Any], List[Any]],
                          prefix: str = "") -> str:
        """
        Generate a cache key from data
        
        Args:
            data: Data to generate key from
            prefix: Optional prefix for the key
            
        Returns:
            Cache key
        """
        try:
            # Convert data to string if it's not already
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            # Generate hash
            hash_obj = hashlib.sha256(data_str.encode())
            hash_str = hash_obj.hexdigest()
            
            # Add prefix if provided
            if prefix:
                key = f"{prefix}:{hash_str}"
            else:
                key = hash_str
            
            return key
        except Exception as e:
            logger.error(f"Error generating cache key: {str(e)}")
            # Return a fallback key
            return f"error_key_{hash(str(data))}"
    
    def should_use_cache(self,
                        query_type: str,
                        model_parameters: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if cache should be used for a query
        
        Args:
            query_type: Type of query
            model_parameters: Model parameters
            
        Returns:
            True if cache should be used, False otherwise
        """
        # Get cache settings
        cache_stats = self.cache_manager.get_all_cache_stats()
        caching_enabled = cache_stats.get("caching_enabled", False)
        
        # If caching is disabled globally, don't use cache
        if not caching_enabled:
            return False
        
        # Check if model parameters indicate deterministic output
        if model_parameters:
            # If temperature is high, results may vary, so don't use cache
            temperature = model_parameters.get("temperature", 0.0)
            if temperature > 0.1:
                logger.info(f"Not using cache due to high temperature: {temperature}")
                return False
            
            # If using a specific seed, it's deterministic, so use cache
            if "seed" in model_parameters:
                return True
        
        # Use cache for specific query types
        cacheable_query_types = ["standard", "factual", "lookup"]
        if query_type.lower() in cacheable_query_types:
            return True
        
        # Default to using cache for most queries
        return True