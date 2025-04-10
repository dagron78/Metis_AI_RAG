#!/usr/bin/env python3
"""
Simple script to try a query with the Metis RAG system.
"""
import asyncio
import logging
import sys
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("try_rag_query")

# Import RAG components
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.models.document import Document, Chunk

async def process_test_documents(vector_store: VectorStore) -> List[str]:
    """
    Process test documents and add them to the vector store.
    Returns a list of document IDs.
    """
    # Test documents with known content
    test_documents = {
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
        }
    }
    
    document_ids = []
    
    # Create Document objects and add them to the vector store
    for doc_id, doc_info in test_documents.items():
        logger.info(f"Processing document: {doc_info['filename']}")
        
        doc = Document(
            id=doc_id,
            filename=doc_info["filename"],
            content=doc_info["content"],
            tags=doc_info["tags"],
            folder=doc_info["folder"]
        )
        
        # Create a single chunk for simplicity
        doc.chunks = [
            Chunk(
                id=f"{doc_id}_chunk_0",
                content=doc_info["content"],
                metadata={
                    "index": 0,
                    "source": doc_info["filename"],
                    "document_id": doc_id,
                    "filename": doc_info["filename"],
                    "tags": doc_info["tags"],
                    "folder": doc_info["folder"]
                }
            )
        ]
        
        # Add document to vector store
        await vector_store.add_document(doc)
        document_ids.append(doc_id)
        
        logger.info(f"Added document {doc_id} to vector store")
    
    return document_ids

async def try_query(query: str):
    """
    Try a query with the RAG system.
    """
    try:
        # Initialize vector store with a test directory
        vector_store = VectorStore(persist_directory="test_query_chroma")
        
        # Check if there are documents in the vector store
        stats = vector_store.get_stats()
        if stats["count"] == 0:
            logger.info("No documents in vector store, adding test documents")
            await process_test_documents(vector_store)
        else:
            logger.info(f"Vector store already contains {stats['count']} chunks")
        
        # Initialize RAG engine
        rag_engine = RAGEngine(vector_store=vector_store)
        
        # Execute query with RAG
        logger.info(f"Executing query: {query}")
        response = await rag_engine.query(
            query=query,
            use_rag=True,
            top_k=3,
            stream=False
        )
        
        # Print the response
        print("\n" + "="*80)
        print(f"QUERY: {query}")
        print("="*80)
        
        if "answer" in response:
            print("\nANSWER:")
            print(response["answer"])
        
        if "sources" in response and response["sources"]:
            print("\nSOURCES:")
            for i, source in enumerate(response["sources"]):
                print(f"[{i+1}] {source.filename} (Score: {source.relevance_score:.2f})")
                print(f"    Excerpt: {source.excerpt[:100]}...")
        
        print("="*80 + "\n")
        
        return response
    except Exception as e:
        logger.error(f"Error trying query: {str(e)}")
        raise

async def main():
    """
    Main function to try a query with the RAG system.
    """
    if len(sys.argv) > 1:
        # Use query from command line arguments
        query = " ".join(sys.argv[1:])
    else:
        # Use default queries
        queries = [
            "What is the architecture of Metis RAG?",
            "What was the revenue reported in Q1 2025?",
            "What are the components of the RAG engine?",
            "What are the strategic initiatives for Q2?",
        ]
        
        for query in queries:
            await try_query(query)
            # Add a small delay between queries
            await asyncio.sleep(1)
        
        return
    
    # Try the user-provided query
    await try_query(query)

if __name__ == "__main__":
    asyncio.run(main())