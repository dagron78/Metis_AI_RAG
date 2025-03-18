# Database Integration

This directory contains the database integration components for the Metis_RAG system.

## Overview

The database integration provides a PostgreSQL-based persistence layer for the Metis_RAG system, allowing for efficient storage and retrieval of documents, conversations, and analytics data.

## Components

### Database Connection (`session.py`)

Provides database connection management with:
- Connection pooling for efficient database access
- Session management with context manager support
- Transaction management with automatic rollback on exceptions
- Database initialization function

### SQLAlchemy Models (`models.py`)

Defines the database schema using SQLAlchemy ORM:
- Document: Stores document metadata and content
- Chunk: Stores document chunks for retrieval
- Tag: Stores document tags
- Folder: Stores folder structure for documents
- Conversation: Stores conversation metadata
- Message: Stores conversation messages
- Citation: Stores citations for messages
- ProcessingJob: Stores document processing job information
- AnalyticsQuery: Stores query analytics data

### Repository Classes (`repositories/`)

Implements the repository pattern for database operations:
- BaseRepository: Common CRUD operations
- DocumentRepository: Document management operations
- ConversationRepository: Conversation and message management
- AnalyticsRepository: Query logging and analytics

### Dependencies (`dependencies.py`)

Provides FastAPI dependency injection for repositories:
- get_db: Database session dependency
- get_document_repository: Document repository dependency
- get_conversation_repository: Conversation repository dependency
- get_analytics_repository: Analytics repository dependency

## Database Migrations

Database migrations are managed using Alembic:
- Configuration: `alembic.ini` in the project root
- Environment: `alembic/env.py`
- Migrations: `alembic/versions/`

## Usage

To use the database components in API endpoints:

```python
from fastapi import Depends
from app.db.dependencies import get_document_repository
from app.db.repositories.document_repository import DocumentRepository

@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    document_repo: DocumentRepository = Depends(get_document_repository)
):
    document = document_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document