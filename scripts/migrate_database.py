#!/usr/bin/env python3
"""
Database Migration Script for Metis RAG

This script migrates data between SQLite and PostgreSQL databases:
1. Export data from source database to JSON
2. Import data to target database from JSON
3. Verify data integrity after migration

Usage:
    python migrate_database.py --source sqlite|postgresql --target sqlite|postgresql [--export-file data/export.json]
"""
import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.session import Base, engine, SessionLocal
from app.core.config import DATABASE_TYPE, DATABASE_URL
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class DatabaseMigrator:
    """Database migration class"""
    
    def __init__(self, source_type: str, target_type: str, export_file: str):
        self.source_type = source_type
        self.target_type = target_type
        self.export_file = export_file
        
        # Initialize source database session
        self.source_url = self._get_database_url(source_type)
        self.source_engine = create_engine(self.source_url)
        self.SourceSession = sessionmaker(autocommit=False, autoflush=False, bind=self.source_engine)
        self.source_session = self.SourceSession()
        
        # Initialize target database session
        self.target_url = self._get_database_url(target_type)
        self.target_engine = create_engine(self.target_url)
        self.TargetSession = sessionmaker(autocommit=False, autoflush=False, bind=self.target_engine)
        self.target_session = self.TargetSession()
        
        print(f"Initialized database migrator")
        print(f"Source database: {source_type} ({self.source_url})")
        print(f"Target database: {target_type} ({self.target_url})")
        print(f"Export file: {export_file}")
    
    def _get_database_url(self, db_type: str) -> str:
        """Get database URL based on type"""
        if db_type == "sqlite":
            return "sqlite:///./data/metis_rag.db"
        elif db_type == "postgresql":
            # Use environment variables or default values
            pg_user = os.environ.get("POSTGRES_USER", "postgres")
            pg_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
            pg_host = os.environ.get("POSTGRES_HOST", "localhost")
            pg_port = os.environ.get("POSTGRES_PORT", "5432")
            pg_db = os.environ.get("POSTGRES_DB", "metis_rag")
            return f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def cleanup(self):
        """Clean up resources"""
        self.source_session.close()
        self.target_session.close()
    
    def export_data(self) -> Dict[str, Any]:
        """Export data from source database to JSON"""
        print("\nExporting data from source database...")
        
        data = {
            "metadata": {
                "source_type": self.source_type,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            },
            "tables": {}
        }
        
        # Get list of tables
        if self.source_type == "sqlite":
            tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        else:
            tables_query = "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public';"
        
        tables_result = self.source_session.execute(text(tables_query))
        tables = [row[0] for row in tables_result]
        
        # Export data from each table
        for table in tables:
            print(f"  Exporting table: {table}")
            
            # Get table data
            data_query = f"SELECT * FROM {table};"
            data_result = self.source_session.execute(text(data_query))
            
            # Get column names
            columns = data_result.keys()
            
            # Convert to list of dictionaries
            rows = []
            for row in data_result:
                # Convert row to dictionary with proper JSON serialization
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # Handle special types
                    if isinstance(value, datetime):
                        row_dict[column] = value.isoformat()
                    elif hasattr(value, '__str__'):
                        row_dict[column] = str(value)
                    else:
                        row_dict[column] = value
                rows.append(row_dict)
            
            # Add to data
            data["tables"][table] = {
                "columns": list(columns),
                "rows": rows
            }
            
            print(f"    Exported {len(rows)} rows")
        
        # Write to file
        os.makedirs(os.path.dirname(self.export_file), exist_ok=True)
        with open(self.export_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to: {self.export_file}")
        return data
    
    def import_data(self) -> Dict[str, Any]:
        """Import data to target database from JSON"""
        print("\nImporting data to target database...")
        
        # Read data from file
        with open(self.export_file, 'r') as f:
            data = json.load(f)
        
        results = {
            "tables": {},
            "total_rows": 0
        }
        
        # Import data to each table
        for table, table_data in data["tables"].items():
            print(f"  Importing table: {table}")
            
            # Skip alembic_version table
            if table == "alembic_version":
                print(f"    Skipping alembic_version table")
                continue
            
            # Clear existing data
            clear_query = f"DELETE FROM {table};"
            try:
                self.target_session.execute(text(clear_query))
                self.target_session.commit()
                print(f"    Cleared existing data")
            except Exception as e:
                self.target_session.rollback()
                print(f"    Error clearing data: {str(e)}")
            
            # Import rows
            rows = table_data["rows"]
            imported_count = 0
            
            for row in rows:
                # Build insert query
                columns = ", ".join(row.keys())
                placeholders = ", ".join([f":{col}" for col in row.keys()])
                insert_query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"
                
                try:
                    self.target_session.execute(text(insert_query), row)
                    imported_count += 1
                except Exception as e:
                    self.target_session.rollback()
                    print(f"    Error importing row: {str(e)}")
            
            # Commit changes
            self.target_session.commit()
            
            # Add to results
            results["tables"][table] = {
                "total_rows": len(rows),
                "imported_rows": imported_count
            }
            results["total_rows"] += imported_count
            
            print(f"    Imported {imported_count}/{len(rows)} rows")
        
        print(f"Data import completed: {results['total_rows']} total rows imported")
        return results
    
    def verify_data(self) -> Dict[str, Any]:
        """Verify data integrity after migration"""
        print("\nVerifying data integrity...")
        
        # Read data from file
        with open(self.export_file, 'r') as f:
            data = json.load(f)
        
        results = {
            "tables": {},
            "success": True
        }
        
        # Verify each table
        for table, table_data in data["tables"].items():
            print(f"  Verifying table: {table}")
            
            # Skip alembic_version table
            if table == "alembic_version":
                print(f"    Skipping alembic_version table")
                continue
            
            # Get row count
            count_query = f"SELECT COUNT(*) FROM {table};"
            source_count = len(table_data["rows"])
            
            try:
                target_count_result = self.target_session.execute(text(count_query))
                target_count = target_count_result.scalar()
                
                # Verify count
                count_match = source_count == target_count
                
                # Add to results
                results["tables"][table] = {
                    "source_count": source_count,
                    "target_count": target_count,
                    "count_match": count_match
                }
                
                if not count_match:
                    results["success"] = False
                
                print(f"    Row count: {target_count}/{source_count} {'✓' if count_match else '✗'}")
            except Exception as e:
                results["tables"][table] = {
                    "source_count": source_count,
                    "target_count": 0,
                    "count_match": False,
                    "error": str(e)
                }
                results["success"] = False
                print(f"    Error verifying table: {str(e)}")
        
        # Print summary
        print("\nVerification Summary:")
        if results["success"]:
            print("  ✓ All tables verified successfully")
        else:
            print("  ✗ Some tables failed verification")
        
        return results
    
    def migrate_database(self) -> Dict[str, Any]:
        """Migrate data between databases"""
        results = {
            "source_type": self.source_type,
            "target_type": self.target_type,
            "export_file": self.export_file,
            "timestamp": datetime.now().isoformat()
        }
        
        # Export data
        export_data = self.export_data()
        results["export"] = {
            "tables": len(export_data["tables"]),
            "total_rows": sum(len(table_data["rows"]) for table_data in export_data["tables"].values())
        }
        
        # Import data
        import_results = self.import_data()
        results["import"] = import_results
        
        # Verify data
        verify_results = self.verify_data()
        results["verify"] = verify_results
        
        # Print summary
        print("\nMigration Summary:")
        print(f"  Source: {self.source_type}")
        print(f"  Target: {self.target_type}")
        print(f"  Tables: {results['export']['tables']}")
        print(f"  Rows: {results['import']['total_rows']}/{results['export']['total_rows']}")
        print(f"  Verification: {'Successful' if verify_results['success'] else 'Failed'}")
        
        return results

async def run_migration(args):
    """Run the database migration"""
    print(f"\nRunning database migration from {args.source} to {args.target}...")
    
    # Create migrator instance
    migrator = DatabaseMigrator(args.source, args.target, args.export_file)
    
    try:
        # Migrate database
        results = migrator.migrate_database()
        
        print("\nMigration completed successfully!")
        return 0
    except Exception as e:
        print(f"Error migrating database: {e}")
        return 1
    finally:
        migrator.cleanup()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Database Migration for Metis RAG")
    parser.add_argument("--source", type=str, choices=["sqlite", "postgresql"], required=True,
                        help="Source database type")
    parser.add_argument("--target", type=str, choices=["sqlite", "postgresql"], required=True,
                        help="Target database type")
    parser.add_argument("--export-file", type=str, default="data/export.json",
                        help="Export file path (default: data/export.json)")
    args = parser.parse_args()
    
    # Check if source and target are the same
    if args.source == args.target:
        print(f"Error: Source and target databases are the same: {args.source}")
        return 1
    
    # Run migration
    result = asyncio.run(run_migration(args))
    
    return result

if __name__ == "__main__":
    sys.exit(main())