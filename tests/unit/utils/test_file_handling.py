#!/usr/bin/env python3
"""
Test suite for evaluating file handling capabilities in the Metis RAG system.
This test suite focuses on different file types, multiple file uploads, and large files.
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
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_file_handling")

# Import RAG components
from app.rag.document_processor import DocumentProcessor
from app.models.document import Document
from app.main import app

# Test client
client = TestClient(app)

# Test file templates
TEST_FILE_TEMPLATES = {
    "txt": {
        "content": """This is a test text file for the Metis RAG system.
It contains multiple lines of text that will be processed and indexed.
The document processor should handle plain text files efficiently.
This file will be used to test the text file processing capabilities."""
    },
    "md": {
        "content": """# Test Markdown File

## Introduction
This is a test markdown file for the Metis RAG system.

## Features
- Supports headers
- Supports lists
- Supports **bold** and *italic* text

## Code Examples
```python
def test_function():
    return "This is a test"
```

## Conclusion
The document processor should handle markdown files correctly."""
    },
    "csv": {
        "content": """id,name,description,value
1,Item 1,This is the first item,100
2,Item 2,This is the second item,200
3,Item 3,This is the third item,300
4,Item 4,This is the fourth item,400
5,Item 5,This is the fifth item,500"""
    }
}

def generate_random_text(size_kb):
    """Generate random text of specified size in KB"""
    chars = string.ascii_letters + string.digits + string.punctuation + ' \n\t'
    # 1 KB is approximately 1000 characters
    return ''.join(random.choice(chars) for _ in range(size_kb * 1000))

@pytest.fixture
def test_files_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp(prefix="metis_rag_test_")
    yield temp_dir
    # Clean up
    shutil.rmtree(temp_dir)

@pytest.fixture
def create_test_files(test_files_dir):
    """Create test files of different types"""
    file_paths = {}
    
    # Create basic test files
    for ext, template in TEST_FILE_TEMPLATES.items():
        file_path = os.path.join(test_files_dir, f"test.{ext}")
        with open(file_path, "w") as f:
            f.write(template["content"])
        file_paths[ext] = file_path
    
    # Create a large text file (1 MB)
    large_file_path = os.path.join(test_files_dir, "large_file.txt")
    with open(large_file_path, "w") as f:
        f.write(generate_random_text(1024))  # 1024 KB = 1 MB
    file_paths["large_txt"] = large_file_path
    
    return file_paths

@pytest.fixture
def document_processor():
    """Create a document processor instance"""
    return DocumentProcessor()

@pytest.mark.asyncio
async def test_file_type_support(document_processor, create_test_files):
    """Test processing of different file types"""
    results = []
    
    for file_type, file_path in create_test_files.items():
        if file_type == "large_txt":
            continue  # Skip large file for this test
            
        logger.info(f"Testing file type: {file_type}")
        
        # Create a document object
        with open(file_path, "r") as f:
            content = f.read()
            
        document = Document(
            id=str(uuid.uuid4()),
            filename=os.path.basename(file_path),
            content=content
        )
        
        # Process the document
        try:
            processed_doc = await document_processor.process_document(document)
            
            # Check if chunks were created
            chunk_count = len(processed_doc.chunks)
            success = chunk_count > 0
            
            logger.info(f"Processed {file_type} file: {success}, {chunk_count} chunks created")
            
            # Store results
            results.append({
                "file_type": file_type,
                "success": success,
                "chunk_count": chunk_count,
                "avg_chunk_size": sum(len(chunk.content) for chunk in processed_doc.chunks) / chunk_count if chunk_count > 0 else 0
            })
            
            # Assertions
            assert success, f"Failed to process {file_type} file"
            assert chunk_count > 0, f"No chunks created for {file_type} file"
            
        except Exception as e:
            logger.error(f"Error processing {file_type} file: {str(e)}")
            results.append({
                "file_type": file_type,
                "success": False,
                "error": str(e)
            })
            assert False, f"Error processing {file_type} file: {str(e)}"
    
    # Save results to file
    results_path = "test_file_type_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"File type test results saved to {os.path.abspath(results_path)}")

@pytest.mark.asyncio
async def test_chunking_strategies(document_processor, create_test_files):
    """Test different chunking strategies"""
    results = []
    
    chunking_strategies = ["recursive", "token", "markdown"]
    file_path = create_test_files["md"]  # Use markdown file for testing chunking strategies
    
    with open(file_path, "r") as f:
        content = f.read()
    
    for strategy in chunking_strategies:
        logger.info(f"Testing chunking strategy: {strategy}")
        
        # Create a custom document processor with the specified chunking strategy
        custom_processor = DocumentProcessor(chunking_strategy=strategy)
        
        # Create a document object
        document = Document(
            id=str(uuid.uuid4()),
            filename=os.path.basename(file_path),
            content=content
        )
        
        # Process the document
        try:
            processed_doc = await custom_processor.process_document(document)
            
            # Check if chunks were created
            chunk_count = len(processed_doc.chunks)
            success = chunk_count > 0
            
            logger.info(f"Processed with {strategy} strategy: {success}, {chunk_count} chunks created")
            
            # Store results
            results.append({
                "chunking_strategy": strategy,
                "success": success,
                "chunk_count": chunk_count,
                "avg_chunk_size": sum(len(chunk.content) for chunk in processed_doc.chunks) / chunk_count if chunk_count > 0 else 0
            })
            
            # Assertions
            assert success, f"Failed to process with {strategy} strategy"
            assert chunk_count > 0, f"No chunks created with {strategy} strategy"
            
        except Exception as e:
            logger.error(f"Error processing with {strategy} strategy: {str(e)}")
            results.append({
                "chunking_strategy": strategy,
                "success": False,
                "error": str(e)
            })
            assert False, f"Error processing with {strategy} strategy: {str(e)}"
    
    # Save results to file
    results_path = "test_chunking_strategy_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Chunking strategy test results saved to {os.path.abspath(results_path)}")

@pytest.mark.asyncio
async def test_large_file_handling(document_processor, create_test_files):
    """Test handling of large files"""
    results = []
    
    file_path = create_test_files["large_txt"]
    
    logger.info(f"Testing large file handling")
    
    # Create a document object
    with open(file_path, "r") as f:
        content = f.read()
        
    document = Document(
        id=str(uuid.uuid4()),
        filename=os.path.basename(file_path),
        content=content
    )
    
    # Process the document
    try:
        start_time = datetime.now()
        processed_doc = await document_processor.process_document(document)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Check if chunks were created
        chunk_count = len(processed_doc.chunks)
        success = chunk_count > 0
        
        file_size_kb = len(content) / 1000
        processing_speed = file_size_kb / processing_time if processing_time > 0 else 0
        
        logger.info(f"Processed large file: {success}, {chunk_count} chunks created")
        logger.info(f"Processing time: {processing_time:.2f} seconds")
        logger.info(f"Processing speed: {processing_speed:.2f} KB/s")
        
        # Store results
        results.append({
            "file_size_kb": file_size_kb,
            "success": success,
            "chunk_count": chunk_count,
            "processing_time_seconds": processing_time,
            "processing_speed_kb_per_second": processing_speed,
            "avg_chunk_size": sum(len(chunk.content) for chunk in processed_doc.chunks) / chunk_count if chunk_count > 0 else 0
        })
        
        # Assertions
        assert success, "Failed to process large file"
        assert chunk_count > 0, "No chunks created for large file"
        
    except Exception as e:
        logger.error(f"Error processing large file: {str(e)}")
        results.append({
            "file_size_kb": len(content) / 1000,
            "success": False,
            "error": str(e)
        })
        assert False, f"Error processing large file: {str(e)}"
    
    # Save results to file
    results_path = "test_large_file_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Large file test results saved to {os.path.abspath(results_path)}")

@pytest.mark.asyncio
async def test_api_file_upload(create_test_files):
    """Test file upload through API"""
    results = []
    
    for file_type, file_path in create_test_files.items():
        if file_type == "large_txt":
            continue  # Skip large file for API test to avoid timeouts
            
        logger.info(f"Testing API upload for file type: {file_type}")
        
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        # Create file-like object for upload
        file_obj = BytesIO(file_content)
        file_obj.name = os.path.basename(file_path)
        
        # Upload the file
        try:
            upload_response = client.post(
                "/api/documents/upload",
                files={"file": (file_obj.name, file_obj, f"text/{file_type}")}
            )
            
            # Check upload response
            assert upload_response.status_code == 200, f"Upload failed with status {upload_response.status_code}"
            upload_data = upload_response.json()
            assert upload_data["success"] is True, "Upload response indicates failure"
            assert "document_id" in upload_data, "No document_id in upload response"
            
            document_id = upload_data["document_id"]
            
            # Process the document
            process_response = client.post(
                "/api/documents/process",
                json={"document_ids": [document_id]}
            )
            
            # Check process response
            assert process_response.status_code == 200, f"Processing failed with status {process_response.status_code}"
            process_data = process_response.json()
            assert process_data["success"] is True, "Process response indicates failure"
            
            # Get document info
            info_response = client.get(f"/api/documents/{document_id}")
            
            # Check info response
            assert info_response.status_code == 200, f"Info request failed with status {info_response.status_code}"
            doc_info = info_response.json()
            
            # Store results
            results.append({
                "file_type": file_type,
                "document_id": document_id,
                "filename": file_obj.name,
                "success": True,
                "chunk_count": doc_info.get("chunk_count", 0) if isinstance(doc_info, dict) else 0
            })
            
            # Clean up - delete the document
            delete_response = client.delete(f"/api/documents/{document_id}")
            assert delete_response.status_code == 200, f"Delete failed with status {delete_response.status_code}"
            
        except Exception as e:
            logger.error(f"Error in API test for {file_type} file: {str(e)}")
            results.append({
                "file_type": file_type,
                "filename": os.path.basename(file_path),
                "success": False,
                "error": str(e)
            })
            assert False, f"Error in API test for {file_type} file: {str(e)}"
    
    # Save results to file
    results_path = "test_api_upload_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"API upload test results saved to {os.path.abspath(results_path)}")

@pytest.mark.asyncio
async def test_multiple_file_upload(create_test_files):
    """Test uploading and processing multiple files simultaneously"""
    results = []
    
    # Skip large file for this test
    file_paths = {k: v for k, v in create_test_files.items() if k != "large_txt"}
    
    logger.info(f"Testing multiple file upload with {len(file_paths)} files")
    
    # Upload all files
    document_ids = []
    
    for file_type, file_path in file_paths.items():
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        # Create file-like object for upload
        file_obj = BytesIO(file_content)
        file_obj.name = os.path.basename(file_path)
        
        # Upload the file
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": (file_obj.name, file_obj, f"text/{file_type}")}
        )
        
        # Check upload response
        assert upload_response.status_code == 200, f"Upload failed with status {upload_response.status_code}"
        upload_data = upload_response.json()
        assert upload_data["success"] is True, "Upload response indicates failure"
        
        document_ids.append(upload_data["document_id"])
    
    # Process all documents at once
    try:
        start_time = datetime.now()
        
        process_response = client.post(
            "/api/documents/process",
            json={"document_ids": document_ids}
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Check process response
        assert process_response.status_code == 200, f"Processing failed with status {process_response.status_code}"
        process_data = process_response.json()
        assert process_data["success"] is True, "Process response indicates failure"
        
        # Get info for all documents
        for doc_id in document_ids:
            info_response = client.get(f"/api/documents/{doc_id}")
            assert info_response.status_code == 200, f"Info request failed for document {doc_id}"
        
        # Store results
        results.append({
            "file_count": len(document_ids),
            "document_ids": document_ids,
            "success": True,
            "processing_time_seconds": processing_time,
            "processing_speed_files_per_second": len(document_ids) / processing_time if processing_time > 0 else 0
        })
        
        # Clean up - delete all documents
        for doc_id in document_ids:
            delete_response = client.delete(f"/api/documents/{doc_id}")
            assert delete_response.status_code == 200, f"Delete failed for document {doc_id}"
            
    except Exception as e:
        logger.error(f"Error in multiple file upload test: {str(e)}")
        results.append({
            "file_count": len(document_ids),
            "success": False,
            "error": str(e)
        })
        assert False, f"Error in multiple file upload test: {str(e)}"
    
    # Save results to file
    results_path = "test_multiple_upload_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Multiple file upload test results saved to {os.path.abspath(results_path)}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])