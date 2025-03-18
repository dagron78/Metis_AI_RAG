"""
Tool - Abstract base class for tools used in the Metis_RAG system
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Tool(ABC):
    """
    Abstract base class for tools
    
    Tools are components that can be used by the system to perform specific tasks,
    such as retrieving information, performing calculations, or querying databases.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize a tool
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"app.rag.tools.{name}")
    
    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """
        Execute the tool with the given input
        
        Args:
            input_data: Tool-specific input
            
        Returns:
            Tool-specific output
        """
        pass
    
    def get_description(self) -> str:
        """
        Get a description of the tool
        
        Returns:
            Tool description
        """
        return self.description
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Get the input schema for the tool
        
        Returns:
            JSON Schema for tool input
        """
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the output schema for the tool
        
        Returns:
            JSON Schema for tool output
        """
        pass
    
    @abstractmethod
    def get_examples(self) -> List[Dict[str, Any]]:
        """
        Get examples of tool usage
        
        Returns:
            List of example input/output pairs
        """
        pass