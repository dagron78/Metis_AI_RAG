"""
Unit tests for the ToolRegistry
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.rag.tools import ToolRegistry
from tests.unit.rag.tools.conftest import MockTool


class TestToolRegistry:
    """Tests for the ToolRegistry class"""
    
    def test_register_and_get_tool(self):
        """Test registering and retrieving a tool"""
        registry = ToolRegistry()
        tool = MockTool()
        
        # Register tool
        registry.register_tool(tool)
        
        # Get tool
        retrieved_tool = registry.get_tool("mock_tool")
        
        assert retrieved_tool is tool
        assert retrieved_tool.name == "mock_tool"
        assert retrieved_tool.get_description() == "Mock tool"
    
    def test_list_tools(self):
        """Test listing registered tools"""
        registry = ToolRegistry()
        tool1 = MockTool(name="tool1", description="Tool 1")
        tool2 = MockTool(name="tool2", description="Tool 2")
        
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
        tool = MockTool()
        
        # Register tool
        registry.register_tool(tool)
        
        # Get examples
        examples = registry.get_tool_examples("mock_tool")
        
        assert len(examples) == 1
        assert "input" in examples[0]
        assert "output" in examples[0]
    
    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist"""
        registry = ToolRegistry()
        
        # Get nonexistent tool
        tool = registry.get_tool("nonexistent")
        
        assert tool is None