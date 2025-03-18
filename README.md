# Metis RAG

Metis RAG is an application that combines conversational AI with Retrieval Augmented Generation (RAG) capabilities. It allows users to chat with large language models while providing relevant context from uploaded documents.

## Features

- Chat with large language models through Ollama
- Upload and process documents (PDF, TXT, CSV, MD)
- Retrieval Augmented Generation for contextual responses
- LLM-enhanced document processing with intelligent chunking strategies
- Advanced query refinement and retrieval enhancement
- Response quality assurance with evaluation and refinement
- Factual accuracy verification and hallucination detection
- Comprehensive audit reports with source tracking
- Document management with tagging and organization
- System monitoring and analytics
- Background Task System for asynchronous processing
- Responsive UI with light/dark mode
- Enhanced logging and debugging capabilities

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
- **Vector Database**: ChromaDB with optimized caching
- **LLM Integration**: Ollama API with enhanced prompt engineering
- **Document Processing**: LangChain with LLM-enhanced dynamic chunking strategies
- **Response Quality**: Comprehensive pipeline for synthesis, evaluation, refinement, and auditing
- **Workflow Orchestration**: LangGraph for adaptive RAG workflows
- **Process Logging**: Detailed logging and audit trail generation
- **Background Task System**: Asynchronous processing with task prioritization and resource management
- **Testing**: Comprehensive test suite for RAG functionality and response quality
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

   Key configuration options include:
   - `DEFAULT_MODEL`: The LLM model to use for RAG responses (default: gemma3:12b)
   - `CHUNKING_JUDGE_MODEL`: The model to use for document analysis (default: gemma3:12b)
   - `USE_CHUNKING_JUDGE`: Enable/disable the Chunking Judge (default: True)
   - `USE_RETRIEVAL_JUDGE`: Enable/disable the Retrieval Judge (default: True)
   - `ENABLE_RESPONSE_QUALITY`: Enable/disable the Response Quality Pipeline (default: True)
   - `QUALITY_THRESHOLD`: Minimum quality score for responses (default: 8.0)
   - `MAX_REFINEMENT_ITERATIONS`: Maximum number of refinement iterations (default: 2)
   - `ENABLE_AUDIT_REPORTS`: Enable/disable audit report generation (default: True)

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
- See quality scores for responses
- View source attributions and citations

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
│   ├── core/        # Core configuration
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
│   ├── static/      # Static files
│   ├── templates/   # HTML templates
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
```

These test scripts create test documents, process them, and test various aspects of the system:
- RAG retrieval tests verify that the system correctly retrieves and uses information from documents
- Response quality tests verify that responses are accurate, complete, relevant, and free from hallucinations
- Integration tests verify that all components work together correctly in end-to-end workflows
- Background task tests verify that the task system correctly handles task submission, execution, prioritization, and resource management

## License

[MIT License](LICENSE)

## Acknowledgements

This project builds upon:
- Metis_Chat
- rag_ollama_mvp