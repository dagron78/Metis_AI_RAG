# Metis_RAG System Visualization

## System Architecture

```mermaid
graph TD
    subgraph "Frontend"
        UI[Web UI]
        API_Client[API Client]
    end

    subgraph "API Layer"
        API[FastAPI Endpoints]
        Auth[Authentication]
        API --> Auth
    end

    subgraph "Core RAG Engine"
        QueryAnalyzer[Query Analyzer]
        QueryPlanner[Query Planner]
        PlanExecutor[Plan Executor]
        ResponseSynthesizer[Response Synthesizer]
        ResponseEvaluator[Response Evaluator]
        ProcessLogger[Process Logger]
        
        QueryAnalyzer --> QueryPlanner
        QueryPlanner --> PlanExecutor
        PlanExecutor --> ResponseSynthesizer
        ResponseSynthesizer --> ResponseEvaluator
        ProcessLogger -.-> QueryAnalyzer
        ProcessLogger -.-> QueryPlanner
        ProcessLogger -.-> PlanExecutor
        ProcessLogger -.-> ResponseSynthesizer
        ProcessLogger -.-> ResponseEvaluator
    end

    subgraph "Tool System"
        ToolRegistry[Tool Registry]
        RAGTool[RAG Tool]
        CalculatorTool[Calculator Tool]
        DatabaseTool[Database Tool]
        
        ToolRegistry --> RAGTool
        ToolRegistry --> CalculatorTool
        ToolRegistry --> DatabaseTool
        PlanExecutor --> ToolRegistry
    end

    subgraph "Document Processing"
        DocumentAnalysisService[Document Analysis Service]
        WorkerPool[Worker Pool]
        ProcessingJob[Processing Job]
        
        DocumentAnalysisService --> WorkerPool
        WorkerPool --> ProcessingJob
    end

    subgraph "Database Layer"
        DB[(PostgreSQL)]
        DocumentRepository[Document Repository]
        ConversationRepository[Conversation Repository]
        AnalyticsRepository[Analytics Repository]
        
        DocumentRepository --> DB
        ConversationRepository --> DB
        AnalyticsRepository --> DB
    end

    subgraph "Vector Store"
        ChromaDB[(ChromaDB)]
        RAGTool --> ChromaDB
    end

    UI --> API_Client
    API_Client --> API
    API --> QueryAnalyzer
    API --> DocumentAnalysisService
    API --> DocumentRepository
    API --> ConversationRepository
    API --> AnalyticsRepository
    RAGTool --> DocumentRepository
    ProcessingJob --> DocumentRepository
```

## Database Schema

```mermaid
erDiagram
    Documents ||--o{ Chunks : contains
    Documents ||--o{ DocumentTags : has
    Tags ||--o{ DocumentTags : used_in
    Documents }|--|| Folders : stored_in
    Conversations ||--o{ Messages : contains
    Messages ||--o{ Citations : references
    Citations }o--|| Documents : cites
    Citations }o--|| Chunks : cites_specific
    ProcessingJobs ||--o{ Documents : processes
    AnalyticsQueries }o--|| Documents : uses
    
    Documents {
        uuid id PK
        string filename
        string content
        jsonb metadata
        string folder
        timestamp uploaded
        string processing_status
        string processing_strategy
        int file_size
        string file_type
        timestamp last_accessed
    }
    
    Chunks {
        uuid id PK
        uuid document_id FK
        string content
        jsonb metadata
        int index
        float embedding_quality
        timestamp created_at
    }
    
    Tags {
        serial id PK
        string name UK
        timestamp created_at
        int usage_count
    }
    
    DocumentTags {
        uuid document_id FK
        int tag_id FK
        timestamp added_at
    }
    
    Folders {
        string path PK
        string name
        string parent_path
        int document_count
        timestamp created_at
    }
    
    Conversations {
        uuid id PK
        timestamp created_at
        timestamp updated_at
        jsonb metadata
        int message_count
    }
    
    Messages {
        serial id PK
        uuid conversation_id FK
        string content
        string role
        timestamp timestamp
        int token_count
    }
    
    Citations {
        serial id PK
        int message_id FK
        uuid document_id FK
        uuid chunk_id FK
        float relevance_score
        string excerpt
        int character_range_start
        int character_range_end
    }
    
    ProcessingJobs {
        uuid id PK
        string status
        timestamp created_at
        timestamp completed_at
        int document_count
        int processed_count
        string strategy
        jsonb metadata
        float progress_percentage
        string error_message
    }
    
    AnalyticsQueries {
        serial id PK
        string query
        string model
        boolean use_rag
        timestamp timestamp
        float response_time_ms
        int token_count
        jsonb document_ids
        string query_type
        boolean successful
    }
```

## Query Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant API as API Layer
    participant QA as Query Analyzer
    participant QP as Query Planner
    participant PE as Plan Executor
    participant TR as Tool Registry
    participant RT as RAG Tool
    participant VS as Vector Store
    participant RS as Response Synthesizer
    participant RE as Response Evaluator
    participant PL as Process Logger

    User->>API: Submit Query
    API->>QA: Analyze Query
    QA->>PL: Log Analysis
    QA->>QP: Create Plan
    QP->>PL: Log Plan
    QP->>PE: Execute Plan
    
    loop For Each Step
        PE->>TR: Get Tool
        TR->>RT: Execute RAG Tool
        RT->>VS: Retrieve Chunks
        VS-->>RT: Return Chunks
        RT-->>PE: Return Results
        PE->>PL: Log Step Results
    end
    
    PE->>RS: Synthesize Response
    RS->>PL: Log Synthesis
    RS->>RE: Evaluate Response
    RE->>PL: Log Evaluation
    
    alt Response Needs Refinement
        RE->>RS: Refine Response
        RS->>PL: Log Refinement
    end
    
    RE-->>API: Return Final Response
    API-->>User: Display Response
```

## Document Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant API as API Layer
    participant DAS as Document Analysis Service
    participant WP as Worker Pool
    participant PJ as Processing Job
    participant DR as Document Repository
    participant VS as Vector Store

    User->>API: Upload Document
    API->>DR: Store Document
    API->>DAS: Analyze Document
    DAS->>WP: Create Processing Job
    WP->>PJ: Execute Job
    
    PJ->>DR: Retrieve Document
    DR-->>PJ: Return Document
    PJ->>PJ: Chunk Document
    PJ->>VS: Store Chunks & Embeddings
    PJ->>DR: Update Document Status
    
    DR-->>API: Return Success
    API-->>User: Confirm Processing
```

## Tool System

```mermaid
classDiagram
    class Tool {
        <<abstract>>
        +String name
        +String description
        +execute(input_data) Any
        +get_description() String
        +get_input_schema() Dict
        +get_output_schema() Dict
        +get_examples() List
    }
    
    class ToolRegistry {
        -Dict tools
        +register_tool(tool) void
        +get_tool(name) Tool
        +list_tools() List
        +get_tool_examples(name) List
        +get_tool_count() int
    }
    
    class RAGTool {
        -RAGEngine rag_engine
        +execute(input_data) Dict
        +get_input_schema() Dict
        +get_output_schema() Dict
        +get_examples() List
    }
    
    class DatabaseTool {
        -DatabaseConnection db_connection
        +execute(input_data) Dict
        +get_input_schema() Dict
        +get_output_schema() Dict
        +get_examples() List
    }
    
    class CalculatorTool {
        +execute(input_data) Dict
        +get_input_schema() Dict
        +get_output_schema() Dict
        +get_examples() List
    }
    
    Tool <|-- RAGTool
    Tool <|-- DatabaseTool
    Tool <|-- CalculatorTool
    ToolRegistry o-- Tool
```

## LangGraph Integration

```mermaid
graph TD
    subgraph "LangGraph State Machine"
        QA[Query Analysis]
        QP[Query Planning]
        PE[Plan Execution]
        RT[Retrieval]
        QR[Query Refinement]
        CO[Context Optimization]
        GN[Generation]
        RE[Response Evaluation]
        RR[Response Refinement]
        CP[Complete]
        
        QA -->|Simple Query| RT
        QA -->|Complex Query| QP
        QP --> PE
        PE --> RT
        RT -->|Needs Refinement| QR
        RT -->|Good Results| CO
        QR --> RT
        CO --> GN
        GN --> RE
        RE -->|Needs Refinement| RR
        RE -->|Good Response| CP
        RR --> RE
    end
```

## Key Components

### Core RAG Engine
- **Query Analyzer**: Determines query complexity and required tools
- **Query Planner**: Creates execution plans for complex queries
- **Plan Executor**: Executes query plans using appropriate tools
- **Response Synthesizer**: Generates coherent responses from execution results
- **Response Evaluator**: Assesses response quality and determines if refinement is needed
- **Process Logger**: Records the entire query processing workflow for auditing

### Tool System
- **Tool Registry**: Manages available tools
- **RAG Tool**: Retrieves information from documents using vector search
- **Calculator Tool**: Performs mathematical calculations
- **Database Tool**: Queries structured data

### Document Processing
- **Document Analysis Service**: Analyzes documents to determine optimal processing strategies
- **Worker Pool**: Manages parallel document processing
- **Processing Job**: Represents a document processing task

### Database Layer
- **Document Repository**: Manages document storage and retrieval
- **Conversation Repository**: Stores conversation history
- **Analytics Repository**: Records query analytics

### Vector Store
- **ChromaDB**: Stores document chunks and embeddings for semantic search