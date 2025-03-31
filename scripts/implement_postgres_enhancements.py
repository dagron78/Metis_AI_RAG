#!/usr/bin/env python3
"""
PostgreSQL-Specific Enhancements for Metis RAG

This script implements PostgreSQL-specific optimizations:
1. JSONB operators for metadata queries
2. Full-text search capabilities
3. Connection pooling configuration
4. Index optimization

Usage:
    python implement_postgres_enhancements.py [--apply]
"""
import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.session import Base, engine, SessionLocal
from app.core.config import DATABASE_TYPE, DATABASE_URL

# SQL scripts for PostgreSQL enhancements
POSTGRES_ENHANCEMENTS = {
    "jsonb_operators": """
-- Add indexes for JSONB operators on metadata fields
CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin ON documents USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata_gin ON chunks USING GIN (metadata);

-- Example of how to query using JSONB operators:
-- SELECT * FROM documents WHERE metadata @> '{"file_type": "pdf"}'::jsonb;
-- SELECT * FROM chunks WHERE metadata @> '{"tags": ["important"]}'::jsonb;
""",

    "full_text_search": """
-- Add tsvector columns for full-text search
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_tsv tsvector;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS content_tsv tsvector;

-- Create update triggers for tsvector columns
CREATE OR REPLACE FUNCTION documents_tsvector_update_trigger() RETURNS trigger AS $$
BEGIN
  NEW.content_tsv := to_tsvector('english', coalesce(NEW.content, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION chunks_tsvector_update_trigger() RETURNS trigger AS $$
BEGIN
  NEW.content_tsv := to_tsvector('english', coalesce(NEW.content, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS documents_tsvector_update ON documents;
CREATE TRIGGER documents_tsvector_update BEFORE INSERT OR UPDATE
ON documents FOR EACH ROW EXECUTE FUNCTION documents_tsvector_update_trigger();

DROP TRIGGER IF EXISTS chunks_tsvector_update ON chunks;
CREATE TRIGGER chunks_tsvector_update BEFORE INSERT OR UPDATE
ON chunks FOR EACH ROW EXECUTE FUNCTION chunks_tsvector_update_trigger();

-- Create GIN indexes for full-text search
CREATE INDEX IF NOT EXISTS idx_documents_content_tsv ON documents USING GIN (content_tsv);
CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv ON chunks USING GIN (content_tsv);

-- Example of how to use full-text search:
-- SELECT * FROM documents WHERE content_tsv @@ to_tsquery('english', 'search & terms');
-- SELECT * FROM chunks WHERE content_tsv @@ to_tsquery('english', 'search & terms');
""",

    "index_optimization": """
-- Add additional indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_documents_filename_folder ON documents (filename, folder);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded ON documents (uploaded);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id_index ON chunks (document_id, index);

-- Add partial indexes for common filters
CREATE INDEX IF NOT EXISTS idx_documents_processing_status_pending ON documents (id) 
WHERE processing_status = 'pending';

CREATE INDEX IF NOT EXISTS idx_documents_processing_status_completed ON documents (id) 
WHERE processing_status = 'completed';

-- Add index for document type filtering
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents ((metadata->>'file_type'));

-- Add index for tag filtering
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN ((metadata->'tags_list'));
""",

    "connection_pooling": """
-- PostgreSQL connection pooling settings (to be added to postgresql.conf)
-- max_connections = 100
-- shared_buffers = 256MB
-- effective_cache_size = 768MB
-- work_mem = 8MB
-- maintenance_work_mem = 64MB
-- max_worker_processes = 8
-- max_parallel_workers_per_gather = 4
-- max_parallel_workers = 8
-- random_page_cost = 1.1
-- effective_io_concurrency = 200
-- checkpoint_completion_target = 0.9
-- wal_buffers = 16MB
-- default_statistics_target = 100
"""
}

# Python code for implementing PostgreSQL-specific repository methods
POSTGRES_REPOSITORY_METHODS = '''
    def search_documents_with_jsonb(self, metadata_query: Dict[str, Any]) -> List[Document]:
        """
        Search documents using PostgreSQL JSONB operators
        
        Args:
            metadata_query: Dictionary of metadata key-value pairs to search for
            
        Returns:
            List of matching documents
        """
        if DATABASE_TYPE != 'postgresql':
            raise ValueError("This method is only available for PostgreSQL")
        
        # Convert Python dict to JSONB query string
        jsonb_query = json.dumps(metadata_query)
        
        # Execute query using JSONB containment operator
        stmt = select(self.model).where(text(f"doc_metadata @> '{jsonb_query}'::jsonb"))
        result = self.db.execute(stmt).scalars().all()
        
        # Convert to Pydantic models
        return [sqlalchemy_document_to_pydantic(doc) for doc in result]
    
    def full_text_search_documents(self, query: str) -> List[Document]:
        """
        Search documents using PostgreSQL full-text search
        
        Args:
            query: Search query string
            
        Returns:
            List of matching documents
        """
        if DATABASE_TYPE != 'postgresql':
            raise ValueError("This method is only available for PostgreSQL")
        
        # Convert query to tsquery format
        ts_query = " & ".join(query.split())
        
        # Execute query using full-text search
        stmt = select(self.model).where(text(f"content_tsv @@ to_tsquery('english', '{ts_query}')"))
        result = self.db.execute(stmt).scalars().all()
        
        # Convert to Pydantic models
        return [sqlalchemy_document_to_pydantic(doc) for doc in result]
    
    def full_text_search_chunks(self, query: str, limit: int = 10) -> List[Chunk]:
        """
        Search chunks using PostgreSQL full-text search
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching chunks
        """
        if DATABASE_TYPE != 'postgresql':
            raise ValueError("This method is only available for PostgreSQL")
        
        # Convert query to tsquery format
        ts_query = " & ".join(query.split())
        
        # Execute query using full-text search with ranking
        stmt = text(f"""
            SELECT c.*, ts_rank(c.content_tsv, to_tsquery('english', :query)) AS rank
            FROM chunks c
            WHERE c.content_tsv @@ to_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(stmt, {"query": ts_query, "limit": limit}).all()
        
        # Convert to Pydantic models
        chunks = []
        for row in result:
            chunk = Chunk(
                id=str(row.id),
                content=row.content,
                metadata=row.chunk_metadata
            )
            chunks.append(chunk)
        
        return chunks
'''

# Connection pooling configuration for app/db/session.py
CONNECTION_POOLING_CONFIG = """
# Create SQLAlchemy engine with optimized connection pooling for PostgreSQL
if DATABASE_TYPE == 'postgresql':
    engine = create_engine(
        DATABASE_URL,
        pool_size=DATABASE_POOL_SIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,   # Recycle connections after 1 hour
        pool_timeout=30,     # Connection timeout
        pool_use_lifo=True,  # Use LIFO to improve locality of reference
        echo_pool=False      # Set to True for debugging connection pool
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=DATABASE_POOL_SIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600
    )
"""

# API endpoint for PostgreSQL-specific features
POSTGRES_API_ENDPOINT = '''
@router.get("/search/advanced", response_model=List[DocumentInfo])
async def advanced_search(
    query: str = Query(None, description="Full-text search query"),
    metadata: str = Query(None, description="JSON metadata query"),
    db: Session = Depends(get_db)
):
    """
    Advanced search endpoint using PostgreSQL-specific features
    """
    if DATABASE_TYPE != 'postgresql':
        raise HTTPException(
            status_code=400,
            detail="Advanced search is only available with PostgreSQL backend"
        )
    
    document_repository = DocumentRepository(db)
    results = []
    
    # Full-text search
    if query:
        results.extend(document_repository.full_text_search_documents(query))
    
    # JSONB metadata search
    if metadata:
        try:
            metadata_query = json.loads(metadata)
            results.extend(document_repository.search_documents_with_jsonb(metadata_query))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON in metadata query"
            )
    
    # Convert to DocumentInfo and deduplicate
    seen_ids = set()
    unique_results = []
    
    for doc in results:
        if doc.id not in seen_ids:
            seen_ids.add(doc.id)
            unique_results.append(DocumentInfo(
                id=doc.id,
                filename=doc.filename,
                chunk_count=len(doc.chunks) if hasattr(doc, 'chunks') else 0,
                metadata=doc.metadata,
                tags=doc.tags if hasattr(doc, 'tags') else [],
                folder=doc.folder,
                uploaded=doc.uploaded
            ))
    
    return unique_results
'''

def check_postgres_connection():
    """Check if PostgreSQL is available and configured"""
    if DATABASE_TYPE != 'postgresql':
        print("Current database is not PostgreSQL. These enhancements are only applicable to PostgreSQL.")
        return False
    
    try:
        # Try to connect to PostgreSQL
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print(f"Successfully connected to PostgreSQL at {DATABASE_URL}")
        return True
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return False

def apply_sql_enhancements(db, enhancement_name):
    """Apply SQL enhancements to the database"""
    print(f"Applying {enhancement_name} enhancements...")
    
    sql = POSTGRES_ENHANCEMENTS[enhancement_name]
    statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
    
    for stmt in statements:
        try:
            db.execute(stmt)
            db.commit()
            print(f"  Successfully executed: {stmt[:60]}...")
        except Exception as e:
            db.rollback()
            print(f"  Error executing statement: {e}")
            print(f"  Statement: {stmt}")

def modify_repository_file():
    """Add PostgreSQL-specific methods to document repository"""
    repo_file = os.path.join(project_root, "app", "db", "repositories", "document_repository.py")
    
    try:
        with open(repo_file, 'r') as f:
            content = f.read()
        
        # Check if methods already exist
        if "search_documents_with_jsonb" in content:
            print("PostgreSQL-specific repository methods already exist.")
            return
        
        # Find the end of the class definition
        import_section = "from app.db.adapters import sqlalchemy_document_to_pydantic, pydantic_document_to_sqlalchemy\n"
        if import_section not in content:
            import_section = "from app.db.adapters import "
        
        # Add imports if needed
        if "import json" not in content:
            content = content.replace(import_section, "import json\n" + import_section)
        
        if "from sqlalchemy import text" not in content:
            content = content.replace(import_section, "from sqlalchemy import text\n" + import_section)
        
        if "from app.core.config import DATABASE_TYPE" not in content:
            content = content.replace(import_section, "from app.core.config import DATABASE_TYPE\n" + import_section)
        
        # Find the end of the class definition
        class_end = content.rfind("}")
        if class_end == -1:
            class_end = content.rfind("return documents")
        
        if class_end != -1:
            # Insert new methods
            new_content = content[:class_end] + "\n" + POSTGRES_REPOSITORY_METHODS + "\n" + content[class_end:]
            
            # Write back to file
            with open(repo_file, 'w') as f:
                f.write(new_content)
            
            print(f"Added PostgreSQL-specific methods to {repo_file}")
        else:
            print(f"Could not find appropriate location to add methods in {repo_file}")
    
    except Exception as e:
        print(f"Error modifying repository file: {e}")

def modify_session_file():
    """Modify session.py to add connection pooling configuration"""
    session_file = os.path.join(project_root, "app", "db", "session.py")
    
    try:
        with open(session_file, 'r') as f:
            content = f.read()
        
        # Check if connection pooling config already exists
        if "pool_use_lifo=True" in content:
            print("Connection pooling configuration already exists.")
            return
        
        # Find the engine creation
        engine_creation = "engine = create_engine("
        if engine_creation in content:
            # Find the end of the engine creation
            engine_end = content.find(")", content.find(engine_creation))
            
            # Replace the engine creation with the new configuration
            new_content = content.replace(
                content[content.find(engine_creation):engine_end+1],
                CONNECTION_POOLING_CONFIG
            )
            
            # Write back to file
            with open(session_file, 'w') as f:
                f.write(new_content)
            
            print(f"Added connection pooling configuration to {session_file}")
        else:
            print(f"Could not find engine creation in {session_file}")
    
    except Exception as e:
        print(f"Error modifying session file: {e}")

def add_api_endpoint():
    """Add PostgreSQL-specific API endpoint"""
    api_file = os.path.join(project_root, "app", "api", "documents.py")
    
    try:
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check if endpoint already exists
        if "def advanced_search" in content:
            print("PostgreSQL-specific API endpoint already exists.")
            return
        
        # Find the imports
        import_section = "from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form, status\n"
        if import_section not in content:
            import_section = "from fastapi import "
        
        # Add imports if needed
        if "import json" not in content:
            content = content.replace(import_section, "import json\n" + import_section)
        
        if "from app.core.config import DATABASE_TYPE" not in content:
            content = content.replace(import_section, "from app.core.config import DATABASE_TYPE\n" + import_section)
        
        # Find the end of the file
        file_end = content.rfind("@router.delete")
        if file_end == -1:
            file_end = len(content)
        
        # Find the last route definition
        last_route = content.rfind("@router")
        if last_route != -1:
            # Find the end of the last route function
            last_route_end = content.find("\n\n", last_route)
            if last_route_end == -1:
                last_route_end = len(content)
            
            # Insert new endpoint
            new_content = content[:last_route_end] + "\n\n" + POSTGRES_API_ENDPOINT + content[last_route_end:]
            
            # Write back to file
            with open(api_file, 'w') as f:
                f.write(new_content)
            
            print(f"Added PostgreSQL-specific API endpoint to {api_file}")
        else:
            print(f"Could not find appropriate location to add endpoint in {api_file}")
    
    except Exception as e:
        print(f"Error adding API endpoint: {e}")

def create_migration_script():
    """Create a migration script for PostgreSQL enhancements"""
    migrations_dir = os.path.join(project_root, "alembic", "versions")
    os.makedirs(migrations_dir, exist_ok=True)
    
    # Create a new migration file
    timestamp = int(time.time())
    migration_file = os.path.join(migrations_dir, f"postgres_enhancements_{timestamp}.py")
    
    migration_content = f"""\"\"\"PostgreSQL enhancements

Revision ID: postgres_enhancements_{timestamp}
Revises: 
Create Date: {datetime.datetime.now().isoformat()}

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from app.core.config import DATABASE_TYPE

# revision identifiers, used by Alembic.
revision = 'postgres_enhancements_{timestamp}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Skip if not PostgreSQL
    if DATABASE_TYPE != 'postgresql':
        return
    
    # Add tsvector columns for full-text search
    op.add_column('documents', sa.Column('content_tsv', TSVECTOR))
    op.add_column('chunks', sa.Column('content_tsv', TSVECTOR))
    
    # Create GIN indexes for JSONB operators
    op.execute(\"\"\"
    CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin ON documents USING GIN (metadata);
    CREATE INDEX IF NOT EXISTS idx_chunks_metadata_gin ON chunks USING GIN (metadata);
    \"\"\")
    
    # Create GIN indexes for full-text search
    op.execute(\"\"\"
    CREATE INDEX IF NOT EXISTS idx_documents_content_tsv ON documents USING GIN (content_tsv);
    CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv ON chunks USING GIN (content_tsv);
    \"\"\")
    
    # Create update triggers for tsvector columns
    op.execute(\"\"\"
    CREATE OR REPLACE FUNCTION documents_tsvector_update_trigger() RETURNS trigger AS $$
    BEGIN
      NEW.content_tsv := to_tsvector('english', coalesce(NEW.content, ''));
      RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    
    CREATE OR REPLACE FUNCTION chunks_tsvector_update_trigger() RETURNS trigger AS $$
    BEGIN
      NEW.content_tsv := to_tsvector('english', coalesce(NEW.content, ''));
      RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS documents_tsvector_update ON documents;
    CREATE TRIGGER documents_tsvector_update BEFORE INSERT OR UPDATE
    ON documents FOR EACH ROW EXECUTE FUNCTION documents_tsvector_update_trigger();
    
    DROP TRIGGER IF EXISTS chunks_tsvector_update ON chunks;
    CREATE TRIGGER chunks_tsvector_update BEFORE INSERT OR UPDATE
    ON chunks FOR EACH ROW EXECUTE FUNCTION chunks_tsvector_update_trigger();
    \"\"\")
    
    # Add additional indexes for common query patterns
    op.create_index('idx_documents_filename_folder', 'documents', ['filename', 'folder'])
    op.create_index('idx_documents_uploaded', 'documents', ['uploaded'])
    op.create_index('idx_chunks_document_id_index', 'chunks', ['document_id', 'index'])
    
    # Add partial indexes for common filters
    op.execute(\"\"\"
    CREATE INDEX IF NOT EXISTS idx_documents_processing_status_pending ON documents (id) 
    WHERE processing_status = 'pending';
    
    CREATE INDEX IF NOT EXISTS idx_documents_processing_status_completed ON documents (id) 
    WHERE processing_status = 'completed';
    \"\"\")
    
    # Add index for document type filtering
    op.execute(\"\"\"
    CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents ((metadata->>'file_type'));
    \"\"\")
    
    # Add index for tag filtering
    op.execute(\"\"\"
    CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN ((metadata->'tags_list'));
    \"\"\")


def downgrade():
    # Skip if not PostgreSQL
    if DATABASE_TYPE != 'postgresql':
        return
    
    # Drop triggers
    op.execute(\"\"\"
    DROP TRIGGER IF EXISTS documents_tsvector_update ON documents;
    DROP TRIGGER IF EXISTS chunks_tsvector_update ON chunks;
    DROP FUNCTION IF EXISTS documents_tsvector_update_trigger();
    DROP FUNCTION IF EXISTS chunks_tsvector_update_trigger();
    \"\"\")
    
    # Drop indexes
    op.execute(\"\"\"
    DROP INDEX IF EXISTS idx_documents_metadata_gin;
    DROP INDEX IF EXISTS idx_chunks_metadata_gin;
    DROP INDEX IF EXISTS idx_documents_content_tsv;
    DROP INDEX IF EXISTS idx_chunks_content_tsv;
    DROP INDEX IF EXISTS idx_documents_filename_folder;
    DROP INDEX IF EXISTS idx_documents_uploaded;
    DROP INDEX IF EXISTS idx_chunks_document_id_index;
    DROP INDEX IF EXISTS idx_documents_processing_status_pending;
    DROP INDEX IF EXISTS idx_documents_processing_status_completed;
    DROP INDEX IF EXISTS idx_documents_file_type;
    DROP INDEX IF EXISTS idx_documents_tags;
    \"\"\")
    
    # Drop columns
    op.drop_column('documents', 'content_tsv')
    op.drop_column('chunks', 'content_tsv')
"""
    
    try:
        with open(migration_file, 'w') as f:
            f.write(migration_content)
        
        print(f"Created migration script: {migration_file}")
    except Exception as e:
        print(f"Error creating migration script: {e}")

def create_postgres_config_guide():
    """Create a guide for PostgreSQL configuration"""
    guide_file = os.path.join(project_root, "docs", "deployment", "postgresql_optimization.md")
    os.makedirs(os.path.dirname(guide_file), exist_ok=True)
    
    guide_content = """# PostgreSQL Optimization Guide for Metis RAG

This guide provides recommendations for optimizing PostgreSQL for use with the Metis RAG system.

## Connection Pooling

The Metis RAG system uses SQLAlchemy's built-in connection pooling, which is configured in `app/db/session.py`. The following settings are used:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,  # Default: 5
    max_overflow=DATABASE_MAX_OVERFLOW,  # Default: 10
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_timeout=30,     # Connection timeout
    pool_use_lifo=True,  # Use LIFO to improve locality of reference
)
```

For production deployments, you may want to adjust these settings based on your expected load:

- `pool_size`: The number of connections to keep open in the pool. For high-traffic applications, increase this to 10-20.
- `max_overflow`: The maximum number of connections to create beyond the pool size. For high-traffic applications, increase this to 20-30.
- `pool_recycle`: The number of seconds after which a connection is recycled. The default of 3600 (1 hour) is usually appropriate.

## PostgreSQL Configuration

For optimal performance, consider the following settings in your `postgresql.conf` file:

```
# Connection settings
max_connections = 100

# Memory settings
shared_buffers = 256MB  # 25% of available RAM, up to 8GB
effective_cache_size = 768MB  # 75% of available RAM
work_mem = 8MB  # Increase for complex queries
maintenance_work_mem = 64MB  # Increase for maintenance operations

# Parallel query settings
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# Cost-based optimizer settings
random_page_cost = 1.1  # For SSDs
effective_io_concurrency = 200  # For SSDs

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Query planning
default_statistics_target = 100
```

Adjust these settings based on your server's available resources.

## JSONB Operators

PostgreSQL's JSONB type provides powerful operators for querying JSON data. The Metis RAG system uses JSONB for storing document and chunk metadata.

Example queries:

```sql
-- Find documents with a specific file type
SELECT * FROM documents WHERE metadata @> '{"file_type": "pdf"}'::jsonb;

-- Find chunks with specific tags
SELECT * FROM chunks WHERE metadata @> '{"tags": ["important"]}'::jsonb;

-- Find documents with a specific metadata field
SELECT * FROM documents WHERE metadata ? 'author';

-- Find documents with a specific metadata value
SELECT * FROM documents WHERE metadata->>'status' = 'processed';
```

## Full-Text Search

PostgreSQL's full-text search capabilities are used for searching document and chunk content.

Example queries:

```sql
-- Search for documents containing specific terms
SELECT * FROM documents 
WHERE content_tsv @@ to_tsquery('english', 'search & terms');

-- Search for chunks containing specific terms, ranked by relevance
SELECT c.*, ts_rank(c.content_tsv, to_tsquery('english', 'search & terms')) AS rank
FROM chunks c
WHERE c.content_tsv @@ to_tsquery('english', 'search & terms')
ORDER BY rank DESC
LIMIT 10;
```

## Indexes

The following indexes are created to optimize common query patterns:

- GIN indexes on JSONB metadata fields for efficient metadata queries
- GIN indexes on tsvector columns for efficient full-text search
- B-tree indexes on common query fields (filename, folder, uploaded)
- Partial indexes for filtering by processing status
- Expression indexes for filtering by file type and tags

## API Endpoints

The PostgreSQL-specific features are exposed through the following API endpoints:

- `GET /api/documents/search/advanced`: Advanced search using full-text search and JSONB operators

Example usage:

```
GET /api/documents/search/advanced?query=important%20information&metadata={"file_type":"pdf","tags":["important"]}
```

## Monitoring

For monitoring PostgreSQL performance, consider using the following tools:

- pg_stat_statements: For tracking query performance
- pgBadger: For analyzing PostgreSQL logs
- pgAdmin: For general PostgreSQL administration and monitoring

## Maintenance

Regular maintenance tasks:

- VACUUM ANALYZE: To update statistics and reclaim space
- REINDEX: To rebuild indexes for optimal performance
- pg_dump: For regular backups

Consider setting up automated maintenance tasks using cron or a similar scheduler.
"""
    
    try:
        with open(guide_file, 'w') as f:
            f.write(guide_content)
        
        print(f"Created PostgreSQL optimization guide: {guide_file}")
    except Exception as e:
        print(f"Error creating guide: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="PostgreSQL-Specific Enhancements for Metis RAG")
    parser.add_argument("--apply", action="store_true", help="Apply the enhancements")
    args = parser.parse_args()
    
    print("PostgreSQL-Specific Enhancements for Metis RAG")
    print("==============================================")
    
    # Check if PostgreSQL is available
    if not check_postgres_connection():
        print("\nSkipping enhancements as PostgreSQL is not available.")
        return 1
    
    if args.apply:
        print("\nApplying PostgreSQL enhancements...")
        
        # Apply SQL enhancements
        db = SessionLocal()
        try:
            for enhancement in POSTGRES_ENHANCEMENTS:
                apply_sql_enhancements(db, enhancement)
        finally:
            db.close()
        
        # Modify repository file
        modify_repository_file()
        
        # Modify session file
        modify_session_file()
        
        # Add API endpoint
        add_api_endpoint()
        
        # Create migration script
        create_migration_script()
        
        # Create PostgreSQL configuration guide
        create_postgres_config_guide()
        
        print("\nPostgreSQL enhancements applied successfully!")
    else:
        print("\nThis script will apply the following enhancements:")
        print("  1. Add JSONB operators for metadata queries")
        print("  2. Add full-text search capabilities")
        print("  3. Optimize connection pooling")
        print("  4. Add index optimizations")
        print("  5. Add PostgreSQL-specific repository methods")
        print("  6. Add PostgreSQL-specific API endpoints")
        print("  7. Create a migration script")
        print("  8. Create a PostgreSQL configuration guide")
        print("\nRun with --apply to apply these enhancements.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())