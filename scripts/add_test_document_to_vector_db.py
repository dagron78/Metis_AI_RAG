import asyncio
import sys
import os
import logging
from pathlib import Path
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("add_test_document_to_vector_db")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.vector_store import VectorStore
from app.models.document import Document, Chunk
from app.rag.ollama_client import OllamaClient
from app.core.config import DEFAULT_EMBEDDING_MODEL

async def add_test_document_to_vector_db():
    """Add a test document to the vector database"""
    logger.info("Adding a test document to the vector database...")
    
    try:
        # Create a test document
        test_document = Document(
            id=str(uuid4()),
            filename="test_document.txt",
            content="This is a test document for the vector database.",
            metadata={"test": True},
            folder="/"
        )
        
        # Create Ollama client for embeddings
        ollama_client = OllamaClient()
        
        # Create test chunks with embeddings
        chunks = []
        for i in range(3):
            chunk_text = f"This is test chunk {i+1} for the vector database."
            logger.info(f"Creating embedding for chunk: '{chunk_text}'")
            
            # Create embedding
            embedding = await ollama_client.create_embedding(chunk_text, model=DEFAULT_EMBEDDING_MODEL)
            
            # Create chunk
            chunk = Chunk(
                id=str(uuid4()),
                content=chunk_text,
                embedding=embedding,
                metadata={
                    "document_id": test_document.id,
                    "index": i,
                    "folder": "/",
                    "is_public": True
                }
            )
            chunks.append(chunk)
        
        # Add chunks to document
        test_document.chunks = chunks
        
        # Create vector store
        vector_store = VectorStore()
        
        # Add document to vector store
        logger.info(f"Adding test document {test_document.id} to vector store")
        await vector_store.add_document(test_document)
        
        # Get vector store statistics
        stats = await vector_store.get_statistics()
        logger.info(f"Vector store statistics: {stats}")
        
        # Test search
        logger.info("Testing search functionality")
        results = await vector_store.search("test chunk", top_k=5)
        
        if results:
            logger.info(f"Found {len(results)} results")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}:")
                logger.info(f"  Content: {result.get('content', '')[:50]}...")
                logger.info(f"  Distance: {result.get('distance', 'N/A')}")
                logger.info(f"  Document ID: {result.get('metadata', {}).get('document_id', 'N/A')}")
        else:
            logger.warning("No results found")
        
    except Exception as e:
        logger.error(f"Error adding test document to vector database: {str(e)}")

if __name__ == "__main__":
    asyncio.run(add_test_document_to_vector_db())