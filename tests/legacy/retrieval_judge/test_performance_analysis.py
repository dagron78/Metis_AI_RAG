#!/usr/bin/env python3
"""
Test script to analyze why the judge-enhanced retrieval is faster than standard retrieval.
This script:
1. Instruments both retrieval methods with detailed timing
2. Analyzes the time spent in each component
3. Investigates caching effects and other optimizations
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
logger = logging.getLogger("test_performance_analysis")

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

class InstrumentedVectorStore(VectorStore):
    """Instrumented version of VectorStore that tracks timing"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.query_cache = {}
    
    async def search(self, query: str, top_k: int = 5, filter_criteria: Optional[Dict[str, Any]] = None):
        """Instrumented version of search"""
        # Check cache
        cache_key = f"{query}_{top_k}_{json.dumps(filter_criteria) if filter_criteria else 'none'}"
        if cache_key in self.query_cache:
            self.cache_hits += 1
            logger.info(f"Vector store cache hit for query: {query[:30]}...")
            return self.query_cache[cache_key]
        
        self.cache_misses += 1
        logger.info(f"Vector store cache miss for query: {query[:30]}...")
        
        # Measure search time
        start_time = time.time()
        result = await super().search(query, top_k, filter_criteria)
        elapsed = time.time() - start_time
        
        # Store timing
        if "search" not in self.timings:
            self.timings["search"] = []
        self.timings["search"].append(elapsed)
        
        # Cache result
        self.query_cache[cache_key] = result
        
        logger.info(f"Vector store search took {elapsed:.2f}s")
        return result

class InstrumentedOllamaClient(OllamaClient):
    """Instrumented version of OllamaClient that tracks timing"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.generate_cache = {}
        self.embedding_cache = {}
    
    async def generate(self, prompt: str, model: Optional[str] = None, system_prompt: Optional[str] = None, 
                      stream: bool = False, parameters: Optional[Dict[str, Any]] = None):
        """Instrumented version of generate"""
        # Check cache for non-streaming requests
        if not stream:
            cache_key = f"{prompt}_{model}_{system_prompt}_{json.dumps(parameters) if parameters else 'none'}"
            if cache_key in self.generate_cache:
                self.cache_hits += 1
                logger.info(f"LLM generate cache hit for prompt: {prompt[:30]}...")
                return self.generate_cache[cache_key]
            
            self.cache_misses += 1
            logger.info(f"LLM generate cache miss for prompt: {prompt[:30]}...")
        
        # Measure generate time
        start_time = time.time()
        result = await super().generate(prompt, model, system_prompt, stream, parameters)
        elapsed = time.time() - start_time
        
        # Store timing
        if "generate" not in self.timings:
            self.timings["generate"] = []
        self.timings["generate"].append(elapsed)
        
        # Cache result for non-streaming requests
        if not stream:
            self.generate_cache[cache_key] = result
        
        logger.info(f"LLM generate took {elapsed:.2f}s")
        return result
    
    async def create_embedding(self, text: str, model: Optional[str] = None):
        """Instrumented version of create_embedding"""
        # Check cache
        cache_key = f"{text}_{model}"
        if cache_key in self.embedding_cache:
            self.cache_hits += 1
            logger.info(f"Embedding cache hit for text: {text[:30]}...")
            return self.embedding_cache[cache_key]
        
        self.cache_misses += 1
        logger.info(f"Embedding cache miss for text: {text[:30]}...")
        
        # Measure embedding time
        start_time = time.time()
        result = await super().create_embedding(text, model)
        elapsed = time.time() - start_time
        
        # Store timing
        if "embedding" not in self.timings:
            self.timings["embedding"] = []
        self.timings["embedding"].append(elapsed)
        
        # Cache result
        self.embedding_cache[cache_key] = result
        
        logger.info(f"Embedding creation took {elapsed:.2f}s")
        return result

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
        
        if "analyze_query" not in self.timings:
            self.timings["analyze_query"] = []
        self.timings["analyze_query"].append(elapsed)
        
        logger.info(f"analyze_query took {elapsed:.2f}s")
        return result
    
    async def evaluate_chunks(self, query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Instrumented version of evaluate_chunks"""
        start_time = time.time()
        result = await super().evaluate_chunks(query, chunks)
        elapsed = time.time() - start_time
        
        if "evaluate_chunks" not in self.timings:
            self.timings["evaluate_chunks"] = []
        self.timings["evaluate_chunks"].append(elapsed)
        
        logger.info(f"evaluate_chunks took {elapsed:.2f}s")
        return result
    
    async def refine_query(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Instrumented version of refine_query"""
        start_time = time.time()
        result = await super().refine_query(query, chunks)
        elapsed = time.time() - start_time
        
        if "refine_query" not in self.timings:
            self.timings["refine_query"] = []
        self.timings["refine_query"].append(elapsed)
        
        logger.info(f"refine_query took {elapsed:.2f}s")
        return result
    
    async def optimize_context(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Instrumented version of optimize_context"""
        start_time = time.time()
        result = await super().optimize_context(query, chunks)
        elapsed = time.time() - start_time
        
        if "optimize_context" not in self.timings:
            self.timings["optimize_context"] = []
        self.timings["optimize_context"].append(elapsed)
        
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
        
        if "enhanced_retrieval" not in self.timings:
            self.timings["enhanced_retrieval"] = []
        self.timings["enhanced_retrieval"].append(elapsed)
        
        logger.info(f"enhanced_retrieval took {elapsed:.2f}s")
        return result

async def create_test_document():
    """Create a test document for RAG testing"""
    logger.info("Creating test document...")
    
    # Create directory for test document
    test_dir = os.path.join("tests", "retrieval_judge", "data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create document file
    doc_path = os.path.join(test_dir, "performance_test_document.md")
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
        filename="performance_test_document.md",
        content=doc_content,
        tags=["technical", "documentation", "architecture"],
        folder="/test"
    )
    
    # Create a vector store
    test_persist_dir = os.path.join("tests", "retrieval_judge", "performance_test_chroma_db")
    os.makedirs(test_persist_dir, exist_ok=True)
    vector_store = InstrumentedVectorStore(persist_directory=test_persist_dir)
    
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

async def run_performance_tests(vector_store):
    """Run performance tests for standard and judge-enhanced retrieval"""
    logger.info("Running performance tests...")
    
    # Create instrumented OllamaClient
    ollama_client = InstrumentedOllamaClient()
    
    # Create instrumented Retrieval Judge
    logger.info(f"Creating Retrieval Judge with model: {JUDGE_MODEL}")
    retrieval_judge = InstrumentedRetrievalJudge(ollama_client=ollama_client, model=JUDGE_MODEL)
    
    # Create engines
    rag_engine_with_judge = InstrumentedRAGEngine(
        vector_store=vector_store,
        ollama_client=ollama_client,
        retrieval_judge=retrieval_judge
    )
    
    rag_engine_standard = InstrumentedRAGEngine(
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
        standard_start_time = time.time()
        standard_response = await rag_engine_standard.query(
            query=query,
            use_rag=True,
            top_k=5,
            stream=False
        )
        standard_total_time = time.time() - standard_start_time
        
        # Test with judge-enhanced retrieval
        logger.info("Running with judge-enhanced retrieval...")
        judge_start_time = time.time()
        judge_response = await rag_engine_with_judge.query(
            query=query,
            use_rag=True,
            top_k=5,
            stream=False
        )
        judge_total_time = time.time() - judge_start_time
        
        # Extract results
        standard_answer = standard_response.get("answer", "")
        standard_sources = standard_response.get("sources", [])
        
        judge_answer = judge_response.get("answer", "")
        judge_sources = judge_response.get("sources", [])
        
        # Log results
        logger.info(f"Standard retrieval: {len(standard_sources)} sources, {standard_total_time:.2f}s")
        logger.info(f"Judge-enhanced retrieval: {len(judge_sources)} sources, {judge_total_time:.2f}s")
        
        # Collect component timings
        standard_component_timings = {}
        judge_component_timings = {}
        
        # Vector store timings
        if hasattr(vector_store, 'timings'):
            for component, times in vector_store.timings.items():
                standard_component_timings[f"vector_store_{component}"] = times[0] if len(times) > 0 else 0
                judge_component_timings[f"vector_store_{component}"] = times[1] if len(times) > 1 else 0
        
        # Ollama client timings
        if hasattr(ollama_client, 'timings'):
            for component, times in ollama_client.timings.items():
                # First half of times are from standard retrieval, second half from judge
                standard_times = [t for i, t in enumerate(times) if i < len(times)//2]
                judge_times = [t for i, t in enumerate(times) if i >= len(times)//2]
                
                standard_component_timings[f"ollama_{component}"] = sum(standard_times)
                judge_component_timings[f"ollama_{component}"] = sum(judge_times)
        
        # Retrieval judge timings
        if hasattr(retrieval_judge, 'timings'):
            for component, times in retrieval_judge.timings.items():
                judge_component_timings[f"judge_{component}"] = sum(times)
        
        # RAG engine timings
        if hasattr(rag_engine_with_judge, 'timings'):
            for component, times in rag_engine_with_judge.timings.items():
                judge_component_timings[f"rag_engine_{component}"] = sum(times)
        
        if hasattr(rag_engine_standard, 'timings'):
            for component, times in rag_engine_standard.timings.items():
                standard_component_timings[f"rag_engine_{component}"] = sum(times)
        
        # Cache statistics
        cache_stats = {
            "vector_store_cache_hits": vector_store.cache_hits,
            "vector_store_cache_misses": vector_store.cache_misses,
            "ollama_cache_hits": ollama_client.cache_hits,
            "ollama_cache_misses": ollama_client.cache_misses
        }
        
        # Store results
        results.append({
            "query": query,
            "standard": {
                "total_time": standard_total_time,
                "sources_count": len(standard_sources),
                "component_timings": standard_component_timings
            },
            "judge": {
                "total_time": judge_total_time,
                "sources_count": len(judge_sources),
                "component_timings": judge_component_timings
            },
            "cache_stats": cache_stats
        })
        
        # Reset timings for next run
        vector_store.timings = {}
        ollama_client.timings = {}
        retrieval_judge.timings = {}
        rag_engine_with_judge.timings = {}
        rag_engine_standard.timings = {}
    
    # Save results to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "performance_analysis_results.json")
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Performance analysis results saved to {os.path.abspath(results_path)}")
    
    return results

async def analyze_performance_results(results):
    """Analyze the performance test results"""
    logger.info("\n=== PERFORMANCE ANALYSIS ===")
    
    # Calculate averages
    avg_standard_time = sum(r["standard"]["total_time"] for r in results) / len(results)
    avg_judge_time = sum(r["judge"]["total_time"] for r in results) / len(results)
    
    logger.info(f"Average standard retrieval time: {avg_standard_time:.2f}s")
    logger.info(f"Average judge-enhanced retrieval time: {avg_judge_time:.2f}s")
    logger.info(f"Time difference: {((avg_judge_time - avg_standard_time) / avg_standard_time * 100):.2f}%")
    
    # Analyze component timings
    standard_component_times = {}
    judge_component_times = {}
    
    for r in results:
        for component, time_value in r["standard"]["component_timings"].items():
            if component not in standard_component_times:
                standard_component_times[component] = []
            standard_component_times[component].append(time_value)
        
        for component, time_value in r["judge"]["component_timings"].items():
            if component not in judge_component_times:
                judge_component_times[component] = []
            judge_component_times[component].append(time_value)
    
    logger.info("\nStandard retrieval component timing averages:")
    for component, times in standard_component_times.items():
        avg_time = sum(times) / len(times)
        logger.info(f"  {component}: {avg_time:.2f}s")
    
    logger.info("\nJudge-enhanced retrieval component timing averages:")
    for component, times in judge_component_times.items():
        avg_time = sum(times) / len(times)
        logger.info(f"  {component}: {avg_time:.2f}s")
    
    # Analyze cache statistics
    total_vector_store_hits = sum(r["cache_stats"]["vector_store_cache_hits"] for r in results)
    total_vector_store_misses = sum(r["cache_stats"]["vector_store_cache_misses"] for r in results)
    total_ollama_hits = sum(r["cache_stats"]["ollama_cache_hits"] for r in results)
    total_ollama_misses = sum(r["cache_stats"]["ollama_cache_misses"] for r in results)
    
    logger.info("\nCache statistics:")
    logger.info(f"  Vector store cache hits: {total_vector_store_hits}")
    logger.info(f"  Vector store cache misses: {total_vector_store_misses}")
    logger.info(f"  Vector store cache hit rate: {total_vector_store_hits/(total_vector_store_hits+total_vector_store_misses)*100:.2f}%")
    logger.info(f"  Ollama cache hits: {total_ollama_hits}")
    logger.info(f"  Ollama cache misses: {total_ollama_misses}")
    logger.info(f"  Ollama cache hit rate: {total_ollama_hits/(total_ollama_hits+total_ollama_misses)*100:.2f}%")
    
    # Analyze potential reasons for performance difference
    logger.info("\nPotential reasons for performance difference:")
    
    # Check if judge retrieves fewer chunks
    avg_standard_sources = sum(r["standard"]["sources_count"] for r in results) / len(results)
    avg_judge_sources = sum(r["judge"]["sources_count"] for r in results) / len(results)
    
    if avg_judge_sources < avg_standard_sources:
        logger.info(f"  - Judge retrieves fewer sources ({avg_judge_sources:.2f} vs {avg_standard_sources:.2f})")
    
    # Check if judge has better cache utilization
    if total_ollama_hits > 0:
        logger.info(f"  - Judge benefits from LLM caching ({total_ollama_hits} cache hits)")
    
    if total_vector_store_hits > 0:
        logger.info(f"  - Judge benefits from vector store caching ({total_vector_store_hits} cache hits)")
    
    # Check if judge optimizes query parameters
    if "judge_analyze_query" in judge_component_times:
        logger.info(f"  - Judge optimizes query parameters (analyze_query: {sum(judge_component_times['judge_analyze_query'])/len(judge_component_times['judge_analyze_query']):.2f}s)")
    
    # Save analysis to file
    analysis = {
        "avg_standard_time": avg_standard_time,
        "avg_judge_time": avg_judge_time,
        "time_difference_percent": ((avg_judge_time - avg_standard_time) / avg_standard_time * 100),
        "standard_component_averages": {component: sum(times) / len(times) for component, times in standard_component_times.items()},
        "judge_component_averages": {component: sum(times) / len(times) for component, times in judge_component_times.items()},
        "cache_statistics": {
            "vector_store_cache_hits": total_vector_store_hits,
            "vector_store_cache_misses": total_vector_store_misses,
            "vector_store_cache_hit_rate": total_vector_store_hits/(total_vector_store_hits+total_vector_store_misses)*100 if (total_vector_store_hits+total_vector_store_misses) > 0 else 0,
            "ollama_cache_hits": total_ollama_hits,
            "ollama_cache_misses": total_ollama_misses,
            "ollama_cache_hit_rate": total_ollama_hits/(total_ollama_hits+total_ollama_misses)*100 if (total_ollama_hits+total_ollama_misses) > 0 else 0
        },
        "avg_standard_sources": avg_standard_sources,
        "avg_judge_sources": avg_judge_sources
    }
    
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    analysis_path = os.path.join(results_dir, "performance_analysis.json")
    
    with open(analysis_path, "w") as f:
        json.dump(analysis, f, indent=2)
    
    logger.info(f"Performance analysis saved to {os.path.abspath(analysis_path)}")
    
    return analysis

async def main():
    """Main test function"""
    logger.info("Starting Retrieval Judge performance analysis...")
    logger.info(f"Using model {JUDGE_MODEL} for the Retrieval Judge")
    
    try:
        # Create test document
        doc_path = await create_test_document()
        
        # Process document
        document, vector_store = await process_document(doc_path)
        
        # Run performance tests
        results = await run_performance_tests(vector_store)
        
        # Analyze results
        analysis = await analyze_performance_results(results)
        
        logger.info("Retrieval Judge performance analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during Retrieval Judge performance analysis: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())