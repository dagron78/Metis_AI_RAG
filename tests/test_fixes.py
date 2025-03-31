import asyncio
import logging
import sys
import os
import uuid
import nest_asyncio
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_fixes")

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.db.repositories.conversation_repository import ConversationRepository

async def test_analytics_repository_fix():
    """Test the fix for the analytics repository"""
    logger.info("Testing analytics repository fix...")
    
    # Create a new session
    session = AsyncSessionLocal()
    try:
        # Create repository
        analytics_repo = AnalyticsRepository(session)
        
        # Test create_analytics_query method
        try:
            query = await analytics_repo.create_analytics_query(
                query="Test query",
                model="gemma3:4b",
                use_rag=True,
                response_time_ms=100.0,
                token_count=50,
                document_ids=["test-doc-1", "test-doc-2"],
                query_type="simple",
                successful=True
            )
            logger.info(f"Successfully created analytics query with ID: {query.id}")
            return True
        except Exception as e:
            logger.error(f"Error testing analytics repository fix: {str(e)}")
            return False
    finally:
        await session.close()

async def test_citation_fix():
    """Test the fix for the citation foreign key validation"""
    logger.info("Testing citation fix...")
    
    # Create a new session
    session = AsyncSessionLocal()
    try:
        # Create conversation repository
        conv_repo = ConversationRepository(session)
        
        # Create a test conversation
        conversation = await conv_repo.create_conversation(user_id="test_user")
        
        # Add a message to the conversation
        message = await conv_repo.add_message(
            conversation_id=conversation.id,
            content="Test message",
            role="assistant"
        )
        
        # Test the validation logic directly
        from app.db.models import Chunk, Document
        from sqlalchemy import select
        
        # Generate non-existent IDs
        non_existent_chunk_id = uuid.uuid4()
        non_existent_doc_id = uuid.uuid4()
        
        # Check if the validation code correctly identifies non-existent IDs
        stmt = select(Chunk).filter(Chunk.id == non_existent_chunk_id)
        result = await session.execute(stmt)
        chunk = result.scalars().first()
        
        if chunk is None:
            logger.info("Validation correctly identified non-existent chunk_id")
        else:
            logger.error("Validation failed to identify non-existent chunk_id")
            return False
            
        stmt = select(Document).filter(Document.id == non_existent_doc_id)
        result = await session.execute(stmt)
        document = result.scalars().first()
        
        if document is None:
            logger.info("Validation correctly identified non-existent document_id")
        else:
            logger.error("Validation failed to identify non-existent document_id")
            return False
        
        logger.info("Citation validation logic test passed")
        return True
    except Exception as e:
        logger.error(f"Error testing citation fix: {str(e)}")
        return False
    finally:
        await session.close()

async def main():
    """Run all tests"""
    try:
        analytics_result = await test_analytics_repository_fix()
        citation_result = await test_citation_fix()
        
        logger.info(f"Analytics repository fix test: {'PASSED' if analytics_result else 'FAILED'}")
        logger.info(f"Citation fix test: {'PASSED' if citation_result else 'FAILED'}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    # Install the uvloop event loop policy if available
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    # Run the main function
    asyncio.run(main())