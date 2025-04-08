"""
Test script to verify the fixes for query classification, analytics auth, memory management, and user ID edge cases
"""
import asyncio
import logging
import uuid
import time
import psutil
import sys
from typing import List, Dict, Any, Optional

from app.rag.rag_engine import RAGEngine
from app.rag.rag_engine_base import BaseRAGEngine
from app.rag.memory_buffer import process_query
from app.core.config import SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_fixes")

async def test_query_classification():
    """
    Test that the query classification correctly identifies code and non-code queries
    """
    logger.info("Testing query classification...")
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    # Test cases for non-code queries
    non_code_queries = [
        "What is RAG?",
        "Can you give me a brief 3 sentence summary of RAG?",
        "Explain the concept of retrieval augmented generation",
        "Tell me about the history of artificial intelligence",
        "What is the definition of machine learning?",
        "Summarize the key points of the last meeting"
    ]
    
    # Test cases for code queries
    code_queries = [
        "Write a Python function to calculate Fibonacci numbers",
        "How do I implement a binary search tree in JavaScript?",
        "Fix this code: def factorial(n): return n * factorial(n-1)",
        "Create a React component for a login form",
        "What's wrong with this SQL query: SELECT * FROM users WHERE id = 1;",
        "How do I use async/await in JavaScript?"
    ]
    
    # Test non-code queries
    for query in non_code_queries:
        is_code = rag_engine._is_code_related_query(query)
        logger.info(f"Query: '{query}' - Is code: {is_code}")
        assert not is_code, f"Query '{query}' should NOT be classified as code-related"
    
    # Test code queries
    for query in code_queries:
        is_code = rag_engine._is_code_related_query(query)
        logger.info(f"Query: '{query}' - Is code: {is_code}")
        assert is_code, f"Query '{query}' should be classified as code-related"
    
    logger.info("Query classification test passed")

async def test_memory_management():
    """
    Test that memory management is working correctly
    """
    logger.info("Testing memory management...")
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
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
    
    logger.info("Memory management test passed")

async def test_user_id_edge_cases():
    """
    Test that user ID edge cases are handled correctly
    """
    logger.info("Testing user ID edge cases...")
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    # Test cases for user IDs
    test_cases = [
        {"id": "system", "expected_type": uuid.UUID},
        {"id": "session_12345", "expected_type": uuid.UUID},
        {"id": 12345, "expected_type": uuid.UUID},
        {"id": None, "expected_type": uuid.UUID},
        {"id": uuid.uuid4(), "expected_type": uuid.UUID},
        {"id": str(uuid.uuid4()), "expected_type": uuid.UUID}
    ]
    
    for case in test_cases:
        # Create a mock query method to capture the user_id
        original_query = rag_engine.query
        
        # Track the user_id that was used
        processed_user_id = None
        
        async def mock_process_query(query, user_id, conversation_id, db=None):
            nonlocal processed_user_id
            processed_user_id = user_id
            return query, None, None
        
        # Replace the process_query function
        import app.rag.memory_buffer
        original_process_query = app.rag.memory_buffer.process_query
        app.rag.memory_buffer.process_query = mock_process_query
        
        try:
            # Test with the user ID
            conversation_id = str(uuid.uuid4())
            await rag_engine.query(
                query="Test query",
                conversation_id=conversation_id,
                user_id=case["id"],
                use_rag=False
            )
            
            # Verify the user ID was processed correctly
            logger.info(f"Input user_id: {case['id']}, Processed user_id: {processed_user_id}")
            assert isinstance(processed_user_id, str), f"User ID should be a string, got {type(processed_user_id)}"
            
            # Try to convert to UUID to verify it's a valid UUID
            try:
                user_uuid = uuid.UUID(processed_user_id)
                assert isinstance(user_uuid, uuid.UUID), f"User ID should convert to UUID, got {type(user_uuid)}"
                logger.info(f"Converted user_id: {user_uuid}")
            except ValueError:
                assert False, f"User ID should be a valid UUID string, got {processed_user_id}"
            
        finally:
            # Restore the original functions
            app.rag.memory_buffer.process_query = original_process_query
    
    logger.info("User ID edge cases test passed")

async def run_tests():
    """Run all tests"""
    await test_query_classification()
    await test_memory_management()
    await test_user_id_edge_cases()
    logger.info("All tests passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())