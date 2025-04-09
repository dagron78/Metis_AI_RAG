#!/usr/bin/env python3
"""
End-to-End test for the Metis RAG system.
This test evaluates the complete pipeline from document upload to query response.
"""

import os
import sys
import json
import asyncio
import logging
import uuid
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_metis_rag_e2e")

import os
from unittest import mock

# Set environment variables for testing
os.environ["CHROMA_DB_DIR"] = "test_e2e_chroma"
os.environ["CACHE_DIR"] = "data/test_cache"

# Import RAG components
from app.main import app
from app.rag.document_processor import DocumentProcessor
from app.models.document import Document, Chunk

# Test client
client = TestClient(app)

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

# Test queries with expected facts to be present in responses
SINGLE_DOC_QUERIES = [
    {
        "query": "What are the specifications of the SmartHome Hub?",
        "expected_facts": [
            "ARM Cortex-A53",
            "quad-core",
            "1.4GHz",
            "2GB RAM",
            "16GB eMMC",
            "Wi-Fi",
            "Bluetooth 5.0",
            "Zigbee 3.0",
            "Z-Wave",
            "5V DC"
        ],
        "target_docs": ["technical_specs"]
    },
    {
        "query": "How do I troubleshoot when devices won't connect?",
        "expected_facts": [
            "within range",
            "30-50 feet",
            "pairing mode",
            "compatible with SmartHome"
        ],
        "target_docs": ["user_guide"]
    },
    {
        "query": "What is the battery life of the motion sensor?",
        "expected_facts": [
            "Motion Sensor",
            "SH-MS100",
            "2 years"
        ],
        "target_docs": ["device_comparison"]
    },
    {
        "query": "How do I authenticate with the SmartHome API?",
        "expected_facts": [
            "OAuth 2.0",
            "access token",
            "Developer Portal",
            "authorization code"
        ],
        "target_docs": ["developer_reference"]
    }
]

MULTI_DOC_QUERIES = [
    {
        "query": "Compare the Motion Sensor and Door Sensor specifications and setup process.",
        "expected_facts": [
            "SH-MS100",
            "SH-DS100",
            "Zigbee",
            "2 years",
            "pairing mode",
            "Add Device"
        ],
        "target_docs": ["device_comparison", "user_guide"]
    },
    {
        "query": "Explain how to integrate a motion sensor with a third-party application.",
        "expected_facts": [
            "API",
            "webhook",
            "OAuth",
            "motion.active",
            "real-time updates",
            "WebSocket"
        ],
        "target_docs": ["developer_reference", "device_comparison"]
    },
    {
        "query": "What security features does the SmartHome system provide for both users and developers?",
        "expected_facts": [
            "End-to-end encryption",
            "AES-256",
            "Certificate-based",
            "OAuth 2.0",
            "webhook signature",
            "HMAC"
        ],
        "target_docs": ["technical_specs", "developer_reference"]
    }
]

COMPLEX_QUERIES = [
    {
        "query": "Which devices require the hub and what protocols do they use?",
        "expected_facts": [
            "Hub Required",
            "Yes",
            "Zigbee",
            "Z-Wave",
            "SHC",
            "RF"
        ],
        "target_docs": ["device_comparison", "technical_specs"]
    },
    {
        "query": "If I want to create a water leak detection system, which devices should I use and how would I set them up?",
        "expected_facts": [
            "Leak Detector",
            "SH-LD100",
            "Water Valve Controller",
            "SH-WV100",
            "Add Device",
            "pairing mode",
            "automation"
        ],
        "target_docs": ["device_comparison", "user_guide", "developer_reference"]
    },
    {
        "query": "What's the difference between Zigbee and Z-Wave devices in the SmartHome ecosystem?",
        "expected_facts": [
            "Zigbee",
            "Z-Wave",
            "range",
            "protocol",
            "devices"
        ],
        "target_docs": ["technical_specs", "device_comparison"]
    }
]

def authenticate_client():
    """Authenticate the test client"""
    logger.info("Authenticating test client...")
    
    # Create a unique test user for this test run
    import uuid
    import requests
    
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    test_password = "testpassword"
    base_url = "http://localhost:8000"
    
    # Use direct requests for authentication
    try:
        # Register the new test user
        logger.info(f"Registering new test user: {test_username}")
        register_response = requests.post(
            f"{base_url}/api/auth/register",
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
            return False
            
        logger.info(f"User {test_username} registered successfully")
        
        # Authenticate with the new user
        login_response = requests.post(
            f"{base_url}/api/auth/token",
            data={
                "username": test_username,
                "password": test_password,
                "grant_type": "password"
            }
        )
        
        if login_response.status_code != 200:
            logger.error(f"Login failed: {login_response.status_code} - {login_response.text}")
            return False
            
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error("No access token in response")
            return False
        
        logger.info(f"Successfully obtained token: {access_token[:10]}...")
            
        # Set the token in the client's headers for subsequent requests
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        
        # Verify authentication
        verify_response = client.get("/api/auth/me")
        if verify_response.status_code == 200:
            logger.info(f"Successfully authenticated as {test_username}")
            return True
        else:
            logger.error(f"Authentication verification failed: {verify_response.status_code} - {verify_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
    
    # If we get here, authentication failed
    logger.warning("Authentication failed. Tests may not work correctly.")
    return False

def verify_test_documents():
    """Verify that all test documents exist"""
    missing_docs = []
    for doc_id, doc_info in TEST_DOCUMENTS.items():
        if not os.path.exists(doc_info["path"]):
            missing_docs.append(doc_info["path"])
    
    if missing_docs:
        logger.error(f"Missing test documents: {', '.join(missing_docs)}")
        logger.error("Please ensure all test documents are created before running the test.")
        pytest.fail(f"Missing test documents: {', '.join(missing_docs)}")
    else:
        logger.info("All test documents verified.")

def test_document_upload_and_processing():
    """Test uploading and processing of all document types"""
    # First verify all test documents exist
    verify_test_documents()
    
    # Authenticate the client
    authenticate_client()
    
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
            pytest.fail(f"Failed to read file {doc_info['path']}: {str(e)}")
        
        # Create file-like object for upload
        file_obj = BytesIO(file_content)
        file_obj.name = os.path.basename(doc_info['path'])
        
        # Upload the file
        try:
            upload_response = client.post(
                "/api/documents/upload",
                files={"file": (file_obj.name, file_obj, doc_info['content_type'])}
            )
            
            # Check upload response
            assert upload_response.status_code == 200, f"Upload failed with status {upload_response.status_code}: {upload_response.text}"
            upload_data = upload_response.json()
            assert upload_data["success"] is True, f"Upload response indicates failure: {upload_data}"
            assert "document_id" in upload_data, "No document_id in upload response"
            
            document_id = upload_data["document_id"]
            uploaded_docs[doc_id] = document_id
            
            logger.info(f"Successfully uploaded {doc_id}, document_id: {document_id}")
            
            # Process the document
            process_response = client.post(
                "/api/documents/process",
                json={"document_ids": [document_id]}
            )
            
            # Check process response
            assert process_response.status_code == 200, f"Processing failed with status {process_response.status_code}: {process_response.text}"
            process_data = process_response.json()
            assert process_data["success"] is True, f"Process response indicates failure: {process_data}"
            
            logger.info(f"Successfully processed {doc_id}")
            
            # Get document info
            info_response = client.get(f"/api/documents/{document_id}")
            
            # Check info response
            assert info_response.status_code == 200, f"Info request failed with status {info_response.status_code}: {info_response.text}"
            doc_info_data = info_response.json()
            
            # Store results
            results.append({
                "document_id": document_id,
                "document_type": doc_info['type'],
                "filename": file_obj.name,
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
            pytest.fail(f"Error in upload/processing test for {doc_id}: {str(e)}")
    
    # Save results to file
    results_path = "test_e2e_upload_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Upload and processing results saved to {os.path.abspath(results_path)}")
    
    # Return the uploaded document IDs for further tests
    return uploaded_docs

def test_single_document_queries():
    """Test queries that target a single document"""
    # Get document IDs from the upload test
    uploaded_docs = test_document_upload_and_processing()
    
    results = []
    
    for test_case in SINGLE_DOC_QUERIES:
        query = test_case["query"]
        expected_facts = test_case["expected_facts"]
        
        logger.info(f"Testing single-document query: '{query}'")
        
        # Execute query with RAG
        response = client.post(
            "/api/chat/query",
            json={
                "message": query,
                "use_rag": True,
                "stream": False
            }
        )
        
        # Check query response
        assert response.status_code == 200, f"Query failed with status {response.status_code}: {response.text}"
        response_data = response.json()
        assert "message" in response_data, "No message in query response"
        
        answer = response_data["message"]
        logger.info(f"Answer: {answer[:100]}...")
        
        # Check if response contains expected facts
        fact_count = sum(1 for fact in expected_facts if fact.lower() in answer.lower())
        fact_percentage = (fact_count / len(expected_facts)) * 100
        
        logger.info(f"Facts found: {fact_count}/{len(expected_facts)} ({fact_percentage:.1f}%)")
        
        # Store results
        results.append({
            "query": query,
            "answer": answer,
            "expected_facts": expected_facts,
            "facts_found": fact_count,
            "fact_percentage": fact_percentage,
            "success": fact_percentage >= 70  # Consider successful if at least 70% of facts are found
        })
        
        # Assert minimum factual accuracy
        assert fact_percentage >= 70, f"Query '{query}' has low factual accuracy: {fact_percentage:.1f}%"
    
    # Save results to file
    results_path = "test_e2e_single_doc_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Single document query results saved to {os.path.abspath(results_path)}")

def test_multi_document_queries():
    """Test queries that require information from multiple documents"""
    # Get document IDs from the upload test
    uploaded_docs = test_document_upload_and_processing()
    
    results = []
    
    for test_case in MULTI_DOC_QUERIES:
        query = test_case["query"]
        expected_facts = test_case["expected_facts"]
        
        logger.info(f"Testing multi-document query: '{query}'")
        
        # Execute query with RAG
        response = client.post(
            "/api/chat/query",
            json={
                "message": query,
                "use_rag": True,
                "stream": False
            }
        )
        
        # Check query response
        assert response.status_code == 200, f"Query failed with status {response.status_code}: {response.text}"
        response_data = response.json()
        assert "message" in response_data, "No message in query response"
        
        answer = response_data["message"]
        logger.info(f"Answer: {answer[:100]}...")
        
        # Check if response contains expected facts
        fact_count = sum(1 for fact in expected_facts if fact.lower() in answer.lower())
        fact_percentage = (fact_count / len(expected_facts)) * 100
        
        logger.info(f"Facts found: {fact_count}/{len(expected_facts)} ({fact_percentage:.1f}%)")
        
        # Store results
        results.append({
            "query": query,
            "answer": answer,
            "expected_facts": expected_facts,
            "facts_found": fact_count,
            "fact_percentage": fact_percentage,
            "success": fact_percentage >= 60  # Consider successful if at least 60% of facts are found (multi-doc is harder)
        })
        
        # Assert minimum factual accuracy
        assert fact_percentage >= 60, f"Query '{query}' has low factual accuracy: {fact_percentage:.1f}%"
    
    # Save results to file
    results_path = "test_e2e_multi_doc_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Multi-document query results saved to {os.path.abspath(results_path)}")

def test_complex_queries():
    """Test complex queries requiring synthesis and analysis"""
    # Get document IDs from the upload test
    uploaded_docs = test_document_upload_and_processing()
    
    results = []
    
    for test_case in COMPLEX_QUERIES:
        query = test_case["query"]
        expected_facts = test_case["expected_facts"]
        
        logger.info(f"Testing complex query: '{query}'")
        
        # Execute query with RAG
        response = client.post(
            "/api/chat/query",
            json={
                "message": query,
                "use_rag": True,
                "stream": False,
                "enable_query_refinement": True  # Enable query refinement for complex queries
            }
        )
        
        # Check query response
        assert response.status_code == 200, f"Query failed with status {response.status_code}: {response.text}"
        response_data = response.json()
        assert "message" in response_data, "No message in query response"
        
        answer = response_data["message"]
        logger.info(f"Answer: {answer[:100]}...")
        
        # Check if response contains expected facts
        fact_count = sum(1 for fact in expected_facts if fact.lower() in answer.lower())
        fact_percentage = (fact_count / len(expected_facts)) * 100
        
        logger.info(f"Facts found: {fact_count}/{len(expected_facts)} ({fact_percentage:.1f}%)")
        
        # Store results
        results.append({
            "query": query,
            "answer": answer,
            "expected_facts": expected_facts,
            "facts_found": fact_count,
            "fact_percentage": fact_percentage,
            "success": fact_percentage >= 60  # Consider successful if at least 60% of facts are found
        })
        
        # Assert minimum factual accuracy
        assert fact_percentage >= 60, f"Query '{query}' has low factual accuracy: {fact_percentage:.1f}%"
    
    # Save results to file
    results_path = "test_e2e_complex_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Complex query results saved to {os.path.abspath(results_path)}")

def test_citation_quality():
    """Test quality of citations in RAG responses"""
    # Get document IDs from the upload test
    uploaded_docs = test_document_upload_and_processing()
    
    # Combine all query types for citation testing
    all_queries = SINGLE_DOC_QUERIES + MULTI_DOC_QUERIES + COMPLEX_QUERIES
    
    results = []
    
    for test_case in all_queries[:3]:  # Test a subset for efficiency
        query = test_case["query"]
        
        logger.info(f"Testing citation quality for query: '{query}'")
        
        # Execute query with RAG
        response = client.post(
            "/api/chat/query",
            json={
                "message": query,
                "use_rag": True,
                "stream": False
            }
        )
        
        # Check query response
        assert response.status_code == 200, f"Query failed with status {response.status_code}: {response.text}"
        response_data = response.json()
        assert "message" in response_data, "No message in query response"
        
        answer = response_data["message"]
        
        # Check for citation markers
        has_citation_markers = "[" in answer and "]" in answer
        
        # Count citations
        citation_count = 0
        for i in range(1, 10):  # Check for citation markers [1] through [9]
            if f"[{i}]" in answer:
                citation_count += 1
        
        logger.info(f"Has citation markers: {has_citation_markers}, Citation count: {citation_count}")
        
        # Store results
        results.append({
            "query": query,
            "answer": answer,
            "has_citation_markers": has_citation_markers,
            "citation_count": citation_count,
            "success": has_citation_markers and citation_count > 0
        })
        
        # Assert citation quality
        assert has_citation_markers, f"Query '{query}' response lacks citation markers"
        assert citation_count > 0, f"Query '{query}' response has no citations"
    
    # Save results to file
    results_path = "test_e2e_citation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Citation quality results saved to {os.path.abspath(results_path)}")

def test_system_performance():
    """Test performance metrics of the RAG system"""
    # Get document IDs from the upload test
    uploaded_docs = test_document_upload_and_processing()
    
    results = []
    
    # Test query performance
    sample_queries = [
        SINGLE_DOC_QUERIES[0]["query"],
        MULTI_DOC_QUERIES[0]["query"],
        COMPLEX_QUERIES[0]["query"]
    ]
    
    for query in sample_queries:
        logger.info(f"Testing performance for query: '{query}'")
        
        # Measure response time
        start_time = time.time()
        
        response = client.post(
            "/api/chat/query",
            json={
                "message": query,
                "use_rag": True,
                "stream": False
            }
        )
        
        response_time = time.time() - start_time
        
        # Check query response
        assert response.status_code == 200, f"Query failed with status {response.status_code}: {response.text}"
        response_data = response.json()
        
        logger.info(f"Response time: {response_time:.2f} seconds")
        
        # Store results
        results.append({
            "query": query,
            "response_time_seconds": response_time,
            "success": response_time < 10  # Consider successful if response time is under 10 seconds
        })
        
        # Assert reasonable performance
        assert response_time < 10, f"Query '{query}' has slow response time: {response_time:.2f} seconds"
    
    # Save results to file
    results_path = "test_e2e_performance_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Performance test results saved to {os.path.abspath(results_path)}")

def test_end_to_end_cleanup():
    """Clean up test documents and generate final report"""
    # Get document IDs from the upload test
    uploaded_docs = test_document_upload_and_processing()
    
    # Clean up all test documents
    for doc_type, doc_id in uploaded_docs.items():
        logger.info(f"Cleaning up document: {doc_type} (ID: {doc_id})")
        
        try:
            delete_response = client.delete(f"/api/documents/{doc_id}")
            assert delete_response.status_code == 200, f"Delete failed with status {delete_response.status_code}: {delete_response.text}"
            
            delete_data = delete_response.json()
            assert delete_data["success"] is True, f"Delete response indicates failure: {delete_data}"
            
            logger.info(f"Successfully deleted document: {doc_type} (ID: {doc_id})")
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_type} (ID: {doc_id}): {str(e)}")
            pytest.fail(f"Error deleting document {doc_type} (ID: {doc_id}): {str(e)}")
    
    # Collect all results files
    result_files = [
        "test_e2e_upload_results.json",
        "test_e2e_single_doc_results.json",
        "test_e2e_multi_doc_results.json",
        "test_e2e_complex_results.json",
        "test_e2e_citation_results.json",
        "test_e2e_performance_results.json"
    ]
    
    # Combine results into a single report
    all_results = {}
    
    for file_path in result_files:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                results = json.load(f)
            
            test_name = file_path.replace("test_e2e_", "").replace("_results.json", "")
            all_results[test_name] = results
    
    # Save comprehensive report
    report_path = "test_e2e_comprehensive_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "test_name": "Metis RAG End-to-End Test",
            "timestamp": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)
    
    logger.info(f"End-to-end test complete. Comprehensive report saved to {os.path.abspath(report_path)}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])