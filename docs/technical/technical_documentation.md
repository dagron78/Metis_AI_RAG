# Metis RAG Technical Documentation

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
- Chunking with configurable strategies:
  - Recursive: Splits text recursively by characters, good for general text
  - Token: Splits text by token count rather than character count, useful for LLMs with token limits
  - Markdown: Splits markdown documents by headers, good for structured documents
  - Semantic: Uses LLM to identify natural semantic boundaries, best for preserving meaning
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

#### Chunking Judge

The Chunking Judge is an LLM-based agent that enhances the document processing pipeline by:
- Analyzing document structure, content type, and formatting
- Selecting the most appropriate chunking strategy (recursive, markdown, or semantic)
- Recommending optimal chunk size and overlap parameters
- Providing detailed justification for its recommendations

Our testing shows the Chunking Judge effectively:
- Recognizes document structures, even identifying markdown-like elements in plain text
- Selects appropriate strategies that align with document structure
- Optimizes parameters based on document characteristics
- Adapts to different document types without manual configuration

#### Semantic Chunker

The Semantic Chunker is an advanced chunking strategy that:
- Uses LLM to identify natural semantic boundaries in text
- Preserves semantic meaning and context in chunks
- Creates more coherent, self-contained chunks than traditional methods
- Respects the logical flow of information in documents

Key features include:
- Intelligent boundary detection based on topic transitions and subject matter shifts
- Handling of long documents by processing in sections
- Caching for performance optimization
- Fallback mechanisms for error handling

#### Retrieval Judge

The Retrieval Judge is an LLM-based agent that enhances the RAG retrieval process by:
- Analyzing queries to determine optimal retrieval parameters
- Evaluating retrieved chunks for relevance
- Refining queries when needed to improve retrieval precision
- Optimizing context assembly for better response generation

Our testing shows the Retrieval Judge significantly improves retrieval quality:
- 89.26% faster retrieval times through effective caching
- Transforms ambiguous queries into specific, detailed requests
- Reduces context size by 76.4% on average while maintaining relevance
- Performs best with domain-specific and complex queries

#### LangGraph RAG Agent

The LangGraph RAG Agent is a state machine-based orchestration layer that coordinates the entire RAG process:

- **State Machine Architecture**: Uses LangGraph to define a flexible, state-based workflow with clear transitions between stages
- **Integrated Components**: Combines the Chunking Judge, Semantic Chunker, and Retrieval Judge into a cohesive system
- **Multi-step Reasoning**: Enables complex, multi-step reasoning during the RAG process through a series of specialized nodes:
  - Query Analysis: Analyzes the query to determine complexity and retrieval parameters
  - Retrieval: Retrieves relevant chunks from the vector store
  - Query Refinement: Refines the query if needed based on initial retrieval
  - Context Optimization: Optimizes the context assembly for generation
  - Generation: Generates the final response using the optimized context

Key features include:
- Conditional logic that adapts the workflow based on query characteristics
- Support for both streaming and non-streaming responses
- Comprehensive state management throughout the RAG process
- Robust error handling and fallback mechanisms
- Detailed logging for transparency and debugging

The LangGraph integration represents a significant advancement in our RAG architecture, moving from a linear pipeline to a more flexible approach that can adapt to different query types and document characteristics.

## Deployment Options

Metis RAG can be deployed in several ways:

1. **Local Development**
   - Run directly with Python and uvicorn
   - Suitable for development and testing

2. **Docker Deployment**
   - Use the provided Dockerfile and docker-compose.yml
   - Containerized deployment for easier management

3. **Production Deployment**
   - Use a reverse proxy like Nginx
   - Configure proper authentication
   - Set up monitoring and logging

## Configuration

Metis RAG is configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| OLLAMA_BASE_URL | URL for Ollama API | http://localhost:11434 |
| DEFAULT_MODEL | Default LLM model | gemma3:4b |
| DEFAULT_EMBEDDING_MODEL | Model for embeddings | nomic-embed-text |
| UPLOAD_DIR | Directory for uploaded files | ./uploads |
| CHROMA_DB_DIR | Directory for vector DB | ./chroma_db |
| CHUNK_SIZE | Default chunk size | 500 |
| CHUNK_OVERLAP | Default chunk overlap | 50 |
| CHUNKING_JUDGE_MODEL | Model for Chunking Judge | gemma3:4b |
| RETRIEVAL_JUDGE_MODEL | Model for Retrieval Judge | gemma3:4b |
| USE_CHUNKING_JUDGE | Enable/disable Chunking Judge | True |
| USE_RETRIEVAL_JUDGE | Enable/disable Retrieval Judge | True |
| USE_LANGGRAPH_AGENT | Enable/disable LangGraph RAG Agent | True |

## API Reference

### Document API

- `POST /api/documents/upload` - Upload a document
- `GET /api/documents/list` - List all documents
- `GET /api/documents/{document_id}` - Get document details
- `DELETE /api/documents/{document_id}` - Delete a document
- `POST /api/documents/process` - Process documents

### Chat API

- `POST /api/chat/message` - Send a chat message
- `GET /api/chat/history` - Get chat history
- `DELETE /api/chat/history` - Clear chat history
- `POST /api/chat/langgraph` - Send a message using the LangGraph RAG Agent

## Performance Considerations

For optimal performance:
- Use appropriate chunking strategies for different document types:
  - Semantic chunking for complex documents where preserving meaning is critical
  - Markdown chunking for structured documents with clear headers
  - Recursive chunking for general text with natural separators
- Configure chunk size based on your specific use case
- Consider hardware requirements for embedding generation
- Monitor vector store size and performance
- Enable the Chunking Judge to automatically select optimal chunking strategies
- Enable the Retrieval Judge for complex queries requiring precision
- Leverage caching for improved performance (33.33% vector store cache hit rate)
- Consider using a smaller model for the Judges in latency-sensitive applications
- For complex queries, use the LangGraph RAG Agent for more sophisticated processing

### Retrieval Judge Performance

Our testing shows that the Retrieval Judge significantly improves retrieval performance:
- 89.26% faster retrieval times compared to standard retrieval (18.41s vs 171.47s on average)
- Effective caching of both vector store queries and LLM responses
- Query analysis takes 9.03s on average
- Query refinement is very fast (2.08s on average)
- Context optimization reduces context size by 76.4% on average

### Semantic Chunking Performance

The Semantic Chunker provides several advantages over traditional chunking methods:
- Creates more coherent, self-contained chunks that maintain semantic integrity
- Reduces the need for large chunk overlaps since boundaries are semantically meaningful
- Improves retrieval precision by ensuring chunks contain complete concepts
- Works particularly well with complex, technical, or narrative content
- Caching mechanism minimizes the performance impact of LLM-based chunking

### LangGraph RAG Agent Performance

The LangGraph RAG Agent provides a more sophisticated approach to RAG:
- Enables complex, multi-step reasoning through a state machine architecture
- Adapts the workflow based on query characteristics and initial retrieval results
- Provides more detailed logging and transparency throughout the RAG process
- Supports both streaming and non-streaming responses
- Integrates all LLM-based components (Chunking Judge, Semantic Chunker, Retrieval Judge) into a cohesive system

While the LangGraph RAG Agent adds some overhead to the initial processing time, it provides significant benefits for complex queries that require multiple retrieval steps or query refinement. For simpler queries, the standard RAG engine may be more efficient.