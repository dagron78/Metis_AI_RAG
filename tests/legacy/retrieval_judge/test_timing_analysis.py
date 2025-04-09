#!/usr/bin/env python3
"""
Test script to analyze the timing differences between standard retrieval and judge-enhanced retrieval.
This script:
1. Creates a test document
2. Runs multiple queries with detailed timing measurements
3. Analyzes the timing differences between components
"""

import os
import sys
import json
import asyncio
import logging
import uuid
import time
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_timing_analysis")

# Import RAG components
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.agents.retrieval_judge import RetrievalJudge
from app.models.document import Document, Chunk

# Define the model to use for the Retrieval Judge
JUDGE_MODEL = "gemma3:4b"

# Test document content
TEST_DOCUMENT = """# Metis RAG Technical Documentation

## Introduction

This document provides technical documentation for the Metis RAG system, a Retrieval-Augmented Generation platform designed for enterprise knowledge management.

## Architecture Overview

Metis RAG follows a modular architecture with the following components:

### Frontend Layer

The frontend is built with HTML, CSS, and JavaScript, providing an intuitive interface for:
- Document management
- Chat interactions
- System configuration
- Analytics and monitoring

### API Layer

The API layer is implemented using FastAPI and provides endpoints for:
- Document upload and management
- Chat interactions
- System configuration
- Analytics data retrieval

### RAG Engine

The core RAG engine consists of:

#### Document Processing

The document processing pipeline handles:
- File validation and parsing
- Text extraction
- Chunking with configurable strategies
- Metadata extraction

#### Vector Store

The vector store is responsible for:
- Storing document embeddings
- Efficient similarity search
- Metadata filtering

#### LLM Integration

The LLM integration component:
- Connects to Ollama for local LLM inference
- Manages prompt templates
- Handles context window optimization
"""

# Test queries
TEST_QUERIES = [
    "What is the architecture of Metis RAG?",
    "What are the components of the RAG engine?",
    "How does the vector store work?",
    "What is the role of the LLM integration component?",
    "How does the document processing pipeline work?"
]

class TimingTracker:
    """Helper class to track timing of operations"""
    def __init__(self):
        self.timings = {}
        self.current_operation = None
        self.start_time = None
    
    def start(self, operation):
        """Start timing an operation"""
        self.current_operation = operation
        self.start_time = time.time()
        logger.info(f"Starting operation: {operation}")
    
    def stop(self):
        """Stop timing the current operation"""
        if self.current_operation and self.start_time:
            elapsed = time.time() - self.start_time
            self.timings[self.current_operation] = elapsed
            logger.info(f"Completed operation: {self.current_operation} in {elapsed:.2f}s")
            self.current_operation = None
            self.start_time = None
    
    def get_summary(self):
        """Get a summary of all timings"""
        return self.timings

async def create_test_document():
    """Create a test document for RAG testing"""
    logger.info("Creating test document...")
    
    # Create directory for test document
    test_dir = os.path.join("tests", "retrieval_judge", "data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create document file
    doc_path = os.path.join(test_dir, "timing_test_document.md")
    with open(doc_path, "w") as f:
        f.write(TEST_DOCUMENT)
    
    logger.info(f"Created test document at {os.path.abspath(doc_path)}")
    return doc_path

async def process_document(doc_path):
    """Process the test document and add it to the vector store"""
    logger.info("Processing test document...")
    
    # Read file content
    with open(doc_path, "r") as f:
        doc_content = f.read()
    
    # Create Document object
    document = Document(
        id=str(uuid.uuid4()),
        filename="timing_test_document.md",
        content=doc_content,
        tags=["technical", "documentation", "architecture"],
        folder="/test"
    )
    
    # Create a vector store
    test_persist_dir = os.path.join("tests", "retrieval_judge", "timing_test_chroma_db")
    os.makedirs(test_persist_dir, exist_ok=True)
    vector_store = VectorStore(persist_directory=test_persist_dir)
    
    # Create chunks
    document.chunks = [
        Chunk(
            id=str(uuid.uuid4()),
            content=doc_content,
            metadata={
                "index": 0,
                "source": doc_path,
                "document_id": document.id
            }
        )
    ]
    
    # Add document to vector store
    await vector_store.add_document(document)
    
    logger.info(f"Added document {document.id} to vector store")
    
    return document, vector_store

class InstrumentedRetrievalJudge(RetrievalJudge):
    """Instrumented version of RetrievalJudge that tracks timing"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings = {}
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Instrumented version of analyze_query"""
        start_time = time.time()
        result = await super().analyze_query(query)
        elapsed = time.time() - start_time
        self.timings["analyze_query"] = elapsed
        logger.info(f"analyze_query took {elapsed:.2f}s")
        return result
    
    async def evaluate_chunks(self, query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Instrumented version of evaluate_chunks"""
        start_time = time.time()
        result = await super().evaluate_chunks(query, chunks)
        elapsed = time.time() - start_time
        self.timings["evaluate_chunks"] = elapsed
        logger.info(f"evaluate_chunks took {elapsed:.2f}s")
        return result
    
    async def optimize_context(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Instrumented version of optimize_context"""
        start_time = time.time()
        result = await super().optimize_context(query, chunks)
        elapsed = time.time() - start_time
        self.timings["optimize_context"] = elapsed
        logger.info(f"optimize_context took {elapsed:.2f}s")
        return result

class InstrumentedRAGEngine(RAGEngine):
    """Instrumented version of RAGEngine that tracks timing"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings = {}
    
    async def _enhanced_retrieval(self, *args, **kwargs):
        """Instrumented version of _enhanced_retrieval"""
        start_time = time.time()
        result = await super()._enhanced_retrieval(*args, **kwargs)
        elapsed = time.time() - start_time
        self.timings["enhanced_retrieval"] = elapsed
        logger.info(f"enhanced_retrieval took {elapsed:.2f}s")
        return result

async def run_timing_tests(vector_store):
    """Run timing tests for standard and judge-enhanced retrieval"""
    logger.info("Running timing tests...")
    
    # Create OllamaClient
    ollama_client = OllamaClient()
    
    # Create instrumented Retrieval Judge
    logger.info(f"Creating Retrieval Judge with model: {JUDGE_MODEL}")
    retrieval_judge = InstrumentedRetrievalJudge(ollama_client=ollama_client, model=JUDGE_MODEL)
    
    # Create engines
    rag_engine_with_judge = InstrumentedRAGEngine(
        vector_store=vector_store,
        ollama_client=ollama_client,
        retrieval_judge=retrieval_judge
    )
    
    rag_engine_standard = RAGEngine(
        vector_store=vector_store,
        ollama_client=ollama_client,
        retrieval_judge=None
    )
    
    results = []
    
    # Run each test query twice - first with standard retrieval, then with judge
    for query in TEST_QUERIES:
        logger.info(f"\n=== Testing query: {query} ===")
        
        # Test with standard retrieval
        logger.info("Running with standard retrieval...")
        standard_tracker = TimingTracker()
        
        standard_tracker.start("standard_total")
        standard_response = await rag_engine_standard.query(
            query=query,
            use_rag=True,
            top_k=5,
            stream=False
        )
        standard_tracker.stop()
        
        # Test with judge-enhanced retrieval
        logger.info("Running with judge-enhanced retrieval...")
        judge_tracker = TimingTracker()
        
        judge_tracker.start("judge_total")
        judge_response = await rag_engine_with_judge.query(
            query=query,
            use_rag=True,
            top_k=5,
            stream=False
        )
        judge_tracker.stop()
        
        # Extract results
        standard_answer = standard_response.get("answer", "")
        standard_sources = standard_response.get("sources", [])
        
        judge_answer = judge_response.get("answer", "")
        judge_sources = judge_response.get("sources", [])
        
        # Log results
        logger.info(f"Standard retrieval: {len(standard_sources)} sources, {standard_tracker.timings['standard_total']:.2f}s")
        logger.info(f"Judge-enhanced retrieval: {len(judge_sources)} sources, {judge_tracker.timings['judge_total']:.2f}s")
        
        # Collect judge component timings
        judge_component_timings = {}
        if hasattr(retrieval_judge, 'timings'):
            judge_component_timings = retrieval_judge.timings.copy()
        
        if hasattr(rag_engine_with_judge, 'timings'):
            judge_component_timings.update(rag_engine_with_judge.timings)
        
        # Clear timings for next run
        retrieval_judge.timings = {}
        rag_engine_with_judge.timings = {}
        
        # Store results
        results.append({
            "query": query,
            "standard": {
                "total_time": standard_tracker.timings['standard_total'],
                "sources_count": len(standard_sources)
            },
            "judge": {
                "total_time": judge_tracker.timings['judge_total'],
                "sources_count": len(judge_sources),
                "component_timings": judge_component_timings
            }
        })
    
    # Save results to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "timing_analysis_results.json")
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Timing analysis results saved to {os.path.abspath(results_path)}")
    
    return results

async def analyze_timing_results(results):
    """Analyze the timing test results"""
    logger.info("\n=== TIMING ANALYSIS ===")
    
    # Calculate averages
    avg_standard_time = sum(r["standard"]["total_time"] for r in results) / len(results)
    avg_judge_time = sum(r["judge"]["total_time"] for r in results) / len(results)
    
    logger.info(f"Average standard retrieval time: {avg_standard_time:.2f}s")
    logger.info(f"Average judge-enhanced retrieval time: {avg_judge_time:.2f}s")
    logger.info(f"Time difference: {((avg_judge_time - avg_standard_time) / avg_standard_time * 100):.2f}%")
    
    # Analyze component timings
    component_times = {}
    for r in results:
        for component, time_value in r["judge"].get("component_timings", {}).items():
            if component not in component_times:
                component_times[component] = []
            component_times[component].append(time_value)
    
    logger.info("\nJudge component timing averages:")
    for component, times in component_times.items():
        avg_time = sum(times) / len(times)
        logger.info(f"  {component}: {avg_time:.2f}s")
    
    # Analyze first run vs. subsequent runs
    first_standard_time = results[0]["standard"]["total_time"]
    first_judge_time = results[0]["judge"]["total_time"]
    
    rest_standard_time = sum(r["standard"]["total_time"] for r in results[1:]) / (len(results) - 1) if len(results) > 1 else 0
    rest_judge_time = sum(r["judge"]["total_time"] for r in results[1:]) / (len(results) - 1) if len(results) > 1 else 0
    
    logger.info("\nFirst run vs. subsequent runs:")
    logger.info(f"  First standard run: {first_standard_time:.2f}s")
    logger.info(f"  Average of subsequent standard runs: {rest_standard_time:.2f}s")
    logger.info(f"  First judge run: {first_judge_time:.2f}s")
    logger.info(f"  Average of subsequent judge runs: {rest_judge_time:.2f}s")
    
    # Check for caching effects
    logger.info("\nPossible explanations for timing differences:")
    
    if first_standard_time > rest_standard_time and first_judge_time > rest_judge_time:
        logger.info("  - Warm-up effect: Both methods show faster performance after the first run")
    
    if avg_judge_time < avg_standard_time:
        logger.info("  - Caching effect: Judge-enhanced retrieval might benefit from caching in the vector store")
        logger.info("  - Model loading: The LLM might be loaded into memory during the first run")
        logger.info("  - Query optimization: The judge might be selecting more efficient retrieval parameters")
    else:
        logger.info("  - Additional processing: Judge operations add overhead as expected")
    
    # Save analysis to file
    analysis = {
        "avg_standard_time": avg_standard_time,
        "avg_judge_time": avg_judge_time,
        "time_difference_percent": ((avg_judge_time - avg_standard_time) / avg_standard_time * 100),
        "component_averages": {component: sum(times) / len(times) for component, times in component_times.items()},
        "first_run": {
            "standard": first_standard_time,
            "judge": first_judge_time
        },
        "subsequent_runs": {
            "standard": rest_standard_time,
            "judge": rest_judge_time
        }
    }
    
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    analysis_path = os.path.join(results_dir, "timing_analysis.json")
    
    with open(analysis_path, "w") as f:
        json.dump(analysis, f, indent=2)
    
    logger.info(f"Timing analysis saved to {os.path.abspath(analysis_path)}")
    
    return analysis

async def main():
    """Main test function"""
    logger.info("Starting Retrieval Judge timing analysis...")
    logger.info(f"Using model {JUDGE_MODEL} for the Retrieval Judge")
    
    try:
        # Create test document
        doc_path = await create_test_document()
        
        # Process document
        document, vector_store = await process_document(doc_path)
        
        # Run timing tests
        results = await run_timing_tests(vector_store)
        
        # Analyze results
        analysis = await analyze_timing_results(results)
        
        logger.info("Retrieval Judge timing analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during Retrieval Judge timing analysis: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())