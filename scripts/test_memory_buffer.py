#!/usr/bin/env python
"""
Test script for the memory buffer functionality
"""
import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import get_session
from app.models.memory import Memory
from app.db.models import Conversation
from app.rag.memory_buffer import add_to_memory_buffer, get_memory_buffer, process_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def test_memory_buffer():
    """Test the memory buffer functionality"""
    try:
        logger.info("Starting memory buffer test")
        
        # Get a database session
        db = await anext(get_session())
        
        # Create a test conversation
        conversation = Conversation(message_count=0)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        conversation_id = conversation.id
        logger.info(f"Created test conversation with ID: {conversation_id}")
        
        # Test adding a memory
        memory = await add_to_memory_buffer(
            conversation_id=conversation_id,
            content="This is a test memory",
            label="test_memory",
            db=db
        )
        logger.info(f"Added memory: {memory.id}")
        
        # Test retrieving memories
        memories = await get_memory_buffer(
            conversation_id=conversation_id,
            db=db
        )
        logger.info(f"Retrieved {len(memories)} memories")
        for i, mem in enumerate(memories):
            logger.info(f"Memory {i+1}: {mem.content}")
        
        # Test processing a memory storage command
        user_id = str(uuid.uuid4())
        query = "Remember this phrase: The sky is blue and the grass is green."
        processed_query, memory_response, memory_operation = await process_query(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db
        )
        logger.info(f"Processed query: {processed_query}")
        logger.info(f"Memory response: {memory_response}")
        logger.info(f"Memory operation: {memory_operation}")
        
        # Test processing a memory recall command
        query = "Recall what I asked you to remember."
        processed_query, memory_response, memory_operation = await process_query(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db
        )
        logger.info(f"Processed query: {processed_query}")
        logger.info(f"Memory response: {memory_response}")
        logger.info(f"Memory operation: {memory_operation}")
        
        # Test processing a regular query
        query = "What is the capital of France?"
        processed_query, memory_response, memory_operation = await process_query(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db
        )
        logger.info(f"Processed query: {processed_query}")
        logger.info(f"Memory response: {memory_response}")
        logger.info(f"Memory operation: {memory_operation}")
        
        logger.info("Memory buffer test completed successfully")
    except Exception as e:
        logger.error(f"Error testing memory buffer: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_memory_buffer())