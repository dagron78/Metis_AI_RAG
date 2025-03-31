"""
Unit tests for the database connection manager
"""
import os
import pytest
import asyncio
import tempfile
from pathlib import Path

from app.db.connection_manager import connection_manager

# Skip PostgreSQL tests if no connection string is provided
POSTGRES_TEST_URL = os.environ.get("TEST_POSTGRES_URL")
SKIP_POSTGRES = POSTGRES_TEST_URL is None

@pytest.fixture
async def sqlite_temp_db():
    """Create a temporary SQLite database for testing"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Register the connection
    conn_id = connection_manager.register_connection(path)
    
    # Return the connection ID and path
    yield conn_id, path
    
    # Clean up
    await connection_manager.close(conn_id)
    if os.path.exists(path):
        os.unlink(path)

@pytest.mark.asyncio
async def test_sqlite_connection_registration():
    """Test SQLite connection registration"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Register the connection
        conn_id = connection_manager.register_connection(path)
        
        # Verify connection type
        assert connection_manager.get_connection_type(conn_id) == 'sqlite'
        
        # Verify connection string
        assert connection_manager.get_connection_string(conn_id) == path
    finally:
        # Clean up
        await connection_manager.close(conn_id)
        if os.path.exists(path):
            os.unlink(path)

@pytest.mark.asyncio
async def test_sqlite_connection_acquisition(sqlite_temp_db):
    """Test SQLite connection acquisition"""
    conn_id, path = sqlite_temp_db
    
    # Get a connection
    conn = await connection_manager.get_sqlite_connection(conn_id)
    
    # Verify it's a valid connection
    assert conn is not None
    
    # Create a table and insert data
    await conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
    await conn.execute("INSERT INTO test (name) VALUES (?)", ("test_value",))
    await conn.commit()
    
    # Query the data
    cursor = await conn.execute("SELECT name FROM test WHERE id = 1")
    row = await cursor.fetchone()
    await cursor.close()
    
    # Verify the data
    assert row is not None
    assert row["name"] == "test_value"

@pytest.mark.asyncio
async def test_sqlite_connection_reuse(sqlite_temp_db):
    """Test SQLite connection reuse"""
    conn_id, path = sqlite_temp_db
    
    # Get a connection
    conn1 = await connection_manager.get_sqlite_connection(conn_id)
    
    # Get another connection with the same ID
    conn2 = await connection_manager.get_sqlite_connection(conn_id)
    
    # Verify they're the same connection
    assert conn1 is conn2

@pytest.mark.asyncio
async def test_connection_manager_close(sqlite_temp_db):
    """Test connection manager close method"""
    conn_id, path = sqlite_temp_db
    
    # Get a connection
    conn = await connection_manager.get_sqlite_connection(conn_id)
    
    # Close the connection
    await connection_manager.close(conn_id)
    
    # Verify the connection is closed
    assert conn_id not in connection_manager._pools

@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_POSTGRES, reason="PostgreSQL connection string not provided")
async def test_postgres_connection_registration():
    """Test PostgreSQL connection registration"""
    # Skip if no PostgreSQL connection string
    if SKIP_POSTGRES:
        return
    
    # Register the connection
    conn_id = connection_manager.register_connection(POSTGRES_TEST_URL)
    
    try:
        # Verify connection type
        assert connection_manager.get_connection_type(conn_id) == 'postgres'
        
        # Verify connection string
        assert connection_manager.get_connection_string(conn_id) == POSTGRES_TEST_URL
    finally:
        # Clean up
        await connection_manager.close(conn_id)

@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_POSTGRES, reason="PostgreSQL connection string not provided")
async def test_postgres_connection_acquisition():
    """Test PostgreSQL connection acquisition"""
    # Skip if no PostgreSQL connection string
    if SKIP_POSTGRES:
        return
    
    # Register the connection
    conn_id = connection_manager.register_connection(POSTGRES_TEST_URL)
    
    try:
        # Get a connection
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        # Verify it's a valid connection
        assert conn is not None
        
        # Execute a simple query
        result = await conn.fetchval("SELECT 1")
        
        # Verify the result
        assert result == 1
    finally:
        # Clean up
        await connection_manager.close(conn_id)

@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_POSTGRES, reason="PostgreSQL connection string not provided")
async def test_postgres_connection_release():
    """Test PostgreSQL connection release"""
    # Skip if no PostgreSQL connection string
    if SKIP_POSTGRES:
        return
    
    # Register the connection
    conn_id = connection_manager.register_connection(POSTGRES_TEST_URL)
    
    try:
        # Get a connection
        conn = await connection_manager.get_postgres_connection(conn_id)
        
        # Release the connection
        await connection_manager.release_postgres_connection(conn_id, conn)
        
        # Verify we can get another connection
        conn2 = await connection_manager.get_postgres_connection(conn_id)
        assert conn2 is not None
    finally:
        # Clean up
        await connection_manager.close(conn_id)

@pytest.mark.asyncio
async def test_generic_get_connection(sqlite_temp_db):
    """Test generic get_connection method"""
    conn_id, path = sqlite_temp_db
    
    # Get a connection using the generic method
    conn = await connection_manager.get_connection(conn_id)
    
    # Verify it's a valid connection
    assert conn is not None
    
    # Create a table and insert data
    await conn.execute("CREATE TABLE test_generic (id INTEGER PRIMARY KEY, name TEXT)")
    await conn.execute("INSERT INTO test_generic (name) VALUES (?)", ("generic_test",))
    await conn.commit()
    
    # Query the data
    cursor = await conn.execute("SELECT name FROM test_generic WHERE id = 1")
    row = await cursor.fetchone()
    await cursor.close()
    
    # Verify the data
    assert row is not None
    assert row["name"] == "generic_test"