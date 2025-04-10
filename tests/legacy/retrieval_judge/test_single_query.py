#!/usr/bin/env python3
"""
Simplified test script to demonstrate the Retrieval Judge with a single query.
This script:
1. Creates a test document
2. Processes the document
3. Runs a single query with both standard retrieval and judge-enhanced retrieval
4. Compares the results
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
logger = logging.getLogger("test_single_query")

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

# Test query
TEST_QUERY = "What are the components of the RAG engine and how do they work together?"

async def create_test_document():
    """Create a test document for RAG testing"""
    logger.info("Creating test document...")
    
    # Create directory for test document
    test_dir = os.path.join("tests", "retrieval_judge", "data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create document file
    doc_path = os.path.join(test_dir, "test_document.md")
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
        filename="test_document.md",
        content=doc_content,
        tags=["technical", "documentation", "architecture"],
        folder="/test"
    )
    
    # Create a vector store
    test_persist_dir = os.path.join("tests", "retrieval_judge", "test_chroma_db")
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

async def run_comparison_test(vector_store):
    """Run a comparison test between standard retrieval and judge-enhanced retrieval"""
    logger.info("Running comparison test...")
    
    # Create OllamaClient
    ollama_client = OllamaClient()
    
    # Create Retrieval Judge with the specified model
    logger.info(f"Creating Retrieval Judge with model: {JUDGE_MODEL}")
    retrieval_judge = RetrievalJudge(ollama_client=ollama_client, model=JUDGE_MODEL)
    
    # Engine with Retrieval Judge
    rag_engine_with_judge = RAGEngine(
        vector_store=vector_store,
        ollama_client=ollama_client,
        retrieval_judge=retrieval_judge
    )
    
    # Engine without Retrieval Judge
    rag_engine_standard = RAGEngine(
        vector_store=vector_store,
        ollama_client=ollama_client,
        retrieval_judge=None
    )
    
    # Test with standard retrieval
    logger.info("Running with standard retrieval...")
    start_time_standard = time.time()
    standard_response = await rag_engine_standard.query(
        query=TEST_QUERY,
        use_rag=True,
        top_k=5,
        stream=False
    )
    standard_time = time.time() - start_time_standard
    
    # Test with judge-enhanced retrieval
    logger.info("Running with judge-enhanced retrieval...")
    start_time_judge = time.time()
    judge_response = await rag_engine_with_judge.query(
        query=TEST_QUERY,
        use_rag=True,
        top_k=5,
        stream=False
    )
    judge_time = time.time() - start_time_judge
    
    # Extract results
    standard_answer = standard_response.get("answer", "")
    standard_sources = standard_response.get("sources", [])
    
    judge_answer = judge_response.get("answer", "")
    judge_sources = judge_response.get("sources", [])
    
    # Log results
    logger.info(f"Standard retrieval: {len(standard_sources)} sources, {standard_time:.2f}s")
    logger.info(f"Judge-enhanced retrieval: {len(judge_sources)} sources, {judge_time:.2f}s")
    
    # Format results for saving
    result = {
        "query": TEST_QUERY,
        "standard": {
            "answer": standard_answer,
            "sources_count": len(standard_sources),
            "time": standard_time
        },
        "judge": {
            "answer": judge_answer,
            "sources_count": len(judge_sources),
            "time": judge_time
        }
    }
    
    # Save result to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    result_path = os.path.join(results_dir, "single_query_result.json")
    
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Test result saved to {os.path.abspath(result_path)}")
    
    # Print comparison
    logger.info("\n=== RETRIEVAL JUDGE COMPARISON ===")
    logger.info(f"Query: {TEST_QUERY}")
    logger.info(f"Standard retrieval time: {standard_time:.2f}s")
    logger.info(f"Judge-enhanced retrieval time: {judge_time:.2f}s")
    logger.info(f"Time difference: {((judge_time - standard_time) / standard_time * 100):.2f}%")
    logger.info(f"Standard sources: {len(standard_sources)}")
    logger.info(f"Judge sources: {len(judge_sources)}")
    
    # Print answers
    logger.info("\nStandard Answer:")
    logger.info(standard_answer[:500] + "..." if len(standard_answer) > 500 else standard_answer)
    
    logger.info("\nJudge-Enhanced Answer:")
    logger.info(judge_answer[:500] + "..." if len(judge_answer) > 500 else judge_answer)
    
    return result

async def main():
    """Main test function"""
    logger.info("Starting Retrieval Judge single query test...")
    logger.info(f"Using model {JUDGE_MODEL} for the Retrieval Judge")
    
    try:
        # Create test document
        doc_path = await create_test_document()
        
        # Process document
        document, vector_store = await process_document(doc_path)
        
        # Run comparison test
        result = await run_comparison_test(vector_store)
        
        logger.info("Retrieval Judge single query test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during Retrieval Judge single query test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())