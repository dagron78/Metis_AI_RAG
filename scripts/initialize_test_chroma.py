#!/usr/bin/env python3
"""
Initialize a fresh ChromaDB database for testing.
This script creates a new ChromaDB database in the test_e2e_chroma directory.
"""

import os
import sys
import shutil
import logging
import chromadb
from chromadb.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("initialize_test_chroma")

def initialize_chroma_db(db_dir: str):
    """
    Initialize a fresh ChromaDB database.
    
    Args:
        db_dir: Directory to store the ChromaDB database
    """
    try:
        logger.info(f"Initializing ChromaDB in directory: {db_dir}")
        
        # Remove existing directory if it exists
        if os.path.exists(db_dir):
            logger.info(f"Removing existing directory: {db_dir}")
            shutil.rmtree(db_dir)
        
        # Create directory
        os.makedirs(db_dir, exist_ok=True)
        
        # Initialize ChromaDB
        chroma_client = chromadb.PersistentClient(
            path=db_dir,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Create a test collection
        collection = chroma_client.create_collection(
            name="documents",
            metadata={"description": "Test collection for documents"}
        )
        
        logger.info(f"Created collection: {collection.name}")
        logger.info(f"ChromaDB initialized successfully in {db_dir}")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Starting ChromaDB initialization...")
    
    # Initialize ChromaDB in test_e2e_chroma directory
    db_dir = "test_e2e_chroma"
    
    if initialize_chroma_db(db_dir):
        logger.info("ChromaDB initialization completed successfully")
        return 0
    else:
        logger.error("ChromaDB initialization failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())