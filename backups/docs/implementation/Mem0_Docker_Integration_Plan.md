# Comprehensive Plan for Enhancing Mem0 Docker Integration in Metis_RAG

This document outlines a detailed plan for enhancing the Mem0 Docker integration in Metis_RAG, addressing key areas of database separation, performance optimization, API key management, and Docker configuration.

## Table of Contents

1. [Docker Configuration Enhancement](#1-docker-configuration-enhancement)
   1. [Updated Docker Compose Configuration](#11-updated-docker-compose-configuration)
   2. [Create a .dockerignore File](#12-create-a-dockerignore-file)
2. [Performance Optimization](#2-performance-optimization)
   1. [Enhanced Mem0 Client with Caching](#21-enhanced-mem0-client-with-caching)
   2. [Database Connection Pooling](#22-database-connection-pooling)
3. [Environment Configuration](#3-environment-configuration)
   1. [Update .env.example](#31-update-envexample)
   2. [Update .env.docker](#32-update-envdocker)
4. [Documentation Enhancement](#4-documentation-enhancement)
   1. [Update README_MEM0_INTEGRATION.md](#41-update-readme_mem0_integrationmd)
5. [Testing Plan](#5-testing-plan)
   1. [Unit Tests](#51-unit-tests)
6. [Prioritized Implementation Steps](#6-prioritized-implementation-steps)
7. [Monitoring and Maintenance](#7-monitoring-and-maintenance)

## 1. Docker Configuration Enhancement

### 1.1 Updated Docker Compose Configuration

Create an enhanced `docker-compose.yml` with detailed comments:

```yaml
version: '3.8'

services:
  # Main Metis RAG application service
  metis-rag:
    build:
      context: ..
      dockerfile: config/Dockerfile
      target: ${METIS_BUILD_TARGET:-base}  # Allows switching between development and production builds
    image: metis-rag:${METIS_VERSION:-latest}
    container_name: metis-rag
    restart: unless-stopped
    ports:
      - "${METIS_PORT:-8000}:8000"  # Expose the API port, configurable via environment
    volumes:
      - ../data:/app/data  # Mount data directory for persistent storage
      - ../config:/app/config  # Mount config directory for easy configuration
    environment:
      # Core application settings
      - METIS_CONFIG_FILE=/app/config/settings.json
      # Database connection settings
      - METIS_DB_TYPE=postgresql
      - METIS_POSTGRES_DSN=postgresql://postgres:postgres@metis-postgres:5432/metis
      # LLM provider settings
      - METIS_LLM_PROVIDER_TYPE=ollama
      - METIS_OLLAMA_BASE_URL=http://ollama:11434
      # Mem0 settings
      - MEM0_ENDPOINT=http://mem0:8050
      - MEM0_API_KEY=${MEM0_ADMIN_API_KEY:-default_dev_key}  # Use env var or default
      - USE_MEM0=True
    networks:
      - metis-network  # Use custom network for service discovery
    depends_on:
      metis-postgres:
        condition: service_healthy  # Wait for PostgreSQL to be ready
      ollama:
        condition: service_healthy  # Wait for Ollama to be ready
      mem0:
        condition: service_healthy  # Wait for Mem0 to be ready
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '2'  # Limit CPU usage
          memory: 2G  # Limit memory usage

  # PostgreSQL database for Metis RAG
  metis-postgres:
    image: postgres:15-alpine  # Use Alpine for smaller image size
    container_name: metis-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=metis
    volumes:
      - metis-postgres-data:/var/lib/postgresql/data  # Persistent volume for database
    ports:
      - "5432:5432"  # Expose PostgreSQL port
    networks:
      - metis-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]  # Check if PostgreSQL is ready
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '1'  # Limit CPU usage
          memory: 1G  # Limit memory usage

  # Ollama LLM service
  ollama:
    image: ollama/ollama:latest
    container_name: metis-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"  # Expose Ollama API port
    volumes:
      - ../data/ollama:/root/.ollama  # Persistent volume for models
    networks:
      - metis-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s  # Longer start period as models may take time to load
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]  # Use GPU for inference

  # PostgreSQL database for Mem0 (separate from Metis RAG database)
  mem0-postgres:
    image: postgres:15-alpine
    container_name: mem0-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=mem0
    volumes:
      - mem0-postgres-data:/var/lib/postgresql/data  # Persistent volume for database
    ports:
      - "5433:5432"  # Use different port to avoid conflict with metis-postgres
    networks:
      - metis-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '1'  # Limit CPU usage
          memory: 1G  # Limit memory usage

  # Mem0 memory service
  mem0:
    image: mem0ai/mem0:latest
    container_name: metis-mem0
    restart: unless-stopped
    ports:
      - "8050:8050"  # Expose Mem0 API port
    environment:
      - DATABASE_URL=postgres://postgres:postgres@mem0-postgres:5432/mem0  # Connect to mem0-postgres
      - MEM0_ADMIN_API_KEY=${MEM0_ADMIN_API_KEY:-default_dev_key}  # Use env var or default
    volumes:
      - ../data/mem0:/app/data  # Persistent volume for Mem0 data
    networks:
      - metis-network
    depends_on:
      mem0-postgres:
        condition: service_healthy  # Wait for PostgreSQL to be ready
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8050/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '1'  # Limit CPU usage
          memory: 1G  # Limit memory usage

# Define custom network for service discovery
networks:
  metis-network:
    driver: bridge

# Define named volumes for persistent data
volumes:
  metis-postgres-data:  # Persistent volume for Metis RAG database
  mem0-postgres-data:   # Persistent volume for Mem0 database
```

### 1.2 Create a .dockerignore File

Create a `.dockerignore` file to exclude unnecessary files from the Docker build context:

```
# Version control
.git
.gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
venv/
venv_py310/

# Data directories
data/
uploads/
chroma_db/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# Logs
logs/
*.log

# Test files
.coverage
htmlcov/
.pytest_cache/
```

## 2. Performance Optimization

### 2.1 Enhanced Mem0 Client with Caching

Update the `app/rag/mem0_client.py` file to include caching and a clear_cache method:

```python
"""
Mem0 client for Metis_RAG with enhanced caching
"""
import os
import logging
from typing import Optional, Dict, Any, List, Union
from cachetools import TTLCache

from app.core.config import SETTINGS

logger = logging.getLogger("app.rag.mem0_client")

# Default agent ID for Metis RAG
METIS_AGENT_ID = "metis_rag_agent"

# Default persona for Metis RAG agent
METIS_PERSONA = """
You are Metis RAG, a helpful assistant that answers questions based on provided documents.
You provide accurate, concise, and helpful responses based on the information in your knowledge base.
When you don't know the answer, you clearly state that you don't have enough information.
"""

# Check if Mem0 is enabled and the package is available
MEM0_AVAILABLE = False
if SETTINGS.use_mem0:
    try:
        from mem0ai import Mem0Client
        MEM0_AVAILABLE = True
    except ImportError:
        logger.warning("mem0ai package not found. Mem0 integration will be disabled.")

# Singleton instance of Mem0Client
_mem0_client: Optional["EnhancedMem0Client"] = None

class EnhancedMem0Client:
    """
    Enhanced Mem0 client with caching capabilities
    """
    def __init__(self, api_key: Optional[str] = None, endpoint: str = "http://localhost:8050"):
        """
        Initialize the enhanced Mem0 client
        
        Args:
            api_key: Optional API key for authentication
            endpoint: Mem0 API endpoint
        """
        from mem0ai import Mem0Client
        
        # Initialize the base client
        if api_key:
            self.client = Mem0Client(api_key=api_key, endpoint=endpoint)
        else:
            self.client = Mem0Client(endpoint=endpoint)
            
        # Initialize caches with appropriate TTLs
        self.human_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
        self.recall_cache = TTLCache(maxsize=1000, ttl=60)  # 1 minute
        self.archival_cache = TTLCache(maxsize=2000, ttl=300)  # 5 minutes
        self.search_cache = TTLCache(maxsize=2000, ttl=120)  # 2 minutes
        
        # Store endpoint for logging
        self.endpoint = endpoint
        
    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear the cache
        
        Args:
            cache_type: Type of cache to clear (human, recall, archival, search, or None for all)
        """
        if cache_type == "human" or cache_type is None:
            self.human_cache.clear()
            logger.debug("Cleared human cache")
            
        if cache_type == "recall" or cache_type is None:
            self.recall_cache.clear()
            logger.debug("Cleared recall cache")
            
        if cache_type == "archival" or cache_type is None:
            self.archival_cache.clear()
            logger.debug("Cleared archival cache")
            
        if cache_type == "search" or cache_type is None:
            self.search_cache.clear()
            logger.debug("Cleared search cache")
            
        if cache_type is None:
            logger.info("Cleared all caches")
        else:
            logger.info(f"Cleared {cache_type} cache")
            
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent information
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent information or None if not found
        """
        cache_key = f"agent:{agent_id}"
        if cache_key in self.human_cache:
            return self.human_cache[cache_key]
            
        try:
            agent = self.client.get_agent(agent_id)
            if agent:
                self.human_cache[cache_key] = agent
            return agent
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {str(e)}")
            return None
            
    def create_agent(self, agent_id: str, name: str, persona: str) -> bool:
        """
        Create a new agent
        
        Args:
            agent_id: Agent ID
            name: Agent name
            persona: Agent persona
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.create_agent(agent_id=agent_id, name=name, persona=persona)
            # Invalidate cache
            cache_key = f"agent:{agent_id}"
            if cache_key in self.human_cache:
                del self.human_cache[cache_key]
            return True
        except Exception as e:
            logger.error(f"Error creating agent {agent_id}: {str(e)}")
            return False
            
    def get_human(self, human_id: str) -> Optional[Dict[str, Any]]:
        """
        Get human information
        
        Args:
            human_id: Human ID
            
        Returns:
            Human information or None if not found
        """
        cache_key = f"human:{human_id}"
        if cache_key in self.human_cache:
            return self.human_cache[cache_key]
            
        try:
            human = self.client.get_human(human_id)
            if human:
                self.human_cache[cache_key] = human
            return human
        except Exception as e:
            logger.error(f"Error getting human {human_id}: {str(e)}")
            return None
            
    def create_human(self, human_id: str, name: str) -> bool:
        """
        Create a new human
        
        Args:
            human_id: Human ID
            name: Human name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.create_human(human_id=human_id, name=name)
            # Invalidate cache
            cache_key = f"human:{human_id}"
            if cache_key in self.human_cache:
                del self.human_cache[cache_key]
            return True
        except Exception as e:
            logger.error(f"Error creating human {human_id}: {str(e)}")
            return False
            
    def append_message(self, agent_id: str, human_id: str, message: Dict[str, str]) -> bool:
        """
        Append a message to recall memory
        
        Args:
            agent_id: Agent ID
            human_id: Human ID
            message: Message to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.append_message(agent_id=agent_id, human_id=human_id, message=message)
            # Invalidate recall cache for this conversation
            cache_prefix = f"recall:{agent_id}:{human_id}"
            keys_to_delete = [k for k in self.recall_cache.keys() if k.startswith(cache_prefix)]
            for k in keys_to_delete:
                del self.recall_cache[k]
            return True
        except Exception as e:
            logger.error(f"Error appending message for {human_id}: {str(e)}")
            return False
            
    def get_recall_memory(self, agent_id: str, human_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get recall memory
        
        Args:
            agent_id: Agent ID
            human_id: Human ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages
        """
        cache_key = f"recall:{agent_id}:{human_id}:{limit}"
        if cache_key in self.recall_cache:
            return self.recall_cache[cache_key]
            
        try:
            recall = self.client.get_recall_memory(agent_id=agent_id, human_id=human_id, limit=limit)
            self.recall_cache[cache_key] = recall
            return recall
        except Exception as e:
            logger.error(f"Error getting recall memory for {human_id}: {str(e)}")
            return []
            
    def create_archival_memory(self, agent_id: str, human_id: str, data: Dict[str, Any], kind: str, replace: bool = False) -> bool:
        """
        Create archival memory
        
        Args:
            agent_id: Agent ID
            human_id: Human ID
            data: Memory data
            kind: Memory kind
            replace: Whether to replace existing memory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.create_archival_memory(
                agent_id=agent_id,
                human_id=human_id,
                data=data,
                kind=kind,
                replace=replace
            )
            # Invalidate archival cache for this kind
            cache_prefix = f"archival:{agent_id}:{human_id}:{kind}"
            keys_to_delete = [k for k in self.archival_cache.keys() if k.startswith(cache_prefix)]
            for k in keys_to_delete:
                del self.archival_cache[k]
                
            # Also invalidate search cache as it might be affected
            search_prefix = f"search:{agent_id}:{human_id}:{kind}"
            keys_to_delete = [k for k in self.search_cache.keys() if k.startswith(search_prefix)]
            for k in keys_to_delete:
                del self.search_cache[k]
                
            return True
        except Exception as e:
            logger.error(f"Error creating archival memory for {human_id}: {str(e)}")
            return False
            
    def get_archival_memory(self, agent_id: str, human_id: str, kind: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get archival memory
        
        Args:
            agent_id: Agent ID
            human_id: Human ID
            kind: Memory kind
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of memories
        """
        cache_key = f"archival:{agent_id}:{human_id}:{kind}:{limit}"
        if cache_key in self.archival_cache:
            return self.archival_cache[cache_key]
            
        try:
            archival = self.client.get_archival_memory(
                agent_id=agent_id,
                human_id=human_id,
                kind=kind,
                limit=limit
            )
            self.archival_cache[cache_key] = archival
            return archival
        except Exception as e:
            logger.error(f"Error getting archival memory for {human_id}: {str(e)}")
            return []
            
    def search_archival_memory(self, agent_id: str, human_id: str, query: Optional[str], kind: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search archival memory
        
        Args:
            agent_id: Agent ID
            human_id: Human ID
            query: Search query
            kind: Memory kind
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        cache_key = f"search:{agent_id}:{human_id}:{kind}:{query}:{limit}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
            
        try:
            results = self.client.search_archival_memory(
                agent_id=agent_id,
                human_id=human_id,
                query=query,
                kind=kind,
                limit=limit
            )
            self.search_cache[cache_key] = results
            return results
        except Exception as e:
            logger.error(f"Error searching archival memory for {human_id}: {str(e)}")
            return []

def get_mem0_client() -> Optional[EnhancedMem0Client]:
    """
    Get the EnhancedMem0Client instance
    
    Returns:
        EnhancedMem0Client instance or None if not configured
    """
    global _mem0_client
    
    if _mem0_client is None:
        try:
            # Check if Mem0 is enabled and available
            if not SETTINGS.use_mem0 or not MEM0_AVAILABLE:
                logger.info("Mem0 integration is disabled or not available")
                return None
                
            # Initialize the client (API key is optional for local development)
            if SETTINGS.mem0_api_key:
                _mem0_client = EnhancedMem0Client(api_key=SETTINGS.mem0_api_key, endpoint=SETTINGS.mem0_endpoint)
                logger.info(f"Initialized Mem0 client with API key and endpoint: {SETTINGS.mem0_endpoint}")
            else:
                _mem0_client = EnhancedMem0Client(endpoint=SETTINGS.mem0_endpoint)
                logger.info(f"Initialized Mem0 client without API key at endpoint: {SETTINGS.mem0_endpoint}")
            
            # Ensure the Metis RAG agent exists
            if not _mem0_client.get_agent(METIS_AGENT_ID):
                _mem0_client.create_agent(
                    agent_id=METIS_AGENT_ID,
                    name="Metis RAG Agent",
                    persona=METIS_PERSONA
                )
                logger.info(f"Created Metis RAG agent with ID: {METIS_AGENT_ID}")
            
            logger.info(f"Initialized Mem0 client with endpoint: {SETTINGS.mem0_endpoint}")
        except Exception as e:
            logger.error(f"Error initializing Mem0 client: {str(e)}")
            return None
    
    return _mem0_client

# Keep the existing functions but update them to use the enhanced client
# (get_or_create_human, store_message, get_conversation_history, etc.)
```

### 2.2 Database Connection Pooling

Ensure proper connection pooling in `app/db/session.py`:

```python
"""
Database session management
"""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import SETTINGS

logger = logging.getLogger("app.db.session")

# Create SQLAlchemy base
Base = declarative_base()

# Create async engine with connection pooling
engine = create_async_engine(
    SETTINGS.database_url,
    echo=SETTINGS.sql_echo,
    pool_size=SETTINGS.database_pool_size,
    max_overflow=SETTINGS.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session
    
    Yields:
        AsyncSession: Database session
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
```

## 3. Environment Configuration

### 3.1 Update .env.example

Update the `.env.example` file to include Mem0 API key:

```
# API settings
API_V1_STR=/api
PROJECT_NAME=Metis RAG

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=gemma3:12b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# LLM Judge settings
CHUNKING_JUDGE_MODEL=gemma3:12b
RETRIEVAL_JUDGE_MODEL=gemma3:12b
USE_CHUNKING_JUDGE=True
USE_RETRIEVAL_JUDGE=True

# LangGraph RAG Agent settings
LANGGRAPH_RAG_MODEL=gemma3:12b
USE_LANGGRAPH_RAG=True
USE_ENHANCED_LANGGRAPH_RAG=True

# Document settings
UPLOAD_DIR=./data/uploads
CHROMA_DB_DIR=./data/chroma_db
CHUNK_SIZE=1500
CHUNK_OVERLAP=150

# Database settings
DATABASE_TYPE=postgresql
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=metis_rag
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/metis_rag
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Security settings
CORS_ORIGINS=*

# Mem0 settings
MEM0_ENDPOINT=http://localhost:8050
MEM0_API_KEY=your_mem0_api_key_here
USE_MEM0=True
```

### 3.2 Update .env.docker

Update the `.env.docker` file to include Mem0 API key:

```
# API settings
API_V1_STR=/api
PROJECT_NAME=Metis RAG

# Ollama settings
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=gemma3:12b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# LLM Judge settings
CHUNKING_JUDGE_MODEL=gemma3:12b
RETRIEVAL_JUDGE_MODEL=gemma3:12b
USE_CHUNKING_JUDGE=True
USE_RETRIEVAL_JUDGE=True

# LangGraph RAG Agent settings
LANGGRAPH_RAG_MODEL=gemma3:12b
USE_LANGGRAPH_RAG=True
USE_ENHANCED_LANGGRAPH_RAG=True

# Document settings
UPLOAD_DIR=/app/data/uploads
CHROMA_DB_DIR=/app/data/chroma_db
CHUNK_SIZE=1500
CHUNK_OVERLAP=150

# Database settings
DATABASE_TYPE=postgresql
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=metis-postgres
DATABASE_PORT=5432
DATABASE_NAME=metis
DATABASE_URL=postgresql://postgres:postgres@metis-postgres:5432/metis
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Security settings
CORS_ORIGINS=*

# Mem0 settings
MEM0_ENDPOINT=http://mem0:8050
MEM0_API_KEY=${MEM0_ADMIN_API_KEY:-default_dev_key}
USE_MEM0=True
```

## 4. Documentation Enhancement

### 4.1 Update README_MEM0_INTEGRATION.md

Update the `app/rag/README_MEM0_INTEGRATION.md` file:

```markdown
# Mem0 Integration for Metis RAG

This document describes how to set up and use the Mem0 integration for Metis RAG.

## Overview

Mem0 is a memory layer for AI applications that provides a way to store and retrieve information related to users, sessions, and documents. It enables more personalized and context-aware interactions in the Metis RAG system.

The integration provides the following features:

- Conversation history storage and retrieval
- User preferences storage and retrieval
- Document interaction tracking
- Enhanced context for RAG queries

## Why Docker for Mem0?

Running Mem0 in Docker is the recommended approach for the following reasons:

### Dependency Isolation
Docker containers encapsulate Mem0 and its dependencies (including PostgreSQL) in an isolated environment. This prevents conflicts with your project's Python environment and other system-level packages.

### Reproducibility
The Docker setup ensures that everyone on your team (and your deployment environment) is using the exact same Mem0 and PostgreSQL configuration. This eliminates "works on my machine" problems.

### Easy Setup
The provided docker-compose.yml file makes it incredibly easy to start and stop Mem0 and its database. You don't need to manually install and configure PostgreSQL.

### Cleanliness
When you're done with Mem0, you can simply stop and remove the containers, leaving your host system clean.

### Production-Like Environment
Using Docker for development brings your development environment closer to a production environment, which often uses containers.

## Setup

### 1. Start Mem0 with Docker Compose

The easiest way to run Mem0 is using Docker Compose:

```bash
docker-compose up -d
```

This will start the entire Metis RAG stack, including:
- Metis RAG application
- PostgreSQL database for Metis RAG
- PostgreSQL database for Mem0
- Mem0 server
- Ollama for LLM inference

The Mem0 server will be accessible at http://localhost:8050.

### 2. Configure Metis RAG

Update your `.env` file to include the Mem0 configuration:

```
# Mem0 settings
MEM0_ENDPOINT=http://localhost:8050
MEM0_API_KEY=your_mem0_api_key_here
USE_MEM0=True
```

For Docker deployment, the API key is set in the docker-compose.yml file and passed to the application as an environment variable.

### 3. Restart Metis RAG

Restart your Metis RAG application to apply the changes.

## Usage

The Mem0 integration is used automatically by the RAG engine when enabled. It provides the following functionality:

### Conversation History

Conversation history is stored in Mem0's recall memory. This allows the system to maintain context across sessions and provide more coherent responses.

```python
# Store a user message
store_message(human_id="user123", role="user", content="What is RAG?")

# Store an assistant message
store_message(human_id="user123", role="assistant", content="RAG stands for Retrieval-Augmented Generation...")

# Get conversation history
history = get_conversation_history(human_id="user123", limit=10)
```

### User Preferences

User preferences are stored in Mem0's archival memory. This allows the system to personalize responses based on user preferences, such as preferred models or response styles.

```python
# Store user preferences
store_user_preferences(human_id="user123", preferences={
    "preferred_model": "gemma3:12b",
    "response_style": "concise",
    "language": "en"
})

# Get user preferences
preferences = get_user_preferences(human_id="user123")
```

### Document Interactions

Document interactions are stored in Mem0's archival memory. This allows the system to track which documents a user has interacted with and provide more relevant responses.

```python
# Store document interaction
store_document_interaction(
    human_id="user123",
    document_id="doc456",
    interaction_type="view",
    data={"timestamp": "2023-01-01T00:00:00Z"}
)

# Get document interactions
interactions = get_document_interactions(
    human_id="user123",
    document_id="doc456",
    interaction_type="view",
    limit=10
)
```

## Performance Considerations

The Mem0 integration includes several performance optimizations:

### Caching

The Mem0 client includes caching for frequently accessed data, reducing the number of API calls to the Mem0 server.

```python
# The EnhancedMem0Client automatically caches:
# - Human and agent information
# - Recall memory (conversation history)
# - Archival memory (user preferences, document interactions)
# - Search results

# You can manually clear the cache if needed:
client = get_mem0_client()
client.clear_cache()  # Clear all caches
client.clear_cache("human")  # Clear only human cache
client.clear_cache("recall")  # Clear only recall cache
```

### Connection Pooling

The PostgreSQL connection uses connection pooling to efficiently manage database connections.

### Batch Operations

Document processing uses batch operations to efficiently process large numbers of documents.

## API

The Mem0 integration provides the following API:

### `get_mem0_client()`

Get the Mem0 client instance.

### `store_message(human_id, role, content)`

Store a message in recall memory.

### `get_conversation_history(human_id, limit=10)`

Get conversation history from recall memory.

### `store_user_preferences(human_id, preferences)`

Store user preferences in archival memory.

### `get_user_preferences(human_id)`

Get user preferences from archival memory.

### `store_document_interaction(human_id, document_id, interaction_type, data)`

Store document interaction in archival memory.

### `get_document_interactions(human_id, document_id=None, interaction_type=None, limit=10)`

Get document interactions from archival memory.

## Troubleshooting

If you encounter issues with the Mem0 integration, check the following:

1. Make sure the Mem0 server is running and accessible at the configured endpoint.
2. Check the logs for any error messages related to Mem0.
3. Make sure the `USE_MEM0` setting is set to `True` in your `.env` file.
4. If you're using an API key, make sure it's correctly configured.
5. For Docker deployments, check that the Mem0 container is healthy using `docker ps`.
6. Check the Mem0 logs using `docker logs metis-mem0`.

## References

- [Mem0 Documentation](https://docs.mem0.ai)
- [Mem0 GitHub Repository](https://github.com/mem0ai/mem0)
```

## 5. Testing Plan

### 5.1 Unit Tests

Create unit tests for the Mem0 client:

```python
"""
Unit tests for Mem0 client
"""
import pytest
from unittest.mock import patch, MagicMock
from app.rag.mem0_client import get_mem0_client, store_message, get_conversation_history

@pytest.fixture
def mock_mem0_client():
    """
    Mock Mem0 client
    """
    with patch("app.rag.mem0_client.EnhancedMem0Client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_settings():
    """
    Mock settings
    """
    with patch("app.rag.mem0_client.SETTINGS") as mock_settings:
        mock_settings.use_mem0 = True
        mock_settings.mem0_endpoint = "http://localhost:8050"
        mock_settings.mem0_api_key = "test_key"
        yield mock_settings

def test_get_mem0_client(mock_mem0_client, mock_settings):
    """
    Test get_mem0_client
    """
    # Reset singleton
    import app.rag.mem0_client
    app.rag.mem0_client._mem0_client = None
    
    # Mock MEM0_AVAILABLE
    with patch("app.rag.mem0_client.MEM0_AVAILABLE", True):
        client = get_mem0_client()
        assert client is not None
        assert client == mock_mem0_client

def test_store_message(mock_mem0_client, mock_settings):
    """
    Test store_message
    """
    # Reset singleton
    import app.rag.mem0_client
    app.rag.mem0_client._mem0_client = None
    
    # Mock MEM0_AVAILABLE and get_or_create_human
    with patch("app.rag.mem0_client.MEM0_AVAILABLE", True):
        with patch("app.rag.mem0_client.get_or_create_human", return_value=True):
            result = store_message("user123", "user", "Hello")
            assert result is True
            mock_mem0_client.append_message.assert_called_once()

def test_get_conversation_history(mock_mem0_client, mock_settings):
    """
    Test get_conversation_history
    """
    # Reset singleton
    import app.rag.mem0_client
    app.rag.mem0_client._mem0_client = None
    
    # Mock MEM0_AVAILABLE
    with patch("app.rag.mem0_client.MEM0_AVAILABLE", True):
        mock_mem0_client.get_recall_memory.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        history = get_conversation_history("user123")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        mock_mem0_client.get_recall_memory.assert_called_once()

def test_clear_cache(mock_mem0_client, mock_settings):
    """
    Test clear_cache
    """
    # Reset singleton
    import app.rag.mem0_client
    app.rag.mem0_client._mem0_client = None
    
    # Mock MEM0_AVAILABLE
    with patch("app.rag.mem0_client.MEM0_AVAILABLE", True):
        client = get_mem0_client()
        
        # Test clearing all caches
        client.clear_cache()
        mock_mem0_client.human_cache.clear.assert_called_once()
        mock_mem0_client.recall_cache.clear.assert_called_once()
        mock_mem0_client.archival_cache.clear.assert_called_once()
        mock_mem0_client.search_cache.clear.assert_called_once()
        
        # Reset mock
        mock_mem0_client.reset_mock()
        
        # Test clearing specific cache
        client.clear_cache("human")
        mock_mem0_client.human_cache.clear.assert_called_once()
        mock_mem0_client.recall_cache.clear.assert_not_called()
        mock_mem0_client.archival_cache.clear.assert_not_called()
        mock_mem0_client.search_cache.clear.assert_not_called()
```

## 6. Prioritized Implementation Steps

Based on your feedback, here are the prioritized implementation steps:

1. **Implement the Mem0Client changes**
   - Update `mem0_client.py` to include caching logic
   - Add the `clear_cache` method
   - Implement the `get_or_create_human` method

2. **Integrate with RAGEngine**
   - Update the `RAGEngine.query` method to use the Mem0Client for storing/retrieving conversation history, user preferences, and document interactions
   - Incorporate user preferences and document interaction data into the retrieval process

3. **Update API Endpoints**
   - Modify the `app/api/chat.py` endpoints to use the updated RAGEngine
   - Pass the user_id to the RAGEngine.query method
   - Add a new endpoint for retrieving conversation history

4. **Update Docker Configuration**
   - Use the provided, improved docker-compose.yml file
   - Create the .dockerignore file
   - Update environment configuration files

5. **Write Tests**
   - Write unit tests for the Mem0Client
   - Write integration tests for the Mem0 integration
   - Write performance tests for the Mem0 integration

6. **Update Documentation**
   - Update README_MEM0_INTEGRATION.md with clear instructions
   - Add code examples for using the Mem0 integration

7. **Deploy and Test**
   - Deploy the updated Docker configuration
   - Run tests to verify functionality and performance
   - Monitor system performance and make adjustments as needed

## 7. Monitoring and Maintenance

1. **Monitor Mem0 Performance**
   - Track API call latency
   - Monitor cache hit rates
   - Adjust cache TTLs based on usage patterns

2. **Monitor PostgreSQL Performance**
   - Track query performance
   - Monitor connection pool usage
   - Adjust pool size and max overflow based on usage patterns

3. **Regular Maintenance**
   - Update Mem0 and PostgreSQL versions
   - Backup Mem0 data
   - Clean up old data to prevent database growth