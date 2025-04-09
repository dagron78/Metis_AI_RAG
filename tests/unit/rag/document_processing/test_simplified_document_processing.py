import os
import time
import asyncio
import pytest
import statistics
import tempfile
import uuid
from typing import List, Dict, Any
from pathlib import Path

# Test configuration
TEST_FILE_SIZES = [
    ("small", 5),      # 5 KB
    ("medium", 50),    # 50 KB
    ("large", 500)     # 500 KB
]

TEST_CHUNKING_STRATEGIES = [
    "recursive",
    "token",
    "markdown"
]

# Number of times to run each test for averaging
NUM_RUNS = 2

class MockDocument:
    """Mock Document class for testing"""
    
    def __init__(self, id, filename, content="", metadata=None, folder="/"):
        self.id = id
        self.filename = filename
        self.content = content
        self.metadata = metadata or {}
        self.folder = folder
        self.chunks = []

class MockDocumentProcessor:
    """Mock DocumentProcessor for testing"""
    
    def __init__(self, chunking_strategy="recursive", chunk_size=1500, chunk_overlap=150):
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def process_document(self, document):
        """
        Mock document processing
        """
        # Simulate processing time based on document size and chunking strategy
        file_size = len(document.content)
        
        # Different strategies have different processing times
        if self.chunking_strategy == "recursive":
            processing_time = 0.5 + (file_size * 0.0001)
        elif self.chunking_strategy == "token":
            processing_time = 0.7 + (file_size * 0.00015)
        elif self.chunking_strategy == "markdown":
            processing_time = 0.6 + (file_size * 0.00012)
        else:
            processing_time = 0.5 + (file_size * 0.0001)
        
        # Simulate processing
        await asyncio.sleep(processing_time)
        
        # Create chunks
        chunk_count = max(1, file_size // self.chunk_size)
        document.chunks = [{"id": f"chunk_{i}", "content": f"Chunk {i} content"} for i in range(chunk_count)]
        
        return document

class MockDocumentAnalysisService:
    """Mock DocumentAnalysisService for testing"""
    
    async def analyze_document(self, document):
        """
        Mock document analysis
        """
        # Simulate analysis time based on document size
        file_size = len(document.content)
        analysis_time = 0.3 + (file_size * 0.00005)
        
        # Simulate analysis
        await asyncio.sleep(analysis_time)
        
        # Determine recommended strategy based on file type
        file_type = document.metadata.get("file_type", "")
        if file_type == "md":
            strategy = "markdown"
        elif file_type == "code":
            strategy = "token"
        else:
            strategy = "recursive"
        
        return {
            "strategy": strategy,
            "parameters": {
                "chunk_size": 1500,
                "chunk_overlap": 150
            },
            "justification": f"Recommended strategy for {file_type} files"
        }

def generate_test_file(size_kb: int, file_type: str = "txt"):
    """Generate test content of the specified size"""
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
    
    return content

async def process_document(document_processor, document, chunking_strategy: str):
    """Process a document and measure performance"""
    start_time = time.time()
    
    # Configure processor with the specified chunking strategy
    processor = MockDocumentProcessor(
        chunking_strategy=chunking_strategy,
        chunk_size=1500,
        chunk_overlap=150
    )
    
    # Process document
    processed_document = await processor.process_document(document)
    
    elapsed_time = time.time() - start_time
    
    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "chunking_strategy": chunking_strategy,
        "elapsed_time": elapsed_time,
        "chunk_count": len(processed_document.chunks),
        "file_size": len(document.content)
    }

async def analyze_document(document_analysis_service, document):
    """Analyze a document and measure performance"""
    start_time = time.time()
    
    # Analyze document
    analysis_result = await document_analysis_service.analyze_document(document)
    
    elapsed_time = time.time() - start_time
    
    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "elapsed_time": elapsed_time,
        "recommended_strategy": analysis_result.get("strategy"),
        "file_size": len(document.content)
    }

async def run_processing_tests():
    """Run document processing performance tests"""
    results = []
    
    for size_name, size_kb in TEST_FILE_SIZES:
        for file_type in ["txt", "md"]:
            # Generate test content
            content = generate_test_file(size_kb, file_type)
            file_name = f"test_{size_name}.{file_type}"
            
            # Create document
            document_id = uuid.uuid4()
            document = MockDocument(
                id=document_id,
                filename=file_name,
                content=content,
                metadata={"file_type": file_type, "test_size": size_name},
                folder="/test"
            )
            
            # Test each chunking strategy
            for strategy in TEST_CHUNKING_STRATEGIES:
                strategy_results = []
                
                for _ in range(NUM_RUNS):
                    result = await process_document(None, document, strategy)
                    strategy_results.append(result)
                
                # Calculate average metrics
                avg_time = statistics.mean([r["elapsed_time"] for r in strategy_results])
                avg_chunk_count = statistics.mean([r["chunk_count"] for r in strategy_results])
                
                results.append({
                    "document_id": str(document.id),
                    "filename": file_name,
                    "file_type": file_type,
                    "size_name": size_name,
                    "size_kb": size_kb,
                    "chunking_strategy": strategy,
                    "avg_elapsed_time": avg_time,
                    "avg_chunk_count": avg_chunk_count,
                    "num_runs": NUM_RUNS
                })
    
    return results

async def run_analysis_tests():
    """Run document analysis performance tests"""
    results = []
    
    for size_name, size_kb in TEST_FILE_SIZES:
        for file_type in ["txt", "md"]:
            # Generate test content
            content = generate_test_file(size_kb, file_type)
            file_name = f"test_analysis_{size_name}.{file_type}"
            
            # Create document
            document_id = uuid.uuid4()
            document = MockDocument(
                id=document_id,
                filename=file_name,
                content=content,
                metadata={"file_type": file_type, "test_size": size_name},
                folder="/test"
            )
            
            # Create document analysis service
            document_analysis_service = MockDocumentAnalysisService()
            
            # Run analysis multiple times
            analysis_results = []
            for _ in range(NUM_RUNS):
                result = await analyze_document(document_analysis_service, document)
                analysis_results.append(result)
            
            # Calculate average metrics
            avg_time = statistics.mean([r["elapsed_time"] for r in analysis_results])
            
            results.append({
                "document_id": str(document.id),
                "filename": file_name,
                "file_type": file_type,
                "size_name": size_name,
                "size_kb": size_kb,
                "avg_elapsed_time": avg_time,
                "recommended_strategy": analysis_results[0]["recommended_strategy"],
                "num_runs": NUM_RUNS
            })
    
    return results

@pytest.mark.asyncio
async def test_document_processing_performance():
    """Test document processing performance"""
    print(f"\nRunning document processing performance test with {len(TEST_FILE_SIZES)} file sizes, {len(TEST_CHUNKING_STRATEGIES)} chunking strategies")
    
    # Run processing tests
    results = await run_processing_tests()
    
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
async def test_document_analysis_performance():
    """Test document analysis performance"""
    print(f"\nRunning document analysis performance test with {len(TEST_FILE_SIZES)} file sizes")
    
    # Run analysis tests
    results = await run_analysis_tests()
    
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
    asyncio.run(test_document_processing_performance())
    asyncio.run(test_document_analysis_performance())