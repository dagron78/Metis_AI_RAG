"""
Simplified document processing test with database integration.

This test verifies that the document processor works correctly with the database,
using the adapter functions to convert between Pydantic and SQLAlchemy models.
"""
import os
import time
import asyncio
import pytest
import tempfile
import shutil
import uuid
from typing import List, Dict, Any
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.rag.document_processor import DocumentProcessor
from app.models.document import Document
from app.db.repositories.document_repository import DocumentRepository
from app.db.models import Base, Folder
from app.db.session import SessionLocal, engine  # Updated import
from app.core.config import UPLOAD_DIR

# Test configuration
TEST_FILE_SIZES = [
    ("small", 5),      # 5 KB
]

TEST_CHUNKING_STRATEGIES = [
    "recursive",
]

# Number of times to run each test for averaging
NUM_RUNS = 1

@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for uploads"""
    temp_dir = tempfile.mkdtemp()
    original_upload_dir = UPLOAD_DIR
    
    # Temporarily override the upload directory
    import app.core.config
    app.core.config.UPLOAD_DIR = temp_dir
    
    yield temp_dir
    
    # Restore the original upload directory and clean up
    app.core.config.UPLOAD_DIR = original_upload_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create root folder
    root_folder = Folder(path="/", name="Root", parent_path=None)
    session.add(root_folder)
    
    # Create test folder
    test_folder = Folder(path="/test/", name="Test", parent_path="/")
    session.add(test_folder)
    
    session.commit()
    
    yield session
    
    session.close()

@pytest.fixture
def document_repository(in_memory_db):
    """Create a document repository for testing"""
    return DocumentRepository(in_memory_db)

@pytest.fixture
def document_processor():
    """Create a document processor for testing"""
    return DocumentProcessor()

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

async def process_document(document_processor, document, chunking_strategy):
    """Process a document and measure performance"""
    start_time = time.time()
    
    # Configure processor with the specified chunking strategy
    processor = DocumentProcessor(
        chunking_strategy=chunking_strategy,
        chunk_size=1500,
        chunk_overlap=150
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

@pytest.mark.asyncio
async def test_document_processing_with_db(temp_upload_dir, document_repository, document_processor):
    """Test document processing with database integration"""
    print(f"\nRunning document processing test with {len(TEST_FILE_SIZES)} file sizes, {len(TEST_CHUNKING_STRATEGIES)} chunking strategies")
    
    # Create test directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    results = []
    
    for size_name, size_kb in TEST_FILE_SIZES:
        for file_type in ["txt"]:
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
                            # Get fresh document for each run
                            fresh_document = document_repository.get_document_with_chunks(document.id)
                            
                            # Process document
                            result = await process_document(document_processor, fresh_document, strategy)
                            strategy_results.append(result)
                            
                            # Save document with chunks
                            document_repository.save_document_with_chunks(fresh_document)
                            
                            # Verify that the document was saved correctly
                            saved_document = document_repository.get_document_with_chunks(document.id)
                            assert saved_document is not None
                            assert len(saved_document.chunks) > 0
                            
                        except Exception as e:
                            print(f"Error processing document {file_name}: {e}")
                            raise
                    
                    # Calculate average metrics
                    avg_time = sum([r["elapsed_time"] for r in strategy_results]) / len(strategy_results)
                    avg_chunk_count = sum([r["chunk_count"] for r in strategy_results]) / len(strategy_results)
                    
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
        if strategy_results:
            avg_time = sum([r["avg_elapsed_time"] for r in strategy_results]) / len(strategy_results)
            strategies[strategy] = avg_time
    
    print("\nAverage Processing Time by Strategy:")
    for strategy, avg_time in strategies.items():
        print(f"{strategy:<15}: {avg_time:.2f}s")
    
    # Calculate overall metrics by file size
    sizes = {}
    for size_name, size_kb in TEST_FILE_SIZES:
        size_results = [r for r in results if r["size_name"] == size_name]
        if size_results:
            avg_time = sum([r["avg_elapsed_time"] for r in size_results]) / len(size_results)
            sizes[size_name] = avg_time
    
    print("\nAverage Processing Time by File Size:")
    for size_name, avg_time in sizes.items():
        print(f"{size_name:<10}: {avg_time:.2f}s")

if __name__ == "__main__":
    # Run the test directly if this file is executed
    import asyncio
    session = SessionLocal()
    try:
        asyncio.run(test_document_processing_with_db(
            tempfile.mkdtemp(),
            DocumentRepository(session),
            DocumentProcessor()
        ))
    finally:
        session.close()