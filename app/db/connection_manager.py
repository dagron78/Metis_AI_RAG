"""
Database connection manager for async database operations
"""
import logging
import uuid
import urllib.parse
from typing import Dict, Any, Optional, Union
import aiosqlite
import asyncpg

class DatabaseConnectionManager:
    """
    Manages async database connections with connection pooling and secure IDs
    
    This class provides a unified interface for managing both SQLite and PostgreSQL
    connections using aiosqlite and asyncpg respectively. It implements connection
    pooling, secure connection ID generation, and proper lifecycle management.
    """
    
    def __init__(self):
        """Initialize the database connection manager"""
        self.logger = logging.getLogger("app.db.connection_manager")
        self._pools = {}  # Connection pools by connection ID
        self._connection_map = {}  # Map connection IDs to connection strings
        self._reverse_map = {}  # Map connection strings to IDs
        self._connection_types = {}  # Track connection types (sqlite or postgres)
    
    def connection_to_uuid(self, connection_string: str) -> str:
        """
        Convert a connection string to a deterministic UUID
        
        Args:
            connection_string: Database connection string
            
        Returns:
            str: UUID representing the connection
        """
        # For SQLite, use the file path
        if connection_string.endswith(('.db', '.sqlite', '.sqlite3')) or connection_string.startswith('sqlite:'):
            # Extract just the path part for SQLite
            if connection_string.startswith('sqlite:'):
                # Handle SQLAlchemy-style connection strings
                path = connection_string.replace('sqlite:///', '')
                path = connection_string.replace('sqlite://', '')
            else:
                path = connection_string
            
            # Create a Version 5 UUID (SHA-1 based)
            return str(uuid.uuid5(uuid.NAMESPACE_URL, f"sqlite:{path}"))
        
        # For PostgreSQL, use a similar approach to pg-mcp
        elif connection_string.startswith('postgresql:'):
            # Parse the connection string
            parsed = urllib.parse.urlparse(connection_string)
            
            # Extract the netloc (user:password@host:port) and path (database name)
            connection_id_string = parsed.netloc + parsed.path
            
            # Create a Version 5 UUID (SHA-1 based)
            return str(uuid.uuid5(uuid.NAMESPACE_URL, connection_id_string))
        
        # Default case - just hash the whole string
        return str(uuid.uuid5(uuid.NAMESPACE_URL, connection_string))
    
    def register_connection(self, connection_string: str) -> str:
        """
        Register a connection string and return its UUID identifier
        
        Args:
            connection_string: Database connection string
            
        Returns:
            str: UUID identifier for this connection
        """
        # Check if already registered
        if connection_string in self._reverse_map:
            return self._reverse_map[connection_string]
        
        # Normalize PostgreSQL connection strings
        if connection_string.startswith('postgres://'):
            connection_string = connection_string.replace('postgres://', 'postgresql://')
        
        # Determine connection type
        if connection_string.endswith(('.db', '.sqlite', '.sqlite3')) or connection_string.startswith('sqlite:'):
            conn_type = 'sqlite'
        elif connection_string.startswith('postgresql://'):
            conn_type = 'postgres'
        else:
            # Try to infer from file extension
            lower_conn = connection_string.lower()
            if any(lower_conn.endswith(ext) for ext in ['.db', '.sqlite', '.sqlite3']):
                conn_type = 'sqlite'
            else:
                raise ValueError(f"Unable to determine connection type for: {connection_string}")
        
        # Generate a new UUID
        conn_id = self.connection_to_uuid(connection_string)
        
        # Store mappings
        self._connection_map[conn_id] = connection_string
        self._reverse_map[connection_string] = conn_id
        self._connection_types[conn_id] = conn_type
        
        self.logger.info(f"Registered new {conn_type} connection with ID {conn_id}")
        return conn_id
    
    def get_connection_string(self, conn_id: str) -> str:
        """
        Get the connection string for a connection ID
        
        Args:
            conn_id: Connection ID
            
        Returns:
            str: Connection string
            
        Raises:
            ValueError: If the connection ID is unknown
        """
        if conn_id not in self._connection_map:
            raise ValueError(f"Unknown connection ID: {conn_id}")
        return self._connection_map[conn_id]
    
    def get_connection_type(self, conn_id: str) -> str:
        """
        Get the connection type (sqlite or postgres) for a connection ID
        
        Args:
            conn_id: Connection ID
            
        Returns:
            str: Connection type ('sqlite' or 'postgres')
            
        Raises:
            ValueError: If the connection ID is unknown
        """
        if conn_id not in self._connection_types:
            raise ValueError(f"Unknown connection ID: {conn_id}")
        return self._connection_types[conn_id]
    
    async def get_connection(self, conn_id: str) -> Union[aiosqlite.Connection, asyncpg.Connection]:
        """
        Get a database connection for the given connection ID
        
        This method returns the appropriate connection type based on the
        registered connection string.
        
        Args:
            conn_id: Connection ID
            
        Returns:
            Union[aiosqlite.Connection, asyncpg.Connection]: Database connection
            
        Raises:
            ValueError: If the connection ID is unknown
        """
        conn_type = self.get_connection_type(conn_id)
        
        if conn_type == 'sqlite':
            return await self.get_sqlite_connection(conn_id)
        elif conn_type == 'postgres':
            return await self.get_postgres_connection(conn_id)
        else:
            raise ValueError(f"Unsupported connection type: {conn_type}")
    
    async def get_sqlite_connection(self, conn_id: str) -> aiosqlite.Connection:
        """
        Get an aiosqlite connection for the given connection ID
        
        Args:
            conn_id: Connection ID
            
        Returns:
            aiosqlite.Connection: SQLite connection
            
        Raises:
            ValueError: If the connection ID is unknown or not a SQLite connection
        """
        if self.get_connection_type(conn_id) != 'sqlite':
            raise ValueError(f"Connection ID {conn_id} is not a SQLite connection")
        
        connection_string = self.get_connection_string(conn_id)
        
        # For SQLite, the connection string is the file path
        # Handle SQLAlchemy-style connection strings
        if connection_string.startswith('sqlite:'):
            if connection_string.startswith('sqlite:///'):
                # Absolute path
                db_path = connection_string[10:]
            elif connection_string.startswith('sqlite://'):
                # Relative path
                db_path = connection_string[9:]
            else:
                db_path = ':memory:'
        else:
            db_path = connection_string
        
        # Create connection if it doesn't exist
        if conn_id not in self._pools:
            self.logger.debug(f"Creating new SQLite connection to {db_path}")
            self._pools[conn_id] = await aiosqlite.connect(db_path)
            # Enable row factory for dict-like access
            self._pools[conn_id].row_factory = aiosqlite.Row
            
        return self._pools[conn_id]
    
    async def get_postgres_connection(self, conn_id: str) -> asyncpg.Connection:
        """
        Get an asyncpg connection from the pool for the given connection ID
        
        Args:
            conn_id: Connection ID
            
        Returns:
            asyncpg.Connection: PostgreSQL connection
            
        Raises:
            ValueError: If the connection ID is unknown or not a PostgreSQL connection
        """
        if self.get_connection_type(conn_id) != 'postgres':
            raise ValueError(f"Connection ID {conn_id} is not a PostgreSQL connection")
        
        connection_string = self.get_connection_string(conn_id)
        
        # Create pool if it doesn't exist
        if conn_id not in self._pools:
            self.logger.debug(f"Creating new PostgreSQL connection pool for {conn_id}")
            self._pools[conn_id] = await asyncpg.create_pool(
                connection_string,
                min_size=2,
                max_size=10,
                command_timeout=60.0,
                # Read-only mode for safety by default
                server_settings={"default_transaction_read_only": "true"}
            )
            
        # Get connection from pool
        return await self._pools[conn_id].acquire()
    
    async def release_postgres_connection(self, conn_id: str, connection: asyncpg.Connection):
        """
        Release a PostgreSQL connection back to the pool
        
        Args:
            conn_id: Connection ID
            connection: PostgreSQL connection to release
            
        Raises:
            ValueError: If the connection ID is unknown or not a PostgreSQL connection
        """
        if self.get_connection_type(conn_id) != 'postgres':
            raise ValueError(f"Connection ID {conn_id} is not a PostgreSQL connection")
            
        if conn_id in self._pools:
            await self._pools[conn_id].release(connection)
    
    async def close(self, conn_id: Optional[str] = None):
        """
        Close a specific or all database connections
        
        Args:
            conn_id: If provided, close only this specific connection.
                    If None, close all connections.
        """
        if conn_id:
            if conn_id in self._pools:
                conn_type = self.get_connection_type(conn_id)
                self.logger.info(f"Closing {conn_type} connection for ID {conn_id}")
                
                pool = self._pools[conn_id]
                if conn_type == 'sqlite':
                    await pool.close()
                else:  # postgres
                    await pool.close()
                    
                del self._pools[conn_id]
                # Keep the mapping for potential reconnection
        else:
            # Close all connection pools
            self.logger.info("Closing all database connections")
            for id, pool in list(self._pools.items()):
                conn_type = self.get_connection_type(id)
                if conn_type == 'sqlite':
                    await pool.close()
                else:  # postgres
                    await pool.close()
                del self._pools[id]

# Create a singleton instance
connection_manager = DatabaseConnectionManager()