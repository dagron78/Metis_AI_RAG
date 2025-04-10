#!/usr/bin/env python3
"""
Test script for Metis RAG retrieval functionality.
This script creates test documents, uploads and processes them,
and then tests the RAG retrieval with specific queries.
"""

import os
import sys
import json
import asyncio
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_rag_retrieval")

# Import RAG components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.models.document import Document, Chunk

# Test document content
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

async def create_test_documents():
    """Create test documents for RAG testing"""
    logger.info("Creating test documents...")
    
    # Create directories for test documents
    os.makedirs("test_docs", exist_ok=True)
    
    # Create Markdown document
    markdown_path = os.path.join("test_docs", "technical_documentation.md")
    with open(markdown_path, "w") as f:
        f.write(MARKDOWN_CONTENT)
    
    # Create PDF-like text document (since we can't easily create a real PDF programmatically)
    pdf_path = os.path.join("test_docs", "quarterly_report.txt")
    with open(pdf_path, "w") as f:
        f.write(PDF_CONTENT)
    
    logger.info(f"Created test documents in {os.path.abspath('test_docs')}")
    return markdown_path, pdf_path

async def process_documents(vector_store, markdown_path, pdf_path):
    """Process the test documents and add them to the vector store"""
    logger.info("Processing test documents...")
    
    # Read file contents first
    with open(markdown_path, "r") as f:
        markdown_content = f.read()
    
    with open(pdf_path, "r") as f:
        pdf_content = f.read()
    
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
    
    # Fix for ChromaDB metadata issue - convert tags to string
    # We'll modify the add_document method in vector_store.py to handle this properly
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
                            "tags_str": tags_str,  # Use string instead of list
                            "folder": document.folder,
                            **chunk.metadata
                        }]
                    )
                
                logger.info(f"Added {len(document.chunks)} chunks to vector store for document {document.id}")
            except Exception as e:
                logger.error(f"Error adding document {document.id} to vector store: {str(e)}")
                raise
    
    # Use our custom vector store
    vector_store = CustomVectorStore()
    
    # Create chunks for Markdown document
    markdown_chunks = [
        Chunk(
            id=str(uuid.uuid4()),
            content=markdown_content,
            metadata={
                "index": 0,
                "source": markdown_path
            }
        )
    ]
    
    # Create chunks for PDF document
    pdf_chunks = [
        Chunk(
            id=str(uuid.uuid4()),
            content=pdf_content,
            metadata={
                "index": 0,
                "source": pdf_path
            }
        )
    ]
    
    # Assign chunks to documents
    markdown_doc.chunks = markdown_chunks
    pdf_doc.chunks = pdf_chunks
    
    # Add documents to vector store
    await vector_store.add_document(markdown_doc)
    await vector_store.add_document(pdf_doc)
    
    logger.info(f"Added documents to vector store: {markdown_doc.id}, {pdf_doc.id}")
    return markdown_doc, pdf_doc, vector_store

async def test_queries(rag_engine):
    """Test RAG retrieval with specific queries"""
    logger.info("Testing RAG retrieval with specific queries...")
    
    test_queries = [
        "What is the architecture of Metis RAG?",
        "What was the revenue reported in Q1 2025?",
        "What are the components of the RAG engine?",
        "What are the strategic initiatives for Q2?",
        "How does the vector store work?",
        "What was the customer retention rate?",
    ]
    
    results = []
    for query in test_queries:
        logger.info(f"Testing query: {query}")
        
        # Execute query with RAG
        response = await rag_engine.query(
            query=query,
            use_rag=True,
            top_k=3,
            stream=False
        )
        
        # Log results
        answer = response.get("answer", "")
        sources = response.get("sources", [])
        
        logger.info(f"Query: {query}")
        logger.info(f"Answer: {answer[:100]}...")
        logger.info(f"Sources: {len(sources)} chunks retrieved")
        
        # Store results for analysis
        results.append({
            "query": query,
            "answer": answer,
            "sources": [
                {
                    "document_id": s.document_id,
                    "chunk_id": s.chunk_id,
                    "relevance_score": s.relevance_score,
                    "excerpt": s.excerpt[:100] + "..." if len(s.excerpt) > 100 else s.excerpt
                }
                for s in sources
            ] if sources else []
        })
    
    # Save results to file
    results_path = os.path.join("test_docs", "rag_test_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to {os.path.abspath(results_path)}")
    return results

async def analyze_results(results):
    """Analyze the test results"""
    logger.info("Analyzing test results...")
    
    # Check if each query has sources
    queries_with_sources = sum(1 for r in results if r["sources"])
    logger.info(f"{queries_with_sources}/{len(results)} queries returned sources")
    
    # Check if answers contain source references
    answers_with_references = sum(1 for r in results if "[" in r["answer"] and "]" in r["answer"])
    logger.info(f"{answers_with_references}/{len(results)} answers contain source references")
    
    # Check for specific content in answers
    architecture_query = next((r for r in results if "architecture" in r["query"].lower()), None)
    revenue_query = next((r for r in results if "revenue" in r["query"].lower()), None)
    
    if architecture_query:
        has_architecture_info = any(keyword in architecture_query["answer"].lower() 
                                   for keyword in ["frontend", "api", "rag engine", "modular"])
        logger.info(f"Architecture query contains relevant information: {has_architecture_info}")
    
    if revenue_query:
        has_revenue_info = any(keyword in revenue_query["answer"].lower() 
                              for keyword in ["4.2", "million", "15%", "increase"])
        logger.info(f"Revenue query contains relevant information: {has_revenue_info}")
    
    # Overall assessment
    success_rate = (queries_with_sources / len(results)) * 100
    logger.info(f"Overall RAG retrieval success rate: {success_rate:.1f}%")
    
    return {
        "queries_with_sources": queries_with_sources,
        "total_queries": len(results),
        "answers_with_references": answers_with_references,
        "success_rate": success_rate
    }

async def main():
    """Main test function"""
    logger.info("Starting RAG retrieval test...")
    
    try:
        # Create test documents
        markdown_path, pdf_path = await create_test_documents()
        
        # Process documents - this now creates and returns our custom vector store
        markdown_doc, pdf_doc, vector_store = await process_documents(None, markdown_path, pdf_path)
        
        # Initialize RAG engine with our custom vector store
        rag_engine = RAGEngine(vector_store=vector_store)
        
        # Test queries
        results = await test_queries(rag_engine)
        
        # Analyze results
        analysis = await analyze_results(results)
        
        logger.info("RAG retrieval test completed successfully")
        logger.info(f"Success rate: {analysis['success_rate']:.1f}%")
        
    except Exception as e:
        logger.error(f"Error during RAG retrieval test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())