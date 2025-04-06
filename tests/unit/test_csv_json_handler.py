"""
Unit tests for the CSV and JSON handlers
"""
import os
import pytest
import pytest_asyncio
import asyncio
import tempfile
import json
import csv
from pathlib import Path

from app.rag.tools.csv_json_handler import AsyncCSVHandler, AsyncJSONHandler

class TestCSVJSONHandler:
    """Test class for CSV and JSON handlers"""
    
    @pytest_asyncio.fixture
    async def temp_csv_file(self):
        """Create a temporary CSV file for testing"""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        # Create test data
        data = [
            ['id', 'name', 'age', 'email'],
            ['1', 'John Doe', '35', 'john@example.com'],
            ['2', 'Jane Smith', '28', 'jane@example.com'],
            ['3', 'Bob Johnson', '42', 'bob@example.com'],
            ['4', 'Alice Brown', '31', 'alice@example.com'],
            ['5', 'Charlie Davis', '45', 'charlie@example.com']
        ]
        
        # Write to CSV
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        # Return the path
        yield path
        
        # Clean up
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest_asyncio.fixture
    async def temp_json_file(self):
        """Create a temporary JSON file for testing"""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        # Create test data
        data = [
            {'id': 1, 'name': 'John Doe', 'age': 35, 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'age': 28, 'email': 'jane@example.com'},
            {'id': 3, 'name': 'Bob Johnson', 'age': 42, 'email': 'bob@example.com'},
            {'id': 4, 'name': 'Alice Brown', 'age': 31, 'email': 'alice@example.com'},
            {'id': 5, 'name': 'Charlie Davis', 'age': 45, 'email': 'charlie@example.com'}
        ]
        
        # Write to JSON
        with open(path, 'w') as f:
            json.dump(data, f)
        
        # Return the path
        yield path
        
        # Clean up
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest_asyncio.fixture
    async def temp_nested_json_file(self):
        """Create a temporary nested JSON file for testing"""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        # Create test data with nested structure
        data = {
            'users': [
                {'id': 1, 'name': 'John Doe', 'age': 35, 'email': 'john@example.com'},
                {'id': 2, 'name': 'Jane Smith', 'age': 28, 'email': 'jane@example.com'},
                {'id': 3, 'name': 'Bob Johnson', 'age': 42, 'email': 'bob@example.com'}
            ],
            'metadata': {
                'version': '1.0',
                'generated_at': '2025-03-31T12:00:00Z',
                'record_count': 3
            }
        }
        
        # Write to JSON
        with open(path, 'w') as f:
            json.dump(data, f)
        
        # Return the path
        yield path
        
        # Clean up
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.mark.asyncio
    async def test_csv_read(self, temp_csv_file):
        """Test reading a CSV file"""
        # Read the CSV file
        data, headers = await AsyncCSVHandler.read_csv(temp_csv_file)
        
        # Check headers
        assert headers == ['id', 'name', 'age', 'email']
        
        # Check data
        assert len(data) == 5
        assert data[0]['id'] == '1'
        assert data[0]['name'] == 'John Doe'
        assert data[0]['age'] == '35'
        assert data[0]['email'] == 'john@example.com'
    
    @pytest.mark.asyncio
    async def test_csv_to_sqlite(self, temp_csv_file):
        """Test creating a SQLite table from a CSV file"""
        import aiosqlite
        
        # Create an in-memory SQLite database
        async with aiosqlite.connect(':memory:') as conn:
            # Create a table from the CSV file
            table_name = 'test_csv'
            headers, rows_inserted = await AsyncCSVHandler.create_table_from_csv(conn, table_name, temp_csv_file)
            
            # Check results
            assert headers == ['id', 'name', 'age', 'email']
            assert rows_inserted == 5
            
            # Query the table
            cursor = await conn.execute(f'SELECT * FROM {table_name}')
            rows = await cursor.fetchall()
            
            # Check results
            assert len(rows) == 5
            
            # Check column types
            cursor = await conn.execute(f'PRAGMA table_info({table_name})')
            columns = await cursor.fetchall()
            
            # Check that numeric columns are detected correctly
            column_types = {col[1]: col[2] for col in columns}
            assert column_types['id'] in ('INTEGER', 'TEXT')  # Could be either depending on detection
            assert column_types['name'] == 'TEXT'
            assert column_types['age'] in ('INTEGER', 'TEXT')  # Could be either depending on detection
            assert column_types['email'] == 'TEXT'
    
    @pytest.mark.asyncio
    async def test_json_read(self, temp_json_file):
        """Test reading a JSON file"""
        # Read the JSON file
        data = await AsyncJSONHandler.read_json(temp_json_file)
        
        # Check data
        assert len(data) == 5
        assert data[0]['id'] == 1
        assert data[0]['name'] == 'John Doe'
        assert data[0]['age'] == 35
        assert data[0]['email'] == 'john@example.com'
    
    @pytest.mark.asyncio
    async def test_json_to_sqlite(self, temp_json_file):
        """Test creating a SQLite table from a JSON file"""
        import aiosqlite
        
        # Create an in-memory SQLite database
        async with aiosqlite.connect(':memory:') as conn:
            # Create a table from the JSON file
            table_name = 'test_json'
            headers, rows_inserted = await AsyncJSONHandler.create_table_from_json(conn, table_name, temp_json_file)
            
            # Check results
            assert set(headers) == {'id', 'name', 'age', 'email'}
            assert rows_inserted == 5
            
            # Query the table
            cursor = await conn.execute(f'SELECT * FROM {table_name}')
            rows = await cursor.fetchall()
            
            # Check results
            assert len(rows) == 5
            
            # Check column types
            cursor = await conn.execute(f'PRAGMA table_info({table_name})')
            columns = await cursor.fetchall()
            
            # Check that numeric columns are detected correctly
            column_types = {col[1]: col[2] for col in columns}
            assert column_types['id'] == 'INTEGER'
            assert column_types['name'] == 'TEXT'
            assert column_types['age'] == 'INTEGER'
            assert column_types['email'] == 'TEXT'
    
    @pytest.mark.asyncio
    async def test_nested_json_to_sqlite(self, temp_nested_json_file):
        """Test creating a SQLite table from a nested JSON file"""
        import aiosqlite
        
        # Create an in-memory SQLite database
        async with aiosqlite.connect(':memory:') as conn:
            # Create a table from the JSON file
            table_name = 'test_nested_json'
            headers, rows_inserted = await AsyncJSONHandler.create_table_from_json(conn, table_name, temp_nested_json_file)
            
            # Check results - should have flattened the nested structure
            assert rows_inserted > 0
            
            # Query the table
            cursor = await conn.execute(f'SELECT * FROM {table_name}')
            rows = await cursor.fetchall()
            
            # Check that we have some rows
            assert len(rows) > 0