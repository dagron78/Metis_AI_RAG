"""
PostgreSQLTool - Tool for PostgreSQL-specific operations
"""
import logging
import time
from typing import Any, Dict, List, Optional, Union

from app.rag.tools.base import Tool
from app.db.connection_manager import connection_manager
from app.db.schema_inspector import schema_inspector

class PostgreSQLTool(Tool):
    """
    Tool for PostgreSQL-specific operations
    
    This tool provides PostgreSQL-specific capabilities, including:
    - Schema introspection
    - Query explanation
    - Vector similarity search (pgvector)
    - Extension management
    """
    
    def __init__(self):
        """
        Initialize the PostgreSQL tool
        """
        super().__init__(
            name="postgresql",
            description="Provides PostgreSQL-specific operations like schema introspection, query explanation, and vector search"
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the PostgreSQL tool
        
        Args:
            input_data: Dictionary containing:
                - operation: Operation to perform
                - connection_id: PostgreSQL connection ID
                - Additional operation-specific parameters
                
        Returns:
            Dictionary containing operation-specific results
        """
        start_time = time.time()
        self.logger.info(f"Executing PostgreSQL operation: {input_data.get('operation')}")
        
        # Extract parameters
        operation = input_data.get("operation")
        connection_id = input_data.get("connection_id")
        
        # Validate input
        if not operation:
            error_msg = "Operation is required"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        if not connection_id:
            error_msg = "Connection ID is required"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        # Check connection type
        try:
            conn_type = connection_manager.get_connection_type(connection_id)
            if conn_type != 'postgres':
                error_msg = f"Connection {connection_id} is not a PostgreSQL connection"
                self.logger.error(error_msg)
                return {"error": error_msg}
        except ValueError as e:
            error_msg = f"Invalid connection ID: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        try:
            # Execute operation
            if operation == "get_schemas":
                result = await schema_inspector.get_schemas(connection_id)
                return {
                    "schemas": result,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_tables":
                schema = input_data.get("schema", "public")
                result = await schema_inspector.get_tables(connection_id, schema)
                return {
                    "tables": result,
                    "schema": schema,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_columns":
                table_name = input_data.get("table_name")
                schema = input_data.get("schema", "public")
                
                if not table_name:
                    return {"error": "Table name is required"}
                
                result = await schema_inspector.get_columns(connection_id, table_name, schema)
                return {
                    "columns": result,
                    "table_name": table_name,
                    "schema": schema,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_indexes":
                table_name = input_data.get("table_name")
                schema = input_data.get("schema", "public")
                
                if not table_name:
                    return {"error": "Table name is required"}
                
                result = await schema_inspector.get_indexes(connection_id, table_name, schema)
                return {
                    "indexes": result,
                    "table_name": table_name,
                    "schema": schema,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_constraints":
                table_name = input_data.get("table_name")
                schema = input_data.get("schema", "public")
                
                if not table_name:
                    return {"error": "Table name is required"}
                
                result = await schema_inspector.get_constraints(connection_id, table_name, schema)
                return {
                    "constraints": result,
                    "table_name": table_name,
                    "schema": schema,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_foreign_keys":
                table_name = input_data.get("table_name")
                schema = input_data.get("schema", "public")
                
                if not table_name:
                    return {"error": "Table name is required"}
                
                result = await schema_inspector.get_foreign_keys(connection_id, table_name, schema)
                return {
                    "foreign_keys": result,
                    "table_name": table_name,
                    "schema": schema,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_table_structure":
                table_name = input_data.get("table_name")
                schema = input_data.get("schema", "public")
                
                if not table_name:
                    return {"error": "Table name is required"}
                
                result = await schema_inspector.get_table_structure(connection_id, table_name, schema)
                return {
                    "table_structure": result,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_database_structure":
                result = await schema_inspector.get_database_structure(connection_id)
                return {
                    "database_structure": result,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_extensions":
                extension_name = input_data.get("extension_name")
                result = await schema_inspector.get_extension_info(connection_id, extension_name)
                return {
                    "extensions": result,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "check_extension":
                extension_name = input_data.get("extension_name")
                
                if not extension_name:
                    return {"error": "Extension name is required"}
                
                result = await schema_inspector.check_extension_installed(connection_id, extension_name)
                return {
                    "extension_name": extension_name,
                    "installed": result,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "get_pgvector_info":
                result = await schema_inspector.get_pgvector_info(connection_id)
                return {
                    "pgvector_info": result,
                    "execution_time": time.time() - start_time
                }
            
            elif operation == "explain_query":
                query = input_data.get("query")
                explain_type = input_data.get("explain_type", "simple")  # simple, analyze, verbose, etc.
                
                if not query:
                    return {"error": "Query is required"}
                
                # Get connection
                conn = await connection_manager.get_postgres_connection(connection_id)
                
                try:
                    # Build EXPLAIN command based on type
                    explain_options = ""
                    if explain_type == "analyze":
                        explain_options = "ANALYZE"
                    elif explain_type == "verbose":
                        explain_options = "VERBOSE"
                    elif explain_type == "analyze_verbose":
                        explain_options = "ANALYZE, VERBOSE"
                    elif explain_type == "analyze_verbose_buffers":
                        explain_options = "ANALYZE, VERBOSE, BUFFERS"
                    elif explain_type == "json":
                        explain_options = "FORMAT JSON"
                    elif explain_type == "analyze_json":
                        explain_options = "ANALYZE, FORMAT JSON"
                    
                    # Execute EXPLAIN
                    explain_query = f"EXPLAIN ({explain_options}) {query}"
                    rows = await conn.fetch(explain_query)
                    
                    # Format result
                    if explain_type in ["json", "analyze_json"]:
                        # For JSON format, return the parsed JSON
                        plan = rows[0][0]
                        return {
                            "query": query,
                            "plan": plan,
                            "execution_time": time.time() - start_time
                        }
                    else:
                        # For text format, concatenate the rows
                        plan_lines = [row[0] for row in rows]
                        plan_text = "\n".join(plan_lines)
                        
                        return {
                            "query": query,
                            "plan_text": plan_text,
                            "execution_time": time.time() - start_time
                        }
                finally:
                    # Release connection back to pool
                    await connection_manager.release_postgres_connection(connection_id, conn)
            
            elif operation == "vector_search":
                table_name = input_data.get("table_name")
                column_name = input_data.get("column_name")
                vector = input_data.get("vector")
                distance_type = input_data.get("distance_type", "cosine")  # cosine, euclidean, inner_product
                limit = input_data.get("limit", 10)
                schema = input_data.get("schema", "public")
                
                if not table_name:
                    return {"error": "Table name is required"}
                if not column_name:
                    return {"error": "Column name is required"}
                if not vector:
                    return {"error": "Vector is required"}
                
                # Check if pgvector is installed
                pgvector_info = await schema_inspector.get_pgvector_info(connection_id)
                if not pgvector_info.get("installed", False):
                    return {"error": "pgvector extension is not installed"}
                
                # Get connection
                conn = await connection_manager.get_postgres_connection(connection_id)
                
                try:
                    # Build vector search query
                    distance_operator = "<->"  # Default: Euclidean distance
                    if distance_type == "cosine":
                        distance_operator = "<=>"
                    elif distance_type == "inner_product":
                        distance_operator = "<#>"
                    
                    # Convert vector to string format
                    vector_str = f"'[{','.join(map(str, vector))}]'"
                    
                    # Execute vector search
                    query = f"""
                    SELECT *, ({column_name} {distance_operator} {vector_str}::vector) AS distance
                    FROM {schema}.{table_name}
                    ORDER BY {column_name} {distance_operator} {vector_str}::vector
                    LIMIT {limit}
                    """
                    
                    rows = await conn.fetch(query)
                    
                    # Convert to list of dictionaries
                    results = [dict(row) for row in rows]
                    
                    return {
                        "results": results,
                        "count": len(results),
                        "distance_type": distance_type,
                        "execution_time": time.time() - start_time
                    }
                finally:
                    # Release connection back to pool
                    await connection_manager.release_postgres_connection(connection_id, conn)
            
            else:
                error_msg = f"Unsupported operation: {operation}"
                self.logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error executing PostgreSQL operation: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Get the input schema for the PostgreSQL tool
        
        Returns:
            JSON Schema for tool input
        """
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": [
                        "get_schemas",
                        "get_tables",
                        "get_columns",
                        "get_indexes",
                        "get_constraints",
                        "get_foreign_keys",
                        "get_table_structure",
                        "get_database_structure",
                        "get_extensions",
                        "check_extension",
                        "get_pgvector_info",
                        "explain_query",
                        "vector_search"
                    ]
                },
                "connection_id": {
                    "type": "string",
                    "description": "PostgreSQL connection ID"
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name (default: 'public')"
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name"
                },
                "column_name": {
                    "type": "string",
                    "description": "Column name"
                },
                "extension_name": {
                    "type": "string",
                    "description": "Extension name"
                },
                "query": {
                    "type": "string",
                    "description": "SQL query to explain"
                },
                "explain_type": {
                    "type": "string",
                    "description": "Type of EXPLAIN to perform",
                    "enum": [
                        "simple",
                        "analyze",
                        "verbose",
                        "analyze_verbose",
                        "analyze_verbose_buffers",
                        "json",
                        "analyze_json"
                    ]
                },
                "vector": {
                    "type": "array",
                    "description": "Vector for similarity search",
                    "items": {
                        "type": "number"
                    }
                },
                "distance_type": {
                    "type": "string",
                    "description": "Distance type for vector search",
                    "enum": [
                        "euclidean",
                        "cosine",
                        "inner_product"
                    ]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1
                }
            },
            "required": ["operation", "connection_id"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the output schema for the PostgreSQL tool
        
        Returns:
            JSON Schema for tool output
        """
        return {
            "type": "object",
            "properties": {
                "schemas": {
                    "type": "array",
                    "description": "List of database schemas"
                },
                "tables": {
                    "type": "array",
                    "description": "List of tables in a schema"
                },
                "columns": {
                    "type": "array",
                    "description": "List of columns in a table"
                },
                "indexes": {
                    "type": "array",
                    "description": "List of indexes for a table"
                },
                "constraints": {
                    "type": "array",
                    "description": "List of constraints for a table"
                },
                "foreign_keys": {
                    "type": "array",
                    "description": "List of foreign keys for a table"
                },
                "table_structure": {
                    "type": "object",
                    "description": "Comprehensive structure of a table"
                },
                "database_structure": {
                    "type": "object",
                    "description": "Comprehensive structure of the database"
                },
                "extensions": {
                    "type": "array",
                    "description": "List of installed extensions"
                },
                "installed": {
                    "type": "boolean",
                    "description": "Whether an extension is installed"
                },
                "pgvector_info": {
                    "type": "object",
                    "description": "Information about pgvector extension"
                },
                "plan_text": {
                    "type": "string",
                    "description": "Query execution plan as text"
                },
                "plan": {
                    "type": "object",
                    "description": "Query execution plan as JSON"
                },
                "results": {
                    "type": "array",
                    "description": "Vector search results"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results returned"
                },
                "execution_time": {
                    "type": "number",
                    "description": "Time taken to execute the operation in seconds"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if the operation failed"
                }
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """
        Get examples of PostgreSQL tool usage
        
        Returns:
            List of example input/output pairs
        """
        return [
            {
                "input": {
                    "operation": "get_schemas",
                    "connection_id": "postgresql://user:password@localhost:5432/mydb"
                },
                "output": {
                    "schemas": [
                        {"schema_name": "public", "owner": "postgres", "description": "standard public schema"},
                        {"schema_name": "app", "owner": "app_user", "description": "application schema"}
                    ],
                    "execution_time": 0.05
                }
            },
            {
                "input": {
                    "operation": "get_tables",
                    "connection_id": "postgresql://user:password@localhost:5432/mydb",
                    "schema": "public"
                },
                "output": {
                    "tables": [
                        {
                            "table_name": "users",
                            "owner": "postgres",
                            "description": "User accounts",
                            "row_estimate": 1000,
                            "exact_row_count": 1042,
                            "total_size": "1024 kB",
                            "type": "table"
                        },
                        {
                            "table_name": "documents",
                            "owner": "postgres",
                            "description": "Document storage",
                            "row_estimate": 5000,
                            "exact_row_count": 4872,
                            "total_size": "8192 kB",
                            "type": "table"
                        }
                    ],
                    "schema": "public",
                    "execution_time": 0.08
                }
            },
            {
                "input": {
                    "operation": "explain_query",
                    "connection_id": "postgresql://user:password@localhost:5432/mydb",
                    "query": "SELECT * FROM users WHERE email LIKE '%example.com'",
                    "explain_type": "analyze"
                },
                "output": {
                    "query": "SELECT * FROM users WHERE email LIKE '%example.com'",
                    "plan_text": "Seq Scan on users  (cost=0.00..25.88 rows=6 width=90) (actual time=0.019..0.021 rows=3 loops=1)\n  Filter: ((email)::text ~~ '%example.com'::text)\n  Rows Removed by Filter: 7\nPlanning Time: 0.066 ms\nExecution Time: 0.048 ms",
                    "execution_time": 0.12
                }
            },
            {
                "input": {
                    "operation": "vector_search",
                    "connection_id": "postgresql://user:password@localhost:5432/mydb",
                    "table_name": "embeddings",
                    "column_name": "embedding",
                    "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
                    "distance_type": "cosine",
                    "limit": 5
                },
                "output": {
                    "results": [
                        {"id": 1, "text": "Sample text 1", "distance": 0.15},
                        {"id": 2, "text": "Sample text 2", "distance": 0.25},
                        {"id": 3, "text": "Sample text 3", "distance": 0.35}
                    ],
                    "count": 3,
                    "distance_type": "cosine",
                    "execution_time": 0.18
                }
            }
        ]