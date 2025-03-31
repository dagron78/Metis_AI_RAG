"""
Schema Inspector - Module for PostgreSQL schema introspection

This module provides methods to retrieve database schema information from PostgreSQL,
including schemas, tables, columns, indexes, and constraints.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
import asyncpg

from app.db.connection_manager import connection_manager

class SchemaInspector:
    """
    PostgreSQL schema introspection utility
    
    This class provides methods to retrieve database schema information from PostgreSQL,
    including schemas, tables, columns, indexes, and constraints.
    """
    
    def __init__(self):
        """Initialize the schema inspector"""
        self.logger = logging.getLogger("app.db.schema_inspector")
        self._cache = {}  # Cache for schema information
    
    async def get_schemas(self, conn_id: str) -> List[Dict[str, Any]]:
        """
        Get a list of schemas in the database
        
        Args:
            conn_id: Connection ID
            
        Returns:
            List of schema information dictionaries
        """
        # Check cache
        cache_key = f"{conn_id}:schemas"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get connection
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type != 'postgres':
            raise ValueError("Schema introspection is only supported for PostgreSQL")
        
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Query schemas
            query = """
            SELECT 
                n.nspname AS schema_name,
                pg_catalog.pg_get_userbyid(n.nspowner) AS owner,
                pg_catalog.obj_description(n.oid, 'pg_namespace') AS description
            FROM pg_catalog.pg_namespace n
            WHERE n.nspname !~ '^pg_' 
              AND n.nspname <> 'information_schema'
            ORDER BY 1;
            """
            
            rows = await conn.fetch(query)
            
            # Convert to list of dictionaries
            schemas = [dict(row) for row in rows]
            
            # Cache results
            self._cache[cache_key] = schemas
            
            return schemas
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    async def get_tables(self, conn_id: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """
        Get a list of tables in the specified schema
        
        Args:
            conn_id: Connection ID
            schema: Schema name (default: 'public')
            
        Returns:
            List of table information dictionaries
        """
        # Check cache
        cache_key = f"{conn_id}:tables:{schema}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get connection
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type != 'postgres':
            raise ValueError("Schema introspection is only supported for PostgreSQL")
        
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Query tables with row counts
            query = """
            SELECT 
                c.relname AS table_name,
                pg_catalog.pg_get_userbyid(c.relowner) AS owner,
                pg_catalog.obj_description(c.oid, 'pg_class') AS description,
                c.reltuples::bigint AS row_estimate,
                pg_catalog.pg_size_pretty(pg_catalog.pg_total_relation_size(c.oid)) AS total_size,
                CASE 
                    WHEN c.relkind = 'r' THEN 'table'
                    WHEN c.relkind = 'v' THEN 'view'
                    WHEN c.relkind = 'm' THEN 'materialized view'
                    WHEN c.relkind = 'f' THEN 'foreign table'
                    ELSE c.relkind::text
                END AS type
            FROM pg_catalog.pg_class c
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'v', 'm', 'f')
              AND n.nspname = $1
              AND pg_catalog.pg_table_is_visible(c.oid)
            ORDER BY c.relname;
            """
            
            rows = await conn.fetch(query, schema)
            
            # Convert to list of dictionaries
            tables = [dict(row) for row in rows]
            
            # Get actual row counts for tables with reasonable size
            for table in tables:
                if table['type'] == 'table' and table['row_estimate'] < 1000000:
                    try:
                        count_query = f"SELECT COUNT(*) AS exact_count FROM {schema}.{table['table_name']}"
                        count_result = await conn.fetchval(count_query)
                        table['exact_row_count'] = count_result
                    except Exception as e:
                        self.logger.warning(f"Could not get exact row count for {schema}.{table['table_name']}: {str(e)}")
                        table['exact_row_count'] = None
                else:
                    table['exact_row_count'] = None
            
            # Cache results
            self._cache[cache_key] = tables
            
            return tables
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    async def get_columns(self, conn_id: str, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """
        Get a list of columns for the specified table
        
        Args:
            conn_id: Connection ID
            table_name: Table name
            schema: Schema name (default: 'public')
            
        Returns:
            List of column information dictionaries
        """
        # Check cache
        cache_key = f"{conn_id}:columns:{schema}.{table_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get connection
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type != 'postgres':
            raise ValueError("Schema introspection is only supported for PostgreSQL")
        
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Query columns
            query = """
            SELECT 
                a.attname AS column_name,
                pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
                CASE 
                    WHEN a.attnotnull THEN 'NO' 
                    ELSE 'YES' 
                END AS is_nullable,
                (SELECT pg_catalog.pg_get_expr(d.adbin, d.adrelid) 
                 FROM pg_catalog.pg_attrdef d 
                 WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef) AS default_value,
                col_description(a.attrelid, a.attnum) AS description,
                a.attnum AS ordinal_position
            FROM pg_catalog.pg_attribute a
            JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE a.attnum > 0 
              AND NOT a.attisdropped
              AND n.nspname = $1
              AND c.relname = $2
            ORDER BY a.attnum;
            """
            
            rows = await conn.fetch(query, schema, table_name)
            
            # Convert to list of dictionaries
            columns = [dict(row) for row in rows]
            
            # Cache results
            self._cache[cache_key] = columns
            
            return columns
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    async def get_indexes(self, conn_id: str, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """
        Get a list of indexes for the specified table
        
        Args:
            conn_id: Connection ID
            table_name: Table name
            schema: Schema name (default: 'public')
            
        Returns:
            List of index information dictionaries
        """
        # Check cache
        cache_key = f"{conn_id}:indexes:{schema}.{table_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get connection
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type != 'postgres':
            raise ValueError("Schema introspection is only supported for PostgreSQL")
        
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Query indexes
            query = """
            SELECT
                i.relname AS index_name,
                am.amname AS index_type,
                pg_catalog.pg_get_indexdef(i.oid, 0, true) AS index_definition,
                CASE 
                    WHEN ix.indisunique THEN 'YES' 
                    ELSE 'NO' 
                END AS is_unique,
                CASE 
                    WHEN ix.indisprimary THEN 'YES' 
                    ELSE 'NO' 
                END AS is_primary,
                pg_catalog.pg_size_pretty(pg_catalog.pg_relation_size(i.oid)) AS index_size,
                pg_catalog.obj_description(i.oid, 'pg_class') AS description
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_catalog.pg_index ix ON c.oid = ix.indrelid
            JOIN pg_catalog.pg_class i ON i.oid = ix.indexrelid
            JOIN pg_catalog.pg_am am ON i.relam = am.oid
            WHERE c.relkind = 'r'
              AND n.nspname = $1
              AND c.relname = $2
            ORDER BY i.relname;
            """
            
            rows = await conn.fetch(query, schema, table_name)
            
            # Convert to list of dictionaries
            indexes = [dict(row) for row in rows]
            
            # Cache results
            self._cache[cache_key] = indexes
            
            return indexes
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    async def get_constraints(self, conn_id: str, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """
        Get a list of constraints for the specified table
        
        Args:
            conn_id: Connection ID
            table_name: Table name
            schema: Schema name (default: 'public')
            
        Returns:
            List of constraint information dictionaries
        """
        # Check cache
        cache_key = f"{conn_id}:constraints:{schema}.{table_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get connection
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type != 'postgres':
            raise ValueError("Schema introspection is only supported for PostgreSQL")
        
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Query constraints
            query = """
            SELECT
                c.conname AS constraint_name,
                CASE c.contype
                    WHEN 'c' THEN 'CHECK'
                    WHEN 'f' THEN 'FOREIGN KEY'
                    WHEN 'p' THEN 'PRIMARY KEY'
                    WHEN 'u' THEN 'UNIQUE'
                    WHEN 't' THEN 'TRIGGER'
                    WHEN 'x' THEN 'EXCLUSION'
                    ELSE c.contype::text
                END AS constraint_type,
                pg_catalog.pg_get_constraintdef(c.oid, true) AS definition,
                c.condeferrable AS is_deferrable,
                c.condeferred AS is_deferred,
                c.convalidated AS is_validated,
                pg_catalog.obj_description(c.oid, 'pg_constraint') AS description
            FROM pg_catalog.pg_constraint c
            JOIN pg_catalog.pg_class r ON r.oid = c.conrelid
            JOIN pg_catalog.pg_namespace n ON n.oid = r.relnamespace
            WHERE r.relname = $2
              AND n.nspname = $1
            ORDER BY c.contype, c.conname;
            """
            
            rows = await conn.fetch(query, schema, table_name)
            
            # Convert to list of dictionaries
            constraints = [dict(row) for row in rows]
            
            # Cache results
            self._cache[cache_key] = constraints
            
            return constraints
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    async def get_foreign_keys(self, conn_id: str, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """
        Get a list of foreign keys for the specified table
        
        Args:
            conn_id: Connection ID
            table_name: Table name
            schema: Schema name (default: 'public')
            
        Returns:
            List of foreign key information dictionaries
        """
        # Check cache
        cache_key = f"{conn_id}:foreign_keys:{schema}.{table_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get connection
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type != 'postgres':
            raise ValueError("Schema introspection is only supported for PostgreSQL")
        
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Query foreign keys
            query = """
            SELECT
                c.conname AS constraint_name,
                n2.nspname AS referenced_schema,
                c2.relname AS referenced_table,
                ARRAY(
                    SELECT attname FROM pg_catalog.pg_attribute
                    WHERE attrelid = c.conrelid AND attnum = ANY(c.conkey)
                ) AS column_names,
                ARRAY(
                    SELECT attname FROM pg_catalog.pg_attribute
                    WHERE attrelid = c.confrelid AND attnum = ANY(c.confkey)
                ) AS referenced_columns,
                CASE c.confupdtype
                    WHEN 'a' THEN 'NO ACTION'
                    WHEN 'r' THEN 'RESTRICT'
                    WHEN 'c' THEN 'CASCADE'
                    WHEN 'n' THEN 'SET NULL'
                    WHEN 'd' THEN 'SET DEFAULT'
                    ELSE NULL
                END AS update_rule,
                CASE c.confdeltype
                    WHEN 'a' THEN 'NO ACTION'
                    WHEN 'r' THEN 'RESTRICT'
                    WHEN 'c' THEN 'CASCADE'
                    WHEN 'n' THEN 'SET NULL'
                    WHEN 'd' THEN 'SET DEFAULT'
                    ELSE NULL
                END AS delete_rule
            FROM pg_catalog.pg_constraint c
            JOIN pg_catalog.pg_class r ON r.oid = c.conrelid
            JOIN pg_catalog.pg_namespace n ON n.oid = r.relnamespace
            JOIN pg_catalog.pg_class c2 ON c2.oid = c.confrelid
            JOIN pg_catalog.pg_namespace n2 ON n2.oid = c2.relnamespace
            WHERE r.relname = $2
              AND n.nspname = $1
              AND c.contype = 'f'
            ORDER BY c.conname;
            """
            
            rows = await conn.fetch(query, schema, table_name)
            
            # Convert to list of dictionaries
            foreign_keys = [dict(row) for row in rows]
            
            # Cache results
            self._cache[cache_key] = foreign_keys
            
            return foreign_keys
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    async def get_table_structure(self, conn_id: str, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """
        Get comprehensive structure information for a table
        
        Args:
            conn_id: Connection ID
            table_name: Table name
            schema: Schema name (default: 'public')
            
        Returns:
            Dictionary with table structure information
        """
        # Check cache
        cache_key = f"{conn_id}:table_structure:{schema}.{table_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get all table components
        tables = await self.get_tables(conn_id, schema)
        table_info = next((t for t in tables if t['table_name'] == table_name), None)
        
        if not table_info:
            raise ValueError(f"Table {schema}.{table_name} not found")
        
        columns = await self.get_columns(conn_id, table_name, schema)
        indexes = await self.get_indexes(conn_id, table_name, schema)
        constraints = await self.get_constraints(conn_id, table_name, schema)
        foreign_keys = await self.get_foreign_keys(conn_id, table_name, schema)
        
        # Combine into a single structure
        table_structure = {
            "table_name": table_name,
            "schema": schema,
            "description": table_info.get('description'),
            "owner": table_info.get('owner'),
            "row_estimate": table_info.get('row_estimate'),
            "exact_row_count": table_info.get('exact_row_count'),
            "total_size": table_info.get('total_size'),
            "type": table_info.get('type'),
            "columns": columns,
            "indexes": indexes,
            "constraints": constraints,
            "foreign_keys": foreign_keys
        }
        
        # Cache results
        self._cache[cache_key] = table_structure
        
        return table_structure
    
    async def get_database_structure(self, conn_id: str) -> Dict[str, Any]:
        """
        Get comprehensive structure information for the entire database
        
        Args:
            conn_id: Connection ID
            
        Returns:
            Dictionary with database structure information
        """
        # Check cache
        cache_key = f"{conn_id}:database_structure"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get connection
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type != 'postgres':
            raise ValueError("Schema introspection is only supported for PostgreSQL")
        
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Get database name and version
            db_name = await conn.fetchval("SELECT current_database()")
            version = await conn.fetchval("SELECT version()")
            
            # Get schemas
            schemas = await self.get_schemas(conn_id)
            
            # Get tables for each schema
            schema_data = []
            for schema in schemas:
                schema_name = schema['schema_name']
                tables = await self.get_tables(conn_id, schema_name)
                
                # Get columns for each table
                table_data = []
                for table in tables:
                    table_name = table['table_name']
                    columns = await self.get_columns(conn_id, table_name, schema_name)
                    indexes = await self.get_indexes(conn_id, table_name, schema_name)
                    constraints = await self.get_constraints(conn_id, table_name, schema_name)
                    
                    table_data.append({
                        "table_name": table_name,
                        "description": table.get('description'),
                        "owner": table.get('owner'),
                        "row_estimate": table.get('row_estimate'),
                        "exact_row_count": table.get('exact_row_count'),
                        "total_size": table.get('total_size'),
                        "type": table.get('type'),
                        "columns": columns,
                        "indexes": indexes,
                        "constraints": constraints
                    })
                
                schema_data.append({
                    "schema_name": schema_name,
                    "description": schema.get('description'),
                    "owner": schema.get('owner'),
                    "tables": table_data
                })
            
            # Get extensions
            extensions_query = """
            SELECT 
                e.extname AS name,
                e.extversion AS version,
                n.nspname AS schema,
                c.description
            FROM pg_catalog.pg_extension e
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = e.extnamespace
            LEFT JOIN pg_catalog.pg_description c ON c.objoid = e.oid
            ORDER BY e.extname;
            """
            
            extension_rows = await conn.fetch(extensions_query)
            extensions = [dict(row) for row in extension_rows]
            
            # Combine into a single structure
            database_structure = {
                "database_name": db_name,
                "version": version,
                "schemas": schema_data,
                "extensions": extensions
            }
            
            # Cache results
            self._cache[cache_key] = database_structure
            
            return database_structure
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    async def get_extension_info(self, conn_id: str, extension_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get information about installed PostgreSQL extensions
        
        Args:
            conn_id: Connection ID
            extension_name: Optional extension name to filter by
            
        Returns:
            List of extension information dictionaries
        """
        # Check cache
        cache_key = f"{conn_id}:extensions:{extension_name or 'all'}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get connection
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type != 'postgres':
            raise ValueError("Schema introspection is only supported for PostgreSQL")
        
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Query extensions
            query = """
            SELECT 
                e.extname AS name,
                e.extversion AS version,
                n.nspname AS schema,
                c.description,
                pg_catalog.pg_get_userbyid(e.extowner) AS owner,
                e.extrelocatable AS relocatable,
                array_to_string(e.extconfig, ', ') AS config_tables
            FROM pg_catalog.pg_extension e
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = e.extnamespace
            LEFT JOIN pg_catalog.pg_description c ON c.objoid = e.oid
            """
            
            if extension_name:
                query += " WHERE e.extname = $1"
                rows = await conn.fetch(query, extension_name)
            else:
                query += " ORDER BY e.extname"
                rows = await conn.fetch(query)
            
            # Convert to list of dictionaries
            extensions = [dict(row) for row in rows]
            
            # Cache results
            self._cache[cache_key] = extensions
            
            return extensions
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    async def check_extension_installed(self, conn_id: str, extension_name: str) -> bool:
        """
        Check if a specific PostgreSQL extension is installed
        
        Args:
            conn_id: Connection ID
            extension_name: Extension name to check
            
        Returns:
            True if the extension is installed, False otherwise
        """
        extensions = await self.get_extension_info(conn_id, extension_name)
        return len(extensions) > 0
    
    async def get_pgvector_info(self, conn_id: str) -> Dict[str, Any]:
        """
        Get information about pgvector extension if installed
        
        Args:
            conn_id: Connection ID
            
        Returns:
            Dictionary with pgvector information or None if not installed
        """
        # Check if pgvector is installed
        is_installed = await self.check_extension_installed(conn_id, 'vector')
        if not is_installed:
            return {"installed": False}
        
        # Get connection
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Get pgvector version
            version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            
            # Get vector columns
            vector_columns_query = """
            SELECT 
                n.nspname AS schema,
                c.relname AS table,
                a.attname AS column,
                t.typname AS type,
                a.atttypmod AS dimensions
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            JOIN pg_type t ON a.atttypid = t.oid
            WHERE t.typname = 'vector'
              AND n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND a.attnum > 0
              AND NOT a.attisdropped
            ORDER BY n.nspname, c.relname, a.attnum;
            """
            
            vector_columns = await conn.fetch(vector_columns_query)
            
            # Get vector indexes
            vector_indexes_query = """
            SELECT 
                n.nspname AS schema,
                c.relname AS table,
                a.attname AS column,
                i.relname AS index_name,
                am.amname AS index_method
            FROM pg_index x
            JOIN pg_class c ON c.oid = x.indrelid
            JOIN pg_class i ON i.oid = x.indexrelid
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(x.indkey)
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_am am ON am.oid = i.relam
            JOIN pg_type t ON a.atttypid = t.oid
            WHERE t.typname = 'vector'
              AND n.nspname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY n.nspname, c.relname, i.relname;
            """
            
            vector_indexes = await conn.fetch(vector_indexes_query)
            
            return {
                "installed": True,
                "version": version,
                "vector_columns": [dict(row) for row in vector_columns],
                "vector_indexes": [dict(row) for row in vector_indexes]
            }
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(conn_id, conn)
    
    def clear_cache(self, conn_id: Optional[str] = None):
        """
        Clear the schema information cache
        
        Args:
            conn_id: Optional connection ID to clear cache for.
                    If None, clear the entire cache.
        """
        if conn_id:
            # Clear cache for specific connection
            keys_to_delete = [key for key in self._cache if key.startswith(f"{conn_id}:")]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            # Clear entire cache
            self._cache = {}

# Create a singleton instance
schema_inspector = SchemaInspector()