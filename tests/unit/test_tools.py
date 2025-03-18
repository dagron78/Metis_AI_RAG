"""
Unit tests for the Tool interface and implementations
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from app.rag.tools import Tool, ToolRegistry, RAGTool


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