#!/usr/bin/env python3
"""
Database Performance Benchmarking Script for Metis RAG

This script benchmarks SQLite vs PostgreSQL performance for various operations:
1. Document insertion and retrieval
2. Chunk storage and retrieval
3. Query performance with different database backends
4. Batch processing performance

Usage:
    python benchmark_database_performance.py --db-type sqlite|postgresql [--html] [--runs 5]
"""
import os
import sys
import json
import time
import asyncio
import argparse
import statistics
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.session import Base, engine, SessionLocal
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.models.document import Document, Chunk
from app.core.config import SETTINGS, DATABASE_TYPE, DATABASE_URL
import uuid
from app.db.models import Document as DBDocument, Chunk as DBChunk
from app.db.adapters import to_uuid_or_str

# Custom adapter function to ensure metadata is a simple dictionary
def custom_pydantic_chunk_to_sqlalchemy(chunk, document_id):
    """
    Convert Pydantic Chunk to SQLAlchemy Chunk with proper metadata handling.
    
    Args:
        chunk: Pydantic Chunk model
        document_id: ID of the parent document
        
    Returns:
        SQLAlchemy Chunk model
    """
    # Handle UUID conversion based on database type
    chunk_id = to_uuid_or_str(chunk.id)
    doc_id = to_uuid_or_str(document_id)
    
    # Extract index from metadata or default to 0
    index = chunk.metadata.get('index', 0) if chunk.metadata else 0
    
    # Ensure metadata is a simple dictionary
    if not isinstance(chunk.metadata, dict):
        metadata = dict(chunk.metadata) if chunk.metadata else {}
    else:
        metadata = chunk.metadata
    
    sqlalchemy_chunk = DBChunk(
        id=chunk_id,
        document_id=doc_id,
        content=chunk.content,
        chunk_metadata=metadata,  # Use our sanitized metadata
        index=index,
        embedding_quality=None  # No embedding quality for benchmark
    )
    return sqlalchemy_chunk

# Custom function to save document with chunks
def custom_save_document_with_chunks(session, document):
    """
    Save a document with its chunks using custom adapter function
    
    Args:
        session: SQLAlchemy session
        document: Pydantic Document model
        
    Returns:
        Saved document (Pydantic model)
    """
    from app.db.adapters import (
        pydantic_document_to_sqlalchemy,
        sqlalchemy_document_to_pydantic,
        is_sqlalchemy_model
    )
    
    try:
        # Convert to SQLAlchemy model if needed
        if not is_sqlalchemy_model(document):
            db_document = pydantic_document_to_sqlalchemy(document)
        else:
            db_document = document
        
        # Check if document exists
        existing = session.query(DBDocument).filter(
            DBDocument.id == db_document.id
        ).first()
        
        if existing:
            # Update existing document
            existing.filename = db_document.filename
            existing.content = db_document.content
            existing.doc_metadata = db_document.doc_metadata
            existing.folder = db_document.folder
            existing.last_accessed = datetime.utcnow()
            existing.processing_status = db_document.processing_status
            existing.processing_strategy = db_document.processing_strategy
            
            # Delete existing chunks
            session.query(DBChunk).filter(
                DBChunk.document_id == existing.id
            ).delete()
            
            # Add new chunks
            if hasattr(document, 'chunks') and document.chunks:
                for i, chunk in enumerate(document.chunks):
                    # Create new chunk using our custom adapter
                    new_chunk = custom_pydantic_chunk_to_sqlalchemy(chunk, existing.id)
                    session.add(new_chunk)
                    
            target_document = existing
        else:
            # For new documents, we need to ensure we don't have ID conflicts
            # First check if a document with this ID already exists
            check_existing = session.query(DBDocument).filter(
                DBDocument.id == db_document.id
            ).first()
            
            if check_existing:
                # Generate a new ID
                db_document.id = uuid.uuid4()
            
            # Add new document
            session.add(db_document)
            session.flush()  # Flush to get the document ID
            
            # Add chunks
            if hasattr(document, 'chunks') and document.chunks:
                for i, chunk in enumerate(document.chunks):
                    # Create new chunk using our custom adapter
                    new_chunk = custom_pydantic_chunk_to_sqlalchemy(chunk, db_document.id)
                    session.add(new_chunk)
                    
            target_document = db_document
        
        # Commit changes
        session.commit()
        
        # Refresh and convert back to Pydantic
        session.refresh(target_document)
        return sqlalchemy_document_to_pydantic(target_document)
    except Exception as e:
        session.rollback()
        print(f"Error saving document with chunks: {str(e)}")
        raise

# Test configuration
TEST_FILE_SIZES = [
    ("small", 5),      # 5 KB
    ("medium", 50),    # 50 KB
    ("large", 500),    # 500 KB
    ("xlarge", 2000)   # 2 MB
]

TEST_CHUNKING_STRATEGIES = [
    "recursive",
    "token"
]

TEST_QUERIES = [
    "What is the main purpose of the RAG system?",
    "How does the document analysis service work?",
    "What are the key components of the LangGraph integration?",
    "Explain the database schema for documents and chunks",
    "How does the memory integration enhance the system?"
]

# Batch sizes for testing
BATCH_SIZES = [1, 5, 10, 20]

class SimpleDocumentProcessor:
    """Simple document processor for benchmarking"""
    
    def __init__(self, chunk_size=1500, chunk_overlap=150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def process_document(self, document: Document) -> Document:
        """Process a document by splitting it into chunks"""
        # Create a simple chunking strategy
        content = document.content
        chunks = []
        
        # Simple chunking by character count with overlap
        for i in range(0, len(content), self.chunk_size - self.chunk_overlap):
            chunk_content = content[i:i + self.chunk_size]
            if chunk_content:
                # Create a simple dictionary for metadata
                chunk_metadata = {
                    "document_id": str(document.id),
                    "index": len(chunks),
                    "strategy": "simple"
                }
                
                chunks.append(
                    Chunk(
                        content=chunk_content,
                        metadata=chunk_metadata
                    )
                )
        
        # Add chunks to document
        document.chunks = chunks
        
        # Update document metadata
        if not document.metadata:
            document.metadata = {}
        document.metadata["chunking"] = {
            "strategy": "simple",
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "chunk_count": len(chunks)
        }
        
        return document

class DatabaseBenchmark:
    """Database performance benchmarking class"""
    
    def __init__(self, db_type: str, num_runs: int = 3):
        self.db_type = db_type
        self.num_runs = num_runs
        self.results = {
            "metadata": {
                "db_type": db_type,
                "timestamp": datetime.now().isoformat(),
                "num_runs": num_runs
            },
            "document_operations": [],
            "chunk_operations": [],
            "query_performance": [],
            "batch_processing": []
        }
        
        # Initialize database session
        self.db_session = SessionLocal()
        
        # Initialize repositories and services
        self.document_repository = DocumentRepository(self.db_session)
        self.analytics_repository = AnalyticsRepository(self.db_session)
        self.document_processor = SimpleDocumentProcessor()
        
        # Create folders in database
        self._ensure_folders_exist()
        
        print(f"Initialized benchmark for {db_type} database")
        print(f"Database URL: {DATABASE_URL}")
        
    def _ensure_folders_exist(self):
        """Ensure the root and benchmark folders exist in the database"""
        try:
            # Import Folder model
            from app.db.models import Folder
            
            # Check if root folder exists
            root_folder = self.db_session.query(Folder).filter(Folder.path == "/").first()
            if not root_folder:
                # Create root folder
                root_folder = Folder(
                    path="/",
                    name="Root",
                    parent_path=None
                )
                self.db_session.add(root_folder)
                self.db_session.commit()
                print("Created root folder in database")
            
            # Check if benchmark folder exists
            benchmark_folder = self.db_session.query(Folder).filter(Folder.path == "/benchmark").first()
            if not benchmark_folder:
                # Create benchmark folder
                benchmark_folder = Folder(
                    path="/benchmark",
                    name="Benchmark",
                    parent_path="/"
                )
                self.db_session.add(benchmark_folder)
                self.db_session.commit()
                print("Created benchmark folder in database")
        except Exception as e:
            self.db_session.rollback()
            print(f"Error creating folders: {e}")
        
    def cleanup(self):
        """Clean up resources"""
        self.db_session.close()
        
    def generate_test_file(self, size_kb: int, file_type: str = "txt"):
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
    
    async def benchmark_document_operations(self):
        """Benchmark document CRUD operations"""
        print("\nBenchmarking document operations...")
        
        results = []
        
        # Ensure test folder exists
        self.document_repository._ensure_folder_exists("/benchmark")
        
        for size_name, size_kb in TEST_FILE_SIZES:
            # Generate test file
            file_path = self.generate_test_file(size_kb, "txt")
            file_name = f"benchmark_{size_name}_{self.db_type}.txt"
            
            try:
                # Read file content
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Benchmark document creation
                create_times = []
                document_ids = []
                
                for _ in range(self.num_runs):
                    # Measure document creation time
                    start_time = time.time()
                    
                    document = self.document_repository.create_document(
                        filename=file_name,
                        content=content,
                        metadata={"file_type": "txt", "test_size": size_name, "benchmark": True},
                        folder="/benchmark"
                    )
                    
                    create_time = time.time() - start_time
                    create_times.append(create_time)
                    document_ids.append(str(document.id))
                
                # Benchmark document retrieval
                retrieve_times = []
                
                for doc_id in document_ids:
                    # Measure document retrieval time
                    start_time = time.time()
                    
                    document = self.document_repository.get_document_with_chunks(doc_id)
                    
                    retrieve_time = time.time() - start_time
                    retrieve_times.append(retrieve_time)
                
                # Benchmark document update
                update_times = []
                
                for doc_id in document_ids:
                    # Measure document update time
                    start_time = time.time()
                    
                    document = self.document_repository.get_document_with_chunks(doc_id)
                    # Create a copy of metadata and update it
                    updated_metadata = document.metadata.copy()
                    updated_metadata["updated"] = True
                    # Use update_document with the document ID
                    self.document_repository.update_document(
                        document_id=doc_id,
                        metadata=updated_metadata
                    )
                    
                    update_time = time.time() - start_time
                    update_times.append(update_time)
                
                # Benchmark document deletion
                delete_times = []
                
                for doc_id in document_ids:
                    # Measure document deletion time
                    start_time = time.time()
                    
                    self.document_repository.delete_document(doc_id)
                    
                    delete_time = time.time() - start_time
                    delete_times.append(delete_time)
                
                # Calculate average metrics
                avg_create_time = statistics.mean(create_times)
                avg_retrieve_time = statistics.mean(retrieve_times)
                avg_update_time = statistics.mean(update_times)
                avg_delete_time = statistics.mean(delete_times)
                
                results.append({
                    "size_name": size_name,
                    "size_kb": size_kb,
                    "avg_create_time": avg_create_time,
                    "avg_retrieve_time": avg_retrieve_time,
                    "avg_update_time": avg_update_time,
                    "avg_delete_time": avg_delete_time,
                    "total_avg_time": avg_create_time + avg_retrieve_time + avg_update_time + avg_delete_time,
                    "num_runs": self.num_runs
                })
                
                print(f"  {size_name} ({size_kb} KB): Create: {avg_create_time:.4f}s, Retrieve: {avg_retrieve_time:.4f}s, Update: {avg_update_time:.4f}s, Delete: {avg_delete_time:.4f}s")
                
            finally:
                # Clean up test file
                try:
                    os.unlink(file_path)
                except:
                    pass
        
        self.results["document_operations"] = results
        return results
    
    async def benchmark_chunk_operations(self):
        """Benchmark chunk operations"""
        print("\nBenchmarking chunk operations...")
        
        results = []
        
        # Ensure test folder exists
        self.document_repository._ensure_folder_exists("/benchmark")
        
        for size_name, size_kb in TEST_FILE_SIZES:
            for strategy in TEST_CHUNKING_STRATEGIES:
                # Generate test file
                file_path = self.generate_test_file(size_kb, "txt")
                file_name = f"benchmark_chunk_{size_name}_{strategy}_{self.db_type}.txt"
                
                try:
                    # Read file content
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Create document in the database
                    document = self.document_repository.create_document(
                        filename=file_name,
                        content=content,
                        metadata={"file_type": "txt", "test_size": size_name, "benchmark": True},
                        folder="/benchmark"
                    )
                    
                    # Get document ID as string
                    document_id_str = str(document.id)
                    
                    # Process document to generate chunks
                    processed_document = await self.document_processor.process_document(document)
                    
                    # Ensure all chunk metadata is a simple dictionary
                    for chunk in processed_document.chunks:
                        if not isinstance(chunk.metadata, dict):
                            chunk.metadata = dict(chunk.metadata) if chunk.metadata else {}
                    
                    # Benchmark chunk insertion
                    start_time = time.time()
                    
                    # Save document with chunks using our custom function
                    custom_save_document_with_chunks(self.db_session, processed_document)
                    
                    chunk_insert_time = time.time() - start_time
                    
                    # Count chunks
                    chunk_count = len(processed_document.chunks)
                    
                    # Benchmark chunk retrieval
                    start_time = time.time()
                    
                    # Get document with chunks
                    retrieved_document = self.document_repository.get_document_with_chunks(document_id_str)
                    
                    chunk_retrieve_time = time.time() - start_time
                    
                    # Benchmark chunk update
                    start_time = time.time()
                    
                    # Update chunks
                    for i, chunk in enumerate(retrieved_document.chunks):
                        chunk.metadata["updated"] = True
                        self.document_repository.update_chunk(chunk)
                    
                    chunk_update_time = time.time() - start_time
                    
                    # Calculate per-chunk times
                    per_chunk_insert_time = chunk_insert_time / chunk_count if chunk_count > 0 else 0
                    per_chunk_retrieve_time = chunk_retrieve_time / chunk_count if chunk_count > 0 else 0
                    per_chunk_update_time = chunk_update_time / chunk_count if chunk_count > 0 else 0
                    
                    results.append({
                        "size_name": size_name,
                        "size_kb": size_kb,
                        "chunking_strategy": strategy,
                        "chunk_count": chunk_count,
                        "chunk_insert_time": chunk_insert_time,
                        "chunk_retrieve_time": chunk_retrieve_time,
                        "chunk_update_time": chunk_update_time,
                        "per_chunk_insert_time": per_chunk_insert_time,
                        "per_chunk_retrieve_time": per_chunk_retrieve_time,
                        "per_chunk_update_time": per_chunk_update_time
                    })
                    
                    print(f"  {size_name} ({size_kb} KB), {strategy}: Chunks: {chunk_count}, Insert: {chunk_insert_time:.4f}s, Retrieve: {chunk_retrieve_time:.4f}s, Update: {chunk_update_time:.4f}s")
                    
                    # Clean up - delete document and chunks
                    self.document_repository.delete_document(document_id_str)
                    
                finally:
                    # Clean up test file
                    try:
                        os.unlink(file_path)
                    except:
                        pass
        
        self.results["chunk_operations"] = results
        return results
    
    async def benchmark_query_performance(self):
        """Benchmark query performance"""
        print("\nBenchmarking query performance...")
        
        results = []
        
        # Load test documents if needed
        await self._load_test_documents()
        
        # Run queries
        for query in TEST_QUERIES:
            query_times = []
            token_counts = []
            source_counts = []
            
            for _ in range(self.num_runs):
                # Measure query time
                start_time = time.time()
                
                # Simple search instead of RAG query
                documents = self.document_repository.search_documents(query, limit=10)
                
                query_time = time.time() - start_time
                query_times.append(query_time)
                token_counts.append(len(query.split()))
                source_counts.append(len(documents))
            
            # Calculate average metrics
            avg_query_time = statistics.mean(query_times)
            avg_token_count = statistics.mean(token_counts)
            avg_source_count = statistics.mean(source_counts)
            
            results.append({
                "query": query,
                "avg_query_time": avg_query_time,
                "avg_token_count": avg_token_count,
                "avg_source_count": avg_source_count,
                "num_runs": self.num_runs
            })
            
            print(f"  Query: '{query[:50]}...': Time: {avg_query_time:.4f}s, Tokens: {avg_token_count:.0f}, Sources: {avg_source_count:.0f}")
        
        self.results["query_performance"] = results
        return results
    
    async def benchmark_batch_processing(self):
        """Benchmark batch document processing"""
        print("\nBenchmarking batch processing...")
        
        results = []
        
        # Ensure test folder exists
        self.document_repository._ensure_folder_exists("/benchmark")
        
        for batch_size in BATCH_SIZES:
            # Generate documents for the batch
            document_ids = []
            file_paths = []
            
            for i in range(batch_size):
                # Generate a medium-sized test file
                file_path = self.generate_test_file(50, "txt")  # 50 KB
                file_name = f"benchmark_batch_{i}_{self.db_type}.txt"
                file_paths.append(file_path)
                
                # Read file content
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Create document in the database
                document = self.document_repository.create_document(
                    filename=file_name,
                    content=content,
                    metadata={"file_type": "txt", "batch_test": True},
                    folder="/benchmark"
                )
                
                # Get document ID as string
                document_id_str = str(document.id)
                document_ids.append(document_id_str)
            
            try:
                # Measure batch processing time
                start_time = time.time()
                
                # Process each document
                for doc_id in document_ids:
                    document = self.document_repository.get_document_with_chunks(doc_id)
                    processed_document = await self.document_processor.process_document(document)
                    
                    # Ensure all chunk metadata is a simple dictionary
                    for chunk in processed_document.chunks:
                        if not isinstance(chunk.metadata, dict):
                            chunk.metadata = dict(chunk.metadata) if chunk.metadata else {}
                    
                    custom_save_document_with_chunks(self.db_session, processed_document)
                
                batch_time = time.time() - start_time
                
                # Calculate per-document time
                per_document_time = batch_time / batch_size
                
                results.append({
                    "batch_size": batch_size,
                    "total_time": batch_time,
                    "per_document_time": per_document_time
                })
                
                print(f"  Batch size {batch_size}: Total: {batch_time:.4f}s, Per document: {per_document_time:.4f}s")
                
                # Clean up - delete documents
                for doc_id in document_ids:
                    self.document_repository.delete_document(doc_id)
                
            finally:
                # Clean up test files
                for file_path in file_paths:
                    try:
                        os.unlink(file_path)
                    except:
                        pass
        
        self.results["batch_processing"] = results
        return results
    
    async def _load_test_documents(self):
        """Load test documents for query benchmarking if needed"""
        # Check if we have documents in the database
        # Use search_documents instead of list_documents
        documents = self.document_repository.search_documents("", limit=5)
        
        if len(documents) >= 5:
            print("  Using existing documents for query benchmarking")
            return
        
        print("  Loading test documents for query benchmarking...")
        
        # Ensure test folder exists
        self.document_repository._ensure_folder_exists("/benchmark")
        
        # Generate and process test documents
        for i, (size_name, size_kb) in enumerate(TEST_FILE_SIZES[:2]):  # Use only small and medium
            # Generate test files in different formats
            for file_type in ["txt", "md"]:
                file_path = self.generate_test_file(size_kb, file_type)
                file_name = f"benchmark_query_{i}_{size_name}.{file_type}"
                
                try:
                    # Read file content
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Create document in the database
                    document = self.document_repository.create_document(
                        filename=file_name,
                        content=content,
                        metadata={"file_type": file_type, "test_size": size_name, "benchmark": True},
                        folder="/benchmark"
                    )
                    
                    # Get document ID as string
                    document_id_str = str(document.id)
                    
                    # Process document
                    processed_document = await self.document_processor.process_document(document)
                    
                    # Ensure all chunk metadata is a simple dictionary
                    for chunk in processed_document.chunks:
                        if not isinstance(chunk.metadata, dict):
                            chunk.metadata = dict(chunk.metadata) if chunk.metadata else {}
                    
                    custom_save_document_with_chunks(self.db_session, processed_document)
                    
                finally:
                    # Clean up test file
                    try:
                        os.unlink(file_path)
                    except:
                        pass
    
    def save_results(self, output_dir: str = None):
        """Save benchmark results to a JSON file"""
        if output_dir is None:
            output_dir = os.path.join(project_root, "tests", "results")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"db_benchmark_{self.db_type}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save results to file
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {filepath}")
        return filepath

def generate_html_report(sqlite_results, postgres_results, output_path):
    """Generate HTML comparison report"""
    # Create HTML report
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Performance Comparison: SQLite vs PostgreSQL</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2, h3 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .chart-container { width: 100%; height: 400px; margin-bottom: 30px; }
            .winner { font-weight: bold; color: green; }
            .loser { color: #d9534f; }
            .summary { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>Database Performance Comparison: SQLite vs PostgreSQL</h1>
        <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <p>This report compares the performance of SQLite and PostgreSQL for the Metis RAG system across various operations:</p>
            <ul>
                <li>Document CRUD operations</li>
                <li>Chunk storage and retrieval</li>
                <li>Query performance</li>
                <li>Batch processing</li>
            </ul>
        </div>
        
        <h2>1. Document Operations</h2>
        <div class="chart-container">
            <canvas id="documentChart"></canvas>
        </div>
        
        <h3>Document Operations Comparison</h3>
        <table>
            <tr>
                <th>File Size</th>
                <th>Operation</th>
                <th>SQLite (s)</th>
                <th>PostgreSQL (s)</th>
                <th>Difference</th>
                <th>Faster DB</th>
            </tr>
    """
    
    # Add document operations comparison
    sqlite_doc_ops = {f"{r['size_name']}": r for r in sqlite_results["document_operations"]}
    postgres_doc_ops = {f"{r['size_name']}": r for r in postgres_results["document_operations"]}
    
    for size_name, size_kb in TEST_FILE_SIZES:
        if size_name in sqlite_doc_ops and size_name in postgres_doc_ops:
            sqlite_data = sqlite_doc_ops[size_name]
            postgres_data = postgres_doc_ops[size_name]
            
            operations = [
                ("Create", "avg_create_time"),
                ("Retrieve", "avg_retrieve_time"),
                ("Update", "avg_update_time"),
                ("Delete", "avg_delete_time"),
                ("Total", "total_avg_time")
            ]
            
            for op_name, op_key in operations:
                sqlite_time = sqlite_data[op_key]
                postgres_time = postgres_data[op_key]
                
                # Calculate difference and determine winner
                diff_pct = ((postgres_time - sqlite_time) / sqlite_time) * 100
                faster_db = "SQLite" if sqlite_time < postgres_time else "PostgreSQL"
                
                # Format cells with winner/loser styling
                sqlite_cell = f'<td class="winner">{sqlite_time:.4f}</td>' if faster_db == "SQLite" else f'<td class="loser">{sqlite_time:.4f}</td>'
                postgres_cell = f'<td class="winner">{postgres_time:.4f}</td>' if faster_db == "PostgreSQL" else f'<td class="loser">{postgres_time:.4f}</td>'
                
                html += f"""
                <tr>
                    <td>{size_name} ({size_kb} KB)</td>
                    <td>{op_name}</td>
                    {sqlite_cell}
                    {postgres_cell}
                    <td>{abs(diff_pct):.2f}%</td>
                    <td>{faster_db}</td>
                </tr>
                """
    
    html += """
        </table>
        
        <h2>2. Chunk Operations</h2>
        <div class="chart-container">
            <canvas id="chunkChart"></canvas>
        </div>
        
        <h3>Chunk Operations Comparison</h3>
        <table>
            <tr>
                <th>File Size</th>
                <th>Strategy</th>
                <th>Operation</th>
                <th>SQLite (s)</th>
                <th>PostgreSQL (s)</th>
                <th>Difference</th>
                <th>Faster DB</th>
            </tr>
    """
    
    # Add chunk operations comparison
    sqlite_chunk_ops = sqlite_results["chunk_operations"]
    postgres_chunk_ops = postgres_results["chunk_operations"]
    
    # Create lookup dictionaries
    sqlite_chunk_dict = {f"{r['size_name']}_{r['chunking_strategy']}": r for r in sqlite_chunk_ops}
    postgres_chunk_dict = {f"{r['size_name']}_{r['chunking_strategy']}": r for r in postgres_chunk_ops}
    
    for size_name, size_kb in TEST_FILE_SIZES:
        for strategy in TEST_CHUNKING_STRATEGIES:
            key = f"{size_name}_{strategy}"
            
            if key in sqlite_chunk_dict and key in postgres_chunk_dict:
                sqlite_data = sqlite_chunk_dict[key]
                postgres_data = postgres_chunk_dict[key]
                
                operations = [
                    ("Insert", "chunk_insert_time"),
                    ("Retrieve", "chunk_retrieve_time"),
                    ("Update", "chunk_update_time"),
                    ("Per-Chunk Insert", "per_chunk_insert_time"),
                    ("Per-Chunk Retrieve", "per_chunk_retrieve_time"),
                    ("Per-Chunk Update", "per_chunk_update_time")
                ]
                
                for op_name, op_key in operations:
                    sqlite_time = sqlite_data[op_key]
                    postgres_time = postgres_data[op_key]
                    
                    # Calculate difference and determine winner
                    if sqlite_time > 0:  # Avoid division by zero
                        diff_pct = ((postgres_time - sqlite_time) / sqlite_time) * 100
                    else:
                        diff_pct = 0
                        
                    faster_db = "SQLite" if sqlite_time < postgres_time else "PostgreSQL"
                    
                    # Format cells with winner/loser styling
                    sqlite_cell = f'<td class="winner">{sqlite_time:.4f}</td>' if faster_db == "SQLite" else f'<td class="loser">{sqlite_time:.4f}</td>'
                    postgres_cell = f'<td class="winner">{postgres_time:.4f}</td>' if faster_db == "PostgreSQL" else f'<td class="loser">{postgres_time:.4f}</td>'
                    
                    html += f"""
                    <tr>
                        <td>{size_name} ({size_kb} KB)</td>
                        <td>{strategy}</td>
                        <td>{op_name}</td>
                        {sqlite_cell}
                        {postgres_cell}
                        <td>{abs(diff_pct):.2f}%</td>
                        <td>{faster_db}</td>
                    </tr>
                    """
    
    html += """
        </table>
        
        <h2>3. Query Performance</h2>
        <div class="chart-container">
            <canvas id="queryChart"></canvas>
        </div>
        
        <h3>Query Performance Comparison</h3>
        <table>
            <tr>
                <th>Query</th>
                <th>SQLite (s)</th>
                <th>PostgreSQL (s)</th>
                <th>Difference</th>
                <th>Faster DB</th>
            </tr>
    """
    
    # Add query performance comparison
    sqlite_query_ops = {r["query"]: r for r in sqlite_results["query_performance"]}
    postgres_query_ops = {r["query"]: r for r in postgres_results["query_performance"]}
    
    for query in TEST_QUERIES:
        if query in sqlite_query_ops and query in postgres_query_ops:
            sqlite_data = sqlite_query_ops[query]
            postgres_data = postgres_query_ops[query]
            
            sqlite_time = sqlite_data["avg_query_time"]
            postgres_time = postgres_data["avg_query_time"]
            
            # Calculate difference and determine winner
            diff_pct = ((postgres_time - sqlite_time) / sqlite_time) * 100
            faster_db = "SQLite" if sqlite_time < postgres_time else "PostgreSQL"
            
            # Format cells with winner/loser styling
            sqlite_cell = f'<td class="winner">{sqlite_time:.4f}</td>' if faster_db == "SQLite" else f'<td class="loser">{sqlite_time:.4f}</td>'
            postgres_cell = f'<td class="winner">{postgres_time:.4f}</td>' if faster_db == "PostgreSQL" else f'<td class="loser">{postgres_time:.4f}</td>'
            
            # Truncate query if too long
            query_display = query[:50] + "..." if len(query) > 50 else query
            
            html += f"""
            <tr>
                <td>{query_display}</td>
                {sqlite_cell}
                {postgres_cell}
                <td>{abs(diff_pct):.2f}%</td>
                <td>{faster_db}</td>
            </tr>
            """
    
    html += """
        </table>
        
        <h2>4. Batch Processing</h2>
        <div class="chart-container">
            <canvas id="batchChart"></canvas>
        </div>
        
        <h3>Batch Processing Comparison</h3>
        <table>
            <tr>
                <th>Batch Size</th>
                <th>Metric</th>
                <th>SQLite (s)</th>
                <th>PostgreSQL (s)</th>
                <th>Difference</th>
                <th>Faster DB</th>
            </tr>
    """
    
    # Add batch processing comparison
    sqlite_batch_ops = {r["batch_size"]: r for r in sqlite_results["batch_processing"]}
    postgres_batch_ops = {r["batch_size"]: r for r in postgres_results["batch_processing"]}
    
    for batch_size in BATCH_SIZES:
        if batch_size in sqlite_batch_ops and batch_size in postgres_batch_ops:
            sqlite_data = sqlite_batch_ops[batch_size]
            postgres_data = postgres_batch_ops[batch_size]
            
            metrics = [
                ("Total Time", "total_time"),
                ("Per-Document Time", "per_document_time")
            ]
            
            for metric_name, metric_key in metrics:
                sqlite_time = sqlite_data[metric_key]
                postgres_time = postgres_data[metric_key]
                
                # Calculate difference and determine winner
                diff_pct = ((postgres_time - sqlite_time) / sqlite_time) * 100
                faster_db = "SQLite" if sqlite_time < postgres_time else "PostgreSQL"
                
                # Format cells with winner/loser styling
                sqlite_cell = f'<td class="winner">{sqlite_time:.4f}</td>' if faster_db == "SQLite" else f'<td class="loser">{sqlite_time:.4f}</td>'
                postgres_cell = f'<td class="winner">{postgres_time:.4f}</td>' if faster_db == "PostgreSQL" else f'<td class="loser">{postgres_time:.4f}</td>'
                
                html += f"""
                <tr>
                    <td>{batch_size}</td>
                    <td>{metric_name}</td>
                    {sqlite_cell}
                    {postgres_cell}
                    <td>{abs(diff_pct):.2f}%</td>
                    <td>{faster_db}</td>
                </tr>
                """
    
    # Prepare data for charts
    sqlite_doc_create_times = [sqlite_doc_ops.get(size[0], {}).get("avg_create_time", 0) for size in TEST_FILE_SIZES]
    postgres_doc_create_times = [postgres_doc_ops.get(size[0], {}).get("avg_create_time", 0) for size in TEST_FILE_SIZES]
    
    sqlite_doc_retrieve_times = [sqlite_doc_ops.get(size[0], {}).get("avg_retrieve_time", 0) for size in TEST_FILE_SIZES]
    postgres_doc_retrieve_times = [postgres_doc_ops.get(size[0], {}).get("avg_retrieve_time", 0) for size in TEST_FILE_SIZES]
    
    # Prepare query data
    query_labels = [f"Query {i+1}" for i in range(len(TEST_QUERIES))]
    sqlite_query_times = [sqlite_query_ops.get(query, {}).get("avg_query_time", 0) for query in TEST_QUERIES]
    postgres_query_times = [postgres_query_ops.get(query, {}).get("avg_query_time", 0) for query in TEST_QUERIES]
    
    # Prepare batch data
    sqlite_batch_times = [sqlite_batch_ops.get(size, {}).get("total_time", 0) for size in BATCH_SIZES]
    postgres_batch_times = [postgres_batch_ops.get(size, {}).get("total_time", 0) for size in BATCH_SIZES]
    
    # Calculate overall recommendations
    sqlite_doc_total = sum(sqlite_doc_create_times) + sum(sqlite_doc_retrieve_times)
    postgres_doc_total = sum(postgres_doc_create_times) + sum(postgres_doc_retrieve_times)
    
    sqlite_chunk_total = sum([r.get("chunk_insert_time", 0) for r in sqlite_chunk_ops])
    postgres_chunk_total = sum([r.get("chunk_insert_time", 0) for r in postgres_chunk_ops])
    
    sqlite_query_total = sum(sqlite_query_times)
    postgres_query_total = sum(postgres_query_times)
    
    sqlite_batch_total = sum(sqlite_batch_times)
    postgres_batch_total = sum(postgres_batch_times)
    
    doc_winner = "SQLite" if sqlite_doc_total < postgres_doc_total else "PostgreSQL"
    chunk_winner = "SQLite" if sqlite_chunk_total < postgres_chunk_total else "PostgreSQL"
    query_winner = "SQLite" if sqlite_query_total < postgres_query_total else "PostgreSQL"
    batch_winner = "SQLite" if sqlite_batch_total < postgres_batch_total else "PostgreSQL"
    
    overall_sqlite = sqlite_doc_total + sqlite_chunk_total + sqlite_query_total + sqlite_batch_total
    overall_postgres = postgres_doc_total + postgres_chunk_total + postgres_query_total + postgres_batch_total
    overall_winner = "SQLite" if overall_sqlite < overall_postgres else "PostgreSQL"
    
    # Convert data to JSON strings for JavaScript
    file_size_labels = [size[0] for size in TEST_FILE_SIZES]
    
    html += f"""
        </table>
        
        <h2>5. Recommendations</h2>
        <div class="summary">
            <p>Based on the benchmark results, here are some recommendations:</p>
            <ul>
                <li><strong>Document Operations:</strong> {doc_winner} performs better for basic document operations.</li>
                <li><strong>Chunk Operations:</strong> {chunk_winner} is more efficient for chunk storage and retrieval.</li>
                <li><strong>Query Performance:</strong> {query_winner} provides faster query response times.</li>
                <li><strong>Batch Processing:</strong> {batch_winner} handles batch processing more efficiently.</li>
            </ul>
            <p><strong>Overall Recommendation:</strong> {overall_winner} appears to be the better choice for this workload based on overall performance.</p>
        </div>
        
        <script>
            // Document operations chart
            const docCtx = document.getElementById('documentChart').getContext('2d');
            const docChart = new Chart(docCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(file_size_labels)},
                    datasets: [
                        {{
                            label: 'SQLite - Create',
                            data: {json.dumps(sqlite_doc_create_times)},
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'PostgreSQL - Create',
                            data: {json.dumps(postgres_doc_create_times)},
                            backgroundColor: 'rgba(255, 99, 132, 0.6)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'SQLite - Retrieve',
                            data: {json.dumps(sqlite_doc_retrieve_times)},
                            backgroundColor: 'rgba(75, 192, 192, 0.6)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'PostgreSQL - Retrieve',
                            data: {json.dumps(postgres_doc_retrieve_times)},
                            backgroundColor: 'rgba(255, 159, 64, 0.6)',
                            borderColor: 'rgba(255, 159, 64, 1)',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Document Operation Times by File Size'
                        }},
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Time (seconds)'
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'File Size'
                            }}
                        }}
                    }}
                }}
            }});
            
            // Query performance chart
            const queryCtx = document.getElementById('queryChart').getContext('2d');
            const queryChart = new Chart(queryCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(query_labels)},
                    datasets: [
                        {{
                            label: 'SQLite',
                            data: {json.dumps(sqlite_query_times)},
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'PostgreSQL',
                            data: {json.dumps(postgres_query_times)},
                            backgroundColor: 'rgba(255, 99, 132, 0.6)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Query Response Times'
                        }},
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Time (seconds)'
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Query'
                            }}
                        }}
                    }}
                }}
            }});
            
            // Batch processing chart
            const batchCtx = document.getElementById('batchChart').getContext('2d');
            const batchChart = new Chart(batchCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(BATCH_SIZES)},
                    datasets: [
                        {{
                            label: 'SQLite',
                            data: {json.dumps(sqlite_batch_times)},
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'PostgreSQL',
                            data: {json.dumps(postgres_batch_times)},
                            backgroundColor: 'rgba(255, 99, 132, 0.6)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Batch Processing Times'
                        }},
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Time (seconds)'
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Batch Size'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Save HTML report
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"\nHTML comparison report saved to: {output_path}")

async def run_benchmark(args):
    """Run the database benchmark"""
    print(f"\nRunning database performance benchmark for {args.db_type}...")
    
    # Create benchmark instance
    benchmark = DatabaseBenchmark(args.db_type, args.runs)
    
    try:
        # Run benchmarks
        await benchmark.benchmark_document_operations()
        await benchmark.benchmark_chunk_operations()
        await benchmark.benchmark_query_performance()
        await benchmark.benchmark_batch_processing()
        
        # Save results
        results_file = benchmark.save_results()
        
        # Store results file path for HTML report generation
        if args.db_type == "sqlite":
            args.sqlite_results = results_file
        else:
            args.postgres_results = results_file
        
        print("\nBenchmark completed successfully!")
        return 0
    except Exception as e:
        print(f"Error running benchmark: {e}")
        return 1
    finally:
        benchmark.cleanup()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Database Performance Benchmarking for Metis RAG")
    parser.add_argument("--db-type", type=str, choices=["sqlite", "postgresql"],
                        help="Database type to benchmark")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs for each test")
    parser.add_argument("--sqlite-results", type=str, help="Path to SQLite results JSON file (for HTML report)")
    parser.add_argument("--postgres-results", type=str, help="Path to PostgreSQL results JSON file (for HTML report)")
    parser.add_argument("--report-only", action="store_true", help="Generate HTML report only without running benchmarks")
    args = parser.parse_args()
    
    # Check if we're only generating a report
    if args.report_only:
        if not args.sqlite_results or not args.postgres_results:
            print("Error: --sqlite-results and --postgres-results are required with --report-only")
            return 1
            
        # Load results
        try:
            with open(args.sqlite_results, 'r') as f:
                sqlite_results = json.load(f)
            
            with open(args.postgres_results, 'r') as f:
                postgres_results = json.load(f)
                
            # Create results directory if it doesn't exist
            results_dir = os.path.join(project_root, "tests", "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # Create HTML report filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = os.path.join(results_dir, f"db_comparison_report_{timestamp}.html")
            
            # Generate HTML report
            generate_html_report(sqlite_results, postgres_results, html_path)
            return 0
        except Exception as e:
            print(f"Error generating report: {e}")
            return 1
    
    # Otherwise, run the benchmark
    if not args.db_type:
        print("Error: --db-type is required when running benchmarks")
        return 1
        
    # Run benchmark
    result = asyncio.run(run_benchmark(args))
    
    # Generate HTML report if requested and both result files are available
    if args.html and hasattr(args, 'sqlite_results') and hasattr(args, 'postgres_results'):
        # Load results
        with open(args.sqlite_results, 'r') as f:
            sqlite_results = json.load(f)
        
        with open(args.postgres_results, 'r') as f:
            postgres_results = json.load(f)
        
        # Create results directory if it doesn't exist
        results_dir = os.path.join(project_root, "tests", "results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Create HTML report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = os.path.join(results_dir, f"db_comparison_report_{timestamp}.html")
        
        # Generate HTML report
        generate_html_report(sqlite_results, postgres_results, html_path)
    
    return result

if __name__ == "__main__":
    sys.exit(main())