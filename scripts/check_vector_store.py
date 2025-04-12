import asyncio
import sys
import os
import logging
from pathlib import Path
from uuid import uuid4

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.core.config import DEFAULT_EMBEDDING_MODEL, CHROMA_DB_DIR
from app.models.document import Document, Chunk

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("check_vector_store")

async def check_vector_store():
    """Check if the vector store is working properly"""
    logger.info(f"Checking vector store at: {CHROMA_DB_DIR}")
    
    try:
        # Create vector store
        vector_store = VectorStore()
        
        # Get statistics
        stats = await vector_store.get_statistics()
        logger.info(f"Vector store statistics: {stats}")
        
        # Create a test document with a chunk
        test_document = Document(
            id=str(uuid4()),
            filename="test_document.txt",
            content="This is a test document",
            doc_metadata={"test": True},
            folder="/",
            processing_status="completed",
            is_public=True  # Set is_public to True to pass the security filter
        )
        
        # Create Ollama client for embeddings
        ollama_client = OllamaClient()
        
        # Create a test chunk with embedding
        test_text = "This is a test chunk for vector store testing"
        embedding = await ollama_client.create_embedding(test_text, model=DEFAULT_EMBEDDING_MODEL)
        
        test_chunk = Chunk(
            id=str(uuid4()),
            content=test_text,
            embedding=embedding,
            metadata={
                "document_id": test_document.id,
                "index": 0,
                "folder": "/",
                "is_public": True  # Add is_public flag to chunk metadata
            }
        )
        
        # Add chunk to document
        test_document.chunks = [test_chunk]
        
        # Add document to vector store
        logger.info(f"Adding test document {test_document.id} to vector store")
        await vector_store.add_document(test_document)
        
        # Get updated statistics
        stats = await vector_store.get_statistics()
        logger.info(f"Vector store statistics after adding document: {stats}")
        
        # Search for the document
        logger.info("Searching for the test document")
        results = await vector_store.search(
            query="test chunk",
            top_k=5
        )
        
        if results:
            logger.info(f"Found {len(results)} results")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}:")
                logger.info(f"  Content: {result.get('content', '')[:50]}...")
                logger.info(f"  Distance: {result.get('distance', 'N/A')}")
                logger.info(f"  Document ID: {result.get('metadata', {}).get('document_id', 'N/A')}")
        else:
            logger.warning("No results found")
        
        # Clean up - delete the test document
        logger.info(f"Cleaning up - deleting test document {test_document.id}")
        vector_store.delete_document(test_document.id)
        
    except Exception as e:
        logger.error(f"Error checking vector store: {str(e)}")
    finally:
        # Close any connections
        pass

if __name__ == "__main__":
    asyncio.run(check_vector_store())