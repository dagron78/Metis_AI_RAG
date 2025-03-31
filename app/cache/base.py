"""
Base cache implementation for Metis_RAG.
"""

import os
import time
import json
import logging
import pickle
from typing import Dict, Any, Optional, Generic, TypeVar, List

T = TypeVar('T')

class Cache(Generic[T]):
    """
    Generic cache implementation with disk persistence.
    
    This class provides a generic caching mechanism with optional disk persistence,
    TTL-based expiration, and size-based pruning.
    
    Attributes:
        name (str): Name of the cache, used for logging and persistence
        ttl (int): Time-to-live in seconds for cache entries
        max_size (int): Maximum number of entries in the cache
        persist (bool): Whether to persist the cache to disk
        persist_dir (str): Directory for cache persistence
        cache (Dict[str, Dict[str, Any]]): In-memory cache storage
        hits (int): Number of cache hits
        misses (int): Number of cache misses
        logger (logging.Logger): Logger instance
    """
    
    def __init__(
        self,
        name: str,
        ttl: int = 3600,
        max_size: int = 1000,
        persist: bool = True,
        persist_dir: str = "data/cache"
    ):
        """
        Initialize a new cache instance.
        
        Args:
            name: Name of the cache, used for logging and persistence
            ttl: Time-to-live in seconds for cache entries (default: 3600)
            max_size: Maximum number of entries in the cache (default: 1000)
            persist: Whether to persist the cache to disk (default: True)
            persist_dir: Directory for cache persistence (default: "data/cache")
        """
        self.name = name
        self.ttl = ttl
        self.max_size = max_size
        self.persist = persist
        self.persist_dir = persist_dir
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0
        self.logger = logging.getLogger(f"app.cache.{name}")
        
        # Create persist directory if needed
        if self.persist:
            os.makedirs(os.path.join(self.persist_dir, self.name), exist_ok=True)
            self._load_from_disk()
            self.logger.info(f"Loaded {len(self.cache)} items from disk cache")
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                self.hits += 1
                self.logger.debug(f"Cache hit for key: {key}")
                return entry["value"]
            else:
                # Expired, remove from cache
                del self.cache[key]
                self.logger.debug(f"Cache entry expired for key: {key}")
        
        self.misses += 1
        self.logger.debug(f"Cache miss for key: {key}")
        return None
    
    def set(self, key: str, value: T) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        self.logger.debug(f"Cache set for key: {key}")
        
        # Prune cache if it gets too large
        if len(self.cache) > self.max_size:
            self._prune()
            
        # Persist to disk if enabled
        if self.persist:
            self._save_to_disk()
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was found and deleted, False otherwise
        """
        if key in self.cache:
            del self.cache[key]
            self.logger.debug(f"Cache entry deleted for key: {key}")
            
            # Persist changes to disk if enabled
            if self.persist:
                self._save_to_disk()
            
            return True
        
        return False
    
    def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        self.cache = {}
        self.logger.info(f"Cache '{self.name}' cleared")
        
        # Persist changes to disk if enabled
        if self.persist:
            self._save_to_disk()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_ratio = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "name": self.name,
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": hit_ratio,
            "ttl_seconds": self.ttl,
            "persist": self.persist
        }
    
    def _prune(self) -> None:
        """
        Remove oldest entries from the cache when it exceeds max_size.
        """
        # Sort by timestamp and keep the newest entries
        sorted_cache = sorted(
            self.cache.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True
        )
        
        # Keep only half of the max cache size
        keep_count = self.max_size // 2
        self.cache = dict(sorted_cache[:keep_count])
        self.logger.info(f"Pruned cache to {keep_count} entries")
        
        # Persist changes to disk if enabled
        if self.persist:
            self._save_to_disk()
    
    def _save_to_disk(self) -> None:
        """
        Save the cache to disk.
        """
        try:
            cache_file = os.path.join(self.persist_dir, self.name, "cache.pickle")
            with open(cache_file, "wb") as f:
                pickle.dump(self.cache, f)
            
            # Save stats separately as JSON for easier inspection
            stats_file = os.path.join(self.persist_dir, self.name, "stats.json")
            with open(stats_file, "w") as f:
                json.dump(self.get_stats(), f, indent=2)
                
            self.logger.debug(f"Cache saved to disk: {cache_file}")
        except Exception as e:
            self.logger.error(f"Error saving cache to disk: {str(e)}")
    
    def _load_from_disk(self) -> None:
        """
        Load the cache from disk.
        """
        try:
            cache_file = os.path.join(self.persist_dir, self.name, "cache.pickle")
            if os.path.exists(cache_file):
                with open(cache_file, "rb") as f:
                    loaded_cache = pickle.load(f)
                
                # Filter out expired entries
                current_time = time.time()
                self.cache = {
                    key: entry
                    for key, entry in loaded_cache.items()
                    if current_time - entry["timestamp"] < self.ttl
                }
                
                self.logger.debug(f"Cache loaded from disk: {cache_file}")
            else:
                self.logger.debug(f"No cache file found at {cache_file}")
        except Exception as e:
            self.logger.error(f"Error loading cache from disk: {str(e)}")
            # Start with an empty cache if loading fails
            self.cache = {}
    
    def get_keys(self) -> List[str]:
        """
        Get all keys in the cache.
        
        Returns:
            List of cache keys
        """
        return list(self.cache.keys())
    
    def get_size(self) -> int:
        """
        Get the current size of the cache.
        
        Returns:
            Number of entries in the cache
        """
        return len(self.cache)
    
    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in the cache and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key exists and is not expired, False otherwise
        """
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return True
            else:
                # Expired, remove from cache
                del self.cache[key]
        
        return False
    
    def update_ttl(self, ttl: int) -> None:
        """
        Update the TTL for the cache.
        
        Args:
            ttl: New TTL in seconds
        """
        self.ttl = ttl
        self.logger.info(f"Cache TTL updated to {ttl} seconds")