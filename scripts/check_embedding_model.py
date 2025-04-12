import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.ollama_client import OllamaClient
from app.core.config import DEFAULT_EMBEDDING_MODEL, OLLAMA_BASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("check_embedding_model")

async def check_embedding_model():
    """Check if the embedding model is available and working"""
    logger.info(f"Checking embedding model: {DEFAULT_EMBEDDING_MODEL}")
    logger.info(f"Ollama base URL: {OLLAMA_BASE_URL}")
    
    try:
        # Create Ollama client
        client = OllamaClient(base_url=OLLAMA_BASE_URL)
        
        # List available models
        logger.info("Listing available models...")
        models = await client.list_models()
        
        # Check if embedding model is in the list
        model_names = [model.get("name") for model in models]
        logger.info(f"Available models: {model_names}")
        
        if DEFAULT_EMBEDDING_MODEL in model_names:
            logger.info(f"Embedding model {DEFAULT_EMBEDDING_MODEL} is available")
        else:
            logger.warning(f"Embedding model {DEFAULT_EMBEDDING_MODEL} is NOT available")
            logger.info("You may need to pull the model using: ollama pull nomic-embed-text")
        
        # Try to create an embedding
        logger.info("Testing embedding creation...")
        embedding = await client.create_embedding("This is a test", model=DEFAULT_EMBEDDING_MODEL)
        
        if embedding and len(embedding) > 0:
            logger.info(f"Successfully created embedding with length {len(embedding)}")
            logger.info(f"First 5 values: {embedding[:5]}")
        else:
            logger.error("Failed to create embedding - empty result")
        
    except Exception as e:
        logger.error(f"Error checking embedding model: {str(e)}")
    finally:
        # Close the client
        await client.client.aclose()

if __name__ == "__main__":
    asyncio.run(check_embedding_model())