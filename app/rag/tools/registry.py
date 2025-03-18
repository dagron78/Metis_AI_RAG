"""
ToolRegistry - Registry for managing tools in the Metis_RAG system
"""
import logging
from typing import Dict, List, Optional, Any

from app.rag.tools.base import Tool

class ToolRegistry:
    """
    Registry for managing tools
    
    The ToolRegistry maintains a collection of tools that can be used by the system.
    It provides methods for registering, retrieving, and listing tools.
    """
    
    def __init__(self):
        """
        Initialize the tool registry
        """
        self.tools: Dict[str, Tool] = {}
        self.logger = logging.getLogger("app.rag.tools.registry")
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool with the registry
        
        Args:
            tool: Tool to register
        """
        self.logger.info(f"Registering tool: {tool.name}")
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name
        
        Args:
            name: Tool name
            
        Returns:
            Tool if found, None otherwise
        """
        tool = self.tools.get(name)
        if not tool:
            self.logger.warning(f"Tool not found: {name}")
        return tool
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools
        
        Returns:
            List of tool information dictionaries
        """
        return [
            {
                "name": tool.name,
                "description": tool.get_description(),
                "input_schema": tool.get_input_schema(),
                "output_schema": tool.get_output_schema()
            }
            for tool in self.tools.values()
        ]
    
    def get_tool_examples(self, name: str) -> List[Dict[str, Any]]:
        """
        Get examples for a specific tool
        
        Args:
            name: Tool name
            
        Returns:
            List of example input/output pairs
        """
        tool = self.get_tool(name)
        if tool:
            return tool.get_examples()
        return []
    
    def get_tool_count(self) -> int:
        """
        Get the number of registered tools
        
        Returns:
            Number of tools
        """
        return len(self.tools)