#!/usr/bin/env python3
"""
Test suite for evaluating the quality of RAG responses in the Metis RAG system.
This test suite focuses on factual accuracy, relevance, and citation quality.
"""

import os
import sys
import json
import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_rag_quality")

# Import RAG components
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.document_processor import DocumentProcessor
from app.models.document import Document, Chunk
from app.models.chat import ChatQuery
from app.main import app

# Test client
client = TestClient(app)

# Test document content with known facts
TEST_DOCUMENTS = {
    "technical_doc": {
        "filename": "technical_documentation.md",
        "content": """# Metis RAG Technical Documentation

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
""",
        "tags": ["technical", "documentation", "architecture"],
        "folder": "/test"
    },
    "business_report": {
        "filename": "quarterly_report.txt",
        "content": """Quarterly Business Report
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
""",
        "tags": ["business", "report", "quarterly"],
        "folder": "/test"
    },
    "product_specs": {
        "filename": "product_specifications.csv",
        "content": """Product ID,Name,Category,Price,Features,Release Date
P001,MetisRAG Enterprise,Software,$4999,Advanced RAG capabilities|Multi-document retrieval|Enterprise security,2025-01-15
P002,MetisRAG Professional,Software,$1999,Standard RAG capabilities|Document management|API access,2025-01-15
P003,MetisRAG Basic,Software,$499,Basic RAG capabilities|Limited document storage|Web interface,2025-01-15
P004,MetisRAG API,Service,$0.10 per query,Pay-per-use|REST API|Developer documentation,2025-02-01
P005,MetisRAG Mobile,Mobile App,$9.99 per month,iOS and Android|Offline capabilities|Voice interface,2025-03-15
""",
        "tags": ["product", "specifications", "pricing"],
        "folder": "/test"
    }
}

# Test queries with expected facts to be present in responses
TEST_QUERIES = [
    {
        "query": "What is the architecture of Metis RAG?",
        "expected_facts": [
            "modular architecture",
            "Frontend Layer",
            "API Layer",
            "RAG Engine",
            "HTML, CSS, and JavaScript",
            "FastAPI"
        ],
        "document_ids": ["technical_doc"]
    },
    {
        "query": "What was the revenue reported in Q1 2025?",
        "expected_facts": [
            "$4.2M",
            "15% increase",
            "year-over-year",
            "net profit of $1.4M"
        ],
        "document_ids": ["business_report"]
    },
    {
        "query": "What are the components of the RAG engine?",
        "expected_facts": [
            "Document Processing",
            "Vector Store",
            "LLM Integration",
            "chunking",
            "embeddings",
            "Ollama"
        ],
        "document_ids": ["technical_doc"]
    },
    {
        "query": "What are the strategic initiatives for Q2?",
        "expected_facts": [
            "International Expansion",
            "European markets",
            "Enterprise Solution",
            "Strategic Partnerships",
            "Operational Efficiency"
        ],
        "document_ids": ["business_report"]
    },
    {
        "query": "What products are available and at what price points?",
        "expected_facts": [
            "MetisRAG Enterprise",
            "$4999",
            "MetisRAG Professional",
            "$1999",
            "MetisRAG Basic",
            "$499"
        ],
        "document_ids": ["product_specs"]
    },
    {
        "query": "What was the customer retention rate and NPS score?",
        "expected_facts": [
            "94%",
            "Net Promoter Score",
            "improved from 42 to 48"
        ],
        "document_ids": ["business_report"]
    }
]

# Test for multi-document queries
MULTI_DOC_QUERIES = [
    {
        "query": "Compare the MetisRAG Enterprise product with the RAG Engine architecture",
        "expected_facts": [
            "MetisRAG Enterprise",
            "$4999",
            "Advanced RAG capabilities",
            "RAG Engine",
            "Document Processing",
            "Vector Store"
        ],
        "document_ids": ["technical_doc", "product_specs"]
    },
    {
        "query": "What is the relationship between the Q1 financial performance and the product offerings?",
        "expected_facts": [
            "$4.2M in revenue",
            "MetisRAG Enterprise",
            "MetisRAG Professional",
            "MetisRAG Basic"
        ],
        "document_ids": ["business_report", "product_specs"]
    }
]

@pytest.fixture
def test_documents_dir():
    """Create a directory for test documents"""
    test_dir = "test_quality_docs"
    os.makedirs(test_dir, exist_ok=True)
    return test_dir

@pytest.fixture
def create_test_documents(test_documents_dir):
    """Create test documents with known facts"""
    document_paths = {}
    
    for doc_id, doc_info in TEST_DOCUMENTS.items():
        file_path = os.path.join(test_documents_dir, doc_info["filename"])
        with open(file_path, "w") as f:
            f.write(doc_info["content"])
        document_paths[doc_id] = file_path
    
    return document_paths

@pytest.fixture
async def setup_vector_store(create_test_documents):
    """Set up vector store with test documents"""
    # Use a separate directory for test ChromaDB
    test_chroma_dir = "test_quality_chroma"
    os.makedirs(test_chroma_dir, exist_ok=True)
    
    # Initialize vector store
    vector_store = VectorStore(persist_directory=test_chroma_dir)
    
    # Create Document objects
    documents = {}
    for doc_id, doc_info in TEST_DOCUMENTS.items():
        doc = Document(
            id=doc_id,
            filename=doc_info["filename"],
            content=doc_info["content"],
            tags=doc_info["tags"],
            folder=doc_info["folder"]
        )
        
        # Create a single chunk for simplicity in testing
        doc.chunks = [
            Chunk(
                id=f"{doc_id}_chunk_0",
                content=doc_info["content"],
                metadata={
                    "index": 0,
                    "source": doc_info["filename"]
                }
            )
        ]
        
        # Add document to vector store
        await vector_store.add_document(doc)
        documents[doc_id] = doc
    
    return vector_store, documents

@pytest.fixture
async def setup_rag_engine(setup_vector_store):
    """Set up RAG engine with test vector store"""
    vector_store, documents = await setup_vector_store
    rag_engine = RAGEngine(vector_store=vector_store)
    return rag_engine, documents

@pytest.mark.asyncio
async def test_factual_accuracy(setup_rag_engine):
    """Test factual accuracy of RAG responses"""
    rag_engine, documents = await setup_rag_engine
    
    results = []
    for test_case in TEST_QUERIES:
        query = test_case["query"]
        expected_facts = test_case["expected_facts"]
        
        # Execute query with RAG
        response = await rag_engine.query(
            query=query,
            use_rag=True,
            top_k=3,
            stream=False
        )
        
        # Check if response contains expected facts
        answer = response.get("answer", "")
        sources = response.get("sources", [])
        
        # Count how many expected facts are present in the answer
        fact_count = sum(1 for fact in expected_facts if fact.lower() in answer.lower())
        fact_percentage = (fact_count / len(expected_facts)) * 100
        
        # Check if sources are from the expected documents
        expected_doc_ids = test_case["document_ids"]
        source_doc_ids = [source.document_id for source in sources]
        correct_sources = all(doc_id in source_doc_ids for doc_id in expected_doc_ids)
        
        # Log results
        logger.info(f"Query: {query}")
        logger.info(f"Answer: {answer[:100]}...")
        logger.info(f"Facts found: {fact_count}/{len(expected_facts)} ({fact_percentage:.1f}%)")
        logger.info(f"Correct sources: {correct_sources}")
        
        # Store results
        results.append({
            "query": query,
            "answer": answer,
            "expected_facts": expected_facts,
            "facts_found": fact_count,
            "fact_percentage": fact_percentage,
            "correct_sources": correct_sources,
            "sources": [
                {
                    "document_id": s.document_id,
                    "relevance_score": s.relevance_score
                }
                for s in sources
            ] if sources else []
        })
    
    # Save results to file
    results_path = "test_quality_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Assert minimum factual accuracy
    for i, result in enumerate(results):
        assert result["fact_percentage"] >= 70, f"Query {i+1} has low factual accuracy: {result['fact_percentage']:.1f}%"
        assert result["correct_sources"], f"Query {i+1} has incorrect sources"

@pytest.mark.asyncio
async def test_multi_document_retrieval(setup_rag_engine):
    """Test retrieval across multiple documents"""
    rag_engine, documents = await setup_rag_engine
    
    results = []
    for test_case in MULTI_DOC_QUERIES:
        query = test_case["query"]
        expected_facts = test_case["expected_facts"]
        
        # Execute query with RAG
        response = await rag_engine.query(
            query=query,
            use_rag=True,
            top_k=5,  # Increase top_k for multi-document queries
            stream=False
        )
        
        # Check if response contains expected facts
        answer = response.get("answer", "")
        sources = response.get("sources", [])
        
        # Count how many expected facts are present in the answer
        fact_count = sum(1 for fact in expected_facts if fact.lower() in answer.lower())
        fact_percentage = (fact_count / len(expected_facts)) * 100
        
        # Check if sources are from multiple documents
        source_doc_ids = set(source.document_id for source in sources)
        multi_doc_retrieval = len(source_doc_ids) > 1
        
        # Check if sources are from the expected documents
        expected_doc_ids = test_case["document_ids"]
        correct_sources = all(doc_id in source_doc_ids for doc_id in expected_doc_ids)
        
        # Log results
        logger.info(f"Multi-doc Query: {query}")
        logger.info(f"Answer: {answer[:100]}...")
        logger.info(f"Facts found: {fact_count}/{len(expected_facts)} ({fact_percentage:.1f}%)")
        logger.info(f"Multi-document retrieval: {multi_doc_retrieval}")
        logger.info(f"Correct sources: {correct_sources}")
        
        # Store results
        results.append({
            "query": query,
            "answer": answer,
            "expected_facts": expected_facts,
            "facts_found": fact_count,
            "fact_percentage": fact_percentage,
            "multi_doc_retrieval": multi_doc_retrieval,
            "correct_sources": correct_sources,
            "source_doc_ids": list(source_doc_ids)
        })
    
    # Save results to file
    results_path = "test_multi_doc_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Assert multi-document retrieval
    for i, result in enumerate(results):
        assert result["multi_doc_retrieval"], f"Query {i+1} failed to retrieve from multiple documents"
        assert result["fact_percentage"] >= 60, f"Query {i+1} has low factual accuracy: {result['fact_percentage']:.1f}%"

@pytest.mark.asyncio
async def test_citation_quality(setup_rag_engine):
    """Test quality of citations in RAG responses"""
    rag_engine, documents = await setup_rag_engine
    
    results = []
    for test_case in TEST_QUERIES:
        query = test_case["query"]
        
        # Execute query with RAG
        response = await rag_engine.query(
            query=query,
            use_rag=True,
            top_k=3,
            stream=False
        )
        
        # Check citations in the answer
        answer = response.get("answer", "")
        sources = response.get("sources", [])
        
        # Check if answer contains citation markers
        has_citation_markers = "[" in answer and "]" in answer
        
        # Check if citations in the answer correspond to sources
        citation_count = 0
        for i in range(1, 10):  # Check for citation markers [1] through [9]
            if f"[{i}]" in answer:
                citation_count += 1
        
        # Check if number of citations is reasonable
        reasonable_citation_count = 0 < citation_count <= len(sources) + 1  # Allow for one extra citation
        
        # Log results
        logger.info(f"Citation Query: {query}")
        logger.info(f"Has citation markers: {has_citation_markers}")
        logger.info(f"Citation count: {citation_count}")
        logger.info(f"Source count: {len(sources)}")
        
        # Store results
        results.append({
            "query": query,
            "has_citation_markers": has_citation_markers,
            "citation_count": citation_count,
            "source_count": len(sources),
            "reasonable_citation_count": reasonable_citation_count
        })
    
    # Save results to file
    results_path = "test_citation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Assert citation quality
    for i, result in enumerate(results):
        assert result["has_citation_markers"], f"Query {i+1} response lacks citation markers"
        assert result["reasonable_citation_count"], f"Query {i+1} has unreasonable citation count"

@pytest.mark.asyncio
async def test_api_integration(create_test_documents):
    """Test integration with API endpoints"""
    # Test document upload and processing through API
    results = []
    
    for doc_id, doc_path in create_test_documents.items():
        doc_info = TEST_DOCUMENTS[doc_id]
        
        # Open the file for upload
        with open(doc_path, "rb") as f:
            # Upload the document
            upload_response = client.post(
                "/api/documents/upload",
                files={"file": (doc_info["filename"], f, "text/plain")}
            )
            
            # Check upload response
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            assert upload_data["success"] is True
            assert "document_id" in upload_data
            
            document_id = upload_data["document_id"]
            
            # Process the document
            process_response = client.post(
                "/api/documents/process",
                json={"document_ids": [document_id]}
            )
            
            # Check process response
            assert process_response.status_code == 200
            process_data = process_response.json()
            assert process_data["success"] is True
            
            # Test query with the uploaded document
            query = next((q["query"] for q in TEST_QUERIES if doc_id in q["document_ids"]), "What is this document about?")
            
            query_response = client.post(
                "/api/chat/query",
                json={
                    "message": query,
                    "use_rag": True,
                    "stream": False
                }
            )
            
            # Check query response
            assert query_response.status_code == 200
            query_data = query_response.json()
            assert "message" in query_data
            assert "conversation_id" in query_data
            
            # Store results
            results.append({
                "document_id": document_id,
                "filename": doc_info["filename"],
                "query": query,
                "response": query_data["message"]
            })
            
            # Clean up - delete the document
            delete_response = client.delete(f"/api/documents/{document_id}")
            assert delete_response.status_code == 200
            delete_data = delete_response.json()
            assert delete_data["success"] is True
    
    # Save results to file
    results_path = "test_api_integration_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])