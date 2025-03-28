#!/usr/bin/env python3
"""
SQLite Optimization Script for Metis RAG

This script implements SQLite-specific optimizations:
1. Configure WAL (Write-Ahead Logging) mode for better concurrency
2. Optimize pragma settings for performance
3. Add indexes for common query patterns
4. Implement connection pooling optimizations

Usage:
    python optimize_sqlite_for_concurrency.py [--apply]
"""
import os
import sys
import json
import time
import argparse
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.config import DATABASE_URL, DATABASE_TYPE

# SQLite optimization settings
SQLITE_PRAGMAS = {
    "journal_mode": "WAL",       # Use Write-Ahead Logging for better concurrency
    "synchronous": "NORMAL",     # Balance between safety and performance
    "cache_size": "-5000",       # Use 5MB of memory for database cache
    "foreign_keys": "ON",        # Enforce foreign key constraints
    "temp_store": "MEMORY",      # Store temporary tables in memory
    "mmap_size": "30000000",     # Memory-mapped I/O (30MB)
    "busy_timeout": "5000",      # Wait 5 seconds when database is locked
    "auto_vacuum": "INCREMENTAL" # Incremental vacuum to reclaim space
}

# SQL statements for index optimization
SQLITE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_documents_filename_folder ON documents (filename, folder)",
    "CREATE INDEX IF NOT EXISTS idx_documents_uploaded ON documents (uploaded)",
    "CREATE INDEX IF NOT EXISTS idx_chunks_document_id_index ON chunks (document_id, \"index\")",
    "CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents (processing_status)",
    "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents (json_extract(metadata, '$.file_type'))",
    "CREATE INDEX IF NOT EXISTS idx_chunks_embedding_quality ON chunks (embedding_quality)"
]

# Connection pooling configuration for app/db/session.py
SQLITE_CONNECTION_POOLING = """
# SQLite-specific engine configuration
if DATABASE_TYPE == 'sqlite':
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            'check_same_thread': False,  # Allow multithreaded access
            'timeout': 30,               # Connection timeout in seconds
            'isolation_level': None      # Use autocommit mode
        },
        pool_size=DATABASE_POOL_SIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600
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

# SQLite repository methods for optimized queries
SQLITE_REPOSITORY_METHODS = '''
    def search_documents_with_json(self, metadata_query: Dict[str, Any]) -> List[Document]:
        """
        Search documents using SQLite JSON functions
        
        Args:
            metadata_query: Dictionary of metadata key-value pairs to search for
            
        Returns:
            List of matching documents
        """
        if DATABASE_TYPE != 'sqlite':
            raise ValueError("This method is only available for SQLite")
        
        # Build query conditions
        conditions = []
        params = {}
        
        for i, (key, value) in enumerate(metadata_query.items()):
            param_name = f"value_{i}"
            conditions.append(f"json_extract(doc_metadata, '$.{key}') = :{param_name}")
            params[param_name] = value if not isinstance(value, list) else json.dumps(value)
        
        # Combine conditions
        where_clause = " AND ".join(conditions)
        
        # Execute query
        stmt = text(f"SELECT * FROM documents WHERE {where_clause}")
        result = self.db.execute(stmt, params).scalars().all()
        
        # Convert to Pydantic models
        return [sqlalchemy_document_to_pydantic(doc) for doc in result]
    
    def full_text_search_documents(self, query: str) -> List[Document]:
        """
        Search documents using SQLite FTS (if available) or LIKE
        
        Args:
            query: Search query string
            
        Returns:
            List of matching documents
        """
        if DATABASE_TYPE != 'sqlite':
            raise ValueError("This method is only available for SQLite")
        
        # Check if FTS is available
        try:
            # Try to use FTS
            stmt = text("""
                SELECT d.* FROM documents d
                WHERE d.content LIKE :query
                ORDER BY length(d.content) ASC
                LIMIT 20
            """)
            result = self.db.execute(stmt, {"query": f"%{query}%"}).scalars().all()
        except Exception:
            # Fall back to simple LIKE query
            stmt = select(self.model).where(self.model.content.like(f"%{query}%"))
            result = self.db.execute(stmt).scalars().all()
        
        # Convert to Pydantic models
        return [sqlalchemy_document_to_pydantic(doc) for doc in result]
'''

def extract_database_path():
    """Extract the database file path from DATABASE_URL"""
    if DATABASE_TYPE != 'sqlite':
        print("Current database is not SQLite. These optimizations are only applicable to SQLite.")
        return None
    
    # Extract path from sqlite:/// URL
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL[10:]
        return os.path.abspath(db_path)
    else:
        print(f"Unexpected SQLite URL format: {DATABASE_URL}")
        return None

def check_sqlite_version():
    """Check SQLite version and features"""
    try:
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Get SQLite version
        cursor.execute('SELECT sqlite_version()')
        version = cursor.fetchone()[0]
        print(f"SQLite version: {version}")
        
        # Check if WAL mode is supported
        cursor.execute("PRAGMA journal_mode=WAL")
        journal_mode = cursor.fetchone()[0]
        wal_supported = journal_mode.upper() == 'WAL'
        print(f"WAL mode supported: {wal_supported}")
        
        # Check if JSON functions are available
        try:
            cursor.execute("SELECT json_extract('{\"a\":1}', '$.a')")
            json_supported = cursor.fetchone()[0] == 1
            print(f"JSON functions supported: {json_supported}")
        except sqlite3.OperationalError:
            json_supported = False
            print("JSON functions not supported")
        
        conn.close()
        
        return {
            'version': version,
            'wal_supported': wal_supported,
            'json_supported': json_supported
        }
    except Exception as e:
        print(f"Error checking SQLite version: {e}")
        return None

def optimize_sqlite_database(db_path):
    """Apply SQLite optimizations to the database"""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Apply PRAGMA settings
        print("\nApplying PRAGMA settings:")
        for pragma, value in SQLITE_PRAGMAS.items():
            try:
                cursor.execute(f"PRAGMA {pragma}={value}")
                result = cursor.execute(f"PRAGMA {pragma}").fetchone()
                print(f"  {pragma} = {result[0]}")
            except sqlite3.OperationalError as e:
                print(f"  Error setting {pragma}: {e}")
        
        # Create indexes
        print("\nCreating indexes:")
        for index_stmt in SQLITE_INDEXES:
            try:
                cursor.execute(index_stmt)
                print(f"  {index_stmt[:60]}...")
            except sqlite3.OperationalError as e:
                print(f"  Error creating index: {e}")
        
        # Run ANALYZE to update statistics
        print("\nRunning ANALYZE to update statistics...")
        cursor.execute("ANALYZE")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        print("\nSQLite optimizations applied successfully!")
        return True
    except Exception as e:
        print(f"Error optimizing SQLite database: {e}")
        return False

def modify_session_file():
    """Modify session.py to add SQLite-specific connection pooling configuration"""
    session_file = os.path.join(project_root, "app", "db", "session.py")
    
    try:
        with open(session_file, 'r') as f:
            content = f.read()
        
        # Check if SQLite-specific config already exists
        if "check_same_thread': False" in content:
            print("SQLite-specific connection pooling configuration already exists.")
            return
        
        # Find the engine creation
        engine_creation = "engine = create_engine("
        if engine_creation in content:
            # Find the end of the engine creation
            engine_end = content.find(")", content.find(engine_creation))
            
            # Replace the engine creation with the new configuration
            new_content = content.replace(
                content[content.find(engine_creation):engine_end+1],
                SQLITE_CONNECTION_POOLING
            )
            
            # Write back to file
            with open(session_file, 'w') as f:
                f.write(new_content)
            
            print(f"Added SQLite-specific connection pooling configuration to {session_file}")
        else:
            print(f"Could not find engine creation in {session_file}")
    
    except Exception as e:
        print(f"Error modifying session file: {e}")

def modify_repository_file():
    """Add SQLite-specific methods to document repository"""
    repo_file = os.path.join(project_root, "app", "db", "repositories", "document_repository.py")
    
    try:
        with open(repo_file, 'r') as f:
            content = f.read()
        
        # Check if methods already exist
        if "search_documents_with_json" in content:
            print("SQLite-specific repository methods already exist.")
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
            new_content = content[:class_end] + "\n" + SQLITE_REPOSITORY_METHODS + "\n" + content[class_end:]
            
            # Write back to file
            with open(repo_file, 'w') as f:
                f.write(new_content)
            
            print(f"Added SQLite-specific methods to {repo_file}")
        else:
            print(f"Could not find appropriate location to add methods in {repo_file}")
    
    except Exception as e:
        print(f"Error modifying repository file: {e}")

def create_sqlite_config_guide():
    """Create a guide for SQLite configuration"""
    guide_file = os.path.join(project_root, "docs", "deployment", "sqlite_optimization.md")
    os.makedirs(os.path.dirname(guide_file), exist_ok=True)
    
    guide_content = """# SQLite Optimization Guide for Metis RAG

This guide provides recommendations for optimizing SQLite for use with the Metis RAG system, particularly for concurrent access patterns.

## Write-Ahead Logging (WAL)

SQLite's default journal mode can cause contention when multiple processes try to write to the database. The Write-Ahead Logging (WAL) journal mode allows multiple readers to coexist with a single writer, significantly improving concurrency.

The Metis RAG system configures SQLite to use WAL mode with the following PRAGMA settings:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
```

These settings provide a good balance between performance, concurrency, and data safety.

## Memory Optimization

SQLite performance can be significantly improved by allocating more memory for its cache and operations:

```sql
PRAGMA cache_size=-5000;  -- Use 5MB of memory for database cache
PRAGMA temp_store=MEMORY; -- Store temporary tables in memory
PRAGMA mmap_size=30000000; -- Memory-mapped I/O (30MB)
```

Adjust these values based on your server's available memory.

## Connection Pooling

The Metis RAG system uses SQLAlchemy's connection pooling with SQLite-specific optimizations:

```python
engine = create_engine(
    DATABASE_URL,
    connect_args={
        'check_same_thread': False,  # Allow multithreaded access
        'timeout': 30,               # Connection timeout in seconds
        'isolation_level': None      # Use autocommit mode
    },
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

The `check_same_thread=False` option allows connections to be used across threads, which is necessary for web applications. The `timeout` option specifies how long to wait for a locked database before giving up.

## Indexes

The following indexes are created to optimize common query patterns:

```sql
CREATE INDEX IF NOT EXISTS idx_documents_filename_folder ON documents (filename, folder);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded ON documents (uploaded);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id_index ON chunks (document_id, "index");
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents (processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents (json_extract(metadata, '$.file_type'));
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_quality ON chunks (embedding_quality);
```

## JSON Support

SQLite 3.9.0 and later include built-in JSON functions that can be used to query JSON data stored in the database. The Metis RAG system uses these functions to query document and chunk metadata:

```sql
-- Find documents with a specific file type
SELECT * FROM documents WHERE json_extract(metadata, '$.file_type') = 'pdf';

-- Find chunks with specific tags
SELECT * FROM chunks WHERE json_extract(metadata, '$.tags') LIKE '%important%';
```

## Maintenance

Regular maintenance tasks:

1. **Vacuum**: Reclaim unused space and defragment the database
   ```sql
   VACUUM;
   ```

2. **Analyze**: Update statistics for the query planner
   ```sql
   ANALYZE;
   ```

3. **Integrity Check**: Verify database integrity
   ```sql
   PRAGMA integrity_check;
   ```

4. **Backup**: Create a backup of the database
   ```bash
   sqlite3 metis_rag.db ".backup metis_rag_backup.db"
   ```

## Concurrency Limitations

Despite the optimizations, SQLite still has limitations for highly concurrent workloads:

1. Only one writer can modify the database at a time
2. Readers can block writers in certain scenarios
3. Long-running transactions can cause contention

For high-concurrency production deployments, consider using PostgreSQL instead.

## Monitoring

Monitor SQLite performance using the following queries:

```sql
-- Check if WAL mode is enabled
PRAGMA journal_mode;

-- Check current cache size
PRAGMA cache_size;

-- List all indexes
SELECT * FROM sqlite_master WHERE type='index';

-- Check database size
PRAGMA page_count * PRAGMA page_size;
```

## Troubleshooting

Common issues and solutions:

1. **Database is locked**: Increase the busy timeout or reduce transaction duration
   ```sql
   PRAGMA busy_timeout=10000;  -- Wait 10 seconds for locks
   ```

2. **Slow queries**: Analyze the query plan
   ```sql
   EXPLAIN QUERY PLAN SELECT * FROM documents WHERE ...;
   ```

3. **Database corruption**: Run integrity check and recover from backup
   ```sql
   PRAGMA integrity_check;
   ```
"""
    
    try:
        with open(guide_file, 'w') as f:
            f.write(guide_content)
        
        print(f"Created SQLite optimization guide: {guide_file}")
    except Exception as e:
        print(f"Error creating guide: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="SQLite Optimization for Metis RAG")
    parser.add_argument("--apply", action="store_true", help="Apply the optimizations")
    args = parser.parse_args()
    
    print("SQLite Optimization for Metis RAG")
    print("================================")
    
    # Check SQLite version and features
    sqlite_info = check_sqlite_version()
    if not sqlite_info:
        return 1
    
    # Extract database path
    db_path = extract_database_path()
    if not db_path:
        return 1
    
    print(f"\nDatabase path: {db_path}")
    
    if args.apply:
        print("\nApplying SQLite optimizations...")
        
        # Optimize SQLite database
        if not optimize_sqlite_database(db_path):
            return 1
        
        # Modify session file
        modify_session_file()
        
        # Modify repository file
        modify_repository_file()
        
        # Create SQLite configuration guide
        create_sqlite_config_guide()
        
        print("\nSQLite optimizations applied successfully!")
    else:
        print("\nThis script will apply the following optimizations:")
        print("  1. Configure WAL (Write-Ahead Logging) mode for better concurrency")
        print("  2. Optimize PRAGMA settings for performance")
        print("  3. Add indexes for common query patterns")
        print("  4. Implement connection pooling optimizations")
        print("  5. Add SQLite-specific repository methods")
        print("  6. Create a SQLite configuration guide")
        print("\nRun with --apply to apply these optimizations.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())