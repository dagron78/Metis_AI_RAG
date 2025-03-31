#!/usr/bin/env python3
"""
Test data generator for Metis RAG testing.
This script generates test documents with known facts for testing the RAG system.
"""

import os
import json
import argparse
import logging
import random
import string
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("generate_test_data")

# Test document templates
TEST_DOCUMENTS = {
    "technical_doc": {
        "filename": "technical_documentation.md",
        "content": """# Metis RAG Technical Documentation

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
    },
    "user_guide": {
        "filename": "user_guide.md",
        "content": """# Metis RAG User Guide

## Getting Started

Welcome to Metis RAG, a powerful Retrieval-Augmented Generation system for enterprise knowledge management. This guide will help you get started with the system.

### Installation

To install Metis RAG, follow these steps:

1. Clone the repository: `git clone https://github.com/example/metis-rag.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables: Copy `.env.example` to `.env` and update as needed
4. Start the application: `python -m app.main`

### First Steps

Once the application is running, you can access it at `http://localhost:8000`. The main interface provides the following sections:

- **Chat**: Interact with the RAG system through a chat interface
- **Documents**: Upload, manage, and organize your documents
- **System**: Configure system settings and monitor performance
- **Analytics**: View usage statistics and performance metrics

## Document Management

### Uploading Documents

To upload documents:

1. Navigate to the Documents page
2. Click the "Upload" button
3. Select one or more files from your computer
4. Click "Upload" to start the upload process

Supported file types include:
- PDF (.pdf)
- Text (.txt)
- Markdown (.md)
- CSV (.csv)

### Processing Documents

After uploading, documents need to be processed before they can be used for RAG:

1. Select the documents you want to process
2. Click the "Process" button
3. Wait for processing to complete

Processing includes:
- Text extraction
- Chunking
- Embedding generation
- Vector store indexing

### Organizing Documents

You can organize documents using folders and tags:

- **Folders**: Create a hierarchical structure for your documents
- **Tags**: Add labels to documents for flexible categorization

## Using the Chat Interface

### Basic Queries

To ask a question:

1. Type your question in the input field
2. Click "Send" or press Enter
3. View the response, including citations to source documents

### Advanced Options

The chat interface provides several advanced options:

- **RAG Toggle**: Enable or disable RAG for specific queries
- **Model Selection**: Choose different language models
- **Parameter Adjustment**: Fine-tune model parameters
- **Conversation History**: View and manage conversation history

## System Configuration

### Model Settings

You can configure the following model settings:

- **Default Model**: Set the default language model
- **Context Window**: Adjust the context window size
- **Temperature**: Control response randomness
- **Top-P**: Adjust nucleus sampling

### Vector Store Settings

Vector store settings include:

- **Embedding Model**: Choose the embedding model
- **Similarity Metric**: Select the similarity metric (cosine, dot product, etc.)
- **Top-K Results**: Set the number of results to retrieve

### Chunking Settings

Chunking settings include:

- **Chunking Strategy**: Choose between recursive, token, or markdown chunking
- **Chunk Size**: Set the chunk size in tokens or characters
- **Chunk Overlap**: Set the overlap between chunks

## Analytics

The analytics dashboard provides insights into:

- **Usage Metrics**: Queries per day, document uploads, etc.
- **Performance Metrics**: Response time, throughput, etc.
- **Document Metrics**: Document count, chunk count, etc.
- **Model Metrics**: Token usage, model performance, etc.

## Troubleshooting

### Common Issues

- **Slow Response Time**: Try reducing the number of retrieved chunks or using a smaller model
- **Poor Relevance**: Check if your documents are properly processed and indexed
- **Processing Errors**: Ensure your documents are in a supported format and not corrupted
- **Connection Issues**: Check if Ollama is running and accessible

### Getting Help

If you encounter issues not covered in this guide, please:

- Check the FAQ section
- Search the knowledge base
- Contact support at support@example.com
""",
        "tags": ["user guide", "documentation", "help"],
        "folder": "/test"
    },
    "api_documentation": {
        "filename": "api_documentation.md",
        "content": """# Metis RAG API Documentation

## Overview

The Metis RAG API provides programmatic access to the Retrieval-Augmented Generation system. This document describes the available endpoints, request/response formats, and authentication methods.

## Base URL

All API endpoints are relative to the base URL:

```
https://api.example.com/v1
```

## Authentication

The API uses API keys for authentication. To authenticate, include your API key in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

You can generate an API key in the System settings page.

## Endpoints

### Chat

#### Query

```
POST /chat/query
```

Submit a query to the RAG system.

**Request Body:**

```json
{
  "message": "What is the architecture of Metis RAG?",
  "conversation_id": "optional-conversation-id",
  "model": "optional-model-name",
  "use_rag": true,
  "stream": false,
  "model_parameters": {
    "temperature": 0.7,
    "top_p": 0.9
  },
  "metadata_filters": {
    "tags": ["technical", "documentation"]
  }
}
```

**Response:**

```json
{
  "message": "Metis RAG follows a modular architecture with the following components: Frontend Layer, API Layer, and RAG Engine. The RAG Engine consists of Document Processing, Vector Store, and LLM Integration. [1]",
  "conversation_id": "conversation-id",
  "citations": [
    {
      "document_id": "doc-id",
      "chunk_id": "chunk-id",
      "relevance_score": 0.92,
      "excerpt": "Metis RAG follows a modular architecture with the following components..."
    }
  ]
}
```

#### List Conversations

```
GET /chat/conversations
```

List all conversations.

**Response:**

```json
{
  "conversations": [
    {
      "id": "conversation-id",
      "created": "2025-01-15T12:34:56Z",
      "updated": "2025-01-15T13:45:67Z",
      "message_count": 10
    }
  ]
}
```

#### Get Conversation

```
GET /chat/conversations/{conversation_id}
```

Get a specific conversation.

**Response:**

```json
{
  "id": "conversation-id",
  "created": "2025-01-15T12:34:56Z",
  "updated": "2025-01-15T13:45:67Z",
  "messages": [
    {
      "content": "What is the architecture of Metis RAG?",
      "role": "user",
      "timestamp": "2025-01-15T12:34:56Z"
    },
    {
      "content": "Metis RAG follows a modular architecture with the following components...",
      "role": "assistant",
      "timestamp": "2025-01-15T12:35:00Z",
      "citations": [
        {
          "document_id": "doc-id",
          "chunk_id": "chunk-id",
          "relevance_score": 0.92,
          "excerpt": "Metis RAG follows a modular architecture with the following components..."
        }
      ]
    }
  ]
}
```

### Documents

#### Upload Document

```
POST /documents/upload
```

Upload a document.

**Request:**

Multipart form data with a `file` field.

**Response:**

```json
{
  "success": true,
  "document_id": "doc-id",
  "filename": "technical_documentation.md",
  "size": 12345
}
```

#### Process Documents

```
POST /documents/process
```

Process uploaded documents.

**Request Body:**

```json
{
  "document_ids": ["doc-id-1", "doc-id-2"],
  "force_reprocess": false,
  "chunking_strategy": "recursive",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

**Response:**

```json
{
  "success": true,
  "processed_count": 2,
  "failed_count": 0,
  "failed_documents": []
}
```

#### List Documents

```
GET /documents/list
```

List all documents.

**Query Parameters:**

- `folder` (optional): Filter by folder
- `tags` (optional): Filter by tags (comma-separated)

**Response:**

```json
[
  {
    "id": "doc-id",
    "filename": "technical_documentation.md",
    "chunk_count": 10,
    "metadata": {
      "file_size": 12345,
      "file_type": "md",
      "created_at": 1642234567,
      "modified_at": 1642234567
    },
    "tags": ["technical", "documentation"],
    "folder": "/test",
    "uploaded": "2025-01-15T12:34:56Z"
  }
]
```

#### Get Document

```
GET /documents/{document_id}
```

Get a specific document.

**Response:**

```json
{
  "id": "doc-id",
  "filename": "technical_documentation.md",
  "content": "# Metis RAG Technical Documentation...",
  "chunk_count": 10,
  "metadata": {
    "file_size": 12345,
    "file_type": "md",
    "created_at": 1642234567,
    "modified_at": 1642234567
  },
  "tags": ["technical", "documentation"],
  "folder": "/test",
  "uploaded": "2025-01-15T12:34:56Z"
}
```

#### Delete Document

```
DELETE /documents/{document_id}
```

Delete a specific document.

**Response:**

```json
{
  "success": true
}
```

### System

#### Health Check

```
GET /system/health
```

Check system health.

**Response:**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "components": {
    "api": "ok",
    "vector_store": "ok",
    "ollama": "ok"
  }
}
```

#### Models

```
GET /system/models
```

List available models.

**Response:**

```json
{
  "models": [
    {
      "name": "llama2",
      "description": "Llama 2 7B",
      "parameters": 7000000000,
      "context_window": 4096
    },
    {
      "name": "mistral",
      "description": "Mistral 7B",
      "parameters": 7000000000,
      "context_window": 8192
    }
  ]
}
```

### Analytics

#### Query Analytics

```
GET /analytics/queries
```

Get query analytics.

**Query Parameters:**

- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `model` (optional): Filter by model

**Response:**

```json
{
  "total_queries": 1234,
  "average_response_time_ms": 567,
  "queries_per_day": [
    {
      "date": "2025-01-15",
      "count": 123
    },
    {
      "date": "2025-01-16",
      "count": 456
    }
  ],
  "models": [
    {
      "name": "llama2",
      "count": 789
    },
    {
      "name": "mistral",
      "count": 345
    }
  ]
}
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

Error responses include a JSON body with details:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Invalid request parameters",
    "details": {
      "message": "This field is required"
    }
  }
}
```

## Rate Limiting

The API is rate limited to 100 requests per minute per API key. If you exceed this limit, you'll receive a 429 Too Many Requests response.

## Pagination

List endpoints support pagination using the `offset` and `limit` query parameters:

```
GET /documents/list?offset=0&limit=10
```

Paginated responses include pagination metadata:

```json
{
  "data": [...],
  "pagination": {
    "total": 123,
    "offset": 0,
    "limit": 10,
    "next": "/documents/list?offset=10&limit=10",
    "previous": null
  }
}
```
""",
        "tags": ["api", "documentation", "reference"],
        "folder": "/test"
    }
}

# Test queries with expected facts
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
        "query": "How do I upload documents to the system?",
        "expected_facts": [
            "Navigate to the Documents page",
            "Click the \"Upload\" button",
            "Select one or more files",
            "Click \"Upload\" to start the upload process"
        ],
        "document_ids": ["user_guide"]
    },
    {
        "query": "What authentication method does the API use?",
        "expected_facts": [
            "API keys",
            "Authorization header",
            "Bearer YOUR_API_KEY"
        ],
        "document_ids": ["api_documentation"]
    }
]

def generate_random_string(length):
    """Generate a random string of specified length"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def generate_test_documents(output_dir, count=None, specific_docs=None):
    """Generate test documents"""
    os.makedirs(output_dir, exist_ok=True)
    
    documents = []
    
    # Determine which documents to generate
    doc_ids = []
    if specific_docs:
        doc_ids = specific_docs
    elif count:
        doc_ids = random.sample(list(TEST_DOCUMENTS.keys()), min(count, len(TEST_DOCUMENTS)))
    else:
        doc_ids = list(TEST_DOCUMENTS.keys())
    
    # Generate documents
    for doc_id in doc_ids:
        doc_info = TEST_DOCUMENTS[doc_id]
        
        # Create document file
        file_path = os.path.join(output_dir, doc_info["filename"])
        with open(file_path, "w") as f:
            f.write(doc_info["content"])
        
        # Store document metadata
        documents.append({
            "id": doc_id,
            "filename": doc_info["filename"],
            "path": file_path,
            "tags": doc_info["tags"],
            "folder": doc_info["folder"]
        })
        
        logger.info(f"Generated document: {file_path}")
    
    # Generate metadata file
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump({
            "documents": documents,
            "generated_at": datetime.now().isoformat()
        }, f, indent=2)
    
    logger.info(f"Generated metadata: {metadata_path}")
    
    return documents

def generate_test_queries(output_dir, count=None, specific_queries=None):
    """Generate test queries"""
    # Determine which queries to generate
    queries = []
    if specific_queries:
        queries = [q for i, q in enumerate(TEST_QUERIES) if i in specific_queries]
    elif count:
        queries = random.sample(TEST_QUERIES, min(count, len(TEST_QUERIES)))
    else:
        queries = TEST_QUERIES
    
    # Generate queries file
    queries_path = os.path.join(output_dir, "test_queries.json")
    with open(queries_path, "w") as f:
        json.dump({
            "queries": queries,
            "generated_at": datetime.now().isoformat()
        }, f, indent=2)
    
    logger.info(f"Generated queries: {queries_path}")
    
    return queries

def generate_large_document(output_dir, size_kb):
    """Generate a large document of specified size in KB"""
    # Generate random content
    content = generate_random_string(size_kb * 1024)
    
    # Create document file
    file_path = os.path.join(output_dir, f"large_document_{size_kb}kb.txt")
    with open(file_path, "w") as f:
        f.write(content)
    
    logger.info(f"Generated large document: {file_path} ({size_kb} KB)")
    
    return file_path

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate test data for Metis RAG testing")
    parser.add_argument("--output-dir", type=str, default="test_data", help="Output directory for test data")
    parser.add_argument("--document-count", type=int, help="Number of documents to generate")
    parser.add_argument("--query-count", type=int, help="Number of queries to generate")
    parser.add_argument("--specific-docs", type=str, help="Specific documents to generate (comma-separated)")
    parser.add_argument("--specific-queries", type=str, help="Specific queries to generate (comma-separated)")
    parser.add_argument("--large-document", type=int, help="Generate a large document of specified size in KB")
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Parse specific documents
    specific_docs = None
    if args.specific_docs:
        specific_docs = args.specific_docs.split(",")
    
    # Parse specific queries
    specific_queries = None
    if args.specific_queries:
        specific_queries = [int(i) for i in args.specific_queries.split(",")]
    
    # Generate test documents
    documents = generate_test_documents(args.output_dir, args.document_count, specific_docs)
    
    # Generate test queries
    queries = generate_test_queries(args.output_dir, args.query_count, specific_queries)
    
    # Generate large document if requested
    if args.large_document:
        large_doc_path = generate_large_document(args.output_dir, args.large_document)
    
    logger.info(f"Test data generation complete. Generated {len(documents)} documents and {len(queries)} queries.")

if __name__ == "__main__":
    main()