"""
Test script for memory functionality in Metis RAG
"""
import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import get_session
from app.rag.memory_buffer import add_to_memory_buffer, get_memory_buffer, process_query
from app.db.models import Conversation, User
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.user_repository import UserRepository
from app.core.security import get_password_hash
from app.models.memory import Memory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_test")

async def test_memory_functionality():
    """
    Test the complete memory functionality
    """
    # Get database session
    db = await anext(get_session())
    
    try:
        # Create a test user
        user_repository = UserRepository(db)
        
        # Generate a unique username
        username = f"test_user_{uuid.uuid4().hex[:8]}"
        email = f"{username}@example.com"
        
        # Create the user
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash("testpassword"),
            is_active=True,
            is_admin=False,
            created_at=datetime.now()
        )
        
        # Add user to database
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        user_id = user.id
        logger.info(f"Created test user with ID: {user_id}")
        
        # Create a conversation repository
        conversation_repository = ConversationRepository(db, user_id)
        
        # Create a new conversation
        conversation = await conversation_repository.create_conversation()
        conversation_id = conversation.id
        logger.info(f"Created conversation with ID: {conversation_id}")
        
        logger.info(f"Created conversation with ID: {conversation_id}")
        # Test 1: Store explicit memory
        logger.info("Test 1: Storing explicit memory")
        memory_content = "My favorite color is blue"
        memory = await add_to_memory_buffer(
            conversation_id=conversation_id,
            content=memory_content,
            label="explicit_memory",
            db=db
        )
        logger.info(f"Stored memory: {memory.content}")
        
        # Test 2: Store implicit memory
        logger.info("Test 2: Storing implicit memory")
        query = "I like to eat pizza"
        await add_to_memory_buffer(
            conversation_id=conversation_id,
            content=query,
            label="implicit_memory",
            db=db
        )
        logger.info(f"Stored implicit memory: {query}")
        
        # Test 3: Process query with explicit memory command
        logger.info("Test 3: Processing query with explicit memory command")
        query = "Remember this: My favorite movie is The Matrix"
        processed_query, memory_response, memory_operation = await process_query(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db
        )
        logger.info(f"Processed query: {processed_query}")
        logger.info(f"Memory response: {memory_response}")
        logger.info(f"Memory operation: {memory_operation}")
        
        # Test 4: Process query with explicit recall command
        logger.info("Test 4: Processing query with explicit recall command")
        query = "Recall my favorite color"
        processed_query, memory_response, memory_operation = await process_query(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db
        )
        logger.info(f"Processed query: {processed_query}")
        logger.info(f"Memory response: {memory_response}")
        logger.info(f"Memory operation: {memory_operation}")
        
        # Test 5: Process query with implicit memory query
        logger.info("Test 5: Processing query with implicit memory query")
        query = "What is my favorite movie?"
        processed_query, memory_response, memory_operation = await process_query(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db
        )
        logger.info(f"Processed query: {processed_query}")
        logger.info(f"Memory response: {memory_response}")
        logger.info(f"Memory operation: {memory_operation}")
        
        # Test 6: Get all memories
        logger.info("Test 6: Getting all memories")
        memories = await get_memory_buffer(
            conversation_id=conversation_id,
            db=db
        )
        logger.info(f"Retrieved {len(memories)} memories")
        for i, memory in enumerate(memories):
            logger.info(f"Memory {i+1}: {memory.content}")
        
        # Test 7: Get memories with search term
        logger.info("Test 7: Getting memories with search term")
        memories = await get_memory_buffer(
            conversation_id=conversation_id,
            search_term="favorite",
            db=db
        )
        logger.info(f"Retrieved {len(memories)} memories with search term 'favorite'")
        for i, memory in enumerate(memories):
            logger.info(f"Memory {i+1}: {memory.content}")
        
        # Test 8: Get memories with specific label
        logger.info("Test 8: Getting memories with specific label")
        memories = await get_memory_buffer(
            conversation_id=conversation_id,
            label="explicit_memory",
            db=db
        )
        logger.info(f"Retrieved {len(memories)} memories with label 'explicit_memory'")
        for i, memory in enumerate(memories):
            logger.info(f"Memory {i+1}: {memory.content}")
        
        logger.info("All memory tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error testing memory functionality: {str(e)}")
        raise
    finally:
        # Close database session
        await db.close()

async def main():
    """
    Main function
    """
    await test_memory_functionality()

if __name__ == "__main__":
    asyncio.run(main())