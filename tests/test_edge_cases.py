#!/usr/bin/env python3
"""
Edge case test suite for the Metis RAG system.
This test suite focuses on unusual inputs, error handling, and system resilience.
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
import random
import string
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_edge_cases")

# Import RAG components
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.document_processor import DocumentProcessor
from app.models.document import Document, Chunk
from app.models.chat import ChatQuery
from app.main import app

# Test client
client = TestClient(app)

# Helper functions
def generate_random_string(length):
    """Generate a random string of specified length"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def generate_binary_file(size_kb):
    """Generate a binary file of specified size in KB"""
    return os.urandom(size_kb * 1024)

@pytest.fixture
def test_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp(prefix="metis_rag_edge_")
    yield temp_dir
    # Clean up
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_empty_document():
    """Test handling of empty documents"""
    # Create an empty document
    empty_doc = Document(
        id=str(uuid.uuid4()),
        filename="empty.txt",
        content=""
    )
    
    # Process the document
    processor = DocumentProcessor()
    
    try:
        processed_doc = await processor.process_document(empty_doc)
        
        # Check if processing succeeded
        assert len(processed_doc.chunks) == 0, "Empty document should result in no chunks"
        logger.info("Empty document processed successfully with 0 chunks")
        
    except Exception as e:
        # Check if the error is handled gracefully
        logger.info(f"Empty document processing resulted in error: {str(e)}")
        assert False, f"Empty document should be handled gracefully, but got error: {str(e)}"

@pytest.mark.asyncio
async def test_very_long_document(test_dir):
    """Test handling of very long documents"""
    # Create a very long document (10 MB)
    file_path = os.path.join(test_dir, "very_long.txt")
    content = generate_random_string(10 * 1024 * 1024 // 10)  # 10 MB of text (approximated)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    # Create document object
    long_doc = Document(
        id=str(uuid.uuid4()),
        filename="very_long.txt",
        content=content
    )
    
    # Process the document
    processor = DocumentProcessor()
    
    try:
        processed_doc = await processor.process_document(long_doc)
        
        # Check if processing succeeded
        assert len(processed_doc.chunks) > 0, "Long document should be chunked"
        logger.info(f"Very long document processed successfully with {len(processed_doc.chunks)} chunks")
        
    except Exception as e:
        # Check if the error is handled gracefully
        logger.info(f"Very long document processing resulted in error: {str(e)}")
        assert False, f"Very long document should be handled gracefully, but got error: {str(e)}"

@pytest.mark.asyncio
async def test_malformed_document(test_dir):
    """Test handling of malformed documents"""
    # Create a malformed document (binary data with text extension)
    file_path = os.path.join(test_dir, "malformed.txt")
    content = generate_binary_file(10)  # 10 KB of binary data
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Try to upload the malformed document via API
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("malformed.txt", f, "text/plain")}
        )
    
    # Check if the API handles the malformed document gracefully
    logger.info(f"Malformed document upload response: {response.status_code}")
    logger.info(f"Response content: {response.content}")
    
    # The API should either accept the file (status 200) or reject it with a clear error
    if response.status_code == 200:
        # If accepted, try to process it
        upload_data = response.json()
        document_id = upload_data["document_id"]
        
        process_response = client.post(
            "/api/documents/process",
            json={"document_ids": [document_id]}
        )
        
        logger.info(f"Malformed document processing response: {process_response.status_code}")
        logger.info(f"Process response content: {process_response.content}")
        
        # Clean up
        client.delete(f"/api/documents/{document_id}")
    
    # We don't assert specific behavior here, just log what happens
    # The important thing is that the system doesn't crash

@pytest.mark.asyncio
async def test_very_long_query():
    """Test handling of very long queries"""
    # Create a very long query (10 KB)
    long_query = generate_random_string(10 * 1024)
    
    # Try to query the system
    response = client.post(
        "/api/chat/query",
        json={
            "message": long_query,
            "use_rag": True,
            "stream": False
        }
    )
    
    # Check if the API handles the long query gracefully
    logger.info(f"Very long query response: {response.status_code}")
    
    # The API should either process the query or reject it with a clear error
    assert response.status_code in [200, 400, 422], f"Unexpected status code: {response.status_code}"
    
    if response.status_code == 200:
        logger.info("Very long query was processed successfully")
    else:
        logger.info(f"Very long query was rejected with status {response.status_code}")
        logger.info(f"Response content: {response.content}")

@pytest.mark.asyncio
async def test_special_characters_query():
    """Test handling of queries with special characters"""
    # Create queries with special characters
    special_queries = [
        "What is RAG? <script>alert('XSS')</script>",
        "SELECT * FROM documents WHERE content LIKE '%secret%'",
        "curl -X POST http://example.com --data 'payload'",
        "Document\0with\0null\0bytes",
        "Multi\nline\nquery\nwith\nnewlines",
        "Query with emoji 🔍 and Unicode characters 你好",
        "Query with control characters \x01\x02\x03\x04\x05"
    ]
    
    results = []
    
    for query in special_queries:
        # Try to query the system
        response = client.post(
            "/api/chat/query",
            json={
                "message": query,
                "use_rag": True,
                "stream": False
            }
        )
        
        # Check if the API handles the special query gracefully
        logger.info(f"Special query '{query[:20]}...' response: {response.status_code}")
        
        # Store results
        results.append({
            "query": query,
            "status_code": response.status_code,
            "success": response.status_code == 200
        })
        
        # The API should either process the query or reject it with a clear error
        assert response.status_code in [200, 400, 422], f"Unexpected status code: {response.status_code}"
    
    # Save results to file
    results_path = "test_special_queries_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Special queries test results saved to {os.path.abspath(results_path)}")

@pytest.mark.asyncio
async def test_network_failure():
    """Test handling of network failures when communicating with Ollama"""
    # Create a mock RAG engine with a failing Ollama client
    ollama_client = AsyncMock()
    ollama_client.generate.side_effect = Exception("Simulated network failure")
    
    rag_engine = RAGEngine(
        ollama_client=ollama_client,
        vector_store=AsyncMock()
    )
    
    # Try to query the RAG engine
    try:
        response = await rag_engine.query(
            query="Test query",
            use_rag=False,  # Disable RAG to focus on Ollama failure
            stream=False
        )
        
        # Check if the error is handled gracefully
        logger.info(f"Network failure response: {response}")
        assert "error" in response, "Network failure should result in an error response"
        
    except Exception as e:
        # If an exception is raised, the error wasn't handled gracefully
        logger.error(f"Network failure resulted in unhandled exception: {str(e)}")
        assert False, f"Network failure should be handled gracefully, but got exception: {str(e)}"

@pytest.mark.asyncio
async def test_invalid_model():
    """Test handling of invalid model name"""
    # Try to query with an invalid model name
    response = client.post(
        "/api/chat/query",
        json={
            "message": "Test query",
            "model": "non_existent_model_12345",
            "use_rag": False,
            "stream": False
        }
    )
    
    # Check if the API handles the invalid model gracefully
    logger.info(f"Invalid model response: {response.status_code}")
    logger.info(f"Response content: {response.content}")
    
    # The API should either fall back to a default model or return a clear error
    assert response.status_code in [200, 400, 422], f"Unexpected status code: {response.status_code}"

@pytest.mark.asyncio
async def test_concurrent_document_processing():
    """Test handling of concurrent document processing requests"""
    # Create multiple small documents
    document_count = 5
    document_ids = []
    
    for i in range(document_count):
        # Create a small document
        content = f"Test document {i}\n" * 100
        
        # Upload the document
        file_obj = BytesIO(content.encode())
        file_obj.name = f"concurrent_test_{i}.txt"
        
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": (file_obj.name, file_obj, "text/plain")}
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_ids.append(upload_data["document_id"])
    
    # Process documents concurrently
    async def process_document(doc_id):
        process_response = client.post(
            "/api/documents/process",
            json={"document_ids": [doc_id]}
        )
        return {
            "document_id": doc_id,
            "status_code": process_response.status_code,
            "success": process_response.status_code == 200
        }
    
    # Create tasks for concurrent processing
    tasks = [process_document(doc_id) for doc_id in document_ids]
    
    # Execute tasks concurrently
    results = await asyncio.gather(*tasks)
    
    # Check results
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Concurrent processing results: {success_count}/{len(results)} successful")
    
    # Clean up
    for doc_id in document_ids:
        client.delete(f"/api/documents/{doc_id}")
    
    # Save results to file
    results_path = "test_concurrent_processing_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Concurrent processing test results saved to {os.path.abspath(results_path)}")
    
    # Assert that at least some documents were processed successfully
    assert success_count > 0, "No documents were processed successfully"

@pytest.mark.asyncio
async def test_invalid_file_types():
    """Test handling of invalid file types"""
    invalid_files = [
        ("executable.exe", generate_binary_file(10), "application/octet-stream"),
        ("image.jpg", generate_binary_file(10), "image/jpeg"),
        ("archive.zip", generate_binary_file(10), "application/zip"),
        ("empty.txt", b"", "text/plain")
    ]
    
    results = []
    
    for filename, content, content_type in invalid_files:
        # Try to upload the invalid file
        file_obj = BytesIO(content)
        file_obj.name = filename
        
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": (filename, file_obj, content_type)}
        )
        
        # Check if the API handles the invalid file gracefully
        logger.info(f"Invalid file '{filename}' upload response: {upload_response.status_code}")
        
        # Store results
        result = {
            "filename": filename,
            "content_type": content_type,
            "status_code": upload_response.status_code,
            "accepted": upload_response.status_code == 200
        }
        
        # If the file was accepted, try to process it
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            document_id = upload_data["document_id"]
            
            process_response = client.post(
                "/api/documents/process",
                json={"document_ids": [document_id]}
            )
            
            result["process_status_code"] = process_response.status_code
            result["process_success"] = process_response.status_code == 200
            
            # Clean up
            client.delete(f"/api/documents/{document_id}")
        
        results.append(result)
    
    # Save results to file
    results_path = "test_invalid_files_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Invalid file types test results saved to {os.path.abspath(results_path)}")

@pytest.mark.asyncio
async def test_malformed_requests():
    """Test handling of malformed API requests"""
    malformed_requests = [
        # Missing required fields
        {"endpoint": "/api/chat/query", "data": {}, "method": "POST"},
        # Invalid data types
        {"endpoint": "/api/chat/query", "data": {"message": 123, "use_rag": "yes"}, "method": "POST"},
        # Extra fields
        {"endpoint": "/api/chat/query", "data": {"message": "Test", "invalid_field": "value"}, "method": "POST"},
        # Invalid JSON
        {"endpoint": "/api/documents/process", "data": "not_json", "method": "POST"},
        # Invalid HTTP method
        {"endpoint": "/api/documents/upload", "data": {}, "method": "PUT"}
    ]
    
    results = []
    
    for req in malformed_requests:
        # Try to make the malformed request
        try:
            if req["method"] == "POST":
                if req["data"] == "not_json":
                    # Send invalid JSON
                    response = client.post(
                        req["endpoint"],
                        data="not_json",
                        headers={"Content-Type": "application/json"}
                    )
                else:
                    # Send normal JSON
                    response = client.post(req["endpoint"], json=req["data"])
            elif req["method"] == "PUT":
                response = client.put(req["endpoint"], json=req["data"])
            else:
                response = client.get(req["endpoint"])
            
            # Check if the API handles the malformed request gracefully
            logger.info(f"Malformed request to {req['endpoint']} response: {response.status_code}")
            
            # Store results
            results.append({
                "endpoint": req["endpoint"],
                "method": req["method"],
                "data": str(req["data"]),
                "status_code": response.status_code,
                "is_error": response.status_code >= 400
            })
            
            # The API should return an error for malformed requests
            assert response.status_code >= 400, f"Malformed request should return error, got {response.status_code}"
            
        except Exception as e:
            # If an exception is raised, the error wasn't handled gracefully
            logger.error(f"Malformed request resulted in unhandled exception: {str(e)}")
            results.append({
                "endpoint": req["endpoint"],
                "method": req["method"],
                "data": str(req["data"]),
                "exception": str(e),
                "is_error": True
            })
    
    # Save results to file
    results_path = "test_malformed_requests_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Malformed requests test results saved to {os.path.abspath(results_path)}")

@pytest.mark.asyncio
async def test_vector_store_resilience():
    """Test vector store resilience to invalid operations"""
    # Create a vector store
    vector_store = VectorStore()
    
    # Test operations that might cause issues
    edge_cases = [
        # Search with empty query
        {"operation": "search", "args": {"query": ""}},
        # Search with very long query
        {"operation": "search", "args": {"query": generate_random_string(10000)}},
        # Search with invalid filter
        {"operation": "search", "args": {"query": "test", "filter_criteria": {"invalid": "filter"}}},
        # Delete non-existent document
        {"operation": "delete", "args": {"document_id": "non_existent_id"}},
        # Update metadata for non-existent document
        {"operation": "update_metadata", "args": {"document_id": "non_existent_id", "metadata_update": {"tag": "value"}}}
    ]
    
    results = []
    
    for case in edge_cases:
        try:
            if case["operation"] == "search":
                await vector_store.search(**case["args"])
            elif case["operation"] == "delete":
                vector_store.delete_document(**case["args"])
            elif case["operation"] == "update_metadata":
                await vector_store.update_document_metadata(**case["args"])
            
            # If we get here, the operation didn't raise an exception
            logger.info(f"Vector store {case['operation']} succeeded with args: {case['args']}")
            results.append({
                "operation": case["operation"],
                "args": str(case["args"]),
                "success": True
            })
            
        except Exception as e:
            # The operation raised an exception
            logger.info(f"Vector store {case['operation']} failed with args: {case['args']}, error: {str(e)}")
            results.append({
                "operation": case["operation"],
                "args": str(case["args"]),
                "success": False,
                "error": str(e)
            })
    
    # Save results to file
    results_path = "test_vector_store_resilience_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Vector store resilience test results saved to {os.path.abspath(results_path)}")

@pytest.mark.asyncio
async def test_generate_edge_case_report():
    """Generate a comprehensive edge case test report"""
    # Check if all result files exist
    result_files = [
        "test_special_queries_results.json",
        "test_concurrent_processing_results.json",
        "test_invalid_files_results.json",
        "test_malformed_requests_results.json",
        "test_vector_store_resilience_results.json"
    ]
    
    missing_files = [f for f in result_files if not os.path.exists(f)]
    
    if missing_files:
        logger.warning(f"Missing result files: {missing_files}")
        logger.warning("Run the individual edge case tests first")
        return
    
    # Load all results
    results = {}
    
    for file_path in result_files:
        with open(file_path, "r") as f:
            results[file_path] = json.load(f)
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "special_queries": {
                "total": len(results["test_special_queries_results.json"]),
                "success": sum(1 for r in results["test_special_queries_results.json"] if r["success"])
            },
            "concurrent_processing": {
                "total": len(results["test_concurrent_processing_results.json"]),
                "success": sum(1 for r in results["test_concurrent_processing_results.json"] if r["success"])
            },
            "invalid_files": {
                "total": len(results["test_invalid_files_results.json"]),
                "accepted": sum(1 for r in results["test_invalid_files_results.json"] if r["accepted"]),
                "processed": sum(1 for r in results["test_invalid_files_results.json"] if r.get("process_success", False))
            },
            "malformed_requests": {
                "total": len(results["test_malformed_requests_results.json"]),
                "error_responses": sum(1 for r in results["test_malformed_requests_results.json"] if r["is_error"])
            },
            "vector_store_resilience": {
                "total": len(results["test_vector_store_resilience_results.json"]),
                "success": sum(1 for r in results["test_vector_store_resilience_results.json"] if r["success"])
            }
        },
        "detailed_results": results
    }
    
    # Save report
    report_path = "edge_case_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Edge case test report saved to {os.path.abspath(report_path)}")
    
    # Generate HTML report
    html_report = f"""<!DOCTYPE html>
<html>
<head>
    <title>Metis RAG Edge Case Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .section {{ margin-bottom: 30px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
    </style>
</head>
<body>
    <h1>Metis RAG Edge Case Test Report</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="section">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Test Category</th>
                <th>Total Tests</th>
                <th>Success Rate</th>
            </tr>
            <tr>
                <td>Special Character Queries</td>
                <td>{report["summary"]["special_queries"]["total"]}</td>
                <td>{report["summary"]["special_queries"]["success"]}/{report["summary"]["special_queries"]["total"]} ({report["summary"]["special_queries"]["success"]/report["summary"]["special_queries"]["total"]*100:.1f}%)</td>
            </tr>
            <tr>
                <td>Concurrent Document Processing</td>
                <td>{report["summary"]["concurrent_processing"]["total"]}</td>
                <td>{report["summary"]["concurrent_processing"]["success"]}/{report["summary"]["concurrent_processing"]["total"]} ({report["summary"]["concurrent_processing"]["success"]/report["summary"]["concurrent_processing"]["total"]*100:.1f}%)</td>
            </tr>
            <tr>
                <td>Invalid File Types</td>
                <td>{report["summary"]["invalid_files"]["total"]}</td>
                <td>Accepted: {report["summary"]["invalid_files"]["accepted"]}/{report["summary"]["invalid_files"]["total"]} ({report["summary"]["invalid_files"]["accepted"]/report["summary"]["invalid_files"]["total"]*100:.1f}%)<br>
                Processed: {report["summary"]["invalid_files"]["processed"]}/{report["summary"]["invalid_files"]["accepted"] if report["summary"]["invalid_files"]["accepted"] > 0 else 1} ({(report["summary"]["invalid_files"]["processed"]/report["summary"]["invalid_files"]["accepted"]*100 if report["summary"]["invalid_files"]["accepted"] > 0 else 0):.1f}%)</td>
            </tr>
            <tr>
                <td>Malformed API Requests</td>
                <td>{report["summary"]["malformed_requests"]["total"]}</td>
                <td>Error Responses: {report["summary"]["malformed_requests"]["error_responses"]}/{report["summary"]["malformed_requests"]["total"]} ({report["summary"]["malformed_requests"]["error_responses"]/report["summary"]["malformed_requests"]["total"]*100:.1f}%)</td>
            </tr>
            <tr>
                <td>Vector Store Resilience</td>
                <td>{report["summary"]["vector_store_resilience"]["total"]}</td>
                <td>{report["summary"]["vector_store_resilience"]["success"]}/{report["summary"]["vector_store_resilience"]["total"]} ({report["summary"]["vector_store_resilience"]["success"]/report["summary"]["vector_store_resilience"]["total"]*100:.1f}%)</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Special Character Queries</h2>
        <table>
            <tr>
                <th>Query</th>
                <th>Status Code</th>
                <th>Result</th>
            </tr>
            {("".join([f"<tr><td>{r['query'][:50]}...</td><td>{r['status_code']}</td><td class=\"{'success' if r['success'] else 'failure'}\">{('Success' if r['success'] else 'Failure')}</td></tr>" for r in results["test_special_queries_results.json"]]))}
        </table>
    </div>
    
    <div class="section">
        <h2>Invalid File Types</h2>
        <table>
            <tr>
                <th>Filename</th>
                <th>Content Type</th>
                <th>Upload Status</th>
                <th>Processing Status</th>
            </tr>
            {("".join([f"<tr><td>{r['filename']}</td><td>{r['content_type']}</td><td class=\"{'success' if r['accepted'] else 'failure'}\">{r['status_code']} ({('Accepted' if r['accepted'] else 'Rejected')})</td><td class=\"{'success' if r.get('process_success', False) else 'failure'}\">{r.get('process_status_code', 'N/A')} ({('Success' if r.get('process_success', False) else 'N/A' if not r['accepted'] else 'Failure')})</td></tr>" for r in results["test_invalid_files_results.json"]]))}
        </table>
    </div>
    
    <div class="section">
        <h2>Malformed API Requests</h2>
        <table>
            <tr>
                <th>Endpoint</th>
                <th>Method</th>
                <th>Data</th>
                <th>Status Code</th>
                <th>Result</th>
            </tr>
            {("".join([f"<tr><td>{r['endpoint']}</td><td>{r['method']}</td><td>{r['data'][:30]}...</td><td>{r.get('status_code', 'Exception')}</td><td class=\"{'success' if r['is_error'] else 'failure'}\">{('Error Response' if r['is_error'] else 'Unexpected Success')}</td></tr>" for r in results["test_malformed_requests_results.json"]]))}
        </table>
    </div>
    
    <div class="section">
        <h2>Vector Store Resilience</h2>
        <table>
            <tr>
                <th>Operation</th>
                <th>Arguments</th>
                <th>Result</th>
                <th>Error</th>
            </tr>
            {("".join([f"<tr><td>{r['operation']}</td><td>{r['args'][:30]}...</td><td class=\"{'success' if r['success'] else 'failure'}\">{('Success' if r['success'] else 'Failure')}</td><td>{r.get('error', 'N/A')}</td></tr>" for r in results["test_vector_store_resilience_results.json"]]))}
        </table>
    </div>
</body>
</html>
"""
    
    html_report_path = "edge_case_test_report.html"
    with open(html_report_path, "w") as f:
        f.write(html_report)
    
    logger.info(f"HTML edge case report saved to {os.path.abspath(html_report_path)}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])