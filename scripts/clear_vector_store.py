#!/usr/bin/env python3
"""
Script to clear the vector store (ChromaDB) completely.
This will remove all documents and their embeddings from the vector store.
"""

import sys
import os
import logging
import asyncio
import chromadb
from chromadb.config import Settings

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import CHROMA_DB_DIR

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("clear_vector_store")

async def clear_vector_store():
    """Clear all documents from the vector store"""
    try:
        logger.info(f"Connecting to ChromaDB at {CHROMA_DB_DIR}")
        
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(
            path=CHROMA_DB_DIR,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Get the collection
        try:
            collection = client.get_collection(name="documents")
            
            # Get count before deletion
            count_before = collection.count()
            logger.info(f"Found {count_before} documents in the vector store")
            
            if count_before > 0:
                # Get all document IDs
                results = collection.get()
                all_ids = results["ids"]
                logger.info(f"Retrieved {len(all_ids)} document IDs")
                
                # Delete all documents by ID
                collection.delete(ids=all_ids)
                logger.info(f"Deleted {len(all_ids)} documents by ID")
            else:
                logger.info("No documents to delete")
            
            # Verify deletion
            count_after = collection.count()
            logger.info(f"Deleted {count_before - count_after} documents from the vector store")
            
            if count_after > 0:
                logger.warning(f"There are still {count_after} documents in the vector store")
            else:
                logger.info("Vector store successfully cleared")
                
        except ValueError as e:
            if "Collection 'documents' does not exist" in str(e):
                logger.info("No 'documents' collection found. Vector store is already empty.")
            else:
                raise
                
    except Exception as e:
        logger.error(f"Error clearing vector store: {str(e)}")
        raise

def clear_vector_store_sync():
    """Synchronous wrapper for clear_vector_store"""
    asyncio.run(clear_vector_store())

if __name__ == "__main__":
    logger.info("Starting vector store clearing process")
    clear_vector_store_sync()
    logger.info("Vector store clearing process completed")