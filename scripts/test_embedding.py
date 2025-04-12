import asyncio
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_embedding")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.ollama_client import OllamaClient
from app.core.config import DEFAULT_EMBEDDING_MODEL

async def test_embedding():
    """Test the embedding functionality"""
    logger.info(f"Testing embedding with model: {DEFAULT_EMBEDDING_MODEL}")
    
    try:
        # Create Ollama client
        client = OllamaClient()
        
        # Test text
        test_text = "This is a test text for embedding."
        
        # Create embedding
        logger.info(f"Creating embedding for text: '{test_text}'")
        embedding = await client.create_embedding(test_text, model=DEFAULT_EMBEDDING_MODEL)
        
        # Check embedding
        if embedding:
            logger.info(f"Successfully created embedding with length: {len(embedding)}")
            logger.info(f"First 5 values: {embedding[:5]}")
        else:
            logger.error("Failed to create embedding: empty embedding returned")
        
        # Close client
        await client.client.aclose()
        
    except Exception as e:
        logger.error(f"Error testing embedding: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_embedding())