# Metis RAG

Metis RAG is an application that combines conversational AI with Retrieval Augmented Generation (RAG) capabilities. It allows users to chat with large language models while providing relevant context from uploaded documents.

## Project Documentation

This repository contains the following key documentation:

- **README.md** (this file): Overview, features, and usage instructions
- **[PLANNING.md](PLANNING.md)**: High-level architecture, design decisions, and technical specifications
- **[TASK.md](TASK.md)**: Current tasks, priorities, and development roadmap

## Features

- Chat with large language models through Ollama
- Upload and process documents (PDF, TXT, CSV, MD)
- Retrieval Augmented Generation for contextual responses
- User authentication and access control
- Multi-user support with resource ownership
- LLM-enhanced document processing with intelligent chunking strategies
- Advanced query refinement and retrieval enhancement
- Response quality assurance with evaluation and refinement
- Factual accuracy verification and hallucination detection
- Comprehensive audit reports with source tracking
- Document management with tagging and organization
- System monitoring and analytics
- Background Task System for asynchronous processing
- Persistent chat memory across conversation turns
- Explicit memory buffer for storing and recalling user information
- Context-aware memory management with priority-based retrieval
- Responsive UI with light/dark mode
- Syntax highlighting for code blocks in responses
- Automatic language detection for code snippets
- Copy-to-clipboard functionality for code blocks
- Enhanced logging and debugging capabilities

## Authentication System

Metis RAG includes a comprehensive authentication system that provides user management and access control:

### User Management

- User registration and login
- Role-based access control (user/admin)
- JWT-based authentication
- Secure password hashing with bcrypt

### Access Control

- Resource ownership validation
- Protected API endpoints
- Route protection middleware
- Multi-user support with data isolation

### Security Features

- Token-based authentication
- Password hashing and validation
- CORS protection
- Security headers
- Route-based access control

For more details, see the [Authentication Documentation](docs/technical/AUTHENTICATION.md).

## LLM-Enhanced RAG System

Metis RAG includes an advanced LLM-enhanced system that improves critical aspects of the RAG pipeline:

### Dynamic Chunking Strategy Selection

The system uses a "Chunking Judge" (an LLM agent) to analyze documents and select the most appropriate chunking strategy and parameters:

- Analyzes document structure, content type, and formatting
- Dynamically selects between recursive, token-based, or markdown chunking strategies
- Recommends optimal chunk size and overlap parameters
- Preserves semantic meaning and document structure
- Adapts to different document types without manual configuration

### Query Refinement and Retrieval Enhancement

The system uses a "Retrieval Judge" (an LLM agent) to improve retrieval quality:

- Analyzes queries and retrieved chunks
- Refines queries to improve retrieval precision
- Evaluates relevance of retrieved chunks
- Re-ranks chunks based on relevance to the query
- Requests additional retrieval when necessary

### Response Quality Pipeline

The system includes a comprehensive response quality pipeline to ensure high-quality responses:

- **Response Synthesis**: Combines retrieval results and tool outputs into coherent responses with proper source attribution
- **Response Evaluation**: Assesses factual accuracy, completeness, relevance, and checks for hallucinations
- **Response Refinement**: Iteratively improves responses based on evaluation results
- **Audit Reporting**: Generates comprehensive audit reports with information source tracking and verification status

### Conversation Memory and User-Chat Relationship Management

The system maintains persistent memory across conversation turns and browser sessions with robust user-conversation relationship management:

- **Context Augmentation**: Includes conversation history in the LLM context for more coherent multi-turn dialogues
- **Memory-Aware Query Analysis**: Analyzes queries in the context of previous conversation turns
- **Memory-Enhanced Planning**: Creates query execution plans that consider conversation history
- **Contextual Response Generation**: Generates responses that maintain continuity with previous exchanges
- **Explicit Memory Commands**: Supports natural language commands for storing and retrieving specific information
  - `Remember this: [information]` - Explicitly store information in memory
  - `Recall [topic]` - Explicitly retrieve information from memory
- **Implicit Memory Storage**: Automatically stores all user queries for future reference
- **Implicit Memory Retrieval**: Recognizes and responds to implicit memory queries like "What is my favorite color?"
- **Memory Categories**: Supports common memory categories like favorite colors, foods, names, etc.
- **Persistent Memory Storage**: Stores memories in the database for long-term retention across sessions
- **Memory Diagnostics**: Provides tools for debugging and monitoring memory functionality
- **Session Persistence**: Maintains conversation context across page refreshes and browser sessions
- **User-Conversation Relationship Management**:
  - Robust permission controls ensuring users can only access their own conversations
  - Secure user ID tracking for conversation ownership
  - Smart error handling for unauthorized access attempts
  - Conversation selection interface to browse and manage past conversations
  - Conversation preview functionality showing message snippets in conversation list
  - Conversation metadata tracking with user-specific customization
  - Security logging for unauthorized access attempts
  - Automatic new conversation creation with clear user feedback

### Quality Assurance Features

- Factual accuracy scoring and verification
- Hallucination detection and removal
- Source attribution and citation tracking
- Iterative refinement until quality thresholds are met
- Comprehensive audit trails for transparency and accountability
- LLM-based process analysis for continuous improvement

These enhancements make the RAG system more adaptable to different document types and query styles, while ensuring responses are accurate, complete, relevant, and free from hallucinations.
## Architecture

Metis RAG is built with the following technologies:

- **Backend**: FastAPI, Python
- **Authentication**: JWT-based authentication with bcrypt password hashing
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Database**: ChromaDB with optimized caching
- **LLM Integration**: Ollama API with enhanced prompt engineering
- **Document Processing**: LangChain with LLM-enhanced dynamic chunking strategies
- **Response Quality**: Comprehensive pipeline for synthesis, evaluation, refinement, and auditing
- **Workflow Orchestration**: LangGraph for adaptive RAG workflows
- **Process Logging**: Detailed logging and audit trail generation
- **Background Task System**: Asynchronous processing with task prioritization and resource management
- **Testing**: Comprehensive test suite for RAG functionality and response quality
- **Deployment**: Docker
- **Text Formatting**: Modular system for formatting code, lists, tables, and markdown

## Text Formatting System

Metis RAG includes a sophisticated text formatting system that enhances the readability and presentation of LLM responses:

### Features

- **Code Block Formatting**: Proper syntax highlighting, language detection, and indentation
- **List Formatting**: Consistent formatting for ordered and unordered lists
- **Table Formatting**: Proper alignment and formatting of markdown tables
- **Markdown Formatting**: Enhanced formatting for headings, emphasis, links, and other markdown elements
- **Performance Monitoring**: Tracking and analytics for formatting operations

### Architecture

The text formatting system follows a modular approach with clear separation of concerns:

- **Formatters**: Specialized components for different types of formatting (code, lists, tables, markdown)
- **Rules**: Patterns and replacements for identifying and formatting specific elements
- **Monitor**: Performance tracking and analytics for formatting operations

For more details, see the [Text Formatting Architecture](docs/technical/text_formatting_architecture.md) documentation.

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

   Key configuration options include:
   - `DEFAULT_MODEL`: The LLM model to use for RAG responses (default: gemma3:12b)
   - `CHUNKING_JUDGE_MODEL`: The model to use for document analysis (default: gemma3:12b)
   - `USE_CHUNKING_JUDGE`: Enable/disable the Chunking Judge (default: True)
   - `USE_RETRIEVAL_JUDGE`: Enable/disable the Retrieval Judge (default: True)
   - `ENABLE_RESPONSE_QUALITY`: Enable/disable the Response Quality Pipeline (default: True)
   - `QUALITY_THRESHOLD`: Minimum quality score for responses (default: 8.0)
   - `MAX_REFINEMENT_ITERATIONS`: Maximum number of refinement iterations (default: 2)
   - `ENABLE_AUDIT_REPORTS`: Enable/disable audit report generation (default: True)
   - `SECRET_KEY`: Secret key for JWT token generation (required for authentication)
   - `ALGORITHM`: Algorithm for JWT token generation (default: HS256)
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes (default: 30)

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
- Send messages to the model with real-time streaming responses
- Toggle RAG functionality and other advanced options
- View citations from source documents with relevance scores
- Access and navigate through your conversation history
- Browse past conversations with preview snippets
- Continue conversations across browser sessions and page refreshes
- Use memory commands to store and retrieve information
- See quality scores for responses with confidence metrics
- View code with syntax highlighting and proper formatting
- Copy code blocks with a single click for easy use
- Automatically detect programming languages in code blocks
- View source attributions and citations from reference documents
- Switch between light and dark modes for comfortable viewing

### Document Management

The document management page allows you to:
- Upload documents
- Process documents for RAG
- View document information
- Delete documents

### Authentication and User Management

The authentication system provides:
- User registration and login pages with secure credential handling
- Secure access to personal resources with permission enforcement
- User-specific conversation history and document management
- Role-based access control for different permission levels
- JWT token-based authentication for secure API access
- Token refresh functionality for persistent sessions
- Protection of sensitive operations with appropriate authorization
- Secure error handling that prevents information leakage
- Security event logging for unauthorized access attempts
- Sanitization of URL parameters to prevent credential exposure

### System Management

The system page allows you to:
- View system statistics
- Manage models
- Check system health

### Audit Reports

The audit reports page allows you to:
- View comprehensive audit reports for queries
- Examine information sources used in responses
- Verify factual accuracy and completeness
- Track reasoning traces and execution timelines
- Identify potential hallucinations
- Export audit reports for compliance and transparency

### Background Task System

The Background Task System allows you to:
- Monitor and manage asynchronous tasks
- View task status, progress, and results
- Prioritize tasks based on importance
- Schedule tasks for future execution
- Define task dependencies for complex workflows
- Monitor system resource usage
- View resource alerts and system health

## Development

### Project Structure

```
metis_rag/
├── app/
│   ├── api/         # API endpoints
│   │   ├── auth.py  # Authentication endpoints
│   │   └── ...      # Other API endpoints
│   ├── core/        # Core configuration
│   │   ├── security.py # Authentication and security
│   │   └── ...      # Other core modules
│   ├── middleware/  # Middleware components
│   │   └── auth.py  # Authentication middleware
│   ├── db/          # Database components
│   │   ├── repositories/ # Repository pattern implementations
│   │   │   ├── user_repository.py # User data access
│   │   │   └── ...    # Other repositories
│   │   └── ...      # Other database modules
│   ├── rag/         # RAG engine
│   │   ├── agents/  # LLM-based agents for RAG enhancement
│   │   ├── response_synthesizer.py  # Response synthesis
│   │   ├── response_evaluator.py    # Response evaluation
│   │   ├── response_refiner.py      # Response refinement
│   │   ├── audit_report_generator.py # Audit reporting
│   │   ├── response_quality_pipeline.py # Quality pipeline
│   │   └── langgraph_states.py      # LangGraph state models
│   ├── tasks/       # Background Task System
│   │   ├── task_manager.py          # Task management
│   │   ├── task_models.py           # Task data models
│   │   ├── scheduler.py             # Task scheduling
│   │   ├── resource_monitor.py      # Resource monitoring
│   │   ├── task_repository.py       # Task database operations
│   │   └── example_tasks.py         # Example task handlers
│   ├── models/      # Data models
│   │   ├── user.py  # User models
│   │   └── ...      # Other models
│   ├── static/      # Static files
│   │   ├── js/      # JavaScript files
│   │   │   ├── main.js # Authentication JS
│   │   │   └── ...  # Other JS files
│   │   └── ...      # Other static files
│   ├── templates/   # HTML templates
│   │   ├── login.html    # Login page
│   │   ├── register.html # Registration page
│   │   └── ...      # Other templates
│   └── utils/       # Utility functions
├── tests/           # Tests
│   ├── unit/        # Unit tests
│   │   └── test_response_quality.py # Response quality tests
│   └── integration/ # Integration tests
│       └── test_response_quality_integration.py # Integration tests
├── uploads/         # Uploaded documents
├── chroma_db/       # ChromaDB data
└── docker-compose.yml
```

### Running Tests

Run tests with pytest:

```bash
pytest
```

For testing specific components:

```bash
# Test RAG retrieval functionality
python test_rag_retrieval.py

# Test response quality components
pytest tests/unit/test_response_quality.py

# Test response quality integration
pytest tests/integration/test_response_quality_integration.py

# Test background task system
python scripts/test_background_tasks.py

# Test authentication system
python scripts/test_authentication.py

# Test memory functionality
python scripts/test_memory_functionality.py
```

The memory functionality test script verifies:
- Creating users and conversations
- Storing explicit memories using the "Remember this" command
- Storing implicit memories from all user queries
- Processing queries with explicit recall commands
- Processing queries with implicit memory-related questions
- Retrieving memories with search terms
- Retrieving memories with specific labels

These test scripts create test documents, process them, and test various aspects of the system:
- RAG retrieval tests verify that the system correctly retrieves and uses information from documents
- Response quality tests verify that responses are accurate, complete, relevant, and free from hallucinations
- Integration tests verify that all components work together correctly in end-to-end workflows
- Background task tests verify that the task system correctly handles task submission, execution, prioritization, and resource management
- Authentication tests verify user registration, login, token generation, and access control for resources
- User-conversation relationship tests verify permission enforcement and conversation management
- Memory persistence tests verify conversation memory works across sessions and page refreshes
- Security tests verify proper handling of unauthorized access attempts and input sanitization

## License

[MIT License](LICENSE)

## Acknowledgements

This project builds upon:
- Metis_Chat
- rag_ollama_mvp