"""
Unit tests for the DatabaseTool
"""
import pytest
import os
import sqlite3
import pandas as pd
import tempfile
from unittest.mock import MagicMock, AsyncMock

from app.rag.tools import DatabaseTool


class TestDatabaseTool:
    """Tests for the DatabaseTool implementation"""
    
    @pytest.mark.asyncio
    async def test_sqlite_query(self, tmp_path):
        """Test querying a SQLite database"""
        # Create a test database
        db_path = os.path.join(tmp_path, "test.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value REAL
            )
        """)
        
        # Insert test data
        test_data = [
            (1, "item1", 10.5),
            (2, "item2", 20.75),
            (3, "item3", 15.25)
        ]
        cursor.executemany("INSERT INTO test_table VALUES (?, ?, ?)", test_data)
        conn.commit()
        conn.close()
        
        # Create database tool
        db_tool = DatabaseTool(data_dir=str(tmp_path))
        
        # Test simple query
        result = await db_tool.execute({
            "query": "SELECT * FROM test_table",
            "source": "test.db"
        })
        
        # Check result
        assert "results" in result
        assert len(result["results"]) == 3
        assert result["results"][0]["id"] == 1
        assert result["results"][0]["name"] == "item1"
        assert result["results"][0]["value"] == 10.5
        assert "columns" in result
        assert result["columns"] == ["id", "name", "value"]
        assert "row_count" in result
        assert result["row_count"] == 3
        assert "execution_time" in result
        
        # Test query with filter
        result = await db_tool.execute({
            "query": "SELECT * FROM test_table WHERE value > ?",
            "source": "test.db",
            "params": [15.0]
        })
        
        # Check result
        assert len(result["results"]) == 2
        assert result["results"][0]["name"] == "item2"
        assert result["results"][1]["name"] == "item3"
        
        # Test query with limit
        result = await db_tool.execute({
            "query": "SELECT * FROM test_table ORDER BY value DESC",
            "source": "test.db",
            "limit": 1
        })
        
        # Check result
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "item2"
    
    @pytest.mark.asyncio
    async def test_csv_query(self, tmp_path):
        """Test querying a CSV file"""
        # Create a test CSV file
        csv_path = os.path.join(tmp_path, "test.csv")
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["product1", "product2", "product3"],
            "price": [9.99, 19.99, 29.99],
            "category": ["A", "B", "A"]
        })
        df.to_csv(csv_path, index=False)
        
        # Create database tool
        db_tool = DatabaseTool(data_dir=str(tmp_path))
        
        # Test simple query
        result = await db_tool.execute({
            "query": "SELECT * FROM data",
            "source": "test.csv"
        })
        
        # Check result
        assert "results" in result
        assert len(result["results"]) == 3
        assert result["results"][0]["id"] == 1
        assert result["results"][0]["name"] == "product1"
        assert result["results"][0]["price"] == 9.99
        assert "columns" in result
        assert set(result["columns"]) == set(["id", "name", "price", "category"])
        
        # Test query with filter
        result = await db_tool.execute({
            "query": "SELECT * FROM data WHERE category = 'A'",
            "source": "test.csv"
        })
        
        # Check result
        assert len(result["results"]) == 2
        assert result["results"][0]["name"] == "product1"
        assert result["results"][1]["name"] == "product3"
    
    @pytest.mark.asyncio
    async def test_json_query(self, tmp_path):
        """Test querying a JSON file"""
        import json
        
        # Create a test JSON file
        json_path = os.path.join(tmp_path, "test.json")
        data = [
            {"id": 1, "name": "user1", "role": "admin", "active": True},
            {"id": 2, "name": "user2", "role": "user", "active": True},
            {"id": 3, "name": "user3", "role": "user", "active": False}
        ]
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        # Create database tool
        db_tool = DatabaseTool(data_dir=str(tmp_path))
        
        # Test simple query
        result = await db_tool.execute({
            "query": "SELECT * FROM data",
            "source": "test.json"
        })
        
        # Check result
        assert "results" in result
        assert len(result["results"]) == 3
        assert result["results"][0]["id"] == 1
        assert result["results"][0]["name"] == "user1"
        assert result["results"][0]["role"] == "admin"
        
        # Test query with filter
        result = await db_tool.execute({
            "query": "SELECT * FROM data WHERE active = true",
            "source": "test.json"
        })
        
        # Check result
        assert len(result["results"]) == 2
        assert result["results"][0]["name"] == "user1"
        assert result["results"][1]["name"] == "user2"
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling"""
        # Create database tool with non-existent directory
        db_tool = DatabaseTool(data_dir="/nonexistent")
        
        # Test query with non-existent source
        result = await db_tool.execute({
            "query": "SELECT * FROM data",
            "source": "nonexistent.db"
        })
        
        # Check result
        assert "error" in result
        
        # Test query with invalid SQL
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test database
            db_path = os.path.join(temp_dir, "test.db")
            conn = sqlite3.connect(db_path)
            conn.close()
            
            # Create database tool
            db_tool = DatabaseTool(data_dir=temp_dir)
            
            # Test invalid SQL
            result = await db_tool.execute({
                "query": "INVALID SQL",
                "source": "test.db"
            })
            
            # Check result
            assert "error" in result
    
    def test_database_schemas(self):
        """Test database tool schemas"""
        # Create database tool
        db_tool = DatabaseTool()
        
        # Check input schema
        input_schema = db_tool.get_input_schema()
        assert input_schema["type"] == "object"
        assert "query" in input_schema["properties"]
        assert "source" in input_schema["properties"]
        assert "params" in input_schema["properties"]
        assert "limit" in input_schema["properties"]
        assert input_schema["required"] == ["query", "source"]
        
        # Check output schema
        output_schema = db_tool.get_output_schema()
        assert output_schema["type"] == "object"
        assert "results" in output_schema["properties"]
        assert "columns" in output_schema["properties"]
        assert "row_count" in output_schema["properties"]
        assert "execution_time" in output_schema["properties"]
        assert "error" in output_schema["properties"]
        
        # Check examples
        examples = db_tool.get_examples()
        assert len(examples) > 0
        assert "input" in examples[0]
        assert "output" in examples[0]