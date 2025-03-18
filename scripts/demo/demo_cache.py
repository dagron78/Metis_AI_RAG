#!/usr/bin/env python
"""
Demo script for the Metis_RAG caching system.

This script demonstrates the usage of the caching system by:
1. Creating cache instances
2. Setting and getting values
3. Measuring performance improvements
4. Showing cache statistics
"""

import os
import sys
import time
import json
import random
import shutil
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.cache import (
    Cache,
    VectorSearchCache,
    DocumentCache,
    LLMResponseCache,
    CacheManager
)

def clear_test_cache_dir():
    """Clear the test cache directory"""
    test_cache_dir = "data/demo_cache"
    if os.path.exists(test_cache_dir):
        shutil.rmtree(test_cache_dir)
    os.makedirs(test_cache_dir, exist_ok=True)
    return test_cache_dir

def demo_basic_cache():
    """Demonstrate basic cache usage"""
    print("\n=== Basic Cache Demo ===")
    
    # Create a cache instance
    cache_dir = clear_test_cache_dir()
    cache = Cache[str](
        name="demo_cache",
        ttl=60,  # 60 seconds TTL
        max_size=100,
        persist=True,
        persist_dir=cache_dir
    )
    
    # Set some values
    print("Setting values...")
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    # Get values
    print(f"key1: {cache.get('key1')}")
    print(f"key2: {cache.get('key2')}")
    print(f"key3: {cache.get('key3')}")
    print(f"non-existent key: {cache.get('non_existent')}")
    
    # Delete a value
    print("\nDeleting key2...")
    cache.delete("key2")
    print(f"key2 after deletion: {cache.get('key2')}")
    
    # Get cache statistics
    print("\nCache statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Clear the cache
    print("\nClearing cache...")
    cache.clear()
    print(f"key1 after clearing: {cache.get('key1')}")
    print(f"key3 after clearing: {cache.get('key3')}")

def demo_vector_search_cache():
    """Demonstrate vector search cache usage"""
    print("\n=== Vector Search Cache Demo ===")
    
    # Create a vector search cache
    cache_dir = clear_test_cache_dir()
    vector_cache = VectorSearchCache(
        ttl=60,
        max_size=100,
        persist=True,
        persist_dir=cache_dir
    )
    
    # Create some test results
    results = [
        {
            "chunk_id": f"chunk{i}",
            "content": f"Test content {i}",
            "metadata": {"document_id": f"doc{i % 3}"},
            "distance": i / 10
        }
        for i in range(1, 6)
    ]
    
    # Set results
    print("Setting search results...")
    vector_cache.set_results("test query", 5, results)
    
    # Get results
    print("\nGetting search results...")
    cached_results = vector_cache.get_results("test query", 5)
    print(f"Found {len(cached_results)} results")
    for i, result in enumerate(cached_results):
        print(f"  Result {i+1}: {result['chunk_id']} (distance: {result['distance']})")
    
    # Invalidate by document ID
    print("\nInvalidating results for doc1...")
    count = vector_cache.invalidate_by_document_id("doc1")
    print(f"Invalidated {count} results")
    
    # Try to get results again
    print("\nGetting search results after invalidation...")
    cached_results = vector_cache.get_results("test query", 5)
    if cached_results is None:
        print("  No results found (cache invalidated)")
    else:
        print(f"  Found {len(cached_results)} results")

def demo_document_cache():
    """Demonstrate document cache usage"""
    print("\n=== Document Cache Demo ===")
    
    # Create a document cache
    cache_dir = clear_test_cache_dir()
    document_cache = DocumentCache(
        ttl=60,
        max_size=100,
        persist=True,
        persist_dir=cache_dir
    )
    
    # Create a test document
    document = {
        "id": "doc1",
        "content": "This is a test document content.",
        "metadata": {
            "filename": "test.txt",
            "tags": ["test", "document", "example"],
            "folder": "/test"
        }
    }
    
    # Set document
    print("Setting document...")
    document_cache.set_document("doc1", document)
    
    # Get document
    print("\nGetting document...")
    cached_document = document_cache.get_document("doc1")
    if cached_document:
        print(f"  Document ID: {cached_document['id']}")
        print(f"  Content: {cached_document['content']}")
        print(f"  Metadata: {cached_document['metadata']}")
    
    # Get document content
    print("\nGetting document content...")
    content = document_cache.get_document_content("doc1")
    print(f"  Content: {content}")
    
    # Get document metadata
    print("\nGetting document metadata...")
    metadata = document_cache.get_document_metadata("doc1")
    print(f"  Metadata: {metadata}")
    
    # Invalidate document
    print("\nInvalidating document...")
    document_cache.invalidate_document("doc1")
    
    # Try to get document again
    print("\nGetting document after invalidation...")
    cached_document = document_cache.get_document("doc1")
    if cached_document is None:
        print("  Document not found (cache invalidated)")
    else:
        print(f"  Document found: {cached_document}")

def demo_llm_response_cache():
    """Demonstrate LLM response cache usage"""
    print("\n=== LLM Response Cache Demo ===")
    
    # Create an LLM response cache
    cache_dir = clear_test_cache_dir()
    llm_cache = LLMResponseCache(
        ttl=60,
        max_size=100,
        persist=True,
        persist_dir=cache_dir
    )
    
    # Create a test response
    response = {
        "response": "This is a test response from the LLM.",
        "model": "test-model",
        "prompt": "What is RAG?",
        "tokens": 15,
        "finish_reason": "stop"
    }
    
    # Set response
    print("Setting LLM response...")
    llm_cache.set_response(
        prompt="What is RAG?",
        model="test-model",
        response=response,
        temperature=0.0
    )
    
    # Get response
    print("\nGetting LLM response...")
    cached_response = llm_cache.get_response(
        prompt="What is RAG?",
        model="test-model",
        temperature=0.0
    )
    if cached_response:
        print(f"  Response: {cached_response['response']}")
        print(f"  Model: {cached_response['model']}")
        print(f"  Tokens: {cached_response.get('tokens')}")
    
    # Try with different temperature
    print("\nGetting LLM response with different temperature...")
    cached_response = llm_cache.get_response(
        prompt="What is RAG?",
        model="test-model",
        temperature=0.5
    )
    if cached_response is None:
        print("  Response not found (different parameters)")
    else:
        print(f"  Response found: {cached_response}")
    
    # Check if response should be cached
    print("\nChecking if response should be cached...")
    should_cache = llm_cache.should_cache_response(
        prompt="What is RAG?",
        model="test-model",
        temperature=0.2,
        response=response
    )
    print(f"  Should cache: {should_cache}")
    
    should_cache = llm_cache.should_cache_response(
        prompt="What is RAG?",
        model="test-model",
        temperature=0.7,  # High temperature
        response=response
    )
    print(f"  Should cache (high temperature): {should_cache}")

def demo_cache_manager():
    """Demonstrate cache manager usage"""
    print("\n=== Cache Manager Demo ===")
    
    # Create a cache manager
    cache_dir = clear_test_cache_dir()
    cache_manager = CacheManager(
        cache_dir=cache_dir,
        enable_caching=True
    )
    
    # Set some values in each cache
    print("Setting values in caches...")
    cache_manager.vector_search_cache.set_results(
        "test query", 
        5, 
        [{"chunk_id": "chunk1", "metadata": {"document_id": "doc1"}}]
    )
    
    cache_manager.document_cache.set_document(
        "doc1", 
        {"id": "doc1", "content": "Test content"}
    )
    
    cache_manager.llm_response_cache.set_response(
        "What is RAG?",
        "test-model",
        {"response": "RAG stands for Retrieval-Augmented Generation"}
    )
    
    # Get cache statistics
    print("\nGetting cache statistics...")
    stats = cache_manager.get_all_cache_stats()
    print(json.dumps(stats, indent=2))
    
    # Invalidate a document
    print("\nInvalidating document doc1...")
    cache_manager.invalidate_document("doc1")
    
    # Check that the document is invalidated in all caches
    print("\nChecking caches after invalidation...")
    vector_results = cache_manager.vector_search_cache.get_results("test query", 5)
    document = cache_manager.document_cache.get_document("doc1")
    
    print(f"  Vector results: {vector_results}")
    print(f"  Document: {document}")
    
    # Clear all caches
    print("\nClearing all caches...")
    cache_manager.clear_all_caches()
    
    # Create a cache manager with caching disabled
    print("\nCreating cache manager with caching disabled...")
    disabled_manager = CacheManager(
        cache_dir=cache_dir,
        enable_caching=False
    )
    
    # Try to set and get values
    print("Setting and getting values with caching disabled...")
    disabled_manager.vector_search_cache.set_results(
        "test query", 
        5, 
        [{"chunk_id": "chunk1"}]
    )
    
    result = disabled_manager.vector_search_cache.get_results("test query", 5)
    print(f"  Result: {result}")
    
    # Get statistics
    print("\nGetting statistics with caching disabled...")
    stats = disabled_manager.get_all_cache_stats()
    print(json.dumps(stats, indent=2))

def demo_performance():
    """Demonstrate performance improvements with caching"""
    print("\n=== Performance Demo ===")
    
    # Create a cache
    cache_dir = clear_test_cache_dir()
    cache = Cache[str](
        name="perf_cache",
        ttl=60,
        max_size=1000,
        persist=True,
        persist_dir=cache_dir
    )
    
    # Function to simulate an expensive operation
    def expensive_operation(key):
        """Simulate an expensive operation"""
        time.sleep(0.1)  # Simulate 100ms of work
        return f"Result for {key}"
    
    # Function to get a value with caching
    def get_with_cache(key):
        """Get a value with caching"""
        # Check cache first
        result = cache.get(key)
        if result is not None:
            return result
        
        # Cache miss, perform expensive operation
        result = expensive_operation(key)
        cache.set(key, result)
        return result
    
    # Measure performance without caching
    print("Measuring performance without caching...")
    keys = [f"key{i}" for i in range(10)]
    
    start_time = time.time()
    for key in keys:
        expensive_operation(key)
    uncached_time = time.time() - start_time
    
    print(f"  Time without caching: {uncached_time:.3f} seconds")
    
    # Measure performance with caching (first run - cache misses)
    print("\nMeasuring performance with caching (first run)...")
    start_time = time.time()
    for key in keys:
        get_with_cache(key)
    first_cached_time = time.time() - start_time
    
    print(f"  Time with caching (first run): {first_cached_time:.3f} seconds")
    
    # Measure performance with caching (second run - cache hits)
    print("\nMeasuring performance with caching (second run)...")
    start_time = time.time()
    for key in keys:
        get_with_cache(key)
    second_cached_time = time.time() - start_time
    
    print(f"  Time with caching (second run): {second_cached_time:.3f} seconds")
    
    # Calculate speedup
    speedup = uncached_time / second_cached_time
    print(f"\nSpeedup with caching: {speedup:.1f}x")
    
    # Get cache statistics
    stats = cache.get_stats()
    print(f"\nCache statistics after performance test:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit ratio: {stats['hit_ratio']:.2f}")

if __name__ == "__main__":
    print("=== Metis_RAG Caching System Demo ===")
    
    # Run demos
    demo_basic_cache()
    demo_vector_search_cache()
    demo_document_cache()
    demo_llm_response_cache()
    demo_cache_manager()
    demo_performance()
    
    print("\nDemo completed successfully!")