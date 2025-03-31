"""
Tool Initializer - Module for initializing and registering tools
"""
import logging
from typing import Optional

from app.rag.tools.registry import ToolRegistry
from app.rag.tools.rag_tool import RAGTool
from app.rag.tools.calculator_tool import CalculatorTool
from app.rag.tools.database_tool import DatabaseTool
from app.rag.tools.postgresql_tool import PostgreSQLTool

logger = logging.getLogger("app.rag.tool_initializer")

# Create a singleton tool registry
tool_registry = ToolRegistry()

def initialize_tools(rag_engine=None) -> ToolRegistry:
    """
    Initialize and register all tools
    
    Args:
        rag_engine: Optional RAG engine instance for the RAG tool
        
    Returns:
        ToolRegistry: The tool registry with all tools registered
    """
    logger.info("Initializing tools")
    
    # Register RAG tool if RAG engine is provided
    if rag_engine:
        logger.info("Registering RAG tool")
        rag_tool = RAGTool(rag_engine)
        tool_registry.register_tool(rag_tool)
    
    # Register calculator tool
    logger.info("Registering calculator tool")
    calculator_tool = CalculatorTool()
    tool_registry.register_tool(calculator_tool)
    
    # Register database tool
    logger.info("Registering database tool")
    database_tool = DatabaseTool()
    tool_registry.register_tool(database_tool)
    
    # Register PostgreSQL tool
    logger.info("Registering PostgreSQL tool")
    postgresql_tool = PostgreSQLTool()
    tool_registry.register_tool(postgresql_tool)
    
    logger.info(f"Registered {tool_registry.get_tool_count()} tools")
    
    return tool_registry

def get_tool_registry() -> ToolRegistry:
    """
    Get the tool registry
    
    Returns:
        ToolRegistry: The tool registry
    """
    return tool_registry