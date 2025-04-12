import asyncio
import sys
import os
import logging
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix_document_paths")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import SETTINGS, UPLOAD_DIR

async def fix_document_paths():
    """Fix document paths in the database to match the actual directory structure"""
    logger.info("Fixing document paths in the database...")
    
    # Extract database path from the URL
    db_path = SETTINGS.database_url.replace("sqlite+aiosqlite:///", "")
    logger.info(f"Database path: {db_path}")
    
    # Define the document mappings
    document_mappings = [
        {
            "id": "71f2e13835d54d35b0e60b9b3c3f612e",  # ID without hyphens
            "filename": "Stuart Kesler Deposition Transcript (00205236xB5A0D).PDF",
            "actual_directory": "5d60702f-ad98-4adc-abc4-1faea55c4a99"
        },
        {
            "id": "6471acbdbafb406c82cb3bfa3a6f4a94",  # ID without hyphens
            "filename": "aboutthementors.txt",
            "actual_directory": "ba1dd5fb-973a-414a-aa96-5b8d715ba09b"
        }
    ]
    
    try:
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update each document's metadata
        for mapping in document_mappings:
            doc_id = mapping["id"]
            actual_dir = mapping["actual_directory"]
            filename = mapping["filename"]
            
            # Get current metadata
            cursor.execute("SELECT doc_metadata FROM documents WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Document {doc_id} not found in database")
                continue
            
            # Parse metadata
            import json
            metadata_str = result[0]
            metadata = json.loads(metadata_str) if metadata_str else {}
            
            # Update file path in metadata
            file_path = os.path.join(UPLOAD_DIR, actual_dir, filename)
            metadata["file_path"] = file_path
            
            # Update metadata in database
            cursor.execute(
                "UPDATE documents SET doc_metadata = ? WHERE id = ?",
                (json.dumps(metadata), doc_id)
            )
            
            # Reset processing status to pending
            cursor.execute(
                "UPDATE documents SET processing_status = 'pending' WHERE id = ?",
                (doc_id,)
            )
            
            logger.info(f"Updated document {doc_id} to use directory {actual_dir}")
        
        # Commit changes
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT id, filename, processing_status, doc_metadata FROM documents")
        updated_documents = cursor.fetchall()
        
        logger.info(f"Updated document status. Current status:")
        for doc in updated_documents:
            logger.info(f"ID: {doc[0]}, Filename: {doc[1]}, Status: {doc[2]}")
            logger.info(f"Metadata: {doc[3]}")
        
        # Close connection
        conn.close()
        
        logger.info("Document paths fixed. You can now run the application to process the documents.")
        logger.info("To trigger document processing, run: python scripts/trigger_document_processing.py")
        
    except Exception as e:
        logger.error(f"Error fixing document paths: {str(e)}")

if __name__ == "__main__":
    asyncio.run(fix_document_paths())