# Metis_RAG Cache System

This module provides a comprehensive caching system for the Metis_RAG application, designed to improve performance by reducing redundant operations and speeding up response times.

## Overview

The caching system consists of the following components:

1. **Base Cache**: A generic cache implementation with disk persistence, TTL-based expiration, and size-based pruning.
2. **VectorSearchCache**: Specialized cache for vector search results.
3. **DocumentCache**: Specialized cache for document content and metadata.
4. **LLMResponseCache**: Specialized cache for LLM responses.
5. **CacheManager**: Central manager for all cache instances.

## Usage

### Basic Cache Usage

```python
from app.cache import Cache

# Create a cache instance
cache = Cache[str](
    name="my_cache",
    ttl=3600,  # 1 hour TTL
    max_size=1000,
    persist=True,
    persist_dir="data/cache"
)

# Set a value
cache.set("key", "value")

# Get a value
value = cache.get("key")

# Delete a value
cache.delete("key")

# Clear the cache
cache.clear()

# Get cache statistics
stats = cache.get_stats()
```

### Vector Search Cache

```python
from app.cache import VectorSearchCache

# Create a vector search cache
vector_cache = VectorSearchCache(
    ttl=3600,
    max_size=1000,
    persist=True,
    persist_dir="data/cache"
)

# Cache search results
vector_cache.set_results(
    query="What is RAG?",
    top_k=5,
    results=[...],  # List of search results
    filter_criteria={"tags": "AI"}
)

# Get cached search results
results = vector_cache.get_results(
    query="What is RAG?",
    top_k=5,
    filter_criteria={"tags": "AI"}
)

# Invalidate cache entries for a document
vector_cache.invalidate_by_document_id("doc123")
```

### Document Cache

```python
from app.cache import DocumentCache

# Create a document cache
document_cache = DocumentCache(
    ttl=7200,  # 2 hours TTL
    max_size=500,
    persist=True,
    persist_dir="data/cache"
)

# Cache a document
document_cache.set_document(
    document_id="doc123",
    document={
        "id": "doc123",
        "content": "Document content...",
        "metadata": {
            "filename": "example.txt",
            "tags": ["example", "document"],
            "folder": "/examples"
        }
    }
)

# Get a cached document
document = document_cache.get_document("doc123")

# Get document content
content = document_cache.get_document_content("doc123")

# Get document metadata
metadata = document_cache.get_document_metadata("doc123")

# Invalidate a document
document_cache.invalidate_document("doc123")

# Get documents by tag
documents = document_cache.get_documents_by_tag("example")

# Get documents by folder
documents = document_cache.get_documents_by_folder("/examples")
```

### LLM Response Cache

```python
from app.cache import LLMResponseCache

# Create an LLM response cache
llm_cache = LLMResponseCache(
    ttl=86400,  # 24 hours TTL
    max_size=2000,
    persist=True,
    persist_dir="data/cache"
)

# Cache an LLM response
llm_cache.set_response(
    prompt="What is RAG?",
    model="gpt-4",
    response={
        "response": "RAG stands for Retrieval-Augmented Generation...",
        "model": "gpt-4",
        "tokens": 150,
        "finish_reason": "stop"
    },
    temperature=0.0
)

# Get a cached LLM response
response = llm_cache.get_response(
    prompt="What is RAG?",
    model="gpt-4",
    temperature=0.0
)

# Invalidate responses for a model
llm_cache.invalidate_by_model("gpt-4")

# Check if a response should be cached
should_cache = llm_cache.should_cache_response(
    prompt="What is RAG?",
    model="gpt-4",
    temperature=0.2,
    response={...}
)
```

### Cache Manager

```python
from app.cache import CacheManager

# Create a cache manager
cache_manager = CacheManager(
    cache_dir="data/cache",
    config_file="config/cache_config.json",
    enable_caching=True
)

# Access individual caches
vector_cache = cache_manager.vector_search_cache
document_cache = cache_manager.document_cache
llm_cache = cache_manager.llm_response_cache

# Clear all caches
cache_manager.clear_all_caches()

# Get statistics for all caches
stats = cache_manager.get_all_cache_stats()

# Update cache configuration
cache_manager.update_cache_config({
    "vector_search_cache": {
        "ttl": 7200
    }
})

# Save configuration to file
cache_manager.save_config("config/cache_config.json")

# Invalidate a document in all caches
cache_manager.invalidate_document("doc123")
```

## Configuration

The cache system can be configured through a JSON configuration file with the following structure:

```json
{
  "vector_search_cache": {
    "ttl": 3600,
    "max_size": 1000,
    "persist": true
  },
  "document_cache": {
    "ttl": 7200,
    "max_size": 500,
    "persist": true
  },
  "llm_response_cache": {
    "ttl": 86400,
    "max_size": 2000,
    "persist": true
  }
}
```

## Cache Persistence

By default, all caches are persisted to disk in the specified `persist_dir`. This allows the cache to survive application restarts. The persistence format is:

- `{persist_dir}/{cache_name}/cache.pickle`: The serialized cache data
- `{persist_dir}/{cache_name}/stats.json`: Cache statistics in JSON format for easier inspection

## Cache Invalidation

The cache system provides several ways to invalidate cache entries:

1. **TTL-based expiration**: Entries automatically expire after the specified TTL.
2. **Size-based pruning**: When the cache exceeds its maximum size, the oldest entries are removed.
3. **Manual invalidation**: Entries can be manually invalidated using the `delete`, `clear`, and specialized invalidation methods.

## Performance Considerations

- **TTL**: Choose appropriate TTL values based on how frequently the underlying data changes.
- **Max Size**: Set the maximum cache size based on memory constraints and usage patterns.
- **Persistence**: Disable persistence for temporary caches or when disk I/O is a concern.
- **Key Generation**: The cache implementations use optimized key generation to minimize collisions.

## Testing

The cache system includes comprehensive unit tests in `tests/unit/test_cache.py`. Run the tests with:

```bash
python -m unittest tests/unit/test_cache.py