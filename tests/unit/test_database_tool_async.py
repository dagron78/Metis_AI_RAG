"""
Unit tests for the async DatabaseTool
"""
import os
import pytest
import asyncio
import tempfile
import json
import pandas as pd
from pathlib import Path

from app.rag.tools.database_tool_async import DatabaseTool

# Skip PostgreSQL tests if no connection string is provided
POSTGRES_TEST_URL = os.environ.get("TEST_POSTGRES_URL")
SKIP_POSTGRES = POSTGRES_TEST_URL is None

@pytest.fixture
def database_tool():
    """Create a DatabaseTool instance for testing"""
    return DatabaseTool()

@pytest.fixture
async def sqlite_temp_db():
    """Create a temporary SQLite database for testing"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create a test table and insert data
    import aiosqlite
    async with aiosqlite.connect(path) as conn:
        await conn.execute("""
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                email TEXT
            )
        """)
        await conn.execute("""
            INSERT INTO test_users (name, age, email) VALUES
            ('John Doe', 35, 'john@example.com'),
            ('Jane Smith', 28, 'jane@example.com'),
            ('Bob Johnson', 42, 'bob@example.com')
        """)
        await conn.commit()
    
    # Return the path
    yield path
    
    # Clean up
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
async def temp_csv_file():
    """Create a temporary CSV file for testing"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    
    # Create test data
    data = {
        'product_id': [1, 2, 3, 4],
        'product_name': ['Smartphone', 'Laptop', 'Headphones', 'Tablet'],
        'price': [699.99, 1299.99, 149.99, 499.99],
        'category': ['Electronics', 'Electronics', 'Electronics', 'Electronics']
    }
    df = pd.DataFrame(data)
    
    # Write to CSV
    df.to_csv(path, index=False)
    
    # Return the path
    yield path
    
    # Clean up
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
async def temp_json_file():
    """Create a temporary JSON file for testing"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    
    # Create test data
    data = [
        {'city': 'New York', 'population': 8336817, 'country': 'USA'},
        {'city': 'Los Angeles', 'population': 3979576, 'country': 'USA'},
        {'city': 'Chicago', 'population': 2693976, 'country': 'USA'},
        {'city': 'Houston', 'population': 2320268, 'country': 'USA'},
        {'city': 'Phoenix', 'population': 1680992, 'country': 'USA'}
    ]
    
    # Write to JSON
    with open(path, 'w') as f:
        json.dump(data, f)
    
    # Return the path
    yield path
    
    # Clean up
    if os.path.exists(path):
        os.unlink(path)

@pytest.mark.asyncio
async def test_sqlite_query(database_tool, sqlite_temp_db):
    """Test querying a SQLite database"""
    # Execute a query
    result = await database_tool.execute({
        'query': 'SELECT * FROM test_users WHERE age > 30',
        'source': sqlite_temp_db
    })
    
    # Check the result
    assert 'error' not in result
    assert 'results' in result
    assert 'columns' in result
    assert 'row_count' in result
    assert 'execution_time' in result
    
    # Check the data
    assert result['row_count'] == 2
    assert len(result['results']) == 2
    assert result['columns'] == ['id', 'name', 'age', 'email']
    
    # Check specific values
    assert any(row['name'] == 'John Doe' for row in result['results'])
    assert any(row['name'] == 'Bob Johnson' for row in result['results'])

@pytest.mark.asyncio
async def test_sqlite_query_with_params(database_tool, sqlite_temp_db):
    """Test querying a SQLite database with parameters"""
    # Execute a query with parameters
    result = await database_tool.execute({
        'query': 'SELECT * FROM test_users WHERE age > :min_age',
        'source': sqlite_temp_db,
        'params': {'min_age': 30}
    })
    
    # Check the result
    assert 'error' not in result
    assert result['row_count'] == 2
    
    # Check specific values
    assert any(row['name'] == 'John Doe' for row in result['results'])
    assert any(row['name'] == 'Bob Johnson' for row in result['results'])

@pytest.mark.asyncio
async def test_sqlite_query_with_limit(database_tool, sqlite_temp_db):
    """Test querying a SQLite database with a limit"""
    # Execute a query with a limit
    result = await database_tool.execute({
        'query': 'SELECT * FROM test_users',
        'source': sqlite_temp_db,
        'limit': 2
    })
    
    # Check the result
    assert 'error' not in result
    assert result['row_count'] == 2
    assert len(result['results']) == 2

@pytest.mark.asyncio
async def test_csv_query(database_tool, temp_csv_file):
    """Test querying a CSV file"""
    # Execute a query
    result = await database_tool.execute({
        'query': 'SELECT * FROM data WHERE price > 500',
        'source': temp_csv_file
    })
    
    # Check the result
    assert 'error' not in result
    assert 'results' in result
    assert 'columns' in result
    assert 'row_count' in result
    assert 'execution_time' in result
    
    # Check the data
    assert result['row_count'] == 3
    assert len(result['results']) == 3
    
    # Check specific values
    product_names = [row['product_name'] for row in result['results']]
    assert 'Smartphone' in product_names
    assert 'Laptop' in product_names
    assert 'Tablet' in product_names

@pytest.mark.asyncio
async def test_json_query(database_tool, temp_json_file):
    """Test querying a JSON file"""
    # Execute a query
    result = await database_tool.execute({
        'query': 'SELECT * FROM data WHERE population > 3000000',
        'source': temp_json_file
    })
    
    # Check the result
    assert 'error' not in result
    assert 'results' in result
    assert 'columns' in result
    assert 'row_count' in result
    assert 'execution_time' in result
    
    # Check the data
    assert result['row_count'] == 2
    assert len(result['results']) == 2
    
    # Check specific values
    cities = [row['city'] for row in result['results']]
    assert 'New York' in cities
    assert 'Los Angeles' in cities

@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_POSTGRES, reason="PostgreSQL connection string not provided")
async def test_postgres_query():
    """Test querying a PostgreSQL database"""
    # Skip if no PostgreSQL connection string
    if SKIP_POSTGRES:
        return
    
    # Create a database tool
    database_tool = DatabaseTool()
    
    # Execute a query
    result = await database_tool.execute({
        'query': 'SELECT 1 as test',
        'source': POSTGRES_TEST_URL
    })
    
    # Check the result
    assert 'error' not in result
    assert 'results' in result
    assert 'columns' in result
    assert 'row_count' in result
    assert 'execution_time' in result
    
    # Check the data
    assert result['row_count'] == 1
    assert len(result['results']) == 1
    assert result['results'][0]['test'] == 1

@pytest.mark.asyncio
async def test_error_handling(database_tool):
    """Test error handling"""
    # Execute a query with an invalid source
    result = await database_tool.execute({
        'query': 'SELECT * FROM test',
        'source': 'nonexistent.db'
    })
    
    # Check the result
    assert 'error' in result
    assert 'results' not in result

@pytest.mark.asyncio
async def test_input_validation(database_tool):
    """Test input validation"""
    # Missing query
    result = await database_tool.execute({
        'source': 'test.db'
    })
    
    # Check the result
    assert 'error' in result
    assert result['error'] == 'Query is required'
    
    # Missing source
    result = await database_tool.execute({
        'query': 'SELECT * FROM test'
    })
    
    # Check the result
    assert 'error' in result
    assert result['error'] == 'Data source is required'