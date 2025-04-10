"""
Simplified unit tests for the async DatabaseTool
"""
import os
import pytest
import pytest_asyncio
import asyncio
import tempfile
import json
import pandas as pd
from pathlib import Path

# Import the connection manager directly
from app.db.connection_manager import connection_manager

# Create a simplified version of the Tool base class for testing
class MockTool:
    """Mock Tool class for testing"""
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.logger = type('MockLogger', (), {
            'info': lambda *args, **kwargs: None,
            'error': lambda *args, **kwargs: None,
            'debug': lambda *args, **kwargs: None,
            'warning': lambda *args, **kwargs: None
        })()

# Import the DatabaseTool class directly from the file
import sys
import inspect
from pathlib import Path

# Get the content of the database_tool_async.py file
database_tool_path = Path(__file__).parent.parent.parent / "app" / "rag" / "tools" / "database_tool_async.py"
with open(database_tool_path, "r") as f:
    code = f.read()

# Replace the Tool import with our MockTool
code = code.replace("from app.rag.tools.base import Tool", "from tests.unit.test_database_tool_simple import MockTool as Tool")

# Create a namespace and execute the code
namespace = {'__file__': str(database_tool_path), 'connection_manager': connection_manager}
exec(code, namespace)

# Get the DatabaseTool class from the namespace
DatabaseTool = namespace['DatabaseTool']

@pytest_asyncio.fixture
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

@pytest_asyncio.fixture
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

@pytest_asyncio.fixture
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

@pytest.fixture
def database_tool():
    """Create a DatabaseTool instance for testing"""
    return DatabaseTool()

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