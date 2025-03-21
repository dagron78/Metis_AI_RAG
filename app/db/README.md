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
  - Uses conv_metadata (JSON field) to store flexible metadata including user_id
  - Tracks message count and timestamps
- Message: Stores conversation messages
- Citation: Stores citations for messages
- ProcessingJob: Stores document processing job information
- AnalyticsQuery: Stores query analytics data

#### Important Note on Metadata Fields

Several models use JSON fields for flexible metadata storage:
- Conversation.conv_metadata: Stores user_id and other conversation metadata
- Document.doc_metadata: Stores document-specific metadata
- Chunk.chunk_metadata: Stores chunk-specific metadata
- ProcessingJob.job_metadata: Stores job-specific metadata

When accessing these fields in code, always use the attribute name (e.g., `conversation.conv_metadata.get("user_id")`) rather than trying to access properties directly (e.g., `conversation.user_id`).

### Repository Classes (`repositories/`)

Implements the repository pattern for database operations:
- BaseRepository: Common CRUD operations
- DocumentRepository: Document management operations
- ConversationRepository: Conversation and message management with async operations
  - Handles conversations, messages, and citations
  - Stores user_id and other metadata in the conv_metadata JSON field
  - Provides methods for conversation history retrieval and search
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

### Document Repository Example

To use the document repository in API endpoints:

```python
from fastapi import Depends
from app.db.dependencies import get_document_repository
from app.db.repositories.document_repository import DocumentRepository

@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    document_repo: DocumentRepository = Depends(get_document_repository)
):
    document = await document_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
```

### Conversation Repository Example

To use the conversation repository with proper metadata handling:

```python
from fastapi import Depends
from app.db.dependencies import get_conversation_repository
from app.db.repositories.conversation_repository import ConversationRepository

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    conversation_repo: ConversationRepository = Depends(get_conversation_repository)
):
    conversation = await conversation_repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Access user_id from metadata correctly
    user_id = conversation.conv_metadata.get("user_id")
    
    # Get messages for this conversation
    messages = await conversation_repo.get_conversation_messages(
        conversation_id=conversation_id,
        limit=100
    )
    
    return {
        "id": str(conversation.id),
        "user_id": user_id,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": messages,
        "message_count": conversation.message_count
    }
```