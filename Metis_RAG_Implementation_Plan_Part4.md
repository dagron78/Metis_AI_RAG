## Phase 6: Performance Optimization (Weeks 11-12)

### Week 11: Caching Implementation

#### Cache Interface
```python
class Cache(Generic[T]):
    """
    Generic cache implementation with disk persistence
    """
    def __init__(
        self,
        name: str,
        ttl: int = 3600,
        max_size: int = 1000,
        persist: bool = True,
        persist_dir: str = "data/cache"
    ):
        self.name = name
        self.ttl = ttl
        self.max_size = max_size
        self.persist = persist
        self.persist_dir = persist_dir
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0
        self.logger = logging.getLogger(f"app.cache.{name}")
        
        # Create persist directory if needed
        if self.persist:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._load_from_disk()
            self.logger.info(f"Loaded {len(self.cache)} items from disk cache")
    
    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                self.hits += 1
                self.logger.debug(f"Cache hit for key: {key}")
                return entry["value"]
            else:
                # Expired, remove from cache
                del self.cache[key]
                self.logger.debug(f"Cache entry expired for key: {key}")
        
        self.misses += 1
        self.logger.debug(f"Cache miss for key: {key}")
        return None
    
    def set(self, key: str, value: T) -> None:
        """Set a value in the cache"""
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        self.logger.debug(f"Cache set for key: {key}")
        
        # Prune cache if it gets too large
        if len(self.cache) > self.max_size:
            self._prune()
            
        # Persist to disk if enabled
        if self.persist:
            self._save_to_disk()
```

#### Cache Implementations
1. Implement VectorSearchCache for caching vector search results
2. Implement DocumentCache for caching document content and metadata
3. Implement LLMResponseCache for caching LLM responses
4. Add cache monitoring and statistics collection

### Week 12: Background Task System

#### Task Manager
```python
class TaskManager:
    """
    Manager for asynchronous tasks
    """
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.tasks: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger("app.services.task_manager")
        
    async def submit(
        self,
        task_id: str,
        func: Callable[..., Awaitable[Any]],
        priority: int = 0,
        *args,
        **kwargs
    ) -> str:
        """
        Submit a task for execution
        
        Args:
            task_id: Unique identifier for the task
            func: Async function to execute
            priority: Task priority (higher values = higher priority)
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Task ID
        """
        if task_id in self.tasks and not self.tasks[task_id].done():
            error_msg = f"Task {task_id} is already running"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Create and start the task
        self.logger.info(f"Submitting task {task_id} with priority {priority}")
        task = asyncio.create_task(self._run_task(task_id, func, priority, *args, **kwargs))
        self.tasks[task_id] = task
        
        return task_id
        
    async def _run_task(
        self,
        task_id: str,
        func: Callable[..., Awaitable[Any]],
        priority: int,
        *args,
        **kwargs
    ) -> Any:
        """
        Run a task with semaphore control
        """
        async with self.semaphore:
            start_time = time.time()
            self.logger.info(f"Starting task {task_id}")
            try:
                result = await func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                self.logger.info(f"Task {task_id} completed successfully in {elapsed_time:.2f}s")
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                self.logger.error(f"Task {task_id} failed after {elapsed_time:.2f}s: {str(e)}")
                raise
            finally:
                # Clean up completed task
                if task_id in self.tasks and self.tasks[task_id].done():
                    del self.tasks[task_id]
```

#### Performance Monitoring
1. Implement comprehensive performance monitoring
2. Add metrics collection for response times and throughput
3. Create performance dashboards
4. Implement adaptive resource management

## Testing Infrastructure

### Unit Tests
```python
class TestDocumentRepository(unittest.TestCase):
    """Test the DocumentRepository class"""
    
    def setUp(self):
        """Set up test database"""
        self.engine = create_engine("postgresql://postgres:postgres@localhost:5432/metis_test")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
    def tearDown(self):
        """Clean up test database"""
        self.session.close()
        
    def test_create_document(self):
        """Test creating a document"""
        repo = DocumentRepository(self.session)
        document = repo.create_document(
            filename="test.txt",
            tags=["test", "document"],
            folder="/test"
        )
        
        self.assertIsNotNone(document.id)
        self.assertEqual(document.filename, "test.txt")
        self.assertEqual(document.folder, "/test")
        self.assertEqual(len(document.tags), 2)
```

### Integration Tests
```python
class TestDocumentAPI(TestCase):
    """Test the document API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = TestClient(app)
        
    def test_upload_document(self):
        """Test uploading a document"""
        # Create test file
        with open("test_file.txt", "w") as f:
            f.write("Test content")
        
        # Upload document
        with open("test_file.txt", "rb") as f:
            response = self.app.post(
                "/api/documents/upload",
                files={"file": ("test_file.txt", f, "text/plain")},
                data={"tags": "test,document", "folder": "/test"}
            )
        
        # Clean up
        os.remove("test_file.txt")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("document_id", response.json())
```

### Performance Tests
```python
class TestRAGPerformance(TestCase):
    """Test RAG performance"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = TestClient(app)
        
        # Create test documents
        self._create_test_documents(100)  # Create 100 test documents
        
    def tearDown(self):
        """Clean up test environment"""
        self._cleanup_test_documents()
        
    def test_simple_query_performance(self):
        """Test performance of simple queries"""
        # Send query
        start_time = time.time()
        response = self.app.post(
            "/api/chat/query",
            json={
                "message": "What is artificial intelligence?",
                "use_rag": True
            }
        )
        elapsed_time = time.time() - start_time
        
        # Check response time
        self.assertLess(elapsed_time, 6.0)  # Should be under 6 seconds
        self.assertEqual(response.status_code, 200)
```

## Dependencies

1. **Database**:
   - SQLAlchemy (ORM for database access)
   - Alembic (database migrations)
   - psycopg2-binary (PostgreSQL driver)

2. **LLM Integration**:
   - httpx (async HTTP client for API calls)
   - tiktoken (token counting for LLMs)
   - langgraph (for state machine implementation)

3. **Document Processing**:
   - PyPDF2 (PDF processing)
   - python-docx (DOCX processing)
   - unstructured (general document processing)
   - langchain (document chunking strategies)

4. **Vector Storage**:
   - chromadb (vector database)
   - sentence-transformers (embedding models)

5. **Web Framework**:
   - FastAPI (API framework)
   - Pydantic (data validation)
   - Jinja2 (templating)
   - uvicorn (ASGI server)

6. **Testing**:
   - pytest (testing framework)
   - pytest-asyncio (async testing)
   - pytest-cov (coverage reporting)
   - pytest-benchmark (performance testing)

7. **Monitoring and Logging**:
   - prometheus-client (metrics)
   - structlog (structured logging)

8. **Memory Management**:
   - mem0 (memory layer for AI applications)

9. **Utilities**:
   - python-multipart (file uploads)
   - python-dotenv (environment variables)
   - cachetools (in-memory caching)

## Deployment

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.10-slim as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/uploads data/chroma_db data/cache

# Expose port
EXPOSE 8000

# Set health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Set entrypoint
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  metis-rag:
    build:
      context: .
      target: ${METIS_BUILD_TARGET:-production}
    image: metis-rag:${METIS_VERSION:-latest}
    container_name: metis-rag
    restart: unless-stopped
    ports:
      - "${METIS_PORT:-8000}:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - METIS_CONFIG_FILE=/app/config/settings.json
      - METIS_DB_TYPE=postgresql
      - METIS_POSTGRES_DSN=postgresql://postgres:postgres@postgres:5432/metis
      - METIS_LLM_PROVIDER_TYPE=ollama
    networks:
      - metis-network
    depends_on:
      - postgres
      - ollama

  postgres:
    image: postgres:15-alpine
    container_name: metis-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=metis
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - metis-network

  ollama:
    image: ollama/ollama:latest
    container_name: metis-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ./data/ollama:/root/.ollama
    networks:
      - metis-network

networks:
  metis-network:
    driver: bridge

volumes:
  postgres-data:
```

## Revised Timeline (More Granular)

### Phase 1: Database Integration (Weeks 1-2)

#### Week 1:
- Choose database backend (PostgreSQL for both development and production)
- Create database schema with all required tables
- Implement DocumentRepository and migrate document storage
- Update document API endpoints to use the database

#### Week 2:
- Implement AnalyticsRepository and migrate analytics storage
- Update analytics API endpoints to use the database
- Implement ConversationRepository and migrate conversation storage
- Update chat API endpoints to use the database

### Phase 2: Intelligent Document Processing (Weeks 3-4)

#### Week 3:
- Implement DocumentAnalysisService with LLM prompt and response parsing
- Create detailed prompts for document analysis
- Integrate with DocumentProcessor
- Add unit and integration tests

#### Week 4:
- Implement ProcessingJob model and DocumentProcessingService
- Create WorkerPool for parallel processing
- Add API endpoints for job management
- Implement progress tracking and cancellation

### Phase 3: Agentic Capabilities Foundation (Weeks 5-6)

#### Week 5:
- Define Tool interface and implement ToolRegistry
- Implement RAGTool, CalculatorTool, and DatabaseTool
- Add unit tests for tools
- Create tool documentation

#### Week 6:
- Implement QueryAnalyzer with LLM-based query analysis
- Create ProcessLogger for comprehensive logging
- Add audit trail capabilities
- Implement API endpoints for query analysis

### Phase 4: Planning and Execution (Weeks 7-8)

#### Week 7:
- Implement QueryPlanner with LLM-based plan generation
- Create PlanExecutor for executing multi-step plans
- Add unit tests for planning and execution
- Create API endpoints for plan management

#### Week 8:
- Define LangGraph state models
  - Implemented QueryAnalysisState, PlanningState, ExecutionState, RetrievalState, GenerationState, and RAGState
  - Created state transitions and conditional edges for adaptive workflows
  - Added state validation and serialization
- Implement LangGraph integration with state machine
  - Created EnhancedLangGraphRAGAgent with state graph construction
  - Integrated QueryPlanner and PlanExecutor for complex queries
  - Added streaming support and execution trace tracking
  - Implemented error handling and recovery mechanisms
- Create conditional edges for adaptive workflows
  - Added complexity-based routing for simple vs. complex queries
  - Implemented tool selection based on query requirements
  - Created feedback loops for query refinement
  - Added context optimization for better responses
- Add API endpoints for LangGraph RAG
  - Created /enhanced_langgraph_query endpoint with streaming support
  - Added configuration flags for enabling/disabling LangGraph features
  - Implemented comprehensive error handling
  - Added detailed API documentation
- Comprehensive testing
  - Created integration tests for all LangGraph components
  - Implemented mock components for testing
  - Added tests for initialization, simple queries, complex queries, streaming, and error handling
  - Ensured all tests pass successfully

### Phase 5: Response Quality (Weeks 9-10)

#### Week 9:
- Implement ResponseSynthesizer for combining results
- Create ResponseEvaluator for quality assessment
- Add unit tests for response quality
- Implement metrics for response quality

#### Week 10:
- Implement ResponseRefiner for improving responses
- Create AuditReportGenerator for verification
- Add API endpoints for audit reports
- Implement visualization for audit trails

### Phase 6: Performance Optimization (Weeks 11-12)

#### Week 11:
- Implement Cache interface and cache implementations
- Add disk-based persistence for caches
- Create cache invalidation strategies
- Add cache statistics and monitoring

#### Week 12:
- Implement TaskManager for background processing
- Add resource monitoring and adaptive scheduling
- Create task prioritization and dependencies
- Implement comprehensive performance testing