import os
import sys
import time
import asyncio
import pytest
import statistics
import tempfile
import uuid
from typing import List, Dict, Any
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from app.rag.document_processor import DocumentProcessor
from app.rag.document_analysis_service import DocumentAnalysisService
from app.rag.vector_store import VectorStore
from app.db.repositories.document_repository import DocumentRepository
from app.db.session import SessionLocal
from app.models.document import Document
from app.core.config import SETTINGS

# Define upload directory using project_root
UPLOAD_DIR = os.path.join(project_root, "data", "uploads")

# Test configuration
TEST_FILE_SIZES = [
    ("small", 5),      # 5 KB
    ("medium", 50),    # 50 KB
    ("large", 500),    # 500 KB
    ("xlarge", 2000)   # 2 MB
]

TEST_CHUNKING_STRATEGIES = [
    "recursive",
    "token",
    "markdown",
    "semantic"
]

# Number of times to run each test for averaging
NUM_RUNS = 3

@pytest.fixture
def db_session():
    """Create a database session for testing"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def document_repository(db_session):
    """Create a document repository for testing"""
    return DocumentRepository(db_session)

@pytest.fixture
def document_processor():
    """Create a document processor for testing"""
    return DocumentProcessor()

@pytest.fixture
def document_analysis_service():
    """Create a document analysis service for testing"""
    return DocumentAnalysisService()

@pytest.fixture
def vector_store():
    """Create a vector store for testing"""
    return VectorStore()

def generate_test_file(size_kb: int, file_type: str = "txt"):
    """Generate a test file of the specified size"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=f".{file_type}")
    
    try:
        # Generate content
        content = ""
        if file_type == "txt":
            # Generate paragraphs of text
            paragraph = "This is a test paragraph for document processing performance testing. " * 10
            paragraphs_needed = (size_kb * 1024) // len(paragraph)
            content = "\n\n".join([paragraph for _ in range(paragraphs_needed)])
        elif file_type == "md":
            # Generate markdown content
            paragraph = "This is a test paragraph for document processing performance testing. " * 10
            paragraphs_needed = (size_kb * 1024) // (len(paragraph) + 20)  # Account for markdown syntax
            
            content = "# Test Document\n\n"
            for i in range(paragraphs_needed):
                content += f"## Section {i+1}\n\n{paragraph}\n\n"
        
        # Write content to file
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        
        return path
    except Exception as e:
        os.close(fd)
        os.unlink(path)
        raise e

async def process_document(document_processor, document: Document, chunking_strategy: str):
    """Process a document and measure performance"""
    start_time = time.time()
    
    # Configure processor with the specified chunking strategy
    processor = DocumentProcessor(
        chunking_strategy=chunking_strategy,
        chunk_size=SETTINGS.chunk_size,
        chunk_overlap=SETTINGS.chunk_overlap
    )
    
    # Process document
    processed_document = await processor.process_document(document)
    
    elapsed_time = time.time() - start_time
    
    # Convert UUID to string if needed
    document_id_str = str(document.id) if document.id else None
    
    # Create document directory path
    document_dir = os.path.join(UPLOAD_DIR, document_id_str)
    document_file_path = os.path.join(document_dir, document.filename)
    
    return {
        "document_id": document_id_str,
        "filename": document.filename,
        "chunking_strategy": chunking_strategy,
        "elapsed_time": elapsed_time,
        "chunk_count": len(processed_document.chunks),
        "file_size": os.path.getsize(document_file_path)
    }

async def analyze_document(document_analysis_service, document: Document):
    """Analyze a document and measure performance"""
    start_time = time.time()
    
    # Analyze document
    analysis_result = await document_analysis_service.analyze_document(document)
    
    elapsed_time = time.time() - start_time
    
    # Convert UUID to string if needed
    document_id_str = str(document.id) if document.id else None
    
    # Create document directory path
    document_dir = os.path.join(UPLOAD_DIR, document_id_str)
    document_file_path = os.path.join(document_dir, document.filename)
    
    return {
        "document_id": document_id_str,
        "filename": document.filename,
        "elapsed_time": elapsed_time,
        "recommended_strategy": analysis_result.get("strategy"),
        "file_size": os.path.getsize(document_file_path)
    }

def ensure_test_folder_exists(document_repository):
    """Ensure the test folder exists"""
    # Create the test folder using the document repository's helper method
    document_repository._ensure_folder_exists("/test")

async def run_processing_tests(document_repository, document_processor, vector_store):
    """Run document processing performance tests"""
    results = []
    
    # Create test directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Ensure the test folder exists in the database
    ensure_test_folder_exists(document_repository)
    
    for size_name, size_kb in TEST_FILE_SIZES:
        for file_type in ["txt", "md"]:
            # Generate test file
            file_path = generate_test_file(size_kb, file_type)
            file_name = f"test_{size_name}.{file_type}"
            
            try:
                # Create document in the database
                document = document_repository.create_document(
                    filename=file_name,
                    content="",
                    metadata={"file_type": file_type, "test_size": size_name},
                    folder="/test"
                )
                
                # Get document ID as string
                document_id_str = str(document.id)
                
                # Create document directory
                document_dir = os.path.join(UPLOAD_DIR, document_id_str)
                os.makedirs(document_dir, exist_ok=True)
                
                # Copy test file to document directory
                document_file_path = os.path.join(document_dir, file_name)
                with open(file_path, 'r') as src, open(document_file_path, 'w') as dst:
                    dst.write(src.read())
                
                # Test each chunking strategy
                for strategy in TEST_CHUNKING_STRATEGIES:
                    strategy_results = []
                    
                    for _ in range(NUM_RUNS):
                        try:
                            result = await process_document(document_processor, document, strategy)
                            strategy_results.append(result)
                        except Exception as e:
                            print(f"Error processing document {file_name}: {e}")
                            raise
                    
                    # Calculate average metrics
                    avg_time = statistics.mean([r["elapsed_time"] for r in strategy_results])
                    avg_chunk_count = statistics.mean([r["chunk_count"] for r in strategy_results])
                    
                    results.append({
                        "document_id": document_id_str,
                        "filename": file_name,
                        "file_type": file_type,
                        "size_name": size_name,
                        "size_kb": size_kb,
                        "chunking_strategy": strategy,
                        "avg_elapsed_time": avg_time,
                        "avg_chunk_count": avg_chunk_count,
                        "num_runs": NUM_RUNS
                    })
            finally:
                # Clean up test file
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    # Save results to file
    results_path = os.path.join(project_root, "tests", "results", "document_processing_performance_results.json")
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    
    import json
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {results_path}")
    
    return results

async def run_analysis_tests(document_repository, document_analysis_service):
    """Run document analysis performance tests"""
    results = []
    
    # Create test directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Ensure the test folder exists in the database
    ensure_test_folder_exists(document_repository)
    
    for size_name, size_kb in TEST_FILE_SIZES:
        for file_type in ["txt", "md"]:
            # Generate test file
            file_path = generate_test_file(size_kb, file_type)
            file_name = f"test_analysis_{size_name}.{file_type}"
            
            try:
                # Create document in the database
                document = document_repository.create_document(
                    filename=file_name,
                    content="",
                    metadata={"file_type": file_type, "test_size": size_name},
                    folder="/test"
                )
                
                # Get document ID as string
                document_id_str = str(document.id)
                
                # Create document directory
                document_dir = os.path.join(UPLOAD_DIR, document_id_str)
                os.makedirs(document_dir, exist_ok=True)
                
                # Copy test file to document directory
                document_file_path = os.path.join(document_dir, file_name)
                with open(file_path, 'r') as src, open(document_file_path, 'w') as dst:
                    dst.write(src.read())
                
                # Run analysis multiple times
                analysis_results = []
                for _ in range(NUM_RUNS):
                    try:
                        result = await analyze_document(document_analysis_service, document)
                        analysis_results.append(result)
                    except Exception as e:
                        print(f"Error analyzing document {file_name}: {e}")
                        raise
                
                # Calculate average metrics
                avg_time = statistics.mean([r["elapsed_time"] for r in analysis_results])
                
                results.append({
                    "document_id": document_id_str,
                    "filename": file_name,
                    "file_type": file_type,
                    "size_name": size_name,
                    "size_kb": size_kb,
                    "avg_elapsed_time": avg_time,
                    "recommended_strategy": analysis_results[0]["recommended_strategy"],
                    "num_runs": NUM_RUNS
                })
            finally:
                # Clean up test file
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    # Save results to file
    results_path = os.path.join(project_root, "tests", "results", "document_analysis_performance_results.json")
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    
    import json
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {results_path}")
    
    return results

@pytest.mark.asyncio
async def test_document_processing_performance(document_repository, document_processor, vector_store):
    """Test document processing performance"""
    print(f"\nRunning document processing performance test with {len(TEST_FILE_SIZES)} file sizes, {len(TEST_CHUNKING_STRATEGIES)} chunking strategies")
    
    # Run processing tests
    results = await run_processing_tests(document_repository, document_processor, vector_store)
    
    # Print results
    print("\nDocument Processing Performance Results:")
    print(f"{'File':<20} | {'Size':<10} | {'Strategy':<15} | {'Avg Time (s)':<12} | {'Avg Chunks':<10}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['filename']:<20} | {result['size_kb']} KB{' ':<5} | {result['chunking_strategy']:<15} | {result['avg_elapsed_time']:<12.2f} | {result['avg_chunk_count']:<10.0f}")
    
    # Calculate overall metrics by strategy
    strategies = {}
    for strategy in TEST_CHUNKING_STRATEGIES:
        strategy_results = [r for r in results if r["chunking_strategy"] == strategy]
        avg_time = statistics.mean([r["avg_elapsed_time"] for r in strategy_results])
        strategies[strategy] = avg_time
    
    print("\nAverage Processing Time by Strategy:")
    for strategy, avg_time in strategies.items():
        print(f"{strategy:<15}: {avg_time:.2f}s")
    
    # Calculate overall metrics by file size
    sizes = {}
    for size_name, size_kb in TEST_FILE_SIZES:
        size_results = [r for r in results if r["size_name"] == size_name]
        avg_time = statistics.mean([r["avg_elapsed_time"] for r in size_results])
        sizes[size_name] = avg_time
    
    print("\nAverage Processing Time by File Size:")
    for size_name, avg_time in sizes.items():
        print(f"{size_name:<10}: {avg_time:.2f}s")

@pytest.mark.asyncio
async def test_document_analysis_performance(document_repository, document_analysis_service):
    """Test document analysis performance"""
    print(f"\nRunning document analysis performance test with {len(TEST_FILE_SIZES)} file sizes")
    
    # Run analysis tests
    results = await run_analysis_tests(document_repository, document_analysis_service)
    
    # Print results
    print("\nDocument Analysis Performance Results:")
    print(f"{'File':<20} | {'Size':<10} | {'Avg Time (s)':<12} | {'Recommended Strategy':<20}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['filename']:<20} | {result['size_kb']} KB{' ':<5} | {result['avg_elapsed_time']:<12.2f} | {result['recommended_strategy']:<20}")
    
    # Calculate overall metrics by file size
    sizes = {}
    for size_name, size_kb in TEST_FILE_SIZES:
        size_results = [r for r in results if r["size_name"] == size_name]
        avg_time = statistics.mean([r["avg_elapsed_time"] for r in size_results])
        sizes[size_name] = avg_time
    
    print("\nAverage Analysis Time by File Size:")
    for size_name, avg_time in sizes.items():
        print(f"{size_name:<10}: {avg_time:.2f}s")

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_document_processing_performance(
        DocumentRepository(SessionLocal()),
        DocumentProcessor(),
        VectorStore()
    ))
    asyncio.run(test_document_analysis_performance(
        DocumentRepository(SessionLocal()),
        DocumentAnalysisService()
    ))