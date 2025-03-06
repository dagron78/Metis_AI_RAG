import logging
import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings

from app.core.config import CHROMA_DB_DIR, DEFAULT_EMBEDDING_MODEL
from app.models.document import Document, Chunk
from app.rag.ollama_client import OllamaClient

logger = logging.getLogger("app.rag.vector_store")

class VectorStore:
    """
    Vector store for document embeddings using ChromaDB with caching for performance
    """
    def __init__(
        self,
        persist_directory: str = CHROMA_DB_DIR,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        enable_cache: bool = True,
        cache_ttl: int = 3600  # 1 hour in seconds
    ):
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.ollama_client = None
        
        # Cache settings
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.max_cache_size = 1000
        
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
                    
                self.collection.add(
                    ids=[chunk.id],
                    embeddings=[chunk.embedding],
                    documents=[chunk.content],
                    metadatas=[{
                        "document_id": document.id,
                        "chunk_index": chunk.metadata.get("index", 0),
                        "filename": document.filename,
                        "tags": document.tags,
                        "folder": document.folder,
                        **chunk.metadata
                    }]
                )
            
            logger.info(f"Added {len(document.chunks)} chunks to vector store for document {document.id}")
        except Exception as e:
            logger.error(f"Error adding document {document.id} to vector store: {str(e)}")
            raise
    
    async def _batch_create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts (batched)"""
        try:
            # Attempt to use Langchain's embed_documents for batch embedding
            from langchain.embeddings import OllamaEmbeddings
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
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query with caching for performance
        """
        try:
            # Check cache if enabled
            if self.enable_cache:
                cache_key = self._create_cache_key(query, top_k, filter_criteria)
                cached_result = self._get_from_cache(cache_key)
                
                if cached_result:
                    self.cache_hits += 1
                    logger.info(f"Cache hit for query: {query[:50]}... (hits: {self.cache_hits}, misses: {self.cache_misses})")
                    return cached_result
                
                self.cache_misses += 1
                logger.info(f"Cache miss for query: {query[:50]}... (hits: {self.cache_hits}, misses: {self.cache_misses})")
            
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
            if filter_criteria:
                logger.info(f"Applying filter criteria: {filter_criteria}")
            
            # Search for similar documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_criteria
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
                    logger.debug(f"  Content preview: {content[:100]}...")
                    
                    formatted_results.append({
                        "chunk_id": chunk_id,
                        "content": content,
                        "metadata": metadata,
                        "distance": distance
                    })
            else:
                logger.warning(f"No results found for query: {query[:50]}...")
            
            logger.info(f"Found {len(formatted_results)} similar documents")
            
            # Log document IDs for easier tracking
            if formatted_results:
                doc_ids = set(result["metadata"]["document_id"] for result in formatted_results)
                logger.info(f"Documents retrieved: {doc_ids}")
            
            # Cache results if enabled
            if self.enable_cache:
                self._add_to_cache(cache_key, formatted_results)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching for documents: {str(e)}")
            raise
    
    def _create_cache_key(self, query: str, top_k: int, filter_criteria: Optional[Dict[str, Any]]) -> str:
        """Create a cache key from the search parameters"""
        # Normalize the query by removing extra whitespace and lowercasing
        normalized_query = " ".join(query.lower().split())
        
        # Convert filter criteria to a stable string representation
        filter_str = json.dumps(filter_criteria or {}, sort_keys=True)
        
        # Combine parameters into a cache key
        return f"{normalized_query}:{top_k}:{filter_str}"
    
    def _get_from_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Get results from cache if they exist and are not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["results"]
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def _add_to_cache(self, key: str, results: List[Dict[str, Any]]) -> None:
        """Add results to cache"""
        self.cache[key] = {
            "results": results,
            "timestamp": time.time()
        }
        
        # Prune cache if it gets too large
        if len(self.cache) > self.max_cache_size:
            self._prune_cache()
    
    def _prune_cache(self) -> None:
        """Remove oldest entries from cache"""
        # Sort by timestamp and keep the newest entries
        sorted_cache = sorted(
            self.cache.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True
        )
        
        # Keep only half of the max cache size
        keep_count = self.max_cache_size // 2
        self.cache = dict(sorted_cache[:keep_count])
        logger.info(f"Pruned cache to {keep_count} entries")
    
    async def search_by_tags(
        self,
        query: str,
        tags: List[str],
        top_k: int = 5,
        additional_filters: Optional[Dict[str, Any]] = None
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
                # ChromaDB doesn't support direct array contains, so we use $in operator
                # This will match if any of the document tags are in the provided tags list
                filter_criteria["tags"] = {"$in": tags}
            
            # Perform search with filters
            return await self.search(query, top_k, filter_criteria)
        except Exception as e:
            logger.error(f"Error searching for documents by tags: {str(e)}")
            raise
    
    async def search_by_folder(
        self,
        query: str,
        folder: str,
        top_k: int = 5,
        additional_filters: Optional[Dict[str, Any]] = None
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
            return await self.search(query, top_k, filter_criteria)
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
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache
        """
        if not self.enable_cache:
            return {"cache_enabled": False}
        
        total_requests = self.cache_hits + self.cache_misses
        hit_ratio = self.cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_enabled": True,
            "cache_size": len(self.cache),
            "cache_max_size": self.max_cache_size,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": hit_ratio,
            "cache_ttl_seconds": self.cache_ttl
        }