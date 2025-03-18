"""
Unit tests for the Tool interface and implementations
"""
import pytest
import asyncio
import math
from unittest.mock import MagicMock, AsyncMock

from app.rag.tools import Tool, ToolRegistry, RAGTool, CalculatorTool, DatabaseTool


class TestTool(Tool):
    """Test implementation of the Tool abstract base class"""
    
    def __init__(self, name="test_tool", description="Test tool"):
        super().__init__(name=name, description=description)
    
    async def execute(self, input_data):
        return {"result": f"Executed {self.name} with input: {input_data}"}
    
    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {
                "test_param": {
                    "type": "string",
                    "description": "Test parameter"
                }
            }
        }
    
    def get_output_schema(self):
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Test result"
                }
            }
        }
    
    def get_examples(self):
        return [
            {
                "input": {"test_param": "test_value"},
                "output": {"result": "Executed test_tool with input: {'test_param': 'test_value'}"}
            }
        ]


class TestToolRegistry:
    """Tests for the ToolRegistry class"""
    
    def test_register_and_get_tool(self):
        """Test registering and retrieving a tool"""
        registry = ToolRegistry()
        tool = TestTool()
        
        # Register tool
        registry.register_tool(tool)
        
        # Get tool
        retrieved_tool = registry.get_tool("test_tool")
        
        assert retrieved_tool is tool
        assert retrieved_tool.name == "test_tool"
        assert retrieved_tool.get_description() == "Test tool"
    
    def test_list_tools(self):
        """Test listing registered tools"""
        registry = ToolRegistry()
        tool1 = TestTool(name="tool1", description="Tool 1")
        tool2 = TestTool(name="tool2", description="Tool 2")
        
        # Register tools
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        # List tools
        tools = registry.list_tools()
        
        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[0]["description"] == "Tool 1"
        assert tools[1]["name"] == "tool2"
        assert tools[1]["description"] == "Tool 2"
    
    def test_get_tool_examples(self):
        """Test getting examples for a tool"""
        registry = ToolRegistry()
        tool = TestTool()
        
        # Register tool
        registry.register_tool(tool)
        
        # Get examples
        examples = registry.get_tool_examples("test_tool")
        
        assert len(examples) == 1
        assert examples[0]["input"] == {"test_param": "test_value"}
        assert examples[0]["output"] == {"result": "Executed test_tool with input: {'test_param': 'test_value'}"}
    
    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist"""
        registry = ToolRegistry()
        
        # Get nonexistent tool
        tool = registry.get_tool("nonexistent")
        
        assert tool is None


class TestRAGTool:
    """Tests for the RAGTool implementation"""
    
    @pytest.mark.asyncio
    async def test_rag_tool_execute(self):
        """Test executing the RAG tool"""
        # Create mock RAG engine
        mock_rag_engine = AsyncMock()
        mock_rag_engine.retrieve.return_value = [
            {
                "content": "Test content",
                "metadata": {"document_id": "doc123"},
                "score": 0.95
            }
        ]
        
        # Create RAG tool
        rag_tool = RAGTool(rag_engine=mock_rag_engine)
        
        # Execute tool
        result = await rag_tool.execute({
            "query": "Test query",
            "top_k": 3
        })
        
        # Check result
        assert "chunks" in result
        assert len(result["chunks"]) == 1
        assert result["chunks"][0]["content"] == "Test content"
        assert result["chunks"][0]["metadata"] == {"document_id": "doc123"}
        assert result["chunks"][0]["score"] == 0.95
        assert "sources" in result
        assert "doc123" in result["sources"]
        assert "execution_time" in result
        
        # Check RAG engine was called correctly
        mock_rag_engine.retrieve.assert_called_once_with(
            query="Test query",
            top_k=3,
            filters={}
        )
    
    def test_rag_tool_schemas(self):
        """Test RAG tool schemas"""
        # Create mock RAG engine
        mock_rag_engine = MagicMock()
        
        # Create RAG tool
        rag_tool = RAGTool(rag_engine=mock_rag_engine)
        
        # Check input schema
        input_schema = rag_tool.get_input_schema()
        assert input_schema["type"] == "object"
        assert "query" in input_schema["properties"]
        assert "top_k" in input_schema["properties"]
        assert "filters" in input_schema["properties"]
        assert input_schema["required"] == ["query"]
        
        # Check output schema
        output_schema = rag_tool.get_output_schema()
        assert output_schema["type"] == "object"
        assert "chunks" in output_schema["properties"]
        assert "sources" in output_schema["properties"]
        assert "execution_time" in output_schema["properties"]
        
        # Check examples
        examples = rag_tool.get_examples()
        assert len(examples) > 0
        assert "input" in examples[0]
        assert "output" in examples[0]


class TestCalculatorTool:
    """Tests for the CalculatorTool implementation"""
    
    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        """Test basic arithmetic operations"""
        calculator = CalculatorTool()
        
        # Test addition
        result = await calculator.execute({"expression": "2 + 3"})
        assert "result" in result
        assert result["result"] == 5
        
        # Test subtraction
        result = await calculator.execute({"expression": "10 - 4"})
        assert result["result"] == 6
        
        # Test multiplication
        result = await calculator.execute({"expression": "3 * 5"})
        assert result["result"] == 15
        
        # Test division
        result = await calculator.execute({"expression": "20 / 4"})
        assert result["result"] == 5
        
        # Test order of operations
        result = await calculator.execute({"expression": "2 + 3 * 4"})
        assert result["result"] == 14
        
        # Test parentheses
        result = await calculator.execute({"expression": "(2 + 3) * 4"})
        assert result["result"] == 20
    
    @pytest.mark.asyncio
    async def test_math_functions(self):
        """Test mathematical functions"""
        calculator = CalculatorTool()
        
        # Test square root
        result = await calculator.execute({"expression": "sqrt(16)"})
        assert result["result"] == 4
        
        # Test power
        result = await calculator.execute({"expression": "pow(2, 3)"})
        assert result["result"] == 8
        
        # Test trigonometric functions
        result = await calculator.execute({"expression": "sin(radians(30))"})
        assert math.isclose(result["result"], 0.5, abs_tol=1e-10)
        
        result = await calculator.execute({"expression": "cos(radians(60))"})
        assert math.isclose(result["result"], 0.5, abs_tol=1e-10)
        
        # Test logarithmic functions
        result = await calculator.execute({"expression": "log10(100)"})
        assert result["result"] == 2
    
    @pytest.mark.asyncio
    async def test_variables(self):
        """Test variable substitution"""
        calculator = CalculatorTool()
        
        # Test simple variable
        result = await calculator.execute({
            "expression": "x + 5",
            "variables": {"x": 10}
        })
        assert result["result"] == 15
        
        # Test multiple variables
        result = await calculator.execute({
            "expression": "x * y + z",
            "variables": {"x": 2, "y": 3, "z": 4}
        })
        assert result["result"] == 10
        
        # Test variables in functions
        result = await calculator.execute({
            "expression": "sqrt(x) + pow(y, 2)",
            "variables": {"x": 16, "y": 3}
        })
        assert result["result"] == 13
    
    @pytest.mark.asyncio
    async def test_unit_conversion(self):
        """Test unit conversions"""
        calculator = CalculatorTool()
        
        # Test length conversion
        result = await calculator.execute({
            "expression": "5",
            "unit_conversion": "km_to_miles"
        })
        assert math.isclose(result["result"], 3.10686, abs_tol=1e-5)
        assert "steps" in result
        assert len(result["steps"]) == 2
        
        # Test temperature conversion
        result = await calculator.execute({
            "expression": "100",
            "unit_conversion": "c_to_f"
        })
        assert result["result"] == 212.0
        assert "steps" in result
        assert len(result["steps"]) == 2
        
        # Test weight conversion
        result = await calculator.execute({
            "expression": "10",
            "unit_conversion": "kg_to_lb"
        })
        assert math.isclose(result["result"], 22.0462, abs_tol=1e-4)
    
    @pytest.mark.asyncio
    async def test_precision(self):
        """Test result precision"""
        calculator = CalculatorTool()
        
        # Test with precision
        result = await calculator.execute({
            "expression": "1 / 3",
            "precision": 2
        })
        assert result["result"] == 0.33
        assert "steps" in result
        assert len(result["steps"]) == 1
        
        # Test with precision and unit conversion
        result = await calculator.execute({
            "expression": "10",
            "unit_conversion": "km_to_miles",
            "precision": 3
        })
        assert result["result"] == 6.214
        assert "steps" in result
        assert len(result["steps"]) == 3  # Initial result, conversion, and rounding
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling"""
        calculator = CalculatorTool()
        
        # Test division by zero
        result = await calculator.execute({"expression": "1 / 0"})
        assert "error" in result
        
        # Test invalid expression
        result = await calculator.execute({"expression": "1 + * 2"})
        assert "error" in result
        
        # Test invalid function
        result = await calculator.execute({"expression": "invalid_func(10)"})
        assert "error" in result
        
        # Test missing required parameter
        result = await calculator.execute({})
        assert "error" in result
        
        # Test invalid unit conversion
        result = await calculator.execute({
            "expression": "10",
            "unit_conversion": "invalid_conversion"
        })
        assert "error" in result
    
    def test_calculator_schemas(self):
        """Test calculator tool schemas"""
        calculator = CalculatorTool()
        
        # Check input schema
        input_schema = calculator.get_input_schema()
        assert input_schema["type"] == "object"
        assert "expression" in input_schema["properties"]
        assert "variables" in input_schema["properties"]
        assert "precision" in input_schema["properties"]
        assert "unit_conversion" in input_schema["properties"]
        assert input_schema["required"] == ["expression"]
        
        # Check output schema
        output_schema = calculator.get_output_schema()
        assert output_schema["type"] == "object"
        assert "result" in output_schema["properties"]
        assert "steps" in output_schema["properties"]
        assert "execution_time" in output_schema["properties"]
        assert "error" in output_schema["properties"]
        
        # Check examples
        examples = calculator.get_examples()
        assert len(examples) > 0
        assert "input" in examples[0]
        assert "output" in examples[0]


class TestDatabaseTool:
    """Tests for the DatabaseTool implementation"""
    
    @pytest.mark.asyncio
    async def test_sqlite_query(self, tmp_path):
        """Test querying a SQLite database"""
        import sqlite3
        import os
        
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
        import pandas as pd
        import os
        
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
        
        # Test aggregation query
        result = await db_tool.execute({
            "query": "SELECT category, AVG(price) as avg_price FROM data GROUP BY category",
            "source": "test.csv"
        })
        
        # Check result
        assert len(result["results"]) == 2
        assert result["results"][0]["category"] == "A"
        assert result["results"][1]["category"] == "B"
        assert abs(result["results"][0]["avg_price"] - 19.99) < 0.01
        assert abs(result["results"][1]["avg_price"] - 19.99) < 0.01
    
    @pytest.mark.asyncio
    async def test_json_query(self, tmp_path):
        """Test querying a JSON file"""
        import json
        import os
        
        # Create a test JSON file
        json_path = os.path.join(tmp_path, "test.json")
        data = [
            {"id": 1, "name": "user1", "email": "user1@example.com", "active": True},
            {"id": 2, "name": "user2", "email": "user2@example.com", "active": False},
            {"id": 3, "name": "user3", "email": "user3@example.com", "active": True}
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
        assert result["results"][0]["email"] == "user1@example.com"
        assert result["results"][0]["active"] == 1  # SQLite converts boolean to integer
        
        # Test query with filter
        result = await db_tool.execute({
            "query": "SELECT * FROM data WHERE active = 1",
            "source": "test.json"
        })
        
        # Check result
        assert len(result["results"]) == 2
        assert result["results"][0]["name"] == "user1"
        assert result["results"][1]["name"] == "user3"
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling"""
        db_tool = DatabaseTool()
        
        # Test missing query
        result = await db_tool.execute({
            "source": "test.db"
        })
        assert "error" in result
        
        # Test missing source
        result = await db_tool.execute({
            "query": "SELECT * FROM test"
        })
        assert "error" in result
        
        # Test invalid source
        result = await db_tool.execute({
            "query": "SELECT * FROM test",
            "source": "nonexistent.db"
        })
        assert "error" in result
    
    def test_database_schemas(self):
        """Test database tool schemas"""
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