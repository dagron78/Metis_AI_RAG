"""
DatabaseTool - Tool for querying structured data with true async implementation
"""
import logging
import time
import json
import re
import asyncio
import aiofiles
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path

from app.rag.tools.base import Tool
from app.db.connection_manager import connection_manager

class DatabaseTool(Tool):
    """
    Tool for querying structured data with true async implementation
    
    This tool allows querying structured data sources using SQL-like syntax.
    It supports:
    - SQLite database queries (using aiosqlite)
    - PostgreSQL database queries (using asyncpg)
    - CSV file queries (converted to SQLite in-memory)
    - JSON file queries (converted to SQLite in-memory)
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the database tool
        
        Args:
            data_dir: Directory containing data files (optional)
        """
        super().__init__(
            name="database",
            description="Queries structured data from databases, CSV, and JSON files"
        )
        self.data_dir = data_dir
        # Use the connection manager instead of maintaining our own connections
        self.connection_manager = connection_manager
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the database tool
        
        Args:
            input_data: Dictionary containing:
                - query: SQL query string
                - source: Data source (database file, CSV file, or JSON file)
                - params: Query parameters (optional)
                - limit: Maximum number of results to return (optional)
                
        Returns:
            Dictionary containing:
                - results: Query results
                - columns: Column names
                - row_count: Number of rows returned
                - execution_time: Time taken to execute the query
                - error: Error message if the query failed
        """
        start_time = time.time()
        self.logger.info(f"Executing database query on source: {input_data.get('source')}")
        
        # Extract parameters
        query = input_data.get("query")
        source = input_data.get("source")
        params = input_data.get("params", {})
        limit = input_data.get("limit")
        
        # Validate input
        if not query:
            error_msg = "Query is required"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        if not source:
            error_msg = "Data source is required"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        try:
            # Resolve source path if data_dir is provided
            source_path = self._resolve_source_path(source)
            
            # Execute query
            results, columns = await self._execute_query(
                query=query,
                source=source_path,
                params=params,
                limit=limit
            )
            
            elapsed_time = time.time() - start_time
            row_count = len(results)
            self.logger.info(f"Database query completed in {elapsed_time:.2f}s. Returned {row_count} rows")
            
            return {
                "results": results,
                "columns": columns,
                "row_count": row_count,
                "execution_time": elapsed_time
            }
        except Exception as e:
            error_msg = f"Error executing database query: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _resolve_source_path(self, source: str) -> str:
        """
        Resolve the source path
        
        Args:
            source: Data source name or path
            
        Returns:
            Resolved source path
        """
        if self.data_dir and not Path(source).is_absolute():
            return str(Path(self.data_dir) / source)
        return source
    
    async def _execute_query(
        self, 
        query: str, 
        source: str, 
        params: Dict[str, Any] = None,
        limit: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute a query on a data source
        
        Args:
            query: SQL query
            source: Data source path
            params: Query parameters
            limit: Maximum number of results
            
        Returns:
            Tuple of (results, columns)
        """
        source_lower = source.lower()
        
        # Apply limit if specified and not already in the query
        if limit is not None and not re.search(r'\bLIMIT\s+\d+\b', query, re.IGNORECASE):
            query = f"{query} LIMIT {limit}"
        
        # Determine source type
        if source_lower.endswith('.db') or source_lower.endswith('.sqlite') or source_lower.endswith('.sqlite3'):
            return await self._query_sqlite(query, source, params)
        elif source_lower.startswith('postgresql://'):
            return await self._query_postgres(query, source, params)
        elif source_lower.endswith('.csv'):
            return await self._query_csv(query, source, params)
        elif source_lower.endswith('.json'):
            return await self._query_json(query, source, params)
        else:
            raise ValueError(f"Unsupported data source type: {source}")
    
    async def _query_sqlite(
        self, 
        query: str, 
        db_path: str, 
        params: Dict[str, Any] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute a query on a SQLite database using aiosqlite
        
        Args:
            query: SQL query
            db_path: Database file path
            params: Query parameters
            
        Returns:
            Tuple of (results, columns)
        """
        # Register the connection with the connection manager
        conn_id = self.connection_manager.register_connection(db_path)
        
        # Get a connection from the connection manager
        conn = await self.connection_manager.get_sqlite_connection(conn_id)
        
        try:
            # Execute query
            if params:
                # Convert dict params to tuple or list based on parameter style
                if isinstance(params, dict):
                    # For named parameters
                    cursor = await conn.execute(query, params)
                else:
                    # For positional parameters
                    cursor = await conn.execute(query, params)
            else:
                cursor = await conn.execute(query)
            
            # Fetch results
            rows = await cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert rows to list of dictionaries
            results = [dict(row) for row in rows]  # aiosqlite.Row objects are already dict-like
            
            await cursor.close()
            return results, columns
        except Exception as e:
            self.logger.error(f"Error executing SQLite query: {str(e)}")
            raise
    
    async def _query_postgres(
        self, 
        query: str, 
        connection_string: str, 
        params: Dict[str, Any] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute a query on a PostgreSQL database using asyncpg
        
        Args:
            query: SQL query
            connection_string: PostgreSQL connection string
            params: Query parameters
            
        Returns:
            Tuple of (results, columns)
        """
        # Register the connection with the connection manager
        conn_id = self.connection_manager.register_connection(connection_string)
        
        # Get a connection from the connection manager
        conn = await self.connection_manager.get_postgres_connection(conn_id)
        
        try:
            # Execute query
            if params:
                # Convert dict params to list for asyncpg
                if isinstance(params, dict):
                    # Replace named parameters with positional parameters
                    # This is a simplistic approach and might not work for all cases
                    param_values = []
                    for key, value in params.items():
                        # Replace :key or %(key)s with $n
                        query = query.replace(f":{key}", f"${len(param_values) + 1}")
                        query = query.replace(f"%({key})s", f"${len(param_values) + 1}")
                        param_values.append(value)
                    
                    # Execute with positional parameters
                    rows = await conn.fetch(query, *param_values)
                else:
                    # For positional parameters
                    rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)
            
            # Get column names from the first row
            columns = [key for key in rows[0].keys()] if rows else []
            
            # Convert rows to list of dictionaries
            results = [dict(row) for row in rows]
            
            return results, columns
        except Exception as e:
            self.logger.error(f"Error executing PostgreSQL query: {str(e)}")
            raise
        finally:
            # Release the connection back to the pool
            await self.connection_manager.release_postgres_connection(conn_id, conn)
    
    async def _query_csv(
        self, 
        query: str, 
        csv_path: str, 
        params: Dict[str, Any] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute a query on a CSV file using aiosqlite
        
        Args:
            query: SQL query
            csv_path: CSV file path
            params: Query parameters
            
        Returns:
            Tuple of (results, columns)
        """
        import pandas as pd
        
        # Create a unique in-memory database name for this CSV
        db_name = f":memory:{Path(csv_path).stem}"
        
        # Register the connection with the connection manager
        conn_id = self.connection_manager.register_connection(":memory:")
        
        # Get a connection from the connection manager
        conn = await self.connection_manager.get_sqlite_connection(conn_id)
        
        try:
            # Read CSV file (pandas doesn't have async version, so we use run_in_executor)
            df = await asyncio.to_thread(pd.read_csv, csv_path)
            
            # Get table name from file path
            table_name = Path(csv_path).stem
            
            # Write dataframe to SQLite (also not async)
            await asyncio.to_thread(df.to_sql, table_name, conn, index=False, if_exists='replace')
            
            # Modify query to use the table name
            modified_query = re.sub(
                r'\bFROM\s+([^\s,]+)',
                f'FROM {table_name}',
                query,
                flags=re.IGNORECASE
            )
            
            # Execute query
            if params:
                # Convert dict params to tuple or list based on parameter style
                if isinstance(params, dict):
                    # For named parameters
                    cursor = await conn.execute(modified_query, params)
                else:
                    # For positional parameters
                    cursor = await conn.execute(modified_query, params)
            else:
                cursor = await conn.execute(modified_query)
            
            # Fetch results
            rows = await cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert rows to list of dictionaries
            results = [dict(row) for row in rows]
            
            await cursor.close()
            return results, columns
        except Exception as e:
            self.logger.error(f"Error executing CSV query: {str(e)}")
            raise
        finally:
            # Close the connection
            await self.connection_manager.close(conn_id)
    
    async def _query_json(
        self, 
        query: str, 
        json_path: str, 
        params: Dict[str, Any] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute a query on a JSON file using aiosqlite
        
        Args:
            query: SQL query
            json_path: JSON file path
            params: Query parameters
            
        Returns:
            Tuple of (results, columns)
        """
        import pandas as pd
        
        # Create a unique in-memory database name for this JSON
        db_name = f":memory:{Path(json_path).stem}"
        
        # Register the connection with the connection manager
        conn_id = self.connection_manager.register_connection(":memory:")
        
        # Get a connection from the connection manager
        conn = await self.connection_manager.get_sqlite_connection(conn_id)
        
        try:
            # Read JSON file asynchronously
            async with aiofiles.open(json_path, 'r') as f:
                content = await f.read()
                data = json.loads(content)
            
            # Convert to dataframe
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Handle nested JSON structures
                if any(isinstance(v, (list, dict)) for v in data.values()):
                    # Normalize nested JSON
                    df = pd.json_normalize(data)
                else:
                    # Simple key-value pairs
                    df = pd.DataFrame([data])
            else:
                raise ValueError("JSON file must contain an object or array")
            
            # Get table name from file path
            table_name = Path(json_path).stem
            
            # Write dataframe to SQLite (not async)
            await asyncio.to_thread(df.to_sql, table_name, conn, index=False, if_exists='replace')
            
            # Modify query to use the table name
            modified_query = re.sub(
                r'\bFROM\s+([^\s,]+)',
                f'FROM {table_name}',
                query,
                flags=re.IGNORECASE
            )
            
            # Execute query
            if params:
                # Convert dict params to tuple or list based on parameter style
                if isinstance(params, dict):
                    # For named parameters
                    cursor = await conn.execute(modified_query, params)
                else:
                    # For positional parameters
                    cursor = await conn.execute(modified_query, params)
            else:
                cursor = await conn.execute(modified_query)
            
            # Fetch results
            rows = await cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert rows to list of dictionaries
            results = [dict(row) for row in rows]
            
            await cursor.close()
            return results, columns
        except Exception as e:
            self.logger.error(f"Error executing JSON query: {str(e)}")
            raise
        finally:
            # Close the connection
            await self.connection_manager.close(conn_id)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Get the input schema for the database tool
        
        Returns:
            JSON Schema for tool input
        """
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query string"
                },
                "source": {
                    "type": "string",
                    "description": "Data source (database file, CSV file, JSON file, or PostgreSQL connection string)"
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters",
                    "additionalProperties": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1
                }
            },
            "required": ["query", "source"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the output schema for the database tool
        
        Returns:
            JSON Schema for tool output
        """
        return {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "description": "Query results",
                    "items": {
                        "type": "object",
                        "additionalProperties": True
                    }
                },
                "columns": {
                    "type": "array",
                    "description": "Column names",
                    "items": {
                        "type": "string"
                    }
                },
                "row_count": {
                    "type": "integer",
                    "description": "Number of rows returned"
                },
                "execution_time": {
                    "type": "number",
                    "description": "Time taken to execute the query in seconds"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if the query failed"
                }
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """
        Get examples of database tool usage
        
        Returns:
            List of example input/output pairs
        """
        return [
            {
                "input": {
                    "query": "SELECT * FROM users WHERE age > 30",
                    "source": "users.db"
                },
                "output": {
                    "results": [
                        {"id": 1, "name": "John Doe", "age": 35, "email": "john@example.com"},
                        {"id": 3, "name": "Bob Smith", "age": 42, "email": "bob@example.com"}
                    ],
                    "columns": ["id", "name", "age", "email"],
                    "row_count": 2,
                    "execution_time": 0.05
                }
            },
            {
                "input": {
                    "query": "SELECT product_name, price FROM products WHERE category = :category",
                    "source": "products.csv",
                    "params": {"category": "Electronics"},
                    "limit": 5
                },
                "output": {
                    "results": [
                        {"product_name": "Smartphone", "price": 699.99},
                        {"product_name": "Laptop", "price": 1299.99},
                        {"product_name": "Headphones", "price": 149.99}
                    ],
                    "columns": ["product_name", "price"],
                    "row_count": 3,
                    "execution_time": 0.08
                }
            },
            {
                "input": {
                    "query": "SELECT city, COUNT(*) as customer_count FROM customers GROUP BY city ORDER BY customer_count DESC",
                    "source": "customers.json",
                    "limit": 3
                },
                "output": {
                    "results": [
                        {"city": "New York", "customer_count": 145},
                        {"city": "Los Angeles", "customer_count": 98},
                        {"city": "Chicago", "customer_count": 76}
                    ],
                    "columns": ["city", "customer_count"],
                    "row_count": 3,
                    "execution_time": 0.12
                }
            },
            {
                "input": {
                    "query": "SELECT u.username, COUNT(o.id) as order_count FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.username ORDER BY order_count DESC LIMIT 5",
                    "source": "postgresql://username:password@localhost:5432/mydb"
                },
                "output": {
                    "results": [
                        {"username": "johndoe", "order_count": 42},
                        {"username": "janedoe", "order_count": 38},
                        {"username": "bobsmith", "order_count": 27}
                    ],
                    "columns": ["username", "order_count"],
                    "row_count": 3,
                    "execution_time": 0.15
                }
            }
        ]