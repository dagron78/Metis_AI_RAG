import os
import time
import unittest
import shutil
from typing import Dict, Any, List

from app.cache.base import Cache
from app.cache.vector_search_cache import VectorSearchCache
from app.cache.document_cache import DocumentCache
from app.cache.llm_response_cache import LLMResponseCache
from app.cache.cache_manager import CacheManager

class TestCache(unittest.TestCase):
    """Test the base Cache class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_cache_dir = "data/test_cache"
        os.makedirs(self.test_cache_dir, exist_ok=True)
        self.cache = Cache[str](
            name="test_cache",
            ttl=1,  # 1 second TTL for faster testing
            max_size=5,
            persist=True,
            persist_dir=self.test_cache_dir
        )
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
    
    def test_set_get(self):
        """Test setting and getting values"""
        # Set a value
        self.cache.set("key1", "value1")
        
        # Get the value
        value = self.cache.get("key1")
        self.assertEqual(value, "value1")
        
        # Get a non-existent key
        value = self.cache.get("non_existent")
        self.assertIsNone(value)
    
    def test_ttl_expiration(self):
        """Test TTL expiration"""
        # Set a value
        self.cache.set("key1", "value1")
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Get the value (should be None)
        value = self.cache.get("key1")
        self.assertIsNone(value)
    
    def test_max_size_pruning(self):
        """Test max size pruning"""
        # Set values up to max_size + 1
        for i in range(6):
            self.cache.set(f"key{i}", f"value{i}")
        
        # Check that the cache size is at most max_size
        self.assertLessEqual(len(self.cache.cache), self.cache.max_size)
        
        # Check that the oldest entries were removed
        self.assertIsNone(self.cache.get("key0"))
        self.assertIsNone(self.cache.get("key1"))
        
        # Check that the newest entries are still there
        self.assertEqual(self.cache.get("key5"), "value5")
    
    def test_clear(self):
        """Test clearing the cache"""
        # Set some values
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        # Clear the cache
        self.cache.clear()
        
        # Check that the cache is empty
        self.assertEqual(len(self.cache.cache), 0)
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))
    
    def test_delete(self):
        """Test deleting a value"""
        # Set some values
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        # Delete a value
        result = self.cache.delete("key1")
        self.assertTrue(result)
        
        # Check that the value is gone
        self.assertIsNone(self.cache.get("key1"))
        self.assertEqual(self.cache.get("key2"), "value2")
        
        # Try to delete a non-existent key
        result = self.cache.delete("non_existent")
        self.assertFalse(result)
    
    def test_get_stats(self):
        """Test getting cache statistics"""
        # Set some values
        self.cache.set("key1", "value1")
        
        # Get a value (hit)
        self.cache.get("key1")
        
        # Get a non-existent value (miss)
        self.cache.get("non_existent")
        
        # Get stats
        stats = self.cache.get_stats()
        
        # Check stats
        self.assertEqual(stats["name"], "test_cache")
        self.assertEqual(stats["size"], 1)
        self.assertEqual(stats["max_size"], 5)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_ratio"], 0.5)
        self.assertEqual(stats["ttl_seconds"], 1)
        self.assertTrue(stats["persist"])
    
    def test_persistence(self):
        """Test cache persistence"""
        # Set a value
        self.cache.set("key1", "value1")
        
        # Create a new cache instance (should load from disk)
        new_cache = Cache[str](
            name="test_cache",
            ttl=1,
            max_size=5,
            persist=True,
            persist_dir=self.test_cache_dir
        )
        
        # Check that the value was loaded
        self.assertEqual(new_cache.get("key1"), "value1")


class TestVectorSearchCache(unittest.TestCase):
    """Test the VectorSearchCache class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_cache_dir = "data/test_cache"
        os.makedirs(self.test_cache_dir, exist_ok=True)
        self.cache = VectorSearchCache(
            ttl=1,  # 1 second TTL for faster testing
            max_size=5,
            persist=True,
            persist_dir=self.test_cache_dir
        )
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
    
    def test_set_get_results(self):
        """Test setting and getting search results"""
        # Create test results
        results = [
            {
                "chunk_id": "chunk1",
                "content": "Test content 1",
                "metadata": {"document_id": "doc1"},
                "distance": 0.1
            },
            {
                "chunk_id": "chunk2",
                "content": "Test content 2",
                "metadata": {"document_id": "doc2"},
                "distance": 0.2
            }
        ]
        
        # Set results
        self.cache.set_results("test query", 2, results)
        
        # Get results
        cached_results = self.cache.get_results("test query", 2)
        self.assertEqual(cached_results, results)
        
        # Get results with different parameters
        cached_results = self.cache.get_results("test query", 3)
        self.assertIsNone(cached_results)
    
    def test_invalidate_by_document_id(self):
        """Test invalidating cache entries by document ID"""
        # Create test results
        results1 = [
            {
                "chunk_id": "chunk1",
                "content": "Test content 1",
                "metadata": {"document_id": "doc1"},
                "distance": 0.1
            },
            {
                "chunk_id": "chunk2",
                "content": "Test content 2",
                "metadata": {"document_id": "doc2"},
                "distance": 0.2
            }
        ]
        
        results2 = [
            {
                "chunk_id": "chunk3",
                "content": "Test content 3",
                "metadata": {"document_id": "doc1"},
                "distance": 0.3
            },
            {
                "chunk_id": "chunk4",
                "content": "Test content 4",
                "metadata": {"document_id": "doc3"},
                "distance": 0.4
            }
        ]
        
        # Set results
        self.cache.set_results("query1", 2, results1)
        self.cache.set_results("query2", 2, results2)
        
        # Invalidate by document ID
        count = self.cache.invalidate_by_document_id("doc1")
        self.assertEqual(count, 2)
        
        # Check that the entries were invalidated
        self.assertIsNone(self.cache.get_results("query1", 2))
        self.assertIsNone(self.cache.get_results("query2", 2))


class TestDocumentCache(unittest.TestCase):
    """Test the DocumentCache class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_cache_dir = "data/test_cache"
        os.makedirs(self.test_cache_dir, exist_ok=True)
        self.cache = DocumentCache(
            ttl=1,  # 1 second TTL for faster testing
            max_size=5,
            persist=True,
            persist_dir=self.test_cache_dir
        )
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
    
    def test_set_get_document(self):
        """Test setting and getting documents"""
        # Create test document
        document = {
            "id": "doc1",
            "content": "Test document content",
            "metadata": {
                "filename": "test.txt",
                "tags": ["test", "document"],
                "folder": "/test"
            }
        }
        
        # Set document
        self.cache.set_document("doc1", document)
        
        # Get document
        cached_document = self.cache.get_document("doc1")
        self.assertEqual(cached_document, document)
        
        # Get document content
        content = self.cache.get_document_content("doc1")
        self.assertEqual(content, "Test document content")
        
        # Get document metadata
        metadata = self.cache.get_document_metadata("doc1")
        self.assertEqual(metadata, document["metadata"])
    
    def test_invalidate_document(self):
        """Test invalidating a document"""
        # Create test document
        document = {
            "id": "doc1",
            "content": "Test document content",
            "metadata": {
                "filename": "test.txt",
                "tags": ["test", "document"],
                "folder": "/test"
            }
        }
        
        # Set document
        self.cache.set_document("doc1", document)
        
        # Invalidate document
        result = self.cache.invalidate_document("doc1")
        self.assertTrue(result)
        
        # Check that the document is gone
        self.assertIsNone(self.cache.get_document("doc1"))
    
    def test_get_documents_by_tag(self):
        """Test getting documents by tag"""
        # Create test documents
        document1 = {
            "id": "doc1",
            "content": "Test document 1",
            "metadata": {
                "filename": "test1.txt",
                "tags": ["test", "document"],
                "folder": "/test"
            }
        }
        
        document2 = {
            "id": "doc2",
            "content": "Test document 2",
            "metadata": {
                "filename": "test2.txt",
                "tags": ["test", "important"],
                "folder": "/test"
            }
        }
        
        # Set documents
        self.cache.set_document("doc1", document1)
        self.cache.set_document("doc2", document2)
        
        # Get documents by tag
        documents = self.cache.get_documents_by_tag("test")
        self.assertEqual(len(documents), 2)
        
        documents = self.cache.get_documents_by_tag("important")
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["id"], "doc2")
    
    def test_get_documents_by_folder(self):
        """Test getting documents by folder"""
        # Create test documents
        document1 = {
            "id": "doc1",
            "content": "Test document 1",
            "metadata": {
                "filename": "test1.txt",
                "tags": ["test"],
                "folder": "/test1"
            }
        }
        
        document2 = {
            "id": "doc2",
            "content": "Test document 2",
            "metadata": {
                "filename": "test2.txt",
                "tags": ["test"],
                "folder": "/test2"
            }
        }
        
        # Set documents
        self.cache.set_document("doc1", document1)
        self.cache.set_document("doc2", document2)
        
        # Get documents by folder
        documents = self.cache.get_documents_by_folder("/test1")
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["id"], "doc1")
        
        documents = self.cache.get_documents_by_folder("/test2")
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["id"], "doc2")


class TestLLMResponseCache(unittest.TestCase):
    """Test the LLMResponseCache class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_cache_dir = "data/test_cache"
        os.makedirs(self.test_cache_dir, exist_ok=True)
        self.cache = LLMResponseCache(
            ttl=1,  # 1 second TTL for faster testing
            max_size=5,
            persist=True,
            persist_dir=self.test_cache_dir
        )
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
    
    def test_set_get_response(self):
        """Test setting and getting LLM responses"""
        # Create test response
        response = {
            "response": "This is a test response",
            "model": "test-model",
            "prompt": "Test prompt",
            "tokens": 10,
            "finish_reason": "stop"
        }
        
        # Set response
        self.cache.set_response(
            prompt="Test prompt",
            model="test-model",
            response=response,
            temperature=0.0
        )
        
        # Get response
        cached_response = self.cache.get_response(
            prompt="Test prompt",
            model="test-model",
            temperature=0.0
        )
        self.assertEqual(cached_response, response)
        
        # Get response with different parameters
        cached_response = self.cache.get_response(
            prompt="Test prompt",
            model="test-model",
            temperature=0.5
        )
        self.assertIsNone(cached_response)
    
    def test_invalidate_by_model(self):
        """Test invalidating cache entries by model"""
        # Create test responses
        response1 = {
            "response": "Response 1",
            "model": "model1",
            "prompt": "Prompt 1"
        }
        
        response2 = {
            "response": "Response 2",
            "model": "model2",
            "prompt": "Prompt 2"
        }
        
        response3 = {
            "response": "Response 3",
            "model": "model1",
            "prompt": "Prompt 3"
        }
        
        # Set responses
        self.cache.set_response("Prompt 1", "model1", response1)
        self.cache.set_response("Prompt 2", "model2", response2)
        self.cache.set_response("Prompt 3", "model1", response3)
        
        # Invalidate by model
        count = self.cache.invalidate_by_model("model1")
        self.assertEqual(count, 2)
        
        # Check that the entries were invalidated
        self.assertIsNone(self.cache.get_response("Prompt 1", "model1"))
        self.assertIsNone(self.cache.get_response("Prompt 3", "model1"))
        self.assertIsNotNone(self.cache.get_response("Prompt 2", "model2"))
    
    def test_should_cache_response(self):
        """Test should_cache_response method"""
        # Test with high temperature (should not cache)
        result = self.cache.should_cache_response(
            prompt="Test prompt",
            model="test-model",
            temperature=0.7,
            response={"response": "Test response"}
        )
        self.assertFalse(result)
        
        # Test with low temperature (should cache)
        result = self.cache.should_cache_response(
            prompt="Test prompt",
            model="test-model",
            temperature=0.2,
            response={"response": "Test response"}
        )
        self.assertTrue(result)
        
        # Test with short response (should not cache)
        result = self.cache.should_cache_response(
            prompt="Test prompt",
            model="test-model",
            temperature=0.2,
            response={"response": "Short"}
        )
        self.assertFalse(result)
        
        # Test with error response (should not cache)
        result = self.cache.should_cache_response(
            prompt="Test prompt",
            model="test-model",
            temperature=0.2,
            response={"response": "Test response", "error": "Some error"}
        )
        self.assertFalse(result)


class TestCacheManager(unittest.TestCase):
    """Test the CacheManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_cache_dir = "data/test_cache"
        os.makedirs(self.test_cache_dir, exist_ok=True)
        self.cache_manager = CacheManager(
            cache_dir=self.test_cache_dir,
            enable_caching=True
        )
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
    
    def test_initialization(self):
        """Test cache manager initialization"""
        self.assertIsInstance(self.cache_manager.vector_search_cache, VectorSearchCache)
        self.assertIsInstance(self.cache_manager.document_cache, DocumentCache)
        self.assertIsInstance(self.cache_manager.llm_response_cache, LLMResponseCache)
    
    def test_clear_all_caches(self):
        """Test clearing all caches"""
        # Set some values in each cache
        self.cache_manager.vector_search_cache.set_results("query", 2, [{"chunk_id": "chunk1"}])
        self.cache_manager.document_cache.set_document("doc1", {"id": "doc1"})
        self.cache_manager.llm_response_cache.set_response("prompt", "model", {"response": "test"})
        
        # Clear all caches
        self.cache_manager.clear_all_caches()
        
        # Check that all caches are empty
        self.assertIsNone(self.cache_manager.vector_search_cache.get_results("query", 2))
        self.assertIsNone(self.cache_manager.document_cache.get_document("doc1"))
        self.assertIsNone(self.cache_manager.llm_response_cache.get_response("prompt", "model"))
    
    def test_get_all_cache_stats(self):
        """Test getting all cache stats"""
        # Get stats
        stats = self.cache_manager.get_all_cache_stats()
        
        # Check stats
        self.assertTrue(stats["caching_enabled"])
        self.assertIn("vector_search_cache", stats)
        self.assertIn("document_cache", stats)
        self.assertIn("llm_response_cache", stats)
    
    def test_invalidate_document(self):
        """Test invalidating a document in all caches"""
        # Set some values in each cache
        self.cache_manager.vector_search_cache.set_results(
            "query", 2, [{"chunk_id": "chunk1", "metadata": {"document_id": "doc1"}}]
        )
        self.cache_manager.document_cache.set_document("doc1", {"id": "doc1"})
        
        # Invalidate document
        self.cache_manager.invalidate_document("doc1")
        
        # Check that the document is invalidated in all caches
        self.assertIsNone(self.cache_manager.vector_search_cache.get_results("query", 2))
        self.assertIsNone(self.cache_manager.document_cache.get_document("doc1"))
    
    def test_disabled_caching(self):
        """Test with caching disabled"""
        # Create a cache manager with caching disabled
        disabled_manager = CacheManager(
            cache_dir=self.test_cache_dir,
            enable_caching=False
        )
        
        # Try to set and get values
        disabled_manager.vector_search_cache.set_results("query", 2, [{"chunk_id": "chunk1"}])
        result = disabled_manager.vector_search_cache.get_results("query", 2)
        
        # Check that caching is effectively disabled
        self.assertIsNone(result)
        
        # Check stats
        stats = disabled_manager.get_all_cache_stats()
        self.assertFalse(stats["caching_enabled"])


if __name__ == "__main__":
    unittest.main()