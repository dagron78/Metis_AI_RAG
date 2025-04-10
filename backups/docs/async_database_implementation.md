# Async Database Implementation

This document provides an overview of the new asynchronous database implementation in Metis RAG, which enhances the system with true async database operations for improved performance and scalability.

## Overview

The original `DatabaseTool` implementation used synchronous SQLite operations wrapped in async methods, which could block the event loop and cause performance issues in an otherwise asynchronous application. The new implementation provides true asynchronous database operations using:

- `aiosqlite` for SQLite databases
- `asyncpg` for PostgreSQL databases
- Asynchronous file operations for CSV and JSON data sources

## Benefits

- **Improved Performance**: Non-blocking database operations allow the application to handle more concurrent requests
- **Reduced Latency**: Async operations prevent the event loop from being blocked during database queries
- **PostgreSQL Support**: Native support for PostgreSQL databases with connection pooling
- **Better Resource Management**: Proper connection lifecycle management with connection pooling
- **Enhanced Security**: Secure connection handling with connection IDs to avoid exposing credentials

## Key Components

### 1. Database Connection Manager

The `DatabaseConnectionManager` class in `app/db/connection_manager.py` provides:

- Connection pooling for both SQLite and PostgreSQL
- Secure connection ID generation
- Connection lifecycle management
- Support for multiple database types

### 2. Async DatabaseTool

The new `DatabaseTool` implementation in `app/rag/tools/database_tool.py` provides:

- True async database operations
- Support for SQLite, PostgreSQL, CSV, and JSON data sources
- Proper error handling and performance logging
- Backward compatibility with existing tool usage patterns

## Migration Guide

### Automatic Migration

The easiest way to migrate is to use the provided migration script:

```bash
python scripts/migrate_to_async_database_tool.py
```

This script will:
1. Rename the old `DatabaseTool` to `DatabaseToolLegacy`
2. Install the new async implementation as `DatabaseTool`
3. Update imports in the codebase
4. Create a backup of the original implementation

### Manual Migration

If you prefer to migrate manually, follow these steps:

1. Rename the existing `app/rag/tools/database_tool.py` to `app/rag/tools/database_tool_legacy.py`
2. Rename the class inside from `DatabaseTool` to `DatabaseToolLegacy`
3. Move `app/rag/tools/database_tool_async.py` to `app/rag/tools/database_tool.py`
4. Update any imports in your code that reference the `DatabaseTool`

### Testing the Migration

After migration, run the tests to ensure everything works correctly:

```bash
pytest tests/unit/test_database_tool_async.py
```

## Using PostgreSQL

The new implementation adds support for PostgreSQL databases. To use PostgreSQL:

1. Ensure you have the required dependencies:
   ```bash
   pip install asyncpg
   ```

2. Use a PostgreSQL connection string as the source:
   ```python
   result = await database_tool.execute({
       'query': 'SELECT * FROM users',
       'source': 'postgresql://username:password@localhost:5432/mydb'
   })
   ```

## Configuration

The database connection manager can be configured through environment variables:

- `DATABASE_POOL_SIZE`: Maximum number of connections in the pool (default: 10)
- `DATABASE_MAX_OVERFLOW`: Maximum number of connections that can be created beyond the pool size (default: 20)
- `DATABASE_POOL_RECYCLE`: Number of seconds after which a connection is recycled (default: 3600)

## Troubleshooting

### Connection Issues

If you experience connection issues:

1. Check that the database server is running and accessible
2. Verify that the connection string is correct
3. Ensure you have the required permissions to access the database
4. Check for firewall or network issues

### Performance Issues

If you experience performance issues:

1. Adjust the connection pool size based on your application's needs
2. Use query parameters to avoid SQL injection and improve performance
3. Add appropriate indexes to your database tables
4. Use the `limit` parameter to restrict the number of results returned

### Compatibility Issues

If you experience compatibility issues:

1. The legacy implementation is still available as `DatabaseToolLegacy`
2. Check for any code that might be directly importing from `database_tool.py`
3. Ensure all async methods are properly awaited

## Advanced Usage

### Custom Connection Management

You can access the connection manager directly for advanced use cases:

```python
from app.db.connection_manager import connection_manager

# Register a connection
conn_id = connection_manager.register_connection('postgresql://username:password@localhost:5432/mydb')

# Get a connection
conn = await connection_manager.get_connection(conn_id)

# Use the connection
# ...

# Close the connection
await connection_manager.close(conn_id)
```

### Transaction Management

For operations that require transactions:

```python
async with connection_manager.get_connection(conn_id) as conn:
    await conn.execute("BEGIN")
    try:
        # Perform multiple operations
        await conn.execute("INSERT INTO users (name) VALUES (?)", ("John",))
        await conn.execute("UPDATE counters SET value = value + 1 WHERE name = ?", ("user_count",))
        await conn.execute("COMMIT")
    except Exception as e:
        await conn.execute("ROLLBACK")
        raise
```

## Future Enhancements

Planned enhancements for future releases:

1. Schema introspection capabilities
2. Query explanation and optimization
3. Support for PostgreSQL extensions like pgvector
4. MCP server interface for AI agent integration