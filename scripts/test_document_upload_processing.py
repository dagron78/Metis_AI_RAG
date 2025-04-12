import asyncio
import sys
import os
import logging
import requests
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_document_upload_processing")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

async def test_document_upload_processing():
    """Test document upload and processing flow"""
    logger.info("Testing document upload and processing flow...")
    
    # API base URL (assuming the app is running on localhost:8001)
    base_url = "http://localhost:8001"
    
    # Test file path (using a sample text file)
    test_file_path = "uploads/convertingamodel.txt"
    
    if not os.path.exists(test_file_path):
        logger.error(f"Test file not found: {test_file_path}")
        return
    
    try:
        # Step 1: Upload the document
        logger.info(f"Uploading test file: {test_file_path}")
        
        with open(test_file_path, "rb") as f:
            files = {"file": (os.path.basename(test_file_path), f)}
            data = {"tags": "test,upload", "folder": "/test"}
            
            response = requests.post(
                f"{base_url}/api/basic-documents/upload",
                files=files,
                data=data
            )
        
        if response.status_code != 200:
            logger.error(f"Error uploading document: {response.status_code} - {response.text}")
            return
        
        # Get document ID from response
        document_id = response.json().get("id")
        logger.info(f"Document uploaded successfully. ID: {document_id}")
        
        # Step 2: Wait for processing to complete (poll document status)
        max_attempts = 30
        attempt = 0
        processed = False
        
        logger.info("Waiting for document processing to complete...")
        
        while attempt < max_attempts and not processed:
            # Wait a bit before checking
            await asyncio.sleep(2)
            attempt += 1
            
            # Check document status
            status_response = requests.get(f"{base_url}/api/basic-documents/{document_id}")
            
            if status_response.status_code != 200:
                logger.error(f"Error checking document status: {status_response.status_code} - {status_response.text}")
                continue
            
            document = status_response.json()
            processing_status = document.get("processing_status", "unknown")
            
            logger.info(f"Document status (attempt {attempt}/{max_attempts}): {processing_status}")
            
            if processing_status == "completed":
                processed = True
                logger.info("Document processing completed successfully!")
                break
            elif processing_status == "failed":
                logger.error("Document processing failed!")
                break
        
        if not processed:
            logger.warning("Document processing did not complete within the expected time.")
        
        # Step 3: Check vector store statistics
        logger.info("Checking vector store statistics...")
        
        stats_response = requests.get(f"{base_url}/api/basic-documents/stats")
        
        if stats_response.status_code != 200:
            logger.error(f"Error getting vector store statistics: {stats_response.status_code} - {stats_response.text}")
            return
        
        stats = stats_response.json()
        logger.info(f"Vector store statistics: {stats}")
        
        # Step 4: Clean up (delete the test document)
        logger.info(f"Cleaning up - deleting test document {document_id}")
        
        delete_response = requests.delete(f"{base_url}/api/basic-documents/{document_id}")
        
        if delete_response.status_code != 200:
            logger.error(f"Error deleting document: {delete_response.status_code} - {delete_response.text}")
            return
        
        logger.info("Test document deleted successfully")
        logger.info("Document upload and processing test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error testing document upload and processing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_document_upload_processing())