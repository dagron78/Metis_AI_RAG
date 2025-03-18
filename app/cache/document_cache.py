"""
Document cache implementation for Metis_RAG.
"""

import hashlib
from typing import Dict, Any, Optional, List, Tuple

from app.cache.base import Cache

class DocumentCache(Cache[Dict[str, Any]]):
    """
    Cache implementation for document content and metadata.
    
    This cache stores document content and metadata to avoid redundant
    database queries and file system access.
    
    Attributes:
        Inherits all attributes from the base Cache class
    """
    
    def __init__(
        self,
        ttl: int = 7200,  # 2 hours default TTL for documents
        max_size: int = 500,  # Lower default max size due to potentially larger entries
        persist: bool = True,
        persist_dir: str = "data/cache"
    ):
        """
        Initialize a new document cache.
        
        Args:
            ttl: Time-to-live in seconds for cache entries (default: 7200)
            max_size: Maximum number of entries in the cache (default: 500)
            persist: Whether to persist the cache to disk (default: True)
            persist_dir: Directory for cache persistence (default: "data/cache")
        """
        super().__init__(
            name="document",
            ttl=ttl,
            max_size=max_size,
            persist=persist,
            persist_dir=persist_dir
        )
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Cached document if found, None otherwise
        """
        cache_key = self._create_document_key(document_id)
        return self.get(cache_key)
    
    def set_document(self, document_id: str, document: Dict[str, Any]) -> None:
        """
        Cache a document.
        
        Args:
            document_id: Document ID
            document: Document data to cache
        """
        cache_key = self._create_document_key(document_id)
        self.set(cache_key, document)
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """
        Get cached document content by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Cached document content if found, None otherwise
        """
        document = self.get_document(document_id)
        if document:
            return document.get("content")
        return None
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached document metadata by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Cached document metadata if found, None otherwise
        """
        document = self.get_document(document_id)
        if document:
            return document.get("metadata", {})
        return None
    
    def invalidate_document(self, document_id: str) -> bool:
        """
        Invalidate a cached document.
        
        Args:
            document_id: Document ID to invalidate
            
        Returns:
            True if the document was found and invalidated, False otherwise
        """
        cache_key = self._create_document_key(document_id)
        return self.delete(cache_key)
    
    def get_documents_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get all cached documents with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of cached documents with the specified tag
        """
        documents = []
        
        for key in self.get_keys():
            if not key.startswith("doc:"):
                continue
                
            document = self.get(key)
            if document and tag in document.get("metadata", {}).get("tags", []):
                documents.append(document)
        
        return documents
    
    def get_documents_by_folder(self, folder: str) -> List[Dict[str, Any]]:
        """
        Get all cached documents in a specific folder.
        
        Args:
            folder: Folder path to filter by
            
        Returns:
            List of cached documents in the specified folder
        """
        documents = []
        
        for key in self.get_keys():
            if not key.startswith("doc:"):
                continue
                
            document = self.get(key)
            if document and document.get("metadata", {}).get("folder") == folder:
                documents.append(document)
        
        return documents
    
    def _create_document_key(self, document_id: str) -> str:
        """
        Create a cache key for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Cache key string
        """
        # Use a simple prefix for document keys
        return f"doc:{document_id}"
    
    def get_document_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached document chunk by ID.
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            Cached document chunk if found, None otherwise
        """
        cache_key = f"chunk:{chunk_id}"
        return self.get(cache_key)
    
    def set_document_chunk(self, chunk_id: str, chunk: Dict[str, Any]) -> None:
        """
        Cache a document chunk.
        
        Args:
            chunk_id: Chunk ID
            chunk: Chunk data to cache
        """
        cache_key = f"chunk:{chunk_id}"
        self.set(cache_key, chunk)
    
    def invalidate_document_chunks(self, document_id: str) -> int:
        """
        Invalidate all cached chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Number of chunks invalidated
        """
        invalidated_count = 0
        
        for key in list(self.get_keys()):
            if not key.startswith("chunk:"):
                continue
                
            chunk = self.get(key)
            if chunk and chunk.get("document_id") == document_id:
                self.delete(key)
                invalidated_count += 1
        
        self.logger.info(f"Invalidated {invalidated_count} chunks for document {document_id}")
        return invalidated_count
    
    def get_cache_stats_by_type(self) -> Dict[str, Tuple[int, int]]:
        """
        Get hit/miss statistics by entry type (document vs. chunk).
        
        Returns:
            Dictionary mapping entry types to (hits, misses) tuples
        """
        # This is a simplified implementation that would need to be enhanced
        # with actual tracking of per-type statistics in a real system
        return {
            "document": (0, 0),
            "chunk": (0, 0)
        }