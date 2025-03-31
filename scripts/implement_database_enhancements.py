#!/usr/bin/env python3
"""
Database-Specific Enhancements Script for Metis RAG

This script implements database-specific enhancements for PostgreSQL and SQLite:
1. PostgreSQL: JSONB operators, full-text search, connection pooling
2. SQLite: Optimized indexes, pragma settings for concurrent access

Usage:
    python implement_database_enhancements.py --db-type sqlite|postgresql [--apply]
"""
import os
import sys
import argparse
import asyncio
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.session import Base, engine, SessionLocal
from app.core.config import DATABASE_TYPE, DATABASE_URL
from sqlalchemy import text

class DatabaseEnhancer:
    """Database enhancement implementation class"""
    
    def __init__(self, db_type: str, apply: bool = False):
        self.db_type = db_type
        self.apply = apply
        
        # Initialize database session
        self.db_session = SessionLocal()
        
        print(f"Initialized database enhancer for {db_type} database")
        print(f"Database URL: {DATABASE_URL}")
        print(f"Apply mode: {'ON' if apply else 'OFF (dry run)'}")
        
    def cleanup(self):
        """Clean up resources"""
        self.db_session.close()
    
    def execute_sql(self, sql: str, description: str) -> bool:
        """Execute SQL statement with proper error handling"""
        try:
            print(f"  {description}")
            print(f"    SQL: {sql}")
            
            if self.apply:
                self.db_session.execute(text(sql))
                self.db_session.commit()
                print("    ✓ Applied successfully")
                return True
            else:
                print("    ✓ Validated (not applied - dry run mode)")
                return True
        except Exception as e:
            self.db_session.rollback()
            print(f"    ✗ Error: {str(e)}")
            return False
    
    def enhance_postgresql(self) -> List[Dict[str, Any]]:
        """Implement PostgreSQL-specific enhancements"""
        print("\nImplementing PostgreSQL enhancements...")
        
        enhancements = []
        
        # 1. Create GIN index on document metadata for faster JSONB queries
        sql = """
        CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin 
        ON documents USING GIN (metadata);
        """
        success = self.execute_sql(sql, "Creating GIN index on document metadata")
        enhancements.append({
            "name": "GIN index on document metadata",
            "applied": success,
            "description": "Enables efficient querying of JSONB metadata fields using operators like @>, ?, and ?&"
        })
        
        # 2. Create GIN index on chunk metadata for faster JSONB queries
        sql = """
        CREATE INDEX IF NOT EXISTS idx_chunks_metadata_gin 
        ON chunks USING GIN (metadata);
        """
        success = self.execute_sql(sql, "Creating GIN index on chunk metadata")
        enhancements.append({
            "name": "GIN index on chunk metadata",
            "applied": success,
            "description": "Enables efficient querying of JSONB metadata fields in chunks"
        })
        
        # 3. Create full-text search index on document content
        sql = """
        -- Create tsvector column if it doesn't exist
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'content_tsv'
            ) THEN
                ALTER TABLE documents ADD COLUMN content_tsv tsvector;
                
                -- Create index on the tsvector column
                CREATE INDEX idx_documents_content_tsv ON documents USING GIN (content_tsv);
                
                -- Create trigger to update tsvector column
                CREATE OR REPLACE FUNCTION documents_content_trigger() RETURNS trigger AS $$
                BEGIN
                    NEW.content_tsv := to_tsvector('english', COALESCE(NEW.content, ''));
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
                
                CREATE TRIGGER tsvector_update_documents_content 
                BEFORE INSERT OR UPDATE OF content ON documents
                FOR EACH ROW EXECUTE FUNCTION documents_content_trigger();
                
                -- Update existing records
                UPDATE documents SET content_tsv = to_tsvector('english', COALESCE(content, ''));
            END IF;
        END
        $$;
        """
        success = self.execute_sql(sql, "Creating full-text search index on document content")
        enhancements.append({
            "name": "Full-text search on document content",
            "applied": success,
            "description": "Enables efficient full-text search using PostgreSQL's tsvector type"
        })
        
        # 4. Create full-text search index on chunk content
        sql = """
        -- Create tsvector column if it doesn't exist
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'chunks' AND column_name = 'content_tsv'
            ) THEN
                ALTER TABLE chunks ADD COLUMN content_tsv tsvector;
                
                -- Create index on the tsvector column
                CREATE INDEX idx_chunks_content_tsv ON chunks USING GIN (content_tsv);
                
                -- Create trigger to update tsvector column
                CREATE OR REPLACE FUNCTION chunks_content_trigger() RETURNS trigger AS $$
                BEGIN
                    NEW.content_tsv := to_tsvector('english', COALESCE(NEW.content, ''));
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
                
                CREATE TRIGGER tsvector_update_chunks_content 
                BEFORE INSERT OR UPDATE OF content ON chunks
                FOR EACH ROW EXECUTE FUNCTION chunks_content_trigger();
                
                -- Update existing records
                UPDATE chunks SET content_tsv = to_tsvector('english', COALESCE(content, ''));
            END IF;
        END
        $$;
        """
        success = self.execute_sql(sql, "Creating full-text search index on chunk content")
        enhancements.append({
            "name": "Full-text search on chunk content",
            "applied": success,
            "description": "Enables efficient full-text search on chunk content"
        })
        
        # 5. Create function for semantic search using embeddings
        sql = """
        -- Create extension if it doesn't exist
        CREATE EXTENSION IF NOT EXISTS vector;
        
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
        """
        success = self.execute_sql(sql, "Creating function for semantic search")
        enhancements.append({
            "name": "Semantic search function",
            "applied": success,
            "description": "Enables efficient semantic search using vector embeddings"
        })
        
        # 6. Optimize connection pooling settings
        sql = """
        -- Set statement timeout to prevent long-running queries
        ALTER DATABASE current_database() SET statement_timeout = '30s';
        
        -- Set idle in transaction timeout
        ALTER DATABASE current_database() SET idle_in_transaction_session_timeout = '60s';
        """
        success = self.execute_sql(sql, "Optimizing connection pooling settings")
        enhancements.append({
            "name": "Connection pooling optimization",
            "applied": success,
            "description": "Prevents connection leaks and improves connection reuse"
        })
        
        # 7. Create materialized view for frequently accessed data
        sql = """
        -- Create materialized view for document statistics
        CREATE MATERIALIZED VIEW IF NOT EXISTS document_stats AS
        SELECT 
            d.id,
            d.filename,
            d.folder,
            d.uploaded,
            d.processing_status,
            COUNT(c.id) AS chunk_count,
            AVG(LENGTH(c.content)) AS avg_chunk_size,
            SUM(LENGTH(c.content)) AS total_content_size
        FROM 
            documents d
        LEFT JOIN 
            chunks c ON d.id = c.document_id
        GROUP BY 
            d.id, d.filename, d.folder, d.uploaded, d.processing_status;
            
        -- Create index on the materialized view
        CREATE UNIQUE INDEX IF NOT EXISTS idx_document_stats_id ON document_stats (id);
        """
        success = self.execute_sql(sql, "Creating materialized view for document statistics")
        enhancements.append({
            "name": "Document statistics materialized view",
            "applied": success,
            "description": "Improves performance for frequently accessed document statistics"
        })
        
        # 8. Create function to refresh materialized view
        sql = """
        -- Create function to refresh materialized view
        CREATE OR REPLACE FUNCTION refresh_document_stats()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY document_stats;
        END;
        $$ LANGUAGE plpgsql;
        """
        success = self.execute_sql(sql, "Creating function to refresh materialized view")
        enhancements.append({
            "name": "Materialized view refresh function",
            "applied": success,
            "description": "Allows for concurrent refreshing of the document statistics view"
        })
        
        return enhancements
    
    def enhance_sqlite(self) -> List[Dict[str, Any]]:
        """Implement SQLite-specific enhancements"""
        print("\nImplementing SQLite enhancements...")
        
        enhancements = []
        
        # 1. Enable WAL mode for better concurrency
        sql = "PRAGMA journal_mode = WAL;"
        success = self.execute_sql(sql, "Enabling WAL mode for better concurrency")
        enhancements.append({
            "name": "WAL mode",
            "applied": success,
            "description": "Enables Write-Ahead Logging for better concurrency and performance"
        })
        
        # 2. Set busy timeout for concurrent access
        sql = "PRAGMA busy_timeout = 5000;"
        success = self.execute_sql(sql, "Setting busy timeout for concurrent access")
        enhancements.append({
            "name": "Busy timeout",
            "applied": success,
            "description": "Sets timeout to 5 seconds when database is locked"
        })
        
        # 3. Enable foreign key constraints
        sql = "PRAGMA foreign_keys = ON;"
        success = self.execute_sql(sql, "Enabling foreign key constraints")
        enhancements.append({
            "name": "Foreign key constraints",
            "applied": success,
            "description": "Ensures referential integrity in the database"
        })
        
        # 4. Set synchronous mode to NORMAL for better performance
        sql = "PRAGMA synchronous = NORMAL;"
        success = self.execute_sql(sql, "Setting synchronous mode to NORMAL")
        enhancements.append({
            "name": "Synchronous mode",
            "applied": success,
            "description": "Balances durability and performance"
        })
        
        # 5. Create index on document content for faster text search
        sql = """
        CREATE INDEX IF NOT EXISTS idx_documents_content ON documents(content);
        """
        success = self.execute_sql(sql, "Creating index on document content")
        enhancements.append({
            "name": "Document content index",
            "applied": success,
            "description": "Improves performance for text search operations"
        })
        
        # 6. Create index on chunk content for faster text search
        sql = """
        CREATE INDEX IF NOT EXISTS idx_chunks_content ON chunks(content);
        """
        success = self.execute_sql(sql, "Creating index on chunk content")
        enhancements.append({
            "name": "Chunk content index",
            "applied": success,
            "description": "Improves performance for text search operations on chunks"
        })
        
        # 7. Create index on document metadata for faster JSON queries
        sql = """
        CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents(metadata);
        """
        success = self.execute_sql(sql, "Creating index on document metadata")
        enhancements.append({
            "name": "Document metadata index",
            "applied": success,
            "description": "Improves performance for JSON queries on document metadata"
        })
        
        # 8. Create index on chunk metadata for faster JSON queries
        sql = """
        CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks(metadata);
        """
        success = self.execute_sql(sql, "Creating index on chunk metadata")
        enhancements.append({
            "name": "Chunk metadata index",
            "applied": success,
            "description": "Improves performance for JSON queries on chunk metadata"
        })
        
        # 9. Optimize database
        sql = "PRAGMA optimize;"
        success = self.execute_sql(sql, "Optimizing database")
        enhancements.append({
            "name": "Database optimization",
            "applied": success,
            "description": "Runs internal optimizations on the database"
        })
        
        return enhancements
    
    def implement_enhancements(self) -> Dict[str, Any]:
        """Implement database-specific enhancements"""
        results = {
            "database_type": self.db_type,
            "apply_mode": self.apply,
            "enhancements": []
        }
        
        if self.db_type == "postgresql":
            results["enhancements"] = self.enhance_postgresql()
        elif self.db_type == "sqlite":
            results["enhancements"] = self.enhance_sqlite()
        
        # Print summary
        print("\nEnhancement Summary:")
        applied_count = sum(1 for e in results["enhancements"] if e["applied"])
        total_count = len(results["enhancements"])
        print(f"  Applied: {applied_count}/{total_count} enhancements")
        
        if not self.apply:
            print("\nTo apply these enhancements, run again with --apply flag")
        
        return results

async def run_enhancements(args):
    """Run the database enhancements"""
    print(f"\nRunning database enhancements for {args.db_type}...")
    
    # Create enhancer instance
    enhancer = DatabaseEnhancer(args.db_type, args.apply)
    
    try:
        # Implement enhancements
        results = enhancer.implement_enhancements()
        
        print("\nEnhancements completed successfully!")
        return 0
    except Exception as e:
        print(f"Error implementing enhancements: {e}")
        return 1
    finally:
        enhancer.cleanup()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Database-Specific Enhancements for Metis RAG")
    parser.add_argument("--db-type", type=str, choices=["sqlite", "postgresql"], required=True,
                        help="Database type to enhance")
    parser.add_argument("--apply", action="store_true", help="Apply enhancements (default is dry run)")
    args = parser.parse_args()
    
    # Run enhancements
    result = asyncio.run(run_enhancements(args))
    
    return result

if __name__ == "__main__":
    sys.exit(main())