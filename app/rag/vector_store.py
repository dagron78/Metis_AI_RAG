import logging
import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import chromadb
from chromadb.config import Settings

from app.core.config import CHROMA_DB_DIR, DEFAULT_EMBEDDING_MODEL
from app.models.document import Document, Chunk
from app.rag.ollama_client import OllamaClient
from app.cache.vector_search_cache import VectorSearchCache

logger = logging.getLogger("app.rag.vector_store")

# Singleton instance
_vector_store_instance = None

class VectorStore:
    """
    Vector store for document embeddings using ChromaDB with caching for performance
    and security filtering based on user permissions
    """
    def __init__(
        self,
        persist_directory: str = CHROMA_DB_DIR,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        enable_cache: bool = True,
        cache_ttl: int = 3600,  # 1 hour in seconds
        cache_max_size: int = 1000,
        cache_persist: bool = True,
        cache_persist_dir: str = "data/cache",
        user_id: Optional[UUID] = None
    ):
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.ollama_client = None
        self.user_id = user_id  # Store the user ID for permission filtering
        
        # Cache settings
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.cache_max_size = cache_max_size
        
        # Initialize the vector search cache
        if self.enable_cache:
            self.vector_cache = VectorSearchCache(
                ttl=cache_ttl,
                max_size=cache_max_size,
                persist=cache_persist,
                persist_dir=cache_persist_dir
            )
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Create or get the collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Vector store initialized with collection 'documents', caching {'enabled' if enable_cache else 'disabled'}")
    
    @staticmethod
    def get_instance(
        persist_directory: str = CHROMA_DB_DIR,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        cache_max_size: int = 1000,
        cache_persist: bool = True,
        cache_persist_dir: str = "data/cache",
        user_id: Optional[UUID] = None
    ) -> 'VectorStore':
        """
        Get the singleton instance of VectorStore
        
        This method ensures that only one instance of VectorStore is created,
        which helps reduce the overhead of initializing the ChromaDB client
        and loading the cache for each request.
        
        Returns:
            VectorStore: The singleton instance
        """
        global _vector_store_instance
        
        if _vector_store_instance is None:
            _vector_store_instance = VectorStore(
                persist_directory=persist_directory,
                embedding_model=embedding_model,
                enable_cache=enable_cache,
                cache_ttl=cache_ttl,
                cache_max_size=cache_max_size,
                cache_persist=cache_persist,
                cache_persist_dir=cache_persist_dir,
                user_id=user_id
            )
            logger.debug("Created new VectorStore singleton instance")
        else:
            # Update user_id if provided
            if user_id is not None:
                _vector_store_instance.user_id = user_id
                logger.debug(f"Updated user_id in VectorStore singleton instance: {user_id}")
        
        return _vector_store_instance
    
    async def add_document(self, document: Document) -> None:
        """
        Add a document to the vector store with batch embedding
        """
        try:
            logger.info(f"Adding document {document.id} to vector store")
            
            # Make sure we have an Ollama client
            if self.ollama_client is None:
                self.ollama_client = OllamaClient()
            
            # Prepare chunks for batch processing
            chunks_to_embed = [chunk for chunk in document.chunks if not chunk.embedding]
            chunk_contents = [chunk.content for chunk in chunks_to_embed]
            
            # Create embeddings in batch if possible
            if chunk_contents:
                try:
                    # Batch embedding
                    embeddings = await self._batch_create_embeddings(chunk_contents)
                    
                    # Assign embeddings to chunks
                    for i, chunk in enumerate(chunks_to_embed):
                        chunk.embedding = embeddings[i]
                except Exception as batch_error:
                    logger.warning(f"Batch embedding failed: {str(batch_error)}. Falling back to sequential embedding.")
                    # Fall back to sequential embedding
                    for chunk in chunks_to_embed:
                        chunk.embedding = await self.ollama_client.create_embedding(
                            text=chunk.content,
                            model=self.embedding_model
                        )
            
            # Add chunks to the collection
            for chunk in document.chunks:
                if not chunk.embedding:
                    logger.warning(f"Chunk {chunk.id} has no embedding, skipping")
                    continue
                    
                # Prepare metadata - convert any lists to strings to satisfy ChromaDB requirements
                metadata = {
                    "document_id": document.id,
                    "chunk_index": chunk.metadata.get("index", 0),
                    "filename": document.filename,
                    "tags": ",".join(document.tags) if document.tags else "",
                    "folder": document.folder
                }
                
                # Add user context and permission information
                if hasattr(document, 'user_id') and document.user_id:
                    metadata["user_id"] = str(document.user_id)
                elif self.user_id:
                    metadata["user_id"] = str(self.user_id)
                
                # Add is_public flag for permission filtering
                if hasattr(document, 'is_public'):
                    metadata["is_public"] = document.is_public
                
                # Add document permissions information from chunk metadata
                if "shared_with" in chunk.metadata:
                    metadata["shared_with"] = chunk.metadata["shared_with"]
                
                if "shared_user_ids" in chunk.metadata:
                    metadata["shared_user_ids"] = chunk.metadata["shared_user_ids"]
                
                # Add any additional metadata from the chunk
                for key, value in chunk.metadata.items():
                    # Convert lists to strings if present
                    if isinstance(value, list):
                        metadata[key] = ",".join(str(item) for item in value)
                    else:
                        metadata[key] = value
                
                self.collection.add(
                    ids=[chunk.id],
                    embeddings=[chunk.embedding],
                    documents=[chunk.content],
                    metadatas=[metadata]
                )
            
            # Clear the cache to ensure we're using the latest embeddings
            self.clear_cache()
            
            logger.info(f"Added {len(document.chunks)} chunks to vector store for document {document.id}")
        except Exception as e:
            logger.error(f"Error adding document {document.id} to vector store: {str(e)}")
            raise
    
    async def _batch_create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts (batched)"""
        try:
            # Attempt to use Langchain's embed_documents for batch embedding
            from langchain_community.embeddings import OllamaEmbeddings
            embeddings_model = OllamaEmbeddings(model=self.embedding_model)
            return embeddings_model.embed_documents(texts)
        except (ImportError, NotImplementedError) as e:
            # Handle the case where the provider doesn't support batch embedding
            logger.warning(f"Batch embedding not supported: {str(e)}. Falling back to sequential embedding.")
            embeddings = []
            for text in texts:
                embedding = await self.ollama_client.create_embedding(text=text, model=self.embedding_model)
                embeddings.append(embedding)
            return embeddings
    
    async def update_document_metadata(self, document_id: str, metadata_update: Dict[str, Any]) -> None:
        """
        Update metadata for all chunks of a document
        """
        try:
            logger.info(f"Updating metadata for document {document_id}")
            
            # Get all chunks for the document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if not results["ids"]:
                logger.warning(f"No chunks found for document {document_id}")
                return
            
            # Update each chunk's metadata
            for i, chunk_id in enumerate(results["ids"]):
                # Get current metadata
                current_metadata = results["metadatas"][i]
                
                # Update with new metadata
                updated_metadata = {**current_metadata, **metadata_update}
                
                # Update in collection
                self.collection.update(
                    ids=[chunk_id],
                    metadatas=[updated_metadata]
                )
            
            logger.info(f"Updated metadata for {len(results['ids'])} chunks of document {document_id}")
        except Exception as e:
            logger.error(f"Error updating metadata for document {document_id}: {str(e)}")
            raise
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query with caching for performance
        and security filtering based on user permissions
        """
        try:
            # Use provided user_id or fall back to the instance's user_id
            effective_user_id = user_id or self.user_id
            
            # Apply security filtering
            secure_filter = self._apply_security_filter(filter_criteria, effective_user_id)
            
            # Check cache if enabled
            if self.enable_cache:
                # Include user_id in cache key to ensure proper isolation
                cache_key_parts = [query, top_k, secure_filter]
                if effective_user_id:
                    cache_key_parts.append(str(effective_user_id))
                
                cached_result = self.vector_cache.get_results(query, top_k, secure_filter)
                
                if cached_result:
                    logger.info(f"Cache hit for query: {query[:50]}...")
                    return cached_result
                
                logger.info(f"Cache miss for query: {query[:50]}...")
            
            logger.info(f"Searching for documents similar to query: {query[:50]}...")
            
            # Make sure we have an Ollama client
            if self.ollama_client is None:
                self.ollama_client = OllamaClient()
            
            # Create query embedding
            query_embedding = await self.ollama_client.create_embedding(
                text=query,
                model=self.embedding_model
            )
            
            # Log the query embedding for debugging
            logger.debug(f"Query embedding (first 5 values): {query_embedding[:5]}")
            
            # Log filter criteria if present
            if secure_filter:
                logger.info(f"Applying security filter criteria: {secure_filter}")
            
            # Search for similar documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=secure_filter
            )
            
            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                logger.info(f"Raw search results: {len(results['ids'][0])} chunks found")
                
                for i in range(len(results["ids"][0])):
                    chunk_id = results["ids"][0][i]
                    content = results["documents"][0][i]
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i] if "distances" in results else None
                    
                    # Log each result for debugging
                    logger.debug(f"Result {i+1}:")
                    logger.debug(f"  Chunk ID: {chunk_id}")
                    logger.debug(f"  Distance: {distance}")
                    logger.debug(f"  Metadata: {metadata}")
                    logger.debug(f"  Content preview: {content[:100] if content is not None else 'None'}...")
                    
                    # Skip adding None content to results or provide a default value
                    if content is not None:
                        formatted_results.append({
                            "chunk_id": chunk_id,
                            "content": content,
                            "metadata": metadata,
                            "distance": distance
                        })
                    else:
                        logger.warning(f"Skipping result with chunk_id {chunk_id} due to None content")
                
                # Apply post-retrieval permission check
                if effective_user_id:
                    formatted_results = self._post_retrieval_permission_check(formatted_results, effective_user_id)
            else:
                logger.warning(f"No results found for query: {query[:50]}...")
            
            logger.info(f"Found {len(formatted_results)} similar documents")
            
            # Log document IDs for easier tracking
            if formatted_results:
                doc_ids = set(result["metadata"]["document_id"] for result in formatted_results)
                logger.info(f"Documents retrieved: {doc_ids}")
            
            # Cache results if enabled
            if self.enable_cache:
                self.vector_cache.set_results(query, top_k, formatted_results, secure_filter)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching for documents: {str(e)}")
            raise
    
    def _apply_security_filter(self, filter_criteria: Optional[Dict[str, Any]], user_id: Optional[UUID]) -> Dict[str, Any]:
        """
        Apply security filtering based on user permissions
        
        Args:
            filter_criteria: Original filter criteria
            user_id: User ID for permission filtering
            
        Returns:
            Updated filter criteria with security constraints
        """
        # Check if developer mode is enabled
        from app.core.config import SETTINGS
        
        # If in developer mode, don't apply any security filtering
        if SETTINGS.developer_mode:
            logger.info("Developer mode: Security filtering disabled for vector store")
            return filter_criteria.copy() if filter_criteria else {}
        
        # Start with the original filter criteria or an empty dict
        secure_filter = filter_criteria.copy() if filter_criteria else {}
        
        # If no user_id, only allow public documents
        if not user_id:
            secure_filter["is_public"] = True
            return secure_filter
        
        # For authenticated users, allow:
        # 1. Documents owned by the user
        # 2. Public documents
        # 3. Documents explicitly shared with the user
        
        # Convert user_id to string for comparison
        user_id_str = str(user_id)
        
        # Create a filter that matches any of:
        # - Documents owned by the user
        # - Public documents
        # - Documents shared with the user
        permission_filter = {
            "$or": [
                {"user_id": user_id_str},                    # Documents owned by the user
                {"is_public": True}                          # Public documents
                # We need to handle shared documents in post-processing since $contains isn't supported
            ]
        }
        
        # Handle shared_user_ids separately since $contains isn't supported
        # We'll do a post-retrieval check for shared documents in _post_retrieval_permission_check
        
        # Log the permission filter for debugging
        logger.debug(f"Applied permission filter for user {user_id_str}: {permission_filter}")
        
        # If there are existing filters, combine them with the permission filter
        if secure_filter:
            # Combine existing filters with permission filter using $and
            return {"$and": [secure_filter, permission_filter]}
        else:
            # Just use the permission filter
            return permission_filter
    
    async def search_by_tags(
        self,
        query: str,
        tags: List[str],
        top_k: int = 5,
        additional_filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents with specific tags
        """
        try:
            logger.info(f"Searching for documents with tags {tags} similar to query: {query[:50]}...")
            
            # Prepare filter criteria
            filter_criteria = additional_filters or {}
            
            # Add tag filter
            if tags:
                # Since ChromaDB doesn't support $contains for metadata filtering,
                # we'll use a different approach for tag filtering
                
                # For a single tag, we can use direct equality
                if len(tags) == 1:
                    tag = tags[0]
                    # Check if the tag is in the comma-separated tags string
                    # This is a simplification - we'll rely more on post-filtering
                    if "tags" not in filter_criteria:
                        filter_criteria["tags"] = {"$eq": tag}
                    else:
                        # If there's already a tags filter, combine with it
                        existing_filter = filter_criteria["tags"]
                        filter_criteria["tags"] = {"$and": [existing_filter, {"$eq": tag}]}
                
                # For multiple tags, we'll retrieve a broader set and filter post-retrieval
                # We'll increase top_k to compensate for post-filtering
                top_k = top_k * 3  # Get more results to account for post-filtering
            
            # Perform search with filters
            results = await self.search(query, top_k, filter_criteria, user_id)
            
            # If we have multiple tags, we need to post-filter the results
            if tags and len(tags) > 1:
                filtered_results = self._post_filter_by_tags(results, tags)
                # Limit to the original top_k
                filtered_results = filtered_results[:top_k // 3]
                return filtered_results
            
            return results
        except Exception as e:
            logger.error(f"Error searching for documents by tags: {str(e)}")
            raise
    
    async def search_by_folder(
        self,
        query: str,
        folder: str,
        top_k: int = 5,
        additional_filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents in a specific folder
        """
        try:
            logger.info(f"Searching for documents in folder {folder} similar to query: {query[:50]}...")
            
            # Prepare filter criteria
            filter_criteria = additional_filters or {}
            
            # Add folder filter
            if folder:
                filter_criteria["folder"] = folder
            
            # Perform search with filters
            return await self.search(query, top_k, filter_criteria, user_id)
        except Exception as e:
            logger.error(f"Error searching for documents by folder: {str(e)}")
            raise
    
    def delete_document(self, document_id: str) -> None:
        """
        Delete a document from the vector store
        """
        try:
            logger.info(f"Deleting document {document_id} from vector store")
            
            # Delete chunks with the given document_id
            self.collection.delete(
                where={"document_id": document_id}
            )
            
            # Invalidate cache entries for this document
            if self.enable_cache:
                self.vector_cache.invalidate_by_document_id(document_id)
                logger.info(f"Invalidated cache entries for document {document_id}")
            
            logger.info(f"Deleted document {document_id} from vector store")
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from vector store: {str(e)}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        """
        try:
            count = self.collection.count()
            stats = {
                "count": count,
                "embeddings_model": self.embedding_model
            }
            
            # Add cache stats if enabled
            if self.enable_cache:
                cache_stats = self.get_cache_stats()
                stats.update(cache_stats)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            raise
    
    def clear_cache(self) -> None:
        """
        Clear the cache to ensure fresh results
        """
        if self.enable_cache:
            self.vector_cache.clear()
            logger.info("Vector store cache cleared")
            
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document from the vector store
        """
        try:
            logger.info(f"Getting chunks for document {document_id} from vector store")
            
            # Get all chunks for the document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if not results["ids"]:
                logger.warning(f"No chunks found for document {document_id}")
                return []
            
            # Format chunks
            chunks = []
            for i in range(len(results["ids"])):
                chunk_id = results["ids"][i]
                content = results["documents"][i]
                metadata = results["metadatas"][i]
                
                chunks.append({
                    "id": chunk_id,
                    "content": content,
                    "metadata": metadata
                })
            
            logger.info(f"Found {len(chunks)} chunks for document {document_id}")
            return chunks
        except Exception as e:
            logger.error(f"Error getting chunks for document {document_id} from vector store: {str(e)}")
            raise
    
    def _post_retrieval_permission_check(self, results: List[Dict[str, Any]], user_id: UUID) -> List[Dict[str, Any]]:
        """
        Perform a secondary permission check on search results
        
        This provides an additional security layer beyond the initial query filtering.
        It verifies that each result is accessible to the user based on:
        1. Document ownership
        2. Public access
        3. Explicit sharing permissions
        
        Args:
            results: List of search results
            user_id: User ID for permission checking
            
        Returns:
            Filtered list of results that the user has permission to access
        """
        # Check if developer mode is enabled
        from app.core.config import SETTINGS
        
        # If in developer mode, bypass permission checks
        if SETTINGS.developer_mode:
            logger.info("Developer mode: Bypassing post-retrieval permission check")
            return results
            
        if not results:
            return results
            
        user_id_str = str(user_id)
        filtered_results = []
        unauthorized_access_attempts = 0
        
        for result in results:
            metadata = result.get("metadata", {})
            document_id = metadata.get("document_id")
            
            # Check permissions
            has_permission = False
            
            # Case 1: User owns the document
            if metadata.get("user_id") == user_id_str:
                has_permission = True
                
            # Case 2: Document is public
            elif metadata.get("is_public") is True:
                has_permission = True
                
            # Case 3: Document is shared with the user
            elif "shared_with" in metadata:
                try:
                    # Parse the shared_with JSON string
                    shared_with = json.loads(metadata["shared_with"])
                    if user_id_str in shared_with:
                        has_permission = True
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Invalid shared_with format in document {document_id}")
            
            # Alternative check using shared_user_ids
            elif "shared_user_ids" in metadata:
                # Handle shared_user_ids which can be a comma-separated string
                try:
                    shared_user_ids = metadata["shared_user_ids"].split(",")
                    if user_id_str in shared_user_ids:
                        has_permission = True
                except (AttributeError, TypeError):
                    logger.warning(f"Invalid shared_user_ids format in document {document_id}")
            
            if has_permission:
                filtered_results.append(result)
            else:
                unauthorized_access_attempts += 1
                logger.warning(f"Blocked unauthorized access attempt to document {document_id} by user {user_id_str}")
        
        # Log summary of permission filtering
        if unauthorized_access_attempts > 0:
            logger.warning(f"Filtered out {unauthorized_access_attempts} results due to permission restrictions")
            
        logger.info(f"Post-retrieval permission check: {len(filtered_results)}/{len(results)} results passed")
        
        return filtered_results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache
        """
        if not self.enable_cache:
            return {"cache_enabled": False}
        
        # Get stats from the vector search cache
        cache_stats = self.vector_cache.get_stats()
        
        return {
            "cache_enabled": True,
            "cache_size": cache_stats["size"],
            "cache_max_size": cache_stats["max_size"],
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            "cache_hit_ratio": cache_stats["hit_ratio"],
            "cache_ttl_seconds": cache_stats["ttl_seconds"],
            "cache_persist": cache_stats["persist"]
        }
        
    def _post_filter_by_tags(self, results: List[Dict[str, Any]], tags: List[str]) -> List[Dict[str, Any]]:
        """
        Filter search results by tags after retrieval
        
        This is used when we can't use the $contains operator in ChromaDB
        
        Args:
            results: List of search results
            tags: List of tags to filter by
            
        Returns:
            Filtered list of results
        """
        if not results or not tags:
            return results
            
        filtered_results = []
        
        for result in results:
            metadata = result.get("metadata", {})
            doc_tags_str = metadata.get("tags", "")
            
            # Skip if no tags
            if not doc_tags_str:
                continue
                
            # Split tags string into list
            try:
                doc_tags = doc_tags_str.split(",")
                
                # Check if any of the requested tags are in the document's tags
                if any(tag in doc_tags for tag in tags):
                    filtered_results.append(result)
            except (AttributeError, TypeError):
                logger.warning(f"Invalid tags format in document {metadata.get('document_id', 'unknown')}")
                
        logger.info(f"Post-filtering by tags: {len(filtered_results)}/{len(results)} results passed")
        
        return filtered_results