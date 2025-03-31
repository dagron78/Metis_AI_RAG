# Product Specifications

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
