#!/usr/bin/env python3
"""
Docker Configuration Update Script for Metis RAG

This script updates the Docker configuration to support both SQLite and PostgreSQL:
1. Updates docker-compose.yml to include PostgreSQL service
2. Creates database initialization scripts
3. Updates Dockerfile to install PostgreSQL client libraries
4. Creates environment-based configuration switching

Usage:
    python update_docker_config.py [--apply]
"""
import os
import sys
import argparse
import shutil
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class DockerConfigUpdater:
    """Docker configuration update class"""
    
    def __init__(self, apply: bool = False):
        self.apply = apply
        self.config_dir = os.path.join(project_root, "config")
        
        print(f"Initialized Docker configuration updater")
        print(f"Apply mode: {'ON' if apply else 'OFF (dry run)'}")
        
    def update_file(self, file_path: str, new_content: str, description: str) -> bool:
        """Update a file with new content"""
        try:
            print(f"  {description}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"    ✗ Error: File not found: {file_path}")
                return False
            
            # Backup file
            backup_path = f"{file_path}.bak"
            if self.apply:
                shutil.copy2(file_path, backup_path)
                print(f"    ✓ Created backup: {backup_path}")
            
            # Write new content
            if self.apply:
                with open(file_path, 'w') as f:
                    f.write(new_content)
                print(f"    ✓ Updated file: {file_path}")
                return True
            else:
                print(f"    ✓ Validated (not applied - dry run mode)")
                return True
        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
            return False
    
    def create_file(self, file_path: str, content: str, description: str) -> bool:
        """Create a new file with content"""
        try:
            print(f"  {description}")
            
            # Check if file already exists
            if os.path.exists(file_path):
                print(f"    ✓ File already exists: {file_path}")
                return True
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write content
            if self.apply:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"    ✓ Created file: {file_path}")
                return True
            else:
                print(f"    ✓ Validated (not applied - dry run mode)")
                return True
        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
            return False
    
    def update_docker_compose(self) -> bool:
        """Update docker-compose.yml to include PostgreSQL service"""
        file_path = os.path.join(self.config_dir, "docker-compose.yml")
        
        new_content = """version: '3.8'

services:
  # Metis RAG API service
  metis-rag:
    build:
      context: ..
      dockerfile: config/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ../data:/app/data
      - ../uploads:/app/uploads
    environment:
      - DATABASE_TYPE=${DATABASE_TYPE:-sqlite}
      - DATABASE_URL=${DATABASE_URL:-sqlite:///./data/metis_rag.db}
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
      - POSTGRES_DB=${POSTGRES_DB:-metis_rag}
      - POSTGRES_HOST=${POSTGRES_HOST:-postgres}
      - POSTGRES_PORT=${POSTGRES_PORT:-5432}
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - metis-network

  # PostgreSQL database service (optional)
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
      - POSTGRES_DB=${POSTGRES_DB:-metis_rag}
    restart: unless-stopped
    networks:
      - metis-network

volumes:
  postgres-data:

networks:
  metis-network:
    driver: bridge
"""
        
        return self.update_file(file_path, new_content, "Updating docker-compose.yml")
    
    def update_dockerfile(self) -> bool:
        """Update Dockerfile to install PostgreSQL client libraries"""
        file_path = os.path.join(self.config_dir, "Dockerfile")
        
        new_content = """FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY config/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/app/
COPY scripts/ /app/scripts/

# Create necessary directories
RUN mkdir -p /app/data /app/uploads

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_TYPE=sqlite
ENV DATABASE_URL=sqlite:///./data/metis_rag.db

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        return self.update_file(file_path, new_content, "Updating Dockerfile")
    
    def update_requirements(self) -> bool:
        """Update requirements.txt to include PostgreSQL dependencies"""
        file_path = os.path.join(self.config_dir, "requirements.txt")
        
        # Read existing requirements
        try:
            with open(file_path, 'r') as f:
                existing_content = f.read()
        except Exception as e:
            print(f"    ✗ Error reading requirements.txt: {str(e)}")
            return False
        
        # Check if psycopg2 is already included
        if "psycopg2" in existing_content:
            print("  PostgreSQL dependencies already in requirements.txt")
            return True
        
        # Add PostgreSQL dependencies
        new_content = existing_content.strip() + "\n\n# PostgreSQL dependencies\npsycopg2-binary>=2.9.5\n"
        
        return self.update_file(file_path, new_content, "Updating requirements.txt")
    
    def create_init_scripts(self) -> bool:
        """Create database initialization scripts"""
        init_dir = os.path.join(self.config_dir, "init-scripts")
        os.makedirs(init_dir, exist_ok=True)
        
        # Create init script
        init_script_path = os.path.join(init_dir, "01-init.sql")
        init_script_content = """-- PostgreSQL initialization script for Metis RAG

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Set configuration
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS public;

-- Grant privileges
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- Create user for application if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'metis_app'
    ) THEN
        CREATE USER metis_app WITH PASSWORD 'metis_password';
    END IF;
END
$$;

-- Grant privileges to application user
GRANT ALL PRIVILEGES ON DATABASE metis_rag TO metis_app;
GRANT ALL PRIVILEGES ON SCHEMA public TO metis_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO metis_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO metis_app;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO metis_app;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO metis_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO metis_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO metis_app;

-- Create function for updating timestamps
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';
"""
        
        init_result = self.create_file(init_script_path, init_script_content, "Creating PostgreSQL initialization script")
        
        # Create functions script
        functions_script_path = os.path.join(init_dir, "02-functions.sql")
        functions_script_content = """-- PostgreSQL functions for Metis RAG

-- Create function for cosine similarity
CREATE OR REPLACE FUNCTION cosine_similarity(a real[], b real[]) 
RETURNS real AS $$
DECLARE
    dot_product real := 0;
    norm_a real := 0;
    norm_b real := 0;
BEGIN
    FOR i IN 1..array_length(a, 1) LOOP
        dot_product := dot_product + (a[i] * b[i]);
        norm_a := norm_a + (a[i] * a[i]);
        norm_b := norm_b + (b[i] * b[i]);
    END LOOP;
    
    IF norm_a = 0 OR norm_b = 0 THEN
        RETURN 0;
    ELSE
        RETURN dot_product / (sqrt(norm_a) * sqrt(norm_b));
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create function for semantic search
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding real[],
    match_threshold real,
    match_count integer
)
RETURNS TABLE(
    chunk_id uuid,
    document_id uuid,
    content text,
    similarity real
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id::uuid as chunk_id,
        c.document_id::uuid,
        c.content,
        cosine_similarity(c.embedding, query_embedding) as similarity
    FROM
        chunks c
    WHERE
        c.embedding IS NOT NULL
    ORDER BY
        cosine_similarity(c.embedding, query_embedding) DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
DECLARE
    view_name text;
BEGIN
    FOR view_name IN (SELECT matviewname FROM pg_matviews)
    LOOP
        EXECUTE 'REFRESH MATERIALIZED VIEW ' || view_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
"""
        
        functions_result = self.create_file(functions_script_path, functions_script_content, "Creating PostgreSQL functions script")
        
        return init_result and functions_result
    
    def create_env_files(self) -> bool:
        """Create environment configuration files"""
        # Create .env.sqlite
        sqlite_env_path = os.path.join(self.config_dir, ".env.sqlite")
        sqlite_env_content = """# SQLite configuration
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/metis_rag.db
"""
        
        sqlite_result = self.create_file(sqlite_env_path, sqlite_env_content, "Creating SQLite environment file")
        
        # Create .env.postgresql
        postgres_env_path = os.path.join(self.config_dir, ".env.postgresql")
        postgres_env_content = """# PostgreSQL configuration
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/metis_rag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=metis_rag
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
"""
        
        postgres_result = self.create_file(postgres_env_path, postgres_env_content, "Creating PostgreSQL environment file")
        
        return sqlite_result and postgres_result
    
    def create_deployment_scripts(self) -> bool:
        """Create deployment scripts"""
        # Create start-sqlite.sh
        sqlite_script_path = os.path.join(self.config_dir, "start-sqlite.sh")
        sqlite_script_content = """#!/bin/bash
# Start Metis RAG with SQLite configuration

# Load SQLite environment variables
export $(grep -v '^#' .env.sqlite | xargs)

# Start the services
docker-compose up -d metis-rag

echo "Metis RAG started with SQLite configuration"
"""
        
        sqlite_result = self.create_file(sqlite_script_path, sqlite_script_content, "Creating SQLite startup script")
        
        # Create start-postgresql.sh
        postgres_script_path = os.path.join(self.config_dir, "start-postgresql.sh")
        postgres_script_content = """#!/bin/bash
# Start Metis RAG with PostgreSQL configuration

# Load PostgreSQL environment variables
export $(grep -v '^#' .env.postgresql | xargs)

# Start the services
docker-compose up -d

echo "Metis RAG started with PostgreSQL configuration"
"""
        
        postgres_result = self.create_file(postgres_script_path, postgres_script_content, "Creating PostgreSQL startup script")
        
        # Make scripts executable
        if self.apply:
            os.chmod(sqlite_script_path, 0o755)
            os.chmod(postgres_script_path, 0o755)
        
        return sqlite_result and postgres_result
    
    def create_documentation(self) -> bool:
        """Create deployment documentation"""
        docs_dir = os.path.join(project_root, "docs", "deployment")
        os.makedirs(docs_dir, exist_ok=True)
        
        doc_path = os.path.join(docs_dir, "database_deployment.md")
        doc_content = """# Metis RAG Database Deployment Guide

This guide explains how to deploy Metis RAG with different database backends.

## Database Options

Metis RAG supports two database backends:

1. **SQLite** - Simple file-based database, good for development and small deployments
2. **PostgreSQL** - Full-featured database, recommended for production and larger deployments

## Deployment with SQLite

SQLite is the simplest option and requires no additional setup:

```bash
cd config
./start-sqlite.sh
```

This will start the Metis RAG API service with SQLite as the database backend.

## Deployment with PostgreSQL

PostgreSQL provides better performance, concurrency, and advanced features:

```bash
cd config
./start-postgresql.sh
```

This will start both the Metis RAG API service and a PostgreSQL database service.

### PostgreSQL Configuration

You can customize the PostgreSQL configuration by editing the `.env.postgresql` file:

```
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/metis_rag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=metis_rag
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

For production deployments, make sure to change the default passwords.

## Database Migration

To migrate from SQLite to PostgreSQL:

1. Export data from SQLite:
   ```bash
   python scripts/export_data.py --output-file data/export.json
   ```

2. Start PostgreSQL:
   ```bash
   cd config
   ./start-postgresql.sh
   ```

3. Import data to PostgreSQL:
   ```bash
   python scripts/import_data.py --input-file data/export.json --db-type postgresql
   ```

## Performance Considerations

- **SQLite**: Good for small to medium deployments with limited concurrent users
- **PostgreSQL**: Better for larger deployments with many concurrent users

PostgreSQL provides several advantages for production use:
- Better concurrency handling
- Full-text search capabilities
- JSONB operators for efficient metadata queries
- Connection pooling
- Better performance with large datasets

## Backup and Restore

### SQLite Backup
```bash
cp data/metis_rag.db data/metis_rag.db.backup
```

### PostgreSQL Backup
```bash
docker exec -t metis-rag_postgres_1 pg_dump -U postgres metis_rag > backup.sql
```

### PostgreSQL Restore
```bash
cat backup.sql | docker exec -i metis-rag_postgres_1 psql -U postgres -d metis_rag
```
"""
        
        return self.create_file(doc_path, doc_content, "Creating deployment documentation")
    
    def update_docker_config(self) -> Dict[str, Any]:
        """Update Docker configuration"""
        print("\nUpdating Docker configuration...")
        
        results = {
            "apply_mode": self.apply,
            "updates": []
        }
        
        # Update docker-compose.yml
        docker_compose_result = self.update_docker_compose()
        results["updates"].append({
            "name": "docker-compose.yml",
            "applied": docker_compose_result
        })
        
        # Update Dockerfile
        dockerfile_result = self.update_dockerfile()
        results["updates"].append({
            "name": "Dockerfile",
            "applied": dockerfile_result
        })
        
        # Update requirements.txt
        requirements_result = self.update_requirements()
        results["updates"].append({
            "name": "requirements.txt",
            "applied": requirements_result
        })
        
        # Create initialization scripts
        init_scripts_result = self.create_init_scripts()
        results["updates"].append({
            "name": "Initialization scripts",
            "applied": init_scripts_result
        })
        
        # Create environment files
        env_files_result = self.create_env_files()
        results["updates"].append({
            "name": "Environment files",
            "applied": env_files_result
        })
        
        # Create deployment scripts
        deployment_scripts_result = self.create_deployment_scripts()
        results["updates"].append({
            "name": "Deployment scripts",
            "applied": deployment_scripts_result
        })
        
        # Create documentation
        documentation_result = self.create_documentation()
        results["updates"].append({
            "name": "Deployment documentation",
            "applied": documentation_result
        })
        
        # Print summary
        print("\nUpdate Summary:")
        applied_count = sum(1 for u in results["updates"] if u["applied"])
        total_count = len(results["updates"])
        print(f"  Applied: {applied_count}/{total_count} updates")
        
        if not self.apply:
            print("\nTo apply these updates, run again with --apply flag")
        
        return results

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Docker Configuration Update for Metis RAG")
    parser.add_argument("--apply", action="store_true", help="Apply updates (default is dry run)")
    args = parser.parse_args()
    
    # Create updater instance
    updater = DockerConfigUpdater(args.apply)
    
    try:
        # Update Docker configuration
        results = updater.update_docker_config()
        
        print("\nDocker configuration update completed successfully!")
        return 0
    except Exception as e:
        print(f"Error updating Docker configuration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())