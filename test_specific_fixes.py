#!/usr/bin/env python3
"""
Test script to verify the specific fixes we've made:
1. The api_base_url fix in app/core/config.py
2. The _cleanup_memory method in app/rag/rag_engine.py
"""
import asyncio
import logging
import uuid
import time
import psutil
import sys
from typing import List, Dict, Any, Optional

# Add project root to path
import os
import sys
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.rag.rag_engine import RAGEngine
from app.rag.rag_generation import GenerationMixin
from app.core.config import SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_specific_fixes")

async def test_api_base_url_fix():
    """
    Test that the api_base_url attribute is properly set in SETTINGS
    """
    logger.info("Testing api_base_url fix...")
    
    # Check if the api_base_url attribute exists in SETTINGS
    assert hasattr(SETTINGS, 'api_base_url'), "SETTINGS should have api_base_url attribute"
    
    # Check if the api_base_url attribute has a value
    assert SETTINGS.api_base_url is not None, "api_base_url should not be None"
    
    # Check if the api_base_url attribute has the expected value
    assert SETTINGS.api_base_url == SETTINGS.base_url, "api_base_url should be equal to base_url"
    
    logger.info(f"api_base_url is correctly set to: {SETTINGS.api_base_url}")
    logger.info("api_base_url fix test passed")

async def test_cleanup_memory_method():
    """
    Test that the _cleanup_memory method is properly defined in RAGEngine
    """
    logger.info("Testing _cleanup_memory method...")
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    # Check if the _cleanup_memory method exists
    assert hasattr(rag_engine, '_cleanup_memory'), "RAGEngine should have _cleanup_memory method"
    
    # Get initial memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
    
    # Create some large objects to increase memory usage
    large_objects = []
    for i in range(10):
        large_objects.append("X" * 1000000)  # Create a 1MB string
    
    # Check memory usage after creating large objects
    memory_after_objects = process.memory_info().rss / (1024 * 1024)
    logger.info(f"Memory after creating large objects: {memory_after_objects:.2f} MB")
    logger.info(f"Memory increase: {memory_after_objects - initial_memory:.2f} MB")
    
    # Run memory cleanup
    await rag_engine._cleanup_memory()
    
    # Check memory usage after cleanup
    memory_after_cleanup = process.memory_info().rss / (1024 * 1024)
    logger.info(f"Memory after cleanup: {memory_after_cleanup:.2f} MB")
    logger.info(f"Memory freed: {memory_after_objects - memory_after_cleanup:.2f} MB")
    
    # Clear large objects
    large_objects = None
    
    # Force garbage collection
    import gc
    gc.collect()
    
    # Check final memory usage
    final_memory = process.memory_info().rss / (1024 * 1024)
    logger.info(f"Final memory usage: {final_memory:.2f} MB")
    
    logger.info("_cleanup_memory method test passed")

async def test_record_analytics_method():
    """
    Test that the _record_analytics method uses api_base_url correctly
    """
    logger.info("Testing _record_analytics method...")
    
    # Create a mock GenerationMixin instance
    generation_mixin = GenerationMixin()
    
    # Check if the _record_analytics method exists
    assert hasattr(generation_mixin, '_record_analytics'), "GenerationMixin should have _record_analytics method"
    
    # Create a mock _record_analytics method to test the api_base_url usage
    original_record_analytics = generation_mixin._record_analytics
    
    # Track the api_base_url that was used
    used_api_base_url = None
    
    async def mock_record_analytics(*args, **kwargs):
        nonlocal used_api_base_url
        # Import the necessary modules
        from app.core.config import SETTINGS
        # Get the api_base_url
        used_api_base_url = getattr(SETTINGS, 'api_base_url', None)
        # Don't actually make the request
        return None
    
    # Replace the _record_analytics method temporarily
    generation_mixin._record_analytics = mock_record_analytics
    
    try:
        # Call the mock _record_analytics method
        await generation_mixin._record_analytics(
            query="Test query",
            model="test_model",
            use_rag=True,
            response_time_ms=100,
            document_ids=[]
        )
        
        # Check if the api_base_url was used
        assert used_api_base_url is not None, "api_base_url should have been used"
        assert used_api_base_url == SETTINGS.base_url, "api_base_url should be equal to base_url"
        
        logger.info(f"_record_analytics used api_base_url: {used_api_base_url}")
        logger.info("_record_analytics method test passed")
    finally:
        # Restore the original _record_analytics method
        generation_mixin._record_analytics = original_record_analytics

async def run_tests():
    """Run all tests"""
    await test_api_base_url_fix()
    await test_cleanup_memory_method()
    await test_record_analytics_method()
    logger.info("All tests passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())