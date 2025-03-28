#!/usr/bin/env python3
"""
Chunking Strategy Optimization Script for Metis RAG

This script tests different chunking strategies and parameters to find the optimal
configuration for each database backend (SQLite and PostgreSQL).

Usage:
    python optimize_chunking_strategy.py --db-type sqlite|postgresql [--runs 3] [--output-file chunking_recommendations.json]
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
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.session import Base, engine, SessionLocal
from app.db.repositories.document_repository import DocumentRepository
from app.models.document import Document, Chunk
from app.core.config import SETTINGS, DATABASE_TYPE, DATABASE_URL
from app.db.models import Document as DBDocument, Chunk as DBChunk
from app.db.adapters import to_uuid_or_str

# Import custom functions from benchmark script
from scripts.benchmark_database_performance import custom_pydantic_chunk_to_sqlalchemy, custom_save_document_with_chunks

# Test configuration
TEST_FILE_SIZES = [
    ("small", 5),      # 5 KB
    ("medium", 50),    # 50 KB
    ("large", 500),    # 500 KB
    ("xlarge", 2000)   # 2 MB
]

# Chunking strategies to test
CHUNKING_STRATEGIES = [
    "recursive",
    "token",
    "markdown",
    "semantic"
]

# Chunk size parameters to test
CHUNK_SIZES = [
    500,    # Small chunks
    1000,   # Medium chunks
    2000,   # Large chunks
    4000    # Extra large chunks
]

# Chunk overlap parameters to test
CHUNK_OVERLAPS = [
    50,     # Minimal overlap
    100,    # Small overlap
    200,    # Medium overlap
    400     # Large overlap
]

class ChunkingStrategyOptimizer:
    """Chunking strategy optimization class"""
    
    def __init__(self, db_type: str, num_runs: int = 3):
        self.db_type = db_type
        self.num_runs = num_runs
        self.results = {
            "metadata": {
                "db_type": db_type,
                "timestamp": datetime.now().isoformat(),
                "num_runs": num_runs
            },
            "strategy_results": [],
            "recommendations": {}
        }
        
        # Initialize database session
        self.db_session = SessionLocal()
        
        # Initialize repositories
        self.document_repository = DocumentRepository(self.db_session)
        
        # Create folders in database
        self._ensure_folders_exist()
        
        print(f"Initialized chunking optimizer for {db_type} database")
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
            
            # Check if optimization folder exists
            opt_folder = self.db_session.query(Folder).filter(Folder.path == "/optimization").first()
            if not opt_folder:
                # Create optimization folder
                opt_folder = Folder(
                    path="/optimization",
                    name="Optimization",
                    parent_path="/"
                )
                self.db_session.add(opt_folder)
                self.db_session.commit()
                print("Created optimization folder in database")
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
    
    class CustomChunkingStrategy:
        """Custom chunking strategy for testing different parameters"""
        
        def __init__(self, strategy: str, chunk_size: int, chunk_overlap: int):
            self.strategy = strategy
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            
        async def process_document(self, document: Document) -> Document:
            """Process a document by splitting it into chunks"""
            from app.rag.document_processor import DocumentProcessor
            
            # Create a document processor with the specified parameters
            processor = DocumentProcessor(
                chunking_strategy=self.strategy,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            
            # Process the document
            processed_document = await processor.process_document(document)
            
            # Ensure all chunk metadata is a simple dictionary
            for chunk in processed_document.chunks:
                if not isinstance(chunk.metadata, dict):
                    chunk.metadata = dict(chunk.metadata) if chunk.metadata else {}
            
            return processed_document
    
    async def test_chunking_strategy(self, strategy: str, chunk_size: int, chunk_overlap: int, file_size: Tuple[str, int]) -> Dict[str, Any]:
        """Test a specific chunking strategy with given parameters"""
        size_name, size_kb = file_size
        
        # Generate test files in different formats
        results = []
        
        for file_type in ["txt", "md"]:
            # Generate test file
            file_path = self.generate_test_file(size_kb, file_type)
            file_name = f"opt_{size_name}_{strategy}_{chunk_size}_{chunk_overlap}_{self.db_type}.{file_type}"
            
            try:
                # Read file content
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Create document in the database
                document = self.document_repository.create_document(
                    filename=file_name,
                    content=content,
                    metadata={
                        "file_type": file_type, 
                        "test_size": size_name, 
                        "optimization": True,
                        "strategy": strategy,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    },
                    folder="/optimization"
                )
                
                # Get document ID as string
                document_id_str = str(document.id)
                
                # Create chunking strategy
                chunking_strategy = self.CustomChunkingStrategy(strategy, chunk_size, chunk_overlap)
                
                # Process times
                process_times = []
                chunk_counts = []
                insert_times = []
                retrieve_times = []
                
                for _ in range(self.num_runs):
                    # Measure document processing time
                    start_time = time.time()
                    processed_document = await chunking_strategy.process_document(document)
                    process_time = time.time() - start_time
                    
                    # Record chunk count
                    chunk_count = len(processed_document.chunks)
                    
                    # Measure chunk insertion time
                    start_time = time.time()
                    custom_save_document_with_chunks(self.db_session, processed_document)
                    insert_time = time.time() - start_time
                    
                    # Measure chunk retrieval time
                    start_time = time.time()
                    retrieved_document = self.document_repository.get_document_with_chunks(document_id_str)
                    retrieve_time = time.time() - start_time
                    
                    # Record times
                    process_times.append(process_time)
                    chunk_counts.append(chunk_count)
                    insert_times.append(insert_time)
                    retrieve_times.append(retrieve_time)
                
                # Calculate average metrics
                avg_process_time = statistics.mean(process_times)
                avg_chunk_count = statistics.mean(chunk_counts)
                avg_insert_time = statistics.mean(insert_times)
                avg_retrieve_time = statistics.mean(retrieve_times)
                
                # Calculate per-chunk times
                per_chunk_process_time = avg_process_time / avg_chunk_count if avg_chunk_count > 0 else 0
                per_chunk_insert_time = avg_insert_time / avg_chunk_count if avg_chunk_count > 0 else 0
                per_chunk_retrieve_time = avg_retrieve_time / avg_chunk_count if avg_chunk_count > 0 else 0
                
                # Calculate overall score (lower is better)
                # Weight factors can be adjusted based on importance
                process_weight = 0.3
                insert_weight = 0.4
                retrieve_weight = 0.3
                
                overall_score = (
                    process_weight * per_chunk_process_time +
                    insert_weight * per_chunk_insert_time +
                    retrieve_weight * per_chunk_retrieve_time
                )
                
                result = {
                    "file_type": file_type,
                    "size_name": size_name,
                    "size_kb": size_kb,
                    "strategy": strategy,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "avg_chunk_count": avg_chunk_count,
                    "avg_process_time": avg_process_time,
                    "avg_insert_time": avg_insert_time,
                    "avg_retrieve_time": avg_retrieve_time,
                    "per_chunk_process_time": per_chunk_process_time,
                    "per_chunk_insert_time": per_chunk_insert_time,
                    "per_chunk_retrieve_time": per_chunk_retrieve_time,
                    "overall_score": overall_score
                }
                
                results.append(result)
                
                print(f"  {file_type}, {size_name} ({size_kb} KB), {strategy}, size={chunk_size}, overlap={chunk_overlap}: " +
                      f"Chunks: {avg_chunk_count:.1f}, Process: {avg_process_time:.4f}s, " +
                      f"Insert: {avg_insert_time:.4f}s, Retrieve: {avg_retrieve_time:.4f}s, " +
                      f"Score: {overall_score:.6f}")
                
                # Clean up - delete document and chunks
                self.document_repository.delete_document(document_id_str)
                
            finally:
                # Clean up test file
                try:
                    os.unlink(file_path)
                except:
                    pass
        
        return {
            "size_name": size_name,
            "size_kb": size_kb,
            "strategy": strategy,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "results": results
        }
    
    async def optimize_chunking_strategies(self):
        """Test different chunking strategies and parameters"""
        print("\nOptimizing chunking strategies...")
        
        # Ensure test folder exists
        self.document_repository._ensure_folder_exists("/optimization")
        
        # Test each combination of parameters
        for size_tuple in TEST_FILE_SIZES:
            for strategy in CHUNKING_STRATEGIES:
                for chunk_size in CHUNK_SIZES:
                    for chunk_overlap in CHUNK_OVERLAPS:
                        # Skip invalid combinations
                        if chunk_overlap >= chunk_size:
                            continue
                            
                        # Test this combination
                        result = await self.test_chunking_strategy(strategy, chunk_size, chunk_overlap, size_tuple)
                        self.results["strategy_results"].append(result)
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.results
    
    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        # Group results by file size and type
        grouped_results = {}
        
        for result in self.results["strategy_results"]:
            for file_result in result["results"]:
                key = f"{file_result['size_name']}_{file_result['file_type']}"
                if key not in grouped_results:
                    grouped_results[key] = []
                grouped_results[key].append(file_result)
        
        # Find best strategy for each file size and type
        recommendations = {}
        
        for key, results in grouped_results.items():
            # Sort by overall score (lower is better)
            sorted_results = sorted(results, key=lambda x: x["overall_score"])
            
            # Get best result
            best_result = sorted_results[0]
            
            # Create recommendation
            recommendation = {
                "file_type": best_result["file_type"],
                "size_name": best_result["size_name"],
                "size_kb": best_result["size_kb"],
                "strategy": best_result["strategy"],
                "chunk_size": best_result["chunk_size"],
                "chunk_overlap": best_result["chunk_overlap"],
                "avg_chunk_count": best_result["avg_chunk_count"],
                "overall_score": best_result["overall_score"],
                "justification": f"This configuration provides the best balance of processing speed, " +
                                f"database insertion performance, and retrieval performance for " +
                                f"{best_result['size_name']} {best_result['file_type']} files."
            }
            
            recommendations[key] = recommendation
        
        # Add recommendations to results
        self.results["recommendations"] = recommendations
        
        # Print recommendations
        print("\nRecommended chunking strategies:")
        for key, recommendation in recommendations.items():
            print(f"  {recommendation['size_name']} {recommendation['file_type']}: " +
                  f"Strategy: {recommendation['strategy']}, " +
                  f"Size: {recommendation['chunk_size']}, " +
                  f"Overlap: {recommendation['chunk_overlap']}")
    
    def save_results(self, output_file: str = None):
        """Save optimization results to a JSON file"""
        if output_file is None:
            # Create results directory if it doesn't exist
            results_dir = os.path.join(project_root, "tests", "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(results_dir, f"chunking_optimization_{self.db_type}_{timestamp}.json")
        
        # Save results to file
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_file}")
        return output_file

async def run_optimization(args):
    """Run the chunking strategy optimization"""
    print(f"\nRunning chunking strategy optimization for {args.db_type}...")
    
    # Create optimizer instance
    optimizer = ChunkingStrategyOptimizer(args.db_type, args.runs)
    
    try:
        # Run optimization
        await optimizer.optimize_chunking_strategies()
        
        # Save results
        optimizer.save_results(args.output_file)
        
        print("\nOptimization completed successfully!")
        return 0
    except Exception as e:
        print(f"Error running optimization: {e}")
        return 1
    finally:
        optimizer.cleanup()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Chunking Strategy Optimization for Metis RAG")
    parser.add_argument("--db-type", type=str, choices=["sqlite", "postgresql"], required=True,
                        help="Database type to optimize for")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs for each test")
    parser.add_argument("--output-file", type=str, help="Output file path for optimization results")
    args = parser.parse_args()
    
    # Run optimization
    result = asyncio.run(run_optimization(args))
    
    return result

if __name__ == "__main__":
    sys.exit(main())