# Metis RAG

Metis RAG is an application that combines conversational AI with Retrieval Augmented Generation (RAG) capabilities. It allows users to chat with large language models while providing relevant context from uploaded documents.

## Features

- Chat with large language models through Ollama
- Upload and process documents (PDF, TXT, CSV, MD)
- Retrieval Augmented Generation for contextual responses
- Document management with tagging and organization
- System monitoring and analytics
- Responsive UI with light/dark mode
- Enhanced logging and debugging capabilities
## Architecture

Metis RAG is built with the following technologies:

- **Backend**: FastAPI, Python
- **Vector Database**: ChromaDB with optimized caching
- **LLM Integration**: Ollama API with enhanced prompt engineering
- **Document Processing**: LangChain with multiple chunking strategies
- **Deployment**: Docker
- **Testing**: Comprehensive test suite for RAG functionality
- **Deployment**: Docker

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Ollama (optional, can run in Docker)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/metis-rag.git
   cd metis-rag
   ```

2. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Build and start the application with Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the application at [http://localhost:8000](http://localhost:8000)

### Running Without Docker

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage

### Chat Interface

The main chat interface allows you to:
- Send messages to the model
- Toggle RAG functionality
- View citations from source documents
- Control conversation history

### Document Management

The document management page allows you to:
- Upload documents
- Process documents for RAG
- View document information
- Delete documents

### System Management

The system page allows you to:
- View system statistics
- Manage models
- Check system health

## Development

### Project Structure

```
metis_rag/
├── app/
│   ├── api/         # API endpoints
│   ├── core/        # Core configuration
│   ├── rag/         # RAG engine
│   ├── models/      # Data models
│   ├── static/      # Static files
│   ├── templates/   # HTML templates
│   └── utils/       # Utility functions
├── tests/           # Tests
├── uploads/         # Uploaded documents
├── chroma_db/       # ChromaDB data
└── docker-compose.yml
```

### Running Tests

Run tests with pytest:

```bash
pytest
```

For testing the RAG retrieval functionality specifically:

```bash
python test_rag_retrieval.py
```

This test script creates test documents, processes them, and tests the RAG retrieval with specific queries to verify that the system correctly retrieves and uses information from the documents.

## License

[MIT License](LICENSE)

## Acknowledgements

This project builds upon:
- Metis_Chat
- rag_ollama_mvp