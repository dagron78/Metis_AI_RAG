"""
Cache manager for Metis_RAG.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic

from app.cache.base import Cache
from app.cache.vector_search_cache import VectorSearchCache
from app.cache.document_cache import DocumentCache
from app.cache.llm_response_cache import LLMResponseCache

T = TypeVar('T')

class CacheManager:
    """
    Manager for all cache instances in the system.
    
    This class provides a centralized way to access and manage all caches,
    including initialization, configuration, and monitoring.
    
    Attributes:
        vector_search_cache: Cache for vector search results
        document_cache: Cache for document content and metadata
        llm_response_cache: Cache for LLM responses
        logger: Logger instance
    """
    
    def __init__(
        self,
        cache_dir: str = "data/cache",
        config_file: Optional[str] = None,
        enable_caching: bool = True
    ):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory for cache persistence (default: "data/cache")
            config_file: Path to cache configuration file (default: None)
            enable_caching: Whether to enable caching (default: True)
        """
        self.cache_dir = cache_dir
        self.enable_caching = enable_caching
        self.logger = logging.getLogger("app.cache.manager")
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load configuration if provided
        self.config = self._load_config(config_file)
        
        # Initialize caches
        self._initialize_caches()
        
        self.logger.info(f"Cache manager initialized with caching {'enabled' if enable_caching else 'disabled'}")
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """
        Load cache configuration from a file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "vector_search_cache": {
                "ttl": 3600,
                "max_size": 1000,
                "persist": True
            },
            "document_cache": {
                "ttl": 7200,
                "max_size": 500,
                "persist": True
            },
            "llm_response_cache": {
                "ttl": 86400,
                "max_size": 2000,
                "persist": True
            }
        }
        
        if not config_file or not os.path.exists(config_file):
            self.logger.info("Using default cache configuration")
            return default_config
        
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                self.logger.info(f"Loaded cache configuration from {config_file}")
                
                # Merge with defaults for any missing values
                for cache_name, default_values in default_config.items():
                    if cache_name not in config:
                        config[cache_name] = default_values
                    else:
                        for key, value in default_values.items():
                            if key not in config[cache_name]:
                                config[cache_name][key] = value
                
                return config
        except Exception as e:
            self.logger.error(f"Error loading cache configuration: {str(e)}")
            return default_config
    
    def _initialize_caches(self) -> None:
        """
        Initialize all cache instances.
        """
        # Only create actual cache instances if caching is enabled
        if self.enable_caching:
            # Initialize vector search cache
            vector_config = self.config["vector_search_cache"]
            self.vector_search_cache = VectorSearchCache(
                ttl=vector_config["ttl"],
                max_size=vector_config["max_size"],
                persist=vector_config["persist"],
                persist_dir=self.cache_dir
            )
            
            # Initialize document cache
            document_config = self.config["document_cache"]
            self.document_cache = DocumentCache(
                ttl=document_config["ttl"],
                max_size=document_config["max_size"],
                persist=document_config["persist"],
                persist_dir=self.cache_dir
            )
            
            # Initialize LLM response cache
            llm_config = self.config["llm_response_cache"]
            self.llm_response_cache = LLMResponseCache(
                ttl=llm_config["ttl"],
                max_size=llm_config["max_size"],
                persist=llm_config["persist"],
                persist_dir=self.cache_dir
            )
        else:
            # Create dummy cache instances that don't actually cache anything
            self.vector_search_cache = self._create_dummy_cache(VectorSearchCache)
            self.document_cache = self._create_dummy_cache(DocumentCache)
            self.llm_response_cache = self._create_dummy_cache(LLMResponseCache)
    
    def _create_dummy_cache(self, cache_class: Type[Cache[T]]) -> Cache[T]:
        """
        Create a dummy cache instance that doesn't actually cache anything.
        
        Args:
            cache_class: Cache class to instantiate
            
        Returns:
            Dummy cache instance
        """
        # Create a cache instance
        dummy_cache = cache_class(
            ttl=1,  # 1 second TTL
            max_size=1,
            persist=False,
            persist_dir=self.cache_dir
        )
        
        # Override the get and set methods to make it truly non-caching
        original_set = dummy_cache.set
        
        def dummy_set(key: str, value: Any) -> None:
            # Do nothing when setting values
            pass
            
        def dummy_get(key: str) -> Optional[T]:
            # Always return None
            return None
            
        # Replace the methods with our dummy implementations
        dummy_cache.set = dummy_set
        dummy_cache.get = dummy_get
        
        return dummy_cache
    
    def clear_all_caches(self) -> None:
        """
        Clear all caches.
        """
        if not self.enable_caching:
            self.logger.info("Caching is disabled, no caches to clear")
            return
            
        self.vector_search_cache.clear()
        self.document_cache.clear()
        self.llm_response_cache.clear()
        self.logger.info("All caches cleared")
    
    def get_all_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all caches.
        
        Returns:
            Dictionary mapping cache names to statistics dictionaries
        """
        if not self.enable_caching:
            return {
                "caching_enabled": False
            }
            
        return {
            "caching_enabled": True,
            "vector_search_cache": self.vector_search_cache.get_stats(),
            "document_cache": self.document_cache.get_stats(),
            "llm_response_cache": self.llm_response_cache.get_stats()
        }
    
    def update_cache_config(self, config: Dict[str, Any]) -> None:
        """
        Update cache configuration.
        
        Args:
            config: New configuration dictionary
        """
        if not self.enable_caching:
            self.logger.info("Caching is disabled, configuration update ignored")
            return
            
        # Update vector search cache configuration
        if "vector_search_cache" in config:
            vector_config = config["vector_search_cache"]
            if "ttl" in vector_config:
                self.vector_search_cache.update_ttl(vector_config["ttl"])
        
        # Update document cache configuration
        if "document_cache" in config:
            document_config = config["document_cache"]
            if "ttl" in document_config:
                self.document_cache.update_ttl(document_config["ttl"])
        
        # Update LLM response cache configuration
        if "llm_response_cache" in config:
            llm_config = config["llm_response_cache"]
            if "ttl" in llm_config:
                self.llm_response_cache.update_ttl(llm_config["ttl"])
        
        # Update internal configuration
        self.config.update(config)
        self.logger.info("Cache configuration updated")
    
    def save_config(self, config_file: str) -> None:
        """
        Save current cache configuration to a file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            with open(config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Cache configuration saved to {config_file}")
        except Exception as e:
            self.logger.error(f"Error saving cache configuration: {str(e)}")
    
    def invalidate_document(self, document_id: str) -> None:
        """
        Invalidate all caches for a specific document.
        
        Args:
            document_id: Document ID to invalidate
        """
        if not self.enable_caching:
            return
            
        # Invalidate document in document cache
        self.document_cache.invalidate_document(document_id)
        
        # Invalidate document chunks in document cache
        self.document_cache.invalidate_document_chunks(document_id)
        
        # Invalidate vector search results containing the document
        self.vector_search_cache.invalidate_by_document_id(document_id)
        
        self.logger.info(f"All caches invalidated for document {document_id}")