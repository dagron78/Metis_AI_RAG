"""
Fixtures for cache unit tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import redis
import json
from datetime import datetime, timedelta

from app.cache.redis_cache import RedisCache
from app.cache.memory_cache import MemoryCache
from app.cache.vector_cache import VectorSearchCache

@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    mock = MagicMock(spec=redis.Redis)
    
    # Mock get method
    mock.get.return_value = json.dumps({"key": "value"}).encode()
    
    # Mock set method
    mock.set.return_value = True
    
    # Mock delete method
    mock.delete.return_value = 1
    
    # Mock exists method
    mock.exists.return_value = 1
    
    # Mock expire method
    mock.expire.return_value = True
    
    # Mock ttl method
    mock.ttl.return_value = 3600
    
    # Mock keys method
    mock.keys.return_value = [b"key1", b"key2", b"key3"]
    
    # Mock pipeline method
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [True, True, True]
    mock.pipeline.return_value = mock_pipeline
    
    return mock

@pytest.fixture
def mock_redis_cache(mock_redis_client):
    """Mock Redis cache"""
    cache = RedisCache(ttl=3600)
    cache.client = mock_redis_client
    return cache

@pytest.fixture
def mock_memory_cache():
    """Mock memory cache"""
    cache = MemoryCache(ttl=3600, max_size=1000)
    
    # Pre-populate with some test data
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    return cache

@pytest.fixture
def mock_vector_search_cache():
    """Mock vector search cache"""
    mock = MagicMock(spec=VectorSearchCache)
    
    # Mock get_results method
    mock.get_results.return_value = [
        {
            "chunk_id": "chunk1",
            "content": "This is a test chunk",
            "metadata": {"document_id": "doc1"},
            "distance": 0.1
        },
        {
            "chunk_id": "chunk2",
            "content": "This is another test chunk",
            "metadata": {"document_id": "doc1"},
            "distance": 0.2
        }
    ]
    
    # Mock set_results method
    mock.set_results.return_value = None
    
    # Mock clear method
    mock.clear.return_value = None
    
    # Mock get_cache_key method
    mock.get_cache_key.return_value = "query:top_k:filter"
    
    return mock

@pytest.fixture
def sample_cache_data():
    """Sample data for cache testing"""
    return {
        "string_value": "test_value",
        "int_value": 42,
        "float_value": 3.14,
        "bool_value": True,
        "list_value": [1, 2, 3, 4, 5],
        "dict_value": {"key1": "value1", "key2": "value2"},
        "complex_value": {
            "name": "Test",
            "values": [1, 2, 3],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
            }
        }
    }

@pytest.fixture
def sample_vector_results():
    """Sample vector search results for cache testing"""
    return [
        {
            "chunk_id": "chunk1",
            "content": "This is a test chunk",
            "metadata": {"document_id": "doc1"},
            "distance": 0.1
        },
        {
            "chunk_id": "chunk2",
            "content": "This is another test chunk",
            "metadata": {"document_id": "doc1"},
            "distance": 0.2
        },
        {
            "chunk_id": "chunk3",
            "content": "This is a third test chunk",
            "metadata": {"document_id": "doc2"},
            "distance": 0.3
        }
    ]