#!/usr/bin/env python3
"""
Direct API testing script for Metis RAG.
This script tests the Metis RAG API directly using the requests library.
"""

import os
import sys
import json
import logging
import uuid
import time
from typing import Dict, Any, List, Optional
import requests
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_api_directly")

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Test documents - paths relative to project root
TEST_DOCUMENTS = {
    "technical_specs": {
        "path": "data/test_docs/smart_home_technical_specs.pdf",
        "type": "pdf",
        "content_type": "application/pdf"
    },
    "user_guide": {
        "path": "data/test_docs/smart_home_user_guide.txt",
        "type": "txt",
        "content_type": "text/plain"
    },
    "device_comparison": {
        "path": "data/test_docs/smart_home_device_comparison.csv",
        "type": "csv",
        "content_type": "text/csv"
    },
    "developer_reference": {
        "path": "data/test_docs/smart_home_developer_reference.md",
        "type": "md",
        "content_type": "text/markdown"
    }
}

# Test queries
TEST_QUERIES = [
    "What are the specifications of the SmartHome Hub?",
    "How do I troubleshoot when devices won't connect?",
    "What is the battery life of the motion sensor?",
    "Compare the Motion Sensor and Door Sensor specifications."
]

def verify_test_documents():
    """Verify that all test documents exist"""
    missing_docs = []
    for doc_id, doc_info in TEST_DOCUMENTS.items():
        if not os.path.exists(doc_info["path"]):
            missing_docs.append(doc_info["path"])
    
    if missing_docs:
        logger.error(f"Missing test documents: {', '.join(missing_docs)}")
        logger.error("Please ensure all test documents are created before running the test.")
        return False
    else:
        logger.info("All test documents verified.")
        return True

def authenticate():
    """
    Authenticate with the API and return the access token.
    
    Returns:
        Access token if authentication successful, None otherwise
    """
    logger.info("Authenticating with API...")
    
    # Create a unique test user for this test run
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    test_password = "testpassword"
    
    try:
        # Register the new test user
        logger.info(f"Registering new test user: {test_username}")
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": test_username,
                "email": f"{test_username}@example.com",
                "password": test_password,
                "full_name": "Test User",
                "is_active": True,
                "is_admin": False
            }
        )
        
        if register_response.status_code != 200:
            logger.error(f"Registration failed: {register_response.status_code} - {register_response.text}")
            return None
            
        logger.info(f"User {test_username} registered successfully")
        
        # Authenticate with the new user
        login_response = requests.post(
            f"{BASE_URL}/api/auth/token",
            data={
                "username": test_username,
                "password": test_password,
                "grant_type": "password"
            }
        )
        
        if login_response.status_code != 200:
            logger.error(f"Login failed: {login_response.status_code} - {login_response.text}")
            return None
            
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error("No access token in response")
            return None
        
        logger.info(f"Successfully obtained token: {access_token[:10]}...")
        return access_token
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None

def upload_and_process_documents(access_token):
    """
    Upload and process all test documents.
    
    Args:
        access_token: Access token for authentication
        
    Returns:
        Dictionary of document IDs keyed by document type
    """
    logger.info("Uploading and processing documents...")
    
    # Set up headers with authentication token
    headers = {"Authorization": f"Bearer {access_token}"}
    
    uploaded_docs = {}
    results = []
    
    # Upload and process each document
    for doc_id, doc_info in TEST_DOCUMENTS.items():
        logger.info(f"Testing upload and processing for {doc_id} ({doc_info['path']})")
        
        # Read file content
        try:
            with open(doc_info['path'], 'rb') as f:
                file_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {doc_info['path']}: {str(e)}")
            continue
        
        # Upload the file
        try:
            files = {"file": (os.path.basename(doc_info['path']), file_content, doc_info['content_type'])}
            upload_response = requests.post(
                f"{BASE_URL}/api/documents/upload",
                headers=headers,
                files=files
            )
            
            if upload_response.status_code != 200:
                logger.error(f"Upload failed: {upload_response.status_code} - {upload_response.text}")
                continue
                
            upload_data = upload_response.json()
            if not upload_data.get("success"):
                logger.error(f"Upload response indicates failure: {upload_data}")
                continue
                
            document_id = upload_data.get("document_id")
            if not document_id:
                logger.error("No document_id in upload response")
                continue
                
            uploaded_docs[doc_id] = document_id
            logger.info(f"Successfully uploaded {doc_id}, document_id: {document_id}")
            
            # Process the document
            process_response = requests.post(
                f"{BASE_URL}/api/documents/process",
                headers=headers,
                json={"document_ids": [document_id]}
            )
            
            if process_response.status_code != 200:
                logger.error(f"Processing failed: {process_response.status_code} - {process_response.text}")
                continue
                
            process_data = process_response.json()
            if not process_data.get("success"):
                logger.error(f"Process response indicates failure: {process_data}")
                continue
                
            logger.info(f"Successfully processed {doc_id}")
            
            # Get document info
            info_response = requests.get(
                f"{BASE_URL}/api/documents/{document_id}",
                headers=headers
            )
            
            if info_response.status_code != 200:
                logger.error(f"Info request failed: {info_response.status_code} - {info_response.text}")
                continue
                
            doc_info_data = info_response.json()
            
            # Store results
            results.append({
                "document_id": document_id,
                "document_type": doc_info['type'],
                "filename": os.path.basename(doc_info['path']),
                "success": True,
                "chunk_count": doc_info_data.get("chunk_count", 0) if isinstance(doc_info_data, dict) else 0
            })
            
        except Exception as e:
            logger.error(f"Error in upload/processing test for {doc_id}: {str(e)}")
            results.append({
                "document_id": doc_id,
                "document_type": doc_info['type'],
                "filename": os.path.basename(doc_info['path']),
                "success": False,
                "error": str(e)
            })
    
    # Save results to file
    results_path = "test_results/api_test_upload_results.json"
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Upload and processing results saved to {os.path.abspath(results_path)}")
    
    return uploaded_docs

def test_queries(access_token, uploaded_docs):
    """
    Test queries against the uploaded documents.
    
    Args:
        access_token: Access token for authentication
        uploaded_docs: Dictionary of document IDs keyed by document type
    """
    logger.info("Testing queries...")
    
    # Set up headers with authentication token
    headers = {"Authorization": f"Bearer {access_token}"}
    
    results = []
    
    # Test each query
    for query in TEST_QUERIES:
        logger.info(f"Testing query: '{query}'")
        
        try:
            # Execute query with RAG
            query_response = requests.post(
                f"{BASE_URL}/api/chat/query",
                headers=headers,
                json={
                    "message": query,
                    "use_rag": True,
                    "stream": False
                }
            )
            
            if query_response.status_code != 200:
                logger.error(f"Query failed: {query_response.status_code} - {query_response.text}")
                continue
                
            response_data = query_response.json()
            if "message" not in response_data:
                logger.error("No message in query response")
                continue
                
            answer = response_data["message"]
            logger.info(f"Answer: {answer[:100]}...")
            
            # Store results
            results.append({
                "query": query,
                "answer": answer,
                "success": True
            })
            
        except Exception as e:
            logger.error(f"Error in query test for '{query}': {str(e)}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })
    
    # Save results to file
    results_path = "test_results/api_test_query_results.json"
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Query results saved to {os.path.abspath(results_path)}")

def cleanup_documents(access_token, uploaded_docs):
    """
    Clean up uploaded documents.
    
    Args:
        access_token: Access token for authentication
        uploaded_docs: Dictionary of document IDs keyed by document type
    """
    logger.info("Cleaning up documents...")
    
    # Set up headers with authentication token
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Delete each document
    for doc_type, doc_id in uploaded_docs.items():
        logger.info(f"Deleting document: {doc_type} (ID: {doc_id})")
        
        try:
            delete_response = requests.delete(
                f"{BASE_URL}/api/documents/{doc_id}",
                headers=headers
            )
            
            if delete_response.status_code != 200:
                logger.error(f"Delete failed: {delete_response.status_code} - {delete_response.text}")
                continue
                
            delete_data = delete_response.json()
            if not delete_data.get("success"):
                logger.error(f"Delete response indicates failure: {delete_data}")
                continue
                
            logger.info(f"Successfully deleted document: {doc_type} (ID: {doc_id})")
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_type} (ID: {doc_id}): {str(e)}")

def main():
    """Main function"""
    logger.info("Starting direct API test...")
    
    # Verify test documents
    if not verify_test_documents():
        logger.error("Test documents verification failed. Aborting test.")
        return 1
    
    # Authenticate
    access_token = authenticate()
    if not access_token:
        logger.error("Authentication failed. Aborting test.")
        return 1
    
    # Upload and process documents
    uploaded_docs = upload_and_process_documents(access_token)
    if not uploaded_docs:
        logger.error("Document upload and processing failed. Aborting test.")
        return 1
    
    # Test queries
    test_queries(access_token, uploaded_docs)
    
    # Clean up documents
    cleanup_documents(access_token, uploaded_docs)
    
    logger.info("Direct API test completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())