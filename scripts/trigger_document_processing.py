import asyncio
import sys
import os
import logging
import requests
import json
import sqlite3
from pathlib import Path
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("trigger_document_processing")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import SETTINGS, API_V1_STR

async def trigger_document_processing():
    """Trigger document processing via API for all pending documents"""
    logger.info("Triggering document processing via API...")
    
    # Extract database path from the URL
    db_path = SETTINGS.database_url.replace("sqlite+aiosqlite:///", "")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all documents in pending status
        cursor.execute("SELECT id, filename FROM documents WHERE processing_status = 'pending'")
        documents = cursor.fetchall()
        
        if not documents:
            logger.info("No pending documents found.")
            return
        
        logger.info(f"Found {len(documents)} documents to process:")
        for doc in documents:
            logger.info(f"ID: {doc[0]}, Filename: {doc[1]}")
        
        # Close connection
        conn.close()
        
        # API base URL (assuming the app is running on localhost:8001)
        base_url = "http://localhost:8001"
        
        # Process each document via API
        for doc_id, filename in documents:
            try:
                # Call the process endpoint with the correct path (using hyphen, not underscore)
                url = f"{base_url}{API_V1_STR}/basic-documents/{doc_id}/process"
                logger.info(f"Calling API to process document: {url}")
                
                response = requests.post(url)
                
                if response.status_code == 200:
                    logger.info(f"Successfully triggered processing for document {doc_id}: {filename}")
                    logger.info(f"Response: {response.json()}")
                else:
                    logger.error(f"Error triggering processing for document {doc_id}: {response.status_code} - {response.text}")
            
            except Exception as e:
                logger.error(f"Error calling API for document {doc_id}: {str(e)}")
        
        logger.info("Document processing triggered. Check the application logs for processing status.")
        logger.info("To check if documents are processed, run: python scripts/check_vector_db_contents.py")
        
    except Exception as e:
        logger.error(f"Error triggering document processing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(trigger_document_processing())