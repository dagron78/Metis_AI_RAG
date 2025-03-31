#!/usr/bin/env python3
"""
Test API endpoints to verify they're working correctly with database repositories
"""
import os
import sys
import json
import asyncio
import argparse
import requests
from datetime import datetime
from uuid import uuid4
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Base URL for API
BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    
    try:
        # Test health check endpoint
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Print results
        print(f"Status: {data['status']}")
        print("Components:")
        for component, info in data['components'].items():
            print(f"  {component}: {info['status']}")
        
        return True
    except Exception as e:
        print(f"Error testing health check endpoint: {e}")
        return False

def test_document_endpoints():
    """Test document API endpoints"""
    print("\n=== Testing Document API Endpoints ===")
    
    try:
        # Test list documents endpoint
        print("\nTesting list documents endpoint...")
        response = requests.get(f"{BASE_URL}/documents/list")
        response.raise_for_status()
        documents = response.json()
        print(f"Found {len(documents)} documents")
        
        # Test document upload endpoint
        print("\nTesting document upload endpoint...")
        # Create a test file
        test_file_path = os.path.join(project_root, "test_upload.txt")
        with open(test_file_path, "w") as f:
            f.write("This is a test document for API endpoint testing.")
        
        # Upload the file
        with open(test_file_path, "rb") as f:
            files = {"file": (os.path.basename(test_file_path), f)}
            data = {"tags": "test,api", "folder": "/test"}
            response = requests.post(f"{BASE_URL}/documents/upload", files=files, data=data)
        
        response.raise_for_status()
        upload_result = response.json()
        document_id = upload_result["document_id"]
        print(f"Uploaded document with ID: {document_id}")
        
        # Test get document endpoint
        print("\nTesting get document endpoint...")
        response = requests.get(f"{BASE_URL}/documents/{document_id}")
        response.raise_for_status()
        document = response.json()
        print(f"Retrieved document: {document['filename']}")
        
        # Test update document tags endpoint
        print("\nTesting update document tags endpoint...")
        tags = ["test", "api", "updated"]
        response = requests.put(
            f"{BASE_URL}/documents/{document_id}/tags",
            json={"tags": tags}
        )
        response.raise_for_status()
        tag_result = response.json()
        print(f"Updated tags: {tag_result['tags']}")
        
        # Test update document folder endpoint
        print("\nTesting update document folder endpoint...")
        folder = "/test/updated"
        response = requests.put(
            f"{BASE_URL}/documents/{document_id}/folder",
            json={"folder": folder}
        )
        response.raise_for_status()
        folder_result = response.json()
        print(f"Updated folder: {folder_result['folder']}")
        
        # Test document processing endpoint
        print("\nTesting document processing endpoint...")
        response = requests.post(
            f"{BASE_URL}/documents/process",
            json={
                "document_ids": [document_id],
                "chunking_strategy": "recursive",
                "force_reprocess": True
            }
        )
        response.raise_for_status()
        process_result = response.json()
        print(f"Processing result: {process_result['message']}")
        
        # Test filter documents endpoint
        print("\nTesting filter documents endpoint...")
        response = requests.post(
            f"{BASE_URL}/documents/filter",
            json={"tags": ["test"], "folder": "/test/updated"}
        )
        response.raise_for_status()
        filter_result = response.json()
        print(f"Found {len(filter_result)} documents matching filter")
        
        # Test get all tags endpoint
        print("\nTesting get all tags endpoint...")
        response = requests.get(f"{BASE_URL}/documents/tags")
        response.raise_for_status()
        tags_result = response.json()
        print(f"Found tags: {tags_result['tags']}")
        
        # Test get all folders endpoint
        print("\nTesting get all folders endpoint...")
        response = requests.get(f"{BASE_URL}/documents/folders")
        response.raise_for_status()
        folders_result = response.json()
        print(f"Found folders: {folders_result['folders']}")
        
        # Test delete document endpoint
        print("\nTesting delete document endpoint...")
        response = requests.delete(f"{BASE_URL}/documents/{document_id}")
        response.raise_for_status()
        delete_result = response.json()
        print(f"Delete result: {delete_result['message']}")
        
        # Clean up test file
        os.remove(test_file_path)
        
        return True
    except Exception as e:
        print(f"Error testing document endpoints: {e}")
        return False

def test_chat_endpoints():
    """Test chat API endpoints"""
    print("\n=== Testing Chat API Endpoints ===")
    
    try:
        # Test chat query endpoint
        print("\nTesting chat query endpoint...")
        query = {
            "message": "What is RAG?",
            "conversation_id": None,
            "user_id": "test_user",
            "model": None,
            "use_rag": True,
            "stream": False
        }
        response = requests.post(f"{BASE_URL}/chat/query", json=query)
        response.raise_for_status()
        query_result = response.json()
        conversation_id = query_result["conversation_id"]
        print(f"Created conversation with ID: {conversation_id}")
        print(f"Response: {query_result['message'][:100]}...")
        
        # Test get conversation history endpoint
        print("\nTesting get conversation history endpoint...")
        response = requests.get(f"{BASE_URL}/chat/history?conversation_id={conversation_id}")
        response.raise_for_status()
        history_result = response.json()
        print(f"Found {len(history_result['messages'])} messages in conversation")
        
        # Test list conversations endpoint
        print("\nTesting list conversations endpoint...")
        response = requests.get(f"{BASE_URL}/chat/list?user_id=test_user")
        response.raise_for_status()
        list_result = response.json()
        print(f"Found {len(list_result['conversations'])} conversations for user")
        
        # Test save conversation endpoint
        print("\nTesting save conversation endpoint...")
        response = requests.post(f"{BASE_URL}/chat/save?conversation_id={conversation_id}")
        response.raise_for_status()
        save_result = response.json()
        print(f"Save result: {save_result['message']}")
        
        # Test clear conversation endpoint
        print("\nTesting clear conversation endpoint...")
        response = requests.delete(f"{BASE_URL}/chat/clear?conversation_id={conversation_id}")
        response.raise_for_status()
        clear_result = response.json()
        print(f"Clear result: {clear_result['message']}")
        
        return True
    except Exception as e:
        print(f"Error testing chat endpoints: {e}")
        return False

def test_analytics_endpoints():
    """Test analytics API endpoints"""
    print("\n=== Testing Analytics API Endpoints ===")
    
    try:
        # Test record query endpoint
        print("\nTesting record query endpoint...")
        query_data = {
            "query": "Test query for analytics",
            "model": "test_model",
            "use_rag": True,
            "response_time_ms": 500,
            "token_count": 100,
            "document_ids": [str(uuid4())],
            "query_type": "test",
            "successful": True
        }
        response = requests.post(f"{BASE_URL}/analytics/record_query", json=query_data)
        response.raise_for_status()
        record_result = response.json()
        print(f"Record result: {record_result['message']}")
        
        # Test query stats endpoint
        print("\nTesting query stats endpoint...")
        response = requests.get(f"{BASE_URL}/analytics/query_stats?time_period=all")
        response.raise_for_status()
        stats_result = response.json()
        print(f"Query count: {stats_result['query_count']}")
        print(f"Average response time: {stats_result['avg_response_time_ms']} ms")
        
        # Test document usage endpoint
        print("\nTesting document usage endpoint...")
        response = requests.get(f"{BASE_URL}/analytics/document_usage?time_period=all")
        response.raise_for_status()
        usage_result = response.json()
        print(f"Document count: {usage_result['document_count']}")
        
        # Test system stats endpoint
        print("\nTesting system stats endpoint...")
        response = requests.get(f"{BASE_URL}/analytics/system_stats")
        response.raise_for_status()
        system_result = response.json()
        print(f"Document count: {system_result['document_count']}")
        print(f"Query count: {system_result['query_count']}")
        
        # Test model performance endpoint
        print("\nTesting model performance endpoint...")
        response = requests.get(f"{BASE_URL}/analytics/model_performance?time_period=all")
        response.raise_for_status()
        model_result = response.json()
        print(f"Found {len(model_result['models'])} models")
        
        # Test query types endpoint
        print("\nTesting query types endpoint...")
        response = requests.get(f"{BASE_URL}/analytics/query_types?time_period=all")
        response.raise_for_status()
        types_result = response.json()
        print(f"Found {len(types_result['query_types'])} query types")
        
        return True
    except Exception as e:
        print(f"Error testing analytics endpoints: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test API endpoints")
    parser.add_argument("--health", action="store_true", help="Test health check endpoint only")
    parser.add_argument("--documents", action="store_true", help="Test document endpoints only")
    parser.add_argument("--chat", action="store_true", help="Test chat endpoints only")
    parser.add_argument("--analytics", action="store_true", help="Test analytics endpoints only")
    args = parser.parse_args()
    
    # If no specific tests are requested, run all tests
    run_all = not (args.health or args.documents or args.chat or args.analytics)
    
    results = {}
    
    # Test health check endpoint
    if run_all or args.health:
        results["health"] = test_health_endpoint()
    
    # Test document endpoints
    if run_all or args.documents:
        results["documents"] = test_document_endpoints()
    
    # Test chat endpoints
    if run_all or args.chat:
        results["chat"] = test_chat_endpoints()
    
    # Test analytics endpoints
    if run_all or args.analytics:
        results["analytics"] = test_analytics_endpoints()
    
    # Print summary
    print("\n=== Test Summary ===")
    all_passed = True
    for test, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{test}: {status}")
        all_passed = all_passed and passed
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())