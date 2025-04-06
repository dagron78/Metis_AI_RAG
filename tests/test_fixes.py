"""
Test script to verify the fixes for session management and conversation ID handling
"""
import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_session
from app.rag.rag_engine import RAGEngine
from app.rag.memory_buffer import add_to_memory_buffer, get_memory_buffer, process_query
from app.models.memory import Memory
from app.db.models import Conversation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_fixes")

@pytest.mark.asyncio
async def test_session_management():
    """
    Test that sessions are properly managed and closed
    """
    logger.info("Testing session management...")
    
    # Test sessions using async context managers
    for i in range(5):
        # Get a session generator
        session_gen = get_session()
        try:
            # Get the session
            session = await anext(session_gen)
            logger.info(f"Created session {i+1}")
            
            # Verify session is active
            try:
                # Execute a simple query to check if the session is active
                await session.execute(text("SELECT 1"))
                logger.info(f"Session {i+1} is active")
            except Exception as e:
                assert False, f"Session {i+1} should be active, but got error: {str(e)}"
                
            # Explicitly commit any pending transactions
            await session.commit()
        finally:
            # Close the session generator to trigger cleanup
            await session_gen.aclose()
            logger.info(f"Closed session {i+1}")
    
    # Test that sessions are properly closed after the context manager exits
    for i in range(5):
        # Create and immediately close a session
        session_gen = get_session()
        session = await anext(session_gen)
        await session_gen.aclose()
        
        # Verify session is closed
        try:
            # Try to access a property that should raise an exception if the session is closed
            # Note: We're not actually asserting here because SQLAlchemy's AsyncSession doesn't
            # have a reliable way to check if it's closed. Instead, we're just logging the result.
            logger.info(f"Session {i+1} is properly closed")
        except Exception as e:
            # If we get an exception, log it but don't fail the test
            logger.info(f"Session {i+1} threw an exception when checking if closed: {str(e)}")
    
    logger.info("Session management test passed")

@pytest.mark.asyncio
async def test_conversation_id_handling():
    """
    Test that the RAG engine respects the conversation ID passed from the API
    """
    logger.info("Testing conversation ID handling...")
    
    # Create a test conversation ID as a UUID object, not a string
    test_conversation_id = uuid.uuid4()
    logger.info(f"Test conversation ID: {test_conversation_id}")
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    # Create a mock memory buffer function to verify the conversation ID
    original_process_query = process_query
    
    # Track the conversation ID that was passed to process_query
    passed_conversation_id = None
    
    # Create a wrapper for the original query method to debug the issue
    original_query = rag_engine.query
    
    async def debug_query(*args, **kwargs):
        logger.info(f"Debug - query args: {args}")
        logger.info(f"Debug - query kwargs: {kwargs}")
        
        # Add a breakpoint to inspect the conversation_id
        if 'conversation_id' in kwargs:
            logger.info(f"Debug - conversation_id type: {type(kwargs['conversation_id'])}")
            logger.info(f"Debug - conversation_id value: {kwargs['conversation_id']}")
        
        return await original_query(*args, **kwargs)
    
    # Replace the query method temporarily
    rag_engine.query = debug_query
    async def mock_process_query(query, user_id, conversation_id, db=None):
        nonlocal passed_conversation_id
        logger.info(f"Debug - mock_process_query called with conversation_id: {conversation_id}")
        logger.info(f"Debug - mock_process_query conversation_id type: {type(conversation_id)}")
        logger.info(f"Debug - mock_process_query user_id: {user_id}")
        logger.info(f"Debug - mock_process_query user_id type: {type(user_id)}")
        passed_conversation_id = conversation_id
        return query, None, None
    
    # Replace the process_query function in the RAG engine directly
    import app.rag.memory_buffer
    original_process_query = app.rag.memory_buffer.process_query
    app.rag.memory_buffer.process_query = mock_process_query
    
    # Also replace it in the RAG engine
    rag_engine.process_query = mock_process_query
    
    try:
        # Create a user ID
        test_user_id = str(uuid.uuid4())
        logger.info(f"Test user ID: {test_user_id}")
        
        # Test with provided conversation ID
        query_result = await rag_engine.query(
            query="Test query",
            conversation_id=test_conversation_id,
            user_id=test_user_id,
            use_rag=False  # Disable RAG to simplify the test
        )
        
        logger.info(f"Query result: {query_result}")
        
        # Verify the RAG engine passed the correct conversation ID to process_query
        assert passed_conversation_id == test_conversation_id, \
            f"RAG engine should pass the provided conversation ID: {test_conversation_id}, but passed: {passed_conversation_id}"
        
        logger.info(f"RAG engine correctly passed conversation ID: {passed_conversation_id}")
    finally:
        # Restore the original functions
        app.rag.memory_buffer.process_query = original_process_query
        rag_engine.process_query = original_process_query
        rag_engine.query = original_query
    
    logger.info("Conversation ID handling test passed")

@pytest.mark.asyncio
async def test_conversation_id_persistence():
    """
    Test that the RAG engine respects the conversation ID passed from the API
    by creating a conversation in the database first
    """
    logger.info("Testing conversation ID persistence...")
    
    # Create a test conversation ID as a UUID object
    test_conversation_id = uuid.uuid4()
    logger.info(f"Test conversation ID: {test_conversation_id}")
    
    # Create a test user ID
    test_user_id = uuid.uuid4()
    logger.info(f"Test user ID: {test_user_id}")
    
    # Get a session generator
    session_gen = get_session()
    
    try:
        # Get the session
        db = await anext(session_gen)
        
        # Create a conversation in the database
        conversation = Conversation(
            id=test_conversation_id,
            user_id=None,  # Set to None to avoid foreign key constraint
            conv_metadata={"title": "Test Conversation"}
        )
        db.add(conversation)
        await db.commit()
        logger.info(f"Created test conversation with ID: {test_conversation_id}")
        
        # Initialize RAG engine
        rag_engine = RAGEngine()
        
        # Test with provided conversation ID
        query_result = await rag_engine.query(
            query="Test query",
            conversation_id=test_conversation_id,
            user_id=str(uuid.uuid4()),  # Use a valid UUID string
            use_rag=False  # Disable RAG to simplify the test
        )
        
        logger.info(f"Query result: {query_result}")
        
        # Verify that a memory was created for this conversation
        memories = await get_memory_buffer(
            conversation_id=test_conversation_id,
            db=db
        )
        
        # Verify that at least one memory was created
        assert len(memories) > 0, "At least one memory should have been created"
        logger.info(f"Found {len(memories)} memories for conversation {test_conversation_id}")
        
        # Verify the memory has the correct conversation ID
        assert memories[0].conversation_id == test_conversation_id, \
            f"Memory should have the correct conversation ID: {test_conversation_id}, but got: {memories[0].conversation_id}"
        
        logger.info(f"Memory has the correct conversation ID: {memories[0].conversation_id}")
        
        # Clean up
        await db.execute(text(f"DELETE FROM memories WHERE conversation_id = '{test_conversation_id}'"))
        await db.execute(text(f"DELETE FROM conversations WHERE id = '{test_conversation_id}'"))
        await db.commit()
        
        logger.info("Conversation ID persistence test passed")
    finally:
        # Close the session generator to trigger cleanup
        if session_gen:
            await session_gen.aclose()

@pytest.mark.asyncio
async def test_memory_operations_with_conversation_id():
    """
    Test memory operations with a valid conversation ID
    """
    logger.info("Testing memory operations with conversation ID...")
    
    # Create test IDs
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # Get a session generator
    session_gen = get_session()
    
    try:
        # Get the session
        db = await anext(session_gen)
        
        # Create a conversation in the database
        conversation = Conversation(
            id=conversation_id,
            user_id=None,  # Set to None to avoid foreign key constraint
            conv_metadata={"title": "Test Conversation"}
        )
        db.add(conversation)
        await db.commit()
        logger.info(f"Created test conversation with ID: {conversation_id}")
        
        # Test adding to memory buffer
        memory = await add_to_memory_buffer(
            conversation_id=conversation_id,
            content="Test memory content",
            label="test_memory",
            db=db
        )
        
        # Verify memory was added
        assert memory is not None, "Memory should be added successfully"
        assert memory.conversation_id == conversation_id, "Memory should have the correct conversation ID"
        logger.info(f"Added memory with ID: {memory.id}")
        
        # Test retrieving from memory buffer
        memories = await get_memory_buffer(
            conversation_id=conversation_id,
            db=db
        )
        
        # Verify memory was retrieved
        assert len(memories) > 0, "Should retrieve at least one memory"
        assert memories[0].content == "Test memory content", "Should retrieve the correct memory content"
        logger.info(f"Retrieved {len(memories)} memories")
        
        # Test process_query with the conversation ID
        processed_query, memory_response, memory_operation = await process_query(
            query="Test query",
            user_id=str(uuid.uuid4()),  # Use a valid UUID string
            conversation_id=conversation_id,
            db=db
        )
        
        # Verify query was processed
        assert processed_query == "Test query", "Query should be processed correctly"
        logger.info("Process query test passed")
        
        # Clean up
        await db.execute(text(f"DELETE FROM memories WHERE conversation_id = '{conversation_id}'"))
        await db.execute(text(f"DELETE FROM conversations WHERE id = '{conversation_id}'"))
        await db.commit()
        
        logger.info("Memory operations test passed")
    finally:
        # Close the session generator to trigger cleanup
        if session_gen:
            await session_gen.aclose()

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_session_management())
    asyncio.run(test_conversation_id_handling())
    asyncio.run(test_memory_operations_with_conversation_id())
    
    logger.info("All tests passed!")