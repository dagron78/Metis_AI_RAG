import asyncio
import sys
import os
from pathlib import Path
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("reset_document_status")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import SETTINGS

async def reset_document_status():
    """Reset document status directly in the database"""
    logger.info("Resetting document status...")
    
    # Extract database path from the URL
    db_path = SETTINGS.database_url.replace("sqlite+aiosqlite:///", "")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all documents in failed status
        cursor.execute("SELECT id, filename, processing_status FROM documents WHERE processing_status = 'failed'")
        documents = cursor.fetchall()
        
        logger.info(f"Found {len(documents)} documents in 'failed' status:")
        for doc in documents:
            logger.info(f"ID: {doc[0]}, Filename: {doc[1]}, Status: {doc[2]}")
        
        # Update document status to pending
        cursor.execute("UPDATE documents SET processing_status = 'pending' WHERE processing_status = 'failed'")
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT id, filename, processing_status FROM documents")
        updated_documents = cursor.fetchall()
        
        logger.info(f"Updated document status. Current status:")
        for doc in updated_documents:
            logger.info(f"ID: {doc[0]}, Filename: {doc[1]}, Status: {doc[2]}")
        
        # Close connection
        conn.close()
        
        logger.info("Document status reset completed. You can now run the application to process the documents.")
        logger.info("To check if documents are processed, run: python scripts/check_vector_db_contents.py")
        
    except Exception as e:
        logger.error(f"Error resetting document status: {str(e)}")

if __name__ == "__main__":
    asyncio.run(reset_document_status())