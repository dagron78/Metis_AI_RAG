import asyncio
import logging
import sys
import os
import nest_asyncio

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.db.repositories.document_repository import DocumentRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

async def test_create_document():
    """Test creating a document using the DocumentRepository"""
    # Create a new session
    session = AsyncSessionLocal()
    try:
        # Create a document repository
        document_repository = DocumentRepository(session)
        
        # Create a document
        document = await document_repository.create_document(
            filename="test_document.txt",
            content="This is a test document.",
            metadata={"source": "test"},
            tags=["test", "sample"],
            folder="/"
        )
        
        logger.info(f"Document created: {document.id}")
        return document
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise
    finally:
        await session.close()

async def main():
    """Main function"""
    try:
        document = await test_create_document()
        logger.info(f"Test completed successfully. Document ID: {document.id}")
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