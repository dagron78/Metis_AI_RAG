#!/usr/bin/env python3
"""
Update Docker Configuration for PostgreSQL Support

This script updates the Docker configuration files to support PostgreSQL:
1. Updates docker-compose.yml to include a PostgreSQL service
2. Updates Dockerfile to install PostgreSQL client libraries
3. Creates database initialization scripts
4. Updates environment configuration

Usage:
    python update_docker_for_postgres.py [--apply]
"""
import os
import sys
import yaml
import argparse
import shutil
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Docker Compose configuration for PostgreSQL
POSTGRES_DOCKER_COMPOSE = """
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: config/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./chroma_db:/app/chroma_db
    environment:
      - DATABASE_TYPE=${DATABASE_TYPE:-postgresql}
      - DATABASE_USER=${DATABASE_USER:-postgres}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD:-postgres}
      - DATABASE_HOST=${DATABASE_HOST:-postgres}
      - DATABASE_PORT=${DATABASE_PORT:-5432}
      - DATABASE_NAME=${DATABASE_NAME:-metis_rag}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://ollama:11434}
      - DEFAULT_MODEL=${DEFAULT_MODEL:-gemma3:12b}
      - DEFAULT_EMBEDDING_MODEL=${DEFAULT_EMBEDDING_MODEL:-nomic-embed-text}
    depends_on:
      - postgres
      - ollama
    restart: unless-stopped
    networks:
      - metis-network

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=${DATABASE_USER:-postgres}
      - POSTGRES_PASSWORD=${DATABASE_PASSWORD:-postgres}
      - POSTGRES_DB=${DATABASE_NAME:-metis_rag}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./config/postgres/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - metis-network

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped
    networks:
      - metis-network

volumes:
  postgres-data:
  ollama-data:

networks:
  metis-network:
    driver: bridge
"""

# Docker Compose configuration for SQLite
SQLITE_DOCKER_COMPOSE = """
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: config/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./chroma_db:/app/chroma_db
    environment:
      - DATABASE_TYPE=${DATABASE_TYPE:-sqlite}
      - DATABASE_URL=${DATABASE_URL:-sqlite:///./test.db}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://ollama:11434}
      - DEFAULT_MODEL=${DEFAULT_MODEL:-gemma3:12b}
      - DEFAULT_EMBEDDING_MODEL=${DEFAULT_EMBEDDING_MODEL:-nomic-embed-text}
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - metis-network

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped
    networks:
      - metis-network

volumes:
  ollama-data:

networks:
  metis-network:
    driver: bridge
"""

# Dockerfile updates for PostgreSQL support
DOCKERFILE_POSTGRES_ADDITIONS = """
# Install PostgreSQL client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install psycopg2 for PostgreSQL support
RUN pip install --no-cache-dir psycopg2-binary
"""

# PostgreSQL initialization script
POSTGRES_INIT_SCRIPT = """
#!/bin/bash
set -e

# Create extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
EOSQL

echo "PostgreSQL initialized with extensions"
"""

# Environment configuration for PostgreSQL
POSTGRES_ENV_CONFIG = """
# Database settings
DATABASE_TYPE=postgresql
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=metis_rag
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Ollama settings
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=gemma3:12b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# Document settings
UPLOAD_DIR=/app/uploads
CHROMA_DB_DIR=/app/chroma_db
CHUNK_SIZE=1500
CHUNK_OVERLAP=150
"""

# Environment configuration for SQLite
SQLITE_ENV_CONFIG = """
# Database settings
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./test.db
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Ollama settings
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=gemma3:12b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# Document settings
UPLOAD_DIR=/app/uploads
CHROMA_DB_DIR=/app/chroma_db
CHUNK_SIZE=1500
CHUNK_OVERLAP=150
"""

def update_docker_compose():
    """Update docker-compose.yml to include PostgreSQL service"""
    docker_compose_file = os.path.join(project_root, "config", "docker-compose.yml")
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(docker_compose_file), exist_ok=True)
    
    # Create PostgreSQL docker-compose.yml
    with open(docker_compose_file, 'w') as f:
        f.write(POSTGRES_DOCKER_COMPOSE.strip())
    
    print(f"Updated {docker_compose_file} with PostgreSQL service")
    
    # Create SQLite docker-compose.yml
    sqlite_docker_compose_file = os.path.join(project_root, "config", "docker-compose.sqlite.yml")
    with open(sqlite_docker_compose_file, 'w') as f:
        f.write(SQLITE_DOCKER_COMPOSE.strip())
    
    print(f"Created {sqlite_docker_compose_file} for SQLite configuration")

def update_dockerfile():
    """Update Dockerfile to install PostgreSQL client libraries"""
    dockerfile = os.path.join(project_root, "config", "Dockerfile")
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(dockerfile), exist_ok=True)
    
    # Check if Dockerfile exists
    if os.path.exists(dockerfile):
        with open(dockerfile, 'r') as f:
            content = f.read()
        
        # Check if PostgreSQL additions already exist
        if "libpq-dev" in content:
            print(f"Dockerfile already includes PostgreSQL client libraries")
            return
        
        # Find a good place to add PostgreSQL additions
        if "RUN pip install" in content:
            # Add before pip install
            new_content = content.replace(
                "RUN pip install",
                DOCKERFILE_POSTGRES_ADDITIONS + "\nRUN pip install"
            )
        else:
            # Add at the end
            new_content = content + "\n" + DOCKERFILE_POSTGRES_ADDITIONS
        
        with open(dockerfile, 'w') as f:
            f.write(new_content)
        
        print(f"Updated {dockerfile} with PostgreSQL client libraries")
    else:
        # Create a basic Dockerfile
        basic_dockerfile = """FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

# Install PostgreSQL client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir psycopg2-binary

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        with open(dockerfile, 'w') as f:
            f.write(basic_dockerfile)
        
        print(f"Created {dockerfile} with PostgreSQL support")

def create_postgres_init_scripts():
    """Create PostgreSQL initialization scripts"""
    init_dir = os.path.join(project_root, "config", "postgres", "init")
    os.makedirs(init_dir, exist_ok=True)
    
    # Create initialization script
    init_script = os.path.join(init_dir, "01-init-extensions.sh")
    with open(init_script, 'w') as f:
        f.write(POSTGRES_INIT_SCRIPT)
    
    # Make script executable
    os.chmod(init_script, 0o755)
    
    print(f"Created PostgreSQL initialization script: {init_script}")

def update_environment_config():
    """Update environment configuration files"""
    # Create PostgreSQL .env file
    postgres_env_file = os.path.join(project_root, "config", ".env.postgres")
    with open(postgres_env_file, 'w') as f:
        f.write(POSTGRES_ENV_CONFIG)
    
    print(f"Created PostgreSQL environment configuration: {postgres_env_file}")
    
    # Create SQLite .env file
    sqlite_env_file = os.path.join(project_root, "config", ".env.sqlite")
    with open(sqlite_env_file, 'w') as f:
        f.write(SQLITE_ENV_CONFIG)
    
    print(f"Created SQLite environment configuration: {sqlite_env_file}")
    
    # Create example .env file
    example_env_file = os.path.join(project_root, "config", ".env.example")
    with open(example_env_file, 'w') as f:
        f.write(POSTGRES_ENV_CONFIG + "\n# Uncomment for SQLite\n# DATABASE_TYPE=sqlite\n# DATABASE_URL=sqlite:///./test.db\n")
    
    print(f"Created example environment configuration: {example_env_file}")

def create_deployment_guide():
    """Create deployment guide for PostgreSQL"""
    guide_file = os.path.join(project_root, "docs", "deployment", "postgres_deployment.md")
    os.makedirs(os.path.dirname(guide_file), exist_ok=True)
    
    guide_content = """# PostgreSQL Deployment Guide for Metis RAG

This guide provides instructions for deploying the Metis RAG system with PostgreSQL.

## Prerequisites

- Docker and Docker Compose
- Git
- Basic knowledge of PostgreSQL

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/metis-rag.git
cd metis-rag
```

### 2. Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
cp config/.env.postgres .env
```

Edit the `.env` file to customize your deployment:

```
# Database settings
DATABASE_TYPE=postgresql
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=metis_rag
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Ollama settings
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=gemma3:12b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# Document settings
UPLOAD_DIR=/app/uploads
CHROMA_DB_DIR=/app/chroma_db
CHUNK_SIZE=1500
CHUNK_OVERLAP=150
```

### 3. Start the Services

```bash
docker-compose up -d
```

This will start the following services:
- PostgreSQL database
- Ollama for LLM inference
- Metis RAG application

### 4. Run Database Migrations

```bash
docker-compose exec app python -m scripts.run_migrations
```

### 5. Access the Application

The application will be available at http://localhost:8000

## PostgreSQL Configuration

The PostgreSQL service is configured with the following settings:

- Data is persisted in a Docker volume (`postgres-data`)
- The database is initialized with the UUID and pg_trgm extensions
- The database is accessible on port 5432

### Connecting to PostgreSQL

To connect to the PostgreSQL database:

```bash
docker-compose exec postgres psql -U postgres -d metis_rag
```

### Backup and Restore

To backup the database:

```bash
docker-compose exec postgres pg_dump -U postgres -d metis_rag > backup.sql
```

To restore the database:

```bash
cat backup.sql | docker-compose exec -T postgres psql -U postgres -d metis_rag
```

## Switching Between SQLite and PostgreSQL

The Metis RAG system supports both SQLite and PostgreSQL. To switch between them:

### Switch to SQLite

1. Update the `.env` file:
```
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./test.db
```

2. Use the SQLite Docker Compose configuration:
```bash
docker-compose -f config/docker-compose.sqlite.yml up -d
```

### Switch to PostgreSQL

1. Update the `.env` file:
```
DATABASE_TYPE=postgresql
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=metis_rag
```

2. Use the PostgreSQL Docker Compose configuration:
```bash
docker-compose up -d
```

## Production Deployment Considerations

For production deployments, consider the following:

### Security

- Change the default PostgreSQL password
- Use a separate PostgreSQL instance with proper backup and monitoring
- Configure SSL for PostgreSQL connections

### Performance

- Increase the PostgreSQL memory settings based on available resources
- Configure connection pooling for high-traffic deployments
- Use a managed PostgreSQL service (AWS RDS, Azure Database, etc.)

### High Availability

- Set up PostgreSQL replication
- Configure automated backups
- Implement a health check and monitoring system

## Troubleshooting

### Database Connection Issues

If the application cannot connect to the database:

1. Check if the PostgreSQL container is running:
```bash
docker-compose ps
```

2. Check the PostgreSQL logs:
```bash
docker-compose logs postgres
```

3. Verify the database connection settings in the `.env` file

### Migration Issues

If database migrations fail:

1. Check the application logs:
```bash
docker-compose logs app
```

2. Run migrations manually:
```bash
docker-compose exec app alembic upgrade head
```

3. Reset the database if needed:
```bash
docker-compose down -v  # This will delete all data!
docker-compose up -d
```
"""
    
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    print(f"Created PostgreSQL deployment guide: {guide_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Update Docker Configuration for PostgreSQL Support")
    parser.add_argument("--apply", action="store_true", help="Apply the changes")
    args = parser.parse_args()
    
    print("Update Docker Configuration for PostgreSQL Support")
    print("================================================")
    
    if args.apply:
        print("\nApplying Docker configuration updates...")
        
        # Update docker-compose.yml
        update_docker_compose()
        
        # Update Dockerfile
        update_dockerfile()
        
        # Create PostgreSQL initialization scripts
        create_postgres_init_scripts()
        
        # Update environment configuration
        update_environment_config()
        
        # Create deployment guide
        create_deployment_guide()
        
        print("\nDocker configuration updates applied successfully!")
        print("\nTo deploy with PostgreSQL:")
        print("1. Copy the environment configuration: cp config/.env.postgres .env")
        print("2. Start the services: docker-compose up -d")
        print("3. Run migrations: docker-compose exec app python -m scripts.run_migrations")
    else:
        print("\nThis script will apply the following changes:")
        print("  1. Update docker-compose.yml to include a PostgreSQL service")
        print("  2. Update Dockerfile to install PostgreSQL client libraries")
        print("  3. Create database initialization scripts")
        print("  4. Update environment configuration")
        print("  5. Create a deployment guide")
        print("\nRun with --apply to apply these changes.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())