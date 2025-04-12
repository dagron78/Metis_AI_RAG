import asyncio
import sys
import os
import logging
import sqlite3
import json
import shutil
from pathlib import Path
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("create_test_pending_document")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import SETTINGS, UPLOAD_DIR

async def create_test_pending_document():
    """Create a test document in the 'pending' state"""
    logger.info("Creating a test document in the 'pending' state...")
    
    # Extract database path from the URL
    db_path = SETTINGS.database_url.replace("sqlite+aiosqlite:///", "")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a test document ID
        document_id = str(uuid4())
        logger.info(f"Generated document ID: {document_id}")
        
        # Create a directory for the document
        document_dir = os.path.join(UPLOAD_DIR, document_id)
        os.makedirs(document_dir, exist_ok=True)
        
        # Copy a test file to the document directory
        test_file_path = "uploads/convertingamodel.txt"
        if not os.path.exists(test_file_path):
            logger.error(f"Test file not found: {test_file_path}")
            return
        
        dest_file_path = os.path.join(document_dir, "test_document.txt")
        shutil.copy(test_file_path, dest_file_path)
        logger.info(f"Copied test file to: {dest_file_path}")
        
        # Insert the document into the database
        cursor.execute(
            """
            INSERT INTO documents (
                id, filename, content, doc_metadata, folder, uploaded, 
                processing_status, is_public
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?)
            """,
            (
                document_id,
                "test_document.txt",
                "",  # Empty content
                json.dumps({"file_path": dest_file_path, "content_type": "text/plain"}),
                "/test",
                "pending",
                True
            )
        )
        conn.commit()
        
        logger.info(f"Created test document in the database with ID: {document_id}")
        logger.info("Document is in the 'pending' state and ready for processing")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating test document: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_test_pending_document())