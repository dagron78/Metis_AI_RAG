#!/usr/bin/env python3
"""
Test script to compare standard retrieval vs. retrieval with the Retrieval Judge enabled.
This script:
1. Creates test documents and processes them
2. Runs test queries with both standard retrieval and judge-enhanced retrieval
3. Compares the results to evaluate the judge's effectiveness
4. Analyzes areas for improvement
"""

import os
import sys
import json
import asyncio
import logging
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_retrieval_judge_comparison")

# Import RAG components
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.agents.retrieval_judge import RetrievalJudge
from app.models.document import Document, Chunk

# Define the model to use for the Retrieval Judge
JUDGE_MODEL = "gemma3:4b"

# Test document content - using the same content as test_rag_retrieval.py
MARKDOWN_CONTENT = """# Metis RAG Technical Documentation

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

PDF_CONTENT = """Quarterly Business Report
Executive Summary
This quarterly report provides an overview of business performance for Q1 2025. Overall, the company
has seen strong growth in key metrics including revenue, customer acquisition, and product
engagement. This document summarizes the performance across departments and outlines strategic
initiatives for the upcoming quarter.

Financial Performance
The company achieved $4.2M in revenue for Q1, representing a 15% increase year-over-year. Gross
margin improved to 72%, up from 68% in the previous quarter. Operating expenses were kept under
control at $2.8M, resulting in a net profit of $1.4M.

Product Development
The product team successfully launched 3 major features this quarter:
- Advanced Analytics Dashboard: Providing deeper insights into user behavior
- Mobile Application Redesign: Improving user experience and engagement
- API Integration Platform: Enabling third-party developers to build on our platform

User engagement metrics show a 22% increase in daily active users following these releases. The
product roadmap for Q2 focuses on scalability improvements and enterprise features.

Marketing and Sales
The marketing team executed campaigns that generated 2,500 new leads, a 30% increase from the
previous quarter. Sales conversion rate improved to 12%, resulting in 300 new customers. Customer
acquisition cost (CAC) decreased by 15% to $350 per customer.

Customer Success
Customer retention rate remained strong at 94%. Net Promoter Score (NPS) improved from 42 to 48.
The support team handled 3,200 tickets with an average response time of 2.5 hours and a satisfaction
rating of 4.8/5.

Strategic Initiatives for Q2
The following initiatives are planned for Q2 2025:
- International Expansion: Launch in European markets
- Enterprise Solution: Develop and release enterprise-grade features
- Strategic Partnerships: Form alliances with complementary service providers
- Operational Efficiency: Implement automation to reduce operational costs
"""

# Additional test document with more technical content
TECHNICAL_SPECS_CONTENT = """# Product Specifications

## System Requirements

The Metis RAG system requires the following minimum specifications:
- CPU: 4 cores, 2.5GHz or higher
- RAM: 16GB minimum, 32GB recommended
- Storage: 100GB SSD
- Operating System: Ubuntu 22.04 LTS, Windows Server 2019, or macOS 12+
- Network: 100Mbps internet connection

## API Reference

### Authentication

All API requests require authentication using JWT tokens. To obtain a token:

```
POST /api/auth/token
{
  "username": "your_username",
  "password": "your_password"
}
```

The response will include an access token valid for 24 hours.

### Document Management

#### Upload Document

```
POST /api/documents/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form fields:
- file: The document file
- tags: Comma-separated tags (optional)
- folder: Target folder path (optional)
```

#### List Documents

```
GET /api/documents/list
Authorization: Bearer <token>
```

Optional query parameters:
- folder: Filter by folder
- tags: Filter by tags (comma-separated)
- page: Page number (default: 1)
- limit: Items per page (default: 20)

### Chat API

#### Create Chat Session

```
POST /api/chat/sessions
Authorization: Bearer <token>
{
  "title": "Optional chat title"
}
```

#### Send Message

```
POST /api/chat/messages
Authorization: Bearer <token>
{
  "session_id": "chat_session_id",
  "content": "Your message here",
  "use_rag": true
}
```

## Performance Benchmarks

The system has been benchmarked with the following results:
- Document processing: 5 pages/second
- Vector search latency: <50ms for 10k documents
- End-to-end query response time: <2 seconds
- Maximum documents: 100,000
- Maximum vector store size: 10GB
"""

# Test queries of varying complexity
TEST_QUERIES = [
    # Simple factual queries
    {
        "query": "What is the architecture of Metis RAG?",
        "complexity": "simple",
        "description": "Simple factual query about architecture"
    },
    {
        "query": "What was the revenue reported in Q1 2025?",
        "complexity": "simple",
        "description": "Simple factual query about revenue"
    },
    
    # Moderate complexity queries
    {
        "query": "What are the components of the RAG engine and how do they work together?",
        "complexity": "moderate",
        "description": "Moderate complexity query requiring synthesis of multiple components"
    },
    {
        "query": "Compare the financial performance metrics from the quarterly report.",
        "complexity": "moderate",
        "description": "Moderate complexity query requiring comparison and analysis"
    },
    
    # Complex analytical queries
    {
        "query": "How does the document processing pipeline handle different file types and what are the implications for retrieval quality?",
        "complexity": "complex",
        "description": "Complex query requiring deep technical understanding and inference"
    },
    {
        "query": "Based on the quarterly report, what strategic initiatives might have the highest ROI and why?",
        "complexity": "complex",
        "description": "Complex query requiring business analysis and inference"
    },
    
    # Ambiguous queries
    {
        "query": "What are the system requirements?",
        "complexity": "ambiguous",
        "description": "Ambiguous query that could refer to different aspects"
    },
    {
        "query": "How does the API work?",
        "complexity": "ambiguous",
        "description": "Ambiguous query with broad scope"
    },
    
    # Multi-part queries
    {
        "query": "What is the vector store responsible for and what are the minimum RAM requirements for the system?",
        "complexity": "multi-part",
        "description": "Multi-part query combining two different topics"
    },
    {
        "query": "Explain the authentication process for the API and list the strategic initiatives for Q2.",
        "complexity": "multi-part",
        "description": "Multi-part query requiring information from different documents"
    }
]

async def create_test_documents():
    """Create test documents for RAG testing"""
    logger.info("Creating test documents...")
    
    # Create directories for test documents
    test_dir = os.path.join("tests", "retrieval_judge", "data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create Markdown document
    markdown_path = os.path.join(test_dir, "technical_documentation.md")
    with open(markdown_path, "w") as f:
        f.write(MARKDOWN_CONTENT)
    
    # Create PDF-like text document
    pdf_path = os.path.join(test_dir, "quarterly_report.txt")
    with open(pdf_path, "w") as f:
        f.write(PDF_CONTENT)
    
    # Create technical specs document
    specs_path = os.path.join(test_dir, "product_specifications.md")
    with open(specs_path, "w") as f:
        f.write(TECHNICAL_SPECS_CONTENT)
    
    logger.info(f"Created test documents in {os.path.abspath(test_dir)}")
    return markdown_path, pdf_path, specs_path

async def process_documents(vector_store, markdown_path, pdf_path, specs_path):
    """Process the test documents and add them to the vector store"""
    logger.info("Processing test documents...")
    
    # Read file contents
    with open(markdown_path, "r") as f:
        markdown_content = f.read()
    
    with open(pdf_path, "r") as f:
        pdf_content = f.read()
    
    with open(specs_path, "r") as f:
        specs_content = f.read()
    
    # Create Document objects
    markdown_doc = Document(
        id=str(uuid.uuid4()),
        filename="technical_documentation.md",
        content=markdown_content,
        tags=["technical", "documentation", "architecture"],
        folder="/test"
    )
    
    pdf_doc = Document(
        id=str(uuid.uuid4()),
        filename="quarterly_report.txt",
        content=pdf_content,
        tags=["business", "report", "quarterly"],
        folder="/test"
    )
    
    specs_doc = Document(
        id=str(uuid.uuid4()),
        filename="product_specifications.md",
        content=specs_content,
        tags=["technical", "specifications", "api"],
        folder="/test"
    )
    
    # Create a custom vector store to handle tags properly
    class CustomVectorStore(VectorStore):
        async def add_document(self, document: Document) -> None:
            """Override to fix tags handling"""
            try:
                logger.info(f"Adding document {document.id} to vector store")
                
                # Make sure we have an Ollama client
                if self.ollama_client is None:
                    self.ollama_client = OllamaClient()
                
                # Prepare chunks for batch processing
                chunks_to_embed = [chunk for chunk in document.chunks if not chunk.embedding]
                chunk_contents = [chunk.content for chunk in chunks_to_embed]
                
                # Create embeddings in batch if possible
                if chunk_contents:
                    try:
                        # Batch embedding
                        embeddings = await self._batch_create_embeddings(chunk_contents)
                        
                        # Assign embeddings to chunks
                        for i, chunk in enumerate(chunks_to_embed):
                            chunk.embedding = embeddings[i]
                    except Exception as batch_error:
                        logger.warning(f"Batch embedding failed: {str(batch_error)}. Falling back to sequential embedding.")
                        # Fall back to sequential embedding
                        for chunk in chunks_to_embed:
                            chunk.embedding = await self.ollama_client.create_embedding(
                                text=chunk.content,
                                model=self.embedding_model
                            )
                
                # Add chunks to the collection
                for chunk in document.chunks:
                    if not chunk.embedding:
                        logger.warning(f"Chunk {chunk.id} has no embedding, skipping")
                        continue
                        
                    # Convert tags to string to avoid ChromaDB error
                    tags_str = ",".join(document.tags) if document.tags else ""
                    
                    self.collection.add(
                        ids=[chunk.id],
                        embeddings=[chunk.embedding],
                        documents=[chunk.content],
                        metadatas=[{
                            "document_id": document.id,
                            "chunk_index": chunk.metadata.get("index", 0),
                            "filename": document.filename,
                            "tags": tags_str,  # Use string instead of list
                            "folder": document.folder,
                            **chunk.metadata
                        }]
                    )
                
                logger.info(f"Added {len(document.chunks)} chunks to vector store for document {document.id}")
            except Exception as e:
                logger.error(f"Error adding document {document.id} to vector store: {str(e)}")
                raise
    
    # Use our custom vector store with a unique persist directory for this test
    test_persist_dir = os.path.join("tests", "retrieval_judge", "test_chroma_db")
    os.makedirs(test_persist_dir, exist_ok=True)
    vector_store = CustomVectorStore(persist_directory=test_persist_dir)
    
    # Create chunks for documents
    # For a more realistic test, we'll split the documents into smaller chunks
    
    # Helper function to create chunks
    def create_chunks(content, doc_id, source_path, chunk_size=500, overlap=100):
        chunks = []
        # Simple chunking by splitting the content
        words = content.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            if len(chunk_words) < 50:  # Skip very small chunks
                continue
                
            chunk_content = " ".join(chunk_words)
            chunks.append(
                Chunk(
                    id=str(uuid.uuid4()),
                    content=chunk_content,
                    metadata={
                        "index": len(chunks),
                        "source": source_path,
                        "document_id": doc_id
                    }
                )
            )
        
        return chunks
    
    # Create chunks for each document
    markdown_doc.chunks = create_chunks(markdown_content, markdown_doc.id, markdown_path)
    pdf_doc.chunks = create_chunks(pdf_content, pdf_doc.id, pdf_path)
    specs_doc.chunks = create_chunks(specs_content, specs_doc.id, specs_path)
    
    # Add documents to vector store
    await vector_store.add_document(markdown_doc)
    await vector_store.add_document(pdf_doc)
    await vector_store.add_document(specs_doc)
    
    logger.info(f"Added documents to vector store: {markdown_doc.id}, {pdf_doc.id}, {specs_doc.id}")
    logger.info(f"Total chunks: {len(markdown_doc.chunks) + len(pdf_doc.chunks) + len(specs_doc.chunks)}")
    
    return markdown_doc, pdf_doc, specs_doc, vector_store

async def run_comparison_tests(vector_store):
    """Run comparison tests between standard retrieval and judge-enhanced retrieval"""
    logger.info("Running comparison tests...")
    
    # Create two RAG engines - one with Retrieval Judge and one without
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
    
    results = []
    
    # Run each test query with both engines
    for query_info in TEST_QUERIES:
        query = query_info["query"]
        complexity = query_info["complexity"]
        description = query_info["description"]
        
        logger.info(f"Testing query: {query}")
        logger.info(f"Complexity: {complexity}")
        
        # Test with standard retrieval
        logger.info("Running with standard retrieval...")
        start_time_standard = time.time()
        standard_response = await rag_engine_standard.query(
            query=query,
            use_rag=True,
            top_k=5,
            stream=False
        )
        standard_time = time.time() - start_time_standard
        
        # Test with judge-enhanced retrieval
        logger.info("Running with judge-enhanced retrieval...")
        start_time_judge = time.time()
        judge_response = await rag_engine_with_judge.query(
            query=query,
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
        
        # Log basic results
        logger.info(f"Standard retrieval: {len(standard_sources)} sources, {standard_time:.2f}s")
        logger.info(f"Judge-enhanced retrieval: {len(judge_sources)} sources, {judge_time:.2f}s")
        
        # Store results for analysis
        results.append({
            "query": query,
            "complexity": complexity,
            "description": description,
            "standard": {
                "answer": standard_answer,
                "sources": [
                    {
                        "document_id": s.document_id,
                        "chunk_id": s.chunk_id,
                        "relevance_score": s.relevance_score,
                        "excerpt": s.excerpt[:100] + "..." if len(s.excerpt) > 100 else s.excerpt
                    }
                    for s in standard_sources
                ] if standard_sources else [],
                "time": standard_time
            },
            "judge": {
                "answer": judge_answer,
                "sources": [
                    {
                        "document_id": s.document_id,
                        "chunk_id": s.chunk_id,
                        "relevance_score": s.relevance_score,
                        "excerpt": s.excerpt[:100] + "..." if len(s.excerpt) > 100 else s.excerpt
                    }
                    for s in judge_sources
                ] if judge_sources else [],
                "time": judge_time
            }
        })
    
    # Save results to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "retrieval_judge_comparison_results.json")
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to {os.path.abspath(results_path)}")
    return results

async def analyze_results(results):
    """Analyze the comparison test results"""
    logger.info("Analyzing comparison test results...")
    
    # Initialize metrics
    metrics = {
        "total_queries": len(results),
        "avg_standard_time": 0,
        "avg_judge_time": 0,
        "avg_standard_sources": 0,
        "avg_judge_sources": 0,
        "queries_with_more_judge_sources": 0,
        "queries_with_more_standard_sources": 0,
        "queries_with_equal_sources": 0,
        "by_complexity": {},
        "improvement_areas": []
    }
    
    # Calculate metrics
    total_standard_time = 0
    total_judge_time = 0
    total_standard_sources = 0
    total_judge_sources = 0
    
    # Initialize complexity metrics
    for complexity in ["simple", "moderate", "complex", "ambiguous", "multi-part"]:
        metrics["by_complexity"][complexity] = {
            "count": 0,
            "avg_standard_time": 0,
            "avg_judge_time": 0,
            "avg_standard_sources": 0,
            "avg_judge_sources": 0,
            "improvement_percentage": 0
        }
    
    # Process each result
    for result in results:
        complexity = result["complexity"]
        standard_sources = len(result["standard"]["sources"])
        judge_sources = len(result["judge"]["sources"])
        standard_time = result["standard"]["time"]
        judge_time = result["judge"]["time"]
        
        # Update totals
        total_standard_time += standard_time
        total_judge_time += judge_time
        total_standard_sources += standard_sources
        total_judge_sources += judge_sources
        
        # Update source comparison counts
        if judge_sources > standard_sources:
            metrics["queries_with_more_judge_sources"] += 1
        elif standard_sources > judge_sources:
            metrics["queries_with_more_standard_sources"] += 1
        else:
            metrics["queries_with_equal_sources"] += 1
        
        # Update complexity metrics
        if complexity in metrics["by_complexity"]:
            metrics["by_complexity"][complexity]["count"] += 1
            metrics["by_complexity"][complexity]["avg_standard_time"] += standard_time
            metrics["by_complexity"][complexity]["avg_judge_time"] += judge_time
            metrics["by_complexity"][complexity]["avg_standard_sources"] += standard_sources
            metrics["by_complexity"][complexity]["avg_judge_sources"] += judge_sources
    
    # Calculate averages
    metrics["avg_standard_time"] = total_standard_time / len(results)
    metrics["avg_judge_time"] = total_judge_time / len(results)
    metrics["avg_standard_sources"] = total_standard_sources / len(results)
    metrics["avg_judge_sources"] = total_judge_sources / len(results)
    
    # Calculate complexity averages and improvement percentages
    for complexity, data in metrics["by_complexity"].items():
        if data["count"] > 0:
            data["avg_standard_time"] /= data["count"]
            data["avg_judge_time"] /= data["count"]
            data["avg_standard_sources"] /= data["count"]
            data["avg_judge_sources"] /= data["count"]
            
            # Calculate improvement percentage in source relevance
            if data["avg_standard_sources"] > 0:
                data["improvement_percentage"] = ((data["avg_judge_sources"] - data["avg_standard_sources"]) / 
                                                data["avg_standard_sources"]) * 100
            else:
                data["improvement_percentage"] = 0
    
    # Identify areas for improvement
    # 1. Check for queries where judge performed worse
    for result in results:
        standard_sources = len(result["standard"]["sources"])
        judge_sources = len(result["judge"]["sources"])
        
        if standard_sources > judge_sources:
            metrics["improvement_areas"].append({
                "query": result["query"],
                "complexity": result["complexity"],
                "issue": "Judge retrieved fewer sources than standard retrieval",
                "standard_sources": standard_sources,
                "judge_sources": judge_sources
            })
        
        # 2. Check for excessive processing time
        if result["judge"]["time"] > result["standard"]["time"] * 2:
            metrics["improvement_areas"].append({
                "query": result["query"],
                "complexity": result["complexity"],
                "issue": "Judge processing time significantly higher",
                "standard_time": result["standard"]["time"],
                "judge_time": result["judge"]["time"]
            })
    
    # Log summary metrics
    logger.info(f"Total queries: {metrics['total_queries']}")
    logger.info(f"Average standard retrieval time: {metrics['avg_standard_time']:.2f}s")
    logger.info(f"Average judge-enhanced retrieval time: {metrics['avg_judge_time']:.2f}s")
    logger.info(f"Average standard sources: {metrics['avg_standard_sources']:.2f}")
    logger.info(f"Average judge-enhanced sources: {metrics['avg_judge_sources']:.2f}")
    logger.info(f"Queries with more judge sources: {metrics['queries_with_more_judge_sources']}")
    logger.info(f"Queries with more standard sources: {metrics['queries_with_more_standard_sources']}")
    logger.info(f"Queries with equal sources: {metrics['queries_with_equal_sources']}")
    
    # Log complexity metrics
    for complexity, data in metrics["by_complexity"].items():
        if data["count"] > 0:
            logger.info(f"\nComplexity: {complexity} ({data['count']} queries)")
            logger.info(f"  Avg standard time: {data['avg_standard_time']:.2f}s")
            logger.info(f"  Avg judge time: {data['avg_judge_time']:.2f}s")
            logger.info(f"  Avg standard sources: {data['avg_standard_sources']:.2f}")
            logger.info(f"  Avg judge sources: {data['avg_judge_sources']:.2f}")
            logger.info(f"  Improvement percentage: {data['improvement_percentage']:.2f}%")
    
    # Log improvement areas
    if metrics["improvement_areas"]:
        logger.info("\nAreas for improvement:")
        for area in metrics["improvement_areas"]:
            logger.info(f"  Query: {area['query']}")
            logger.info(f"  Issue: {area['issue']}")
    
    # Save metrics to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    metrics_path = os.path.join(results_dir, "retrieval_judge_metrics.json")
    
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Analysis metrics saved to {os.path.abspath(metrics_path)}")
    return metrics

async def main():
    """Main test function"""
    logger.info("Starting Retrieval Judge comparison test...")
    logger.info(f"Using model {JUDGE_MODEL} for the Retrieval Judge")
    
    try:
        # Create test documents
        markdown_path, pdf_path, specs_path = await create_test_documents()
        
        # Process documents
        markdown_doc, pdf_doc, specs_doc, vector_store = await process_documents(
            None, markdown_path, pdf_path, specs_path
        )
        
        # Run comparison tests
        results = await run_comparison_tests(vector_store)
        
        # Analyze results
        metrics = await analyze_results(results)
        
        # Print summary
        logger.info("\n=== RETRIEVAL JUDGE COMPARISON SUMMARY ===")
        logger.info(f"Total queries tested: {metrics['total_queries']}")
        
        # Calculate overall improvement
        source_improvement = ((metrics['avg_judge_sources'] - metrics['avg_standard_sources']) / 
                             metrics['avg_standard_sources'] * 100) if metrics['avg_standard_sources'] > 0 else 0
        
        time_difference = ((metrics['avg_judge_time'] - metrics['avg_standard_time']) / 
                          metrics['avg_standard_time'] * 100) if metrics['avg_standard_time'] > 0 else 0
        
        logger.info(f"Overall source relevance improvement: {source_improvement:.2f}%")
        logger.info(f"Processing time difference: {time_difference:.2f}%")
        
        # Effectiveness by query complexity
        logger.info("\nEffectiveness by query complexity:")
        for complexity, data in metrics["by_complexity"].items():
            if data["count"] > 0:
                logger.info(f"  {complexity.capitalize()}: {data['improvement_percentage']:.2f}% improvement")
        
        # Improvement areas summary
        if metrics["improvement_areas"]:
            logger.info(f"\nIdentified {len(metrics['improvement_areas'])} areas for improvement")
        else:
            logger.info("\nNo specific areas for improvement identified")
        
        logger.info("Retrieval Judge comparison test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during Retrieval Judge comparison test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())