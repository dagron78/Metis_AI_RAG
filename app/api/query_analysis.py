"""
API endpoints for query analysis
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.rag.query_analyzer import QueryAnalyzer
from app.rag.tools import ToolRegistry
from app.rag.process_logger import ProcessLogger
from app.db.dependencies import get_db

router = APIRouter(
    prefix="/api/query",
    tags=["query"],
    responses={404: {"description": "Not found"}},
)

class QueryAnalysisRequest(BaseModel):
    """Query analysis request model"""
    query: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class QueryAnalysisResponse(BaseModel):
    """Query analysis response model"""
    query_id: str
    complexity: str
    requires_tools: List[str]
    sub_queries: List[str]
    reasoning: str

class ToolExecutionRequest(BaseModel):
    """Tool execution request model"""
    query_id: str
    tool_name: str
    tool_input: Dict[str, Any]

class ToolExecutionResponse(BaseModel):
    """Tool execution response model"""
    query_id: str
    tool_name: str
    tool_output: Dict[str, Any]
    execution_time: float

@router.post("/analyze", response_model=QueryAnalysisResponse)
async def analyze_query(
    request: QueryAnalysisRequest,
    query_analyzer: QueryAnalyzer = Depends(),
    process_logger: ProcessLogger = Depends(),
    db_session = Depends(get_db)
):
    """
    Analyze a query to determine its complexity and requirements
    
    Args:
        request: Query analysis request
        
    Returns:
        Query analysis response
    """
    # Generate a unique query ID
    import uuid
    query_id = str(uuid.uuid4())
    
    # Start process logging
    process_logger.start_process(query_id=query_id, query=request.query)
    
    # Analyze the query
    analysis = await query_analyzer.analyze(request.query)
    
    # Log the analysis step
    process_logger.log_step(
        query_id=query_id,
        step_name="query_analysis",
        step_data=analysis
    )
    
    # Return the analysis
    return QueryAnalysisResponse(
        query_id=query_id,
        complexity=analysis.get("complexity", "simple"),
        requires_tools=analysis.get("requires_tools", []),
        sub_queries=analysis.get("sub_queries", []),
        reasoning=analysis.get("reasoning", "")
    )

@router.post("/execute-tool", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    tool_registry: ToolRegistry = Depends(),
    process_logger: ProcessLogger = Depends(),
    db_session = Depends(get_db)
):
    """
    Execute a tool with the given input
    
    Args:
        request: Tool execution request
        
    Returns:
        Tool execution response
    """
    # Get the tool
    tool = tool_registry.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {request.tool_name}")
    
    # Execute the tool
    import time
    start_time = time.time()
    tool_output = await tool.execute(request.tool_input)
    execution_time = time.time() - start_time
    
    # Log the tool execution
    process_logger.log_tool_usage(
        query_id=request.query_id,
        tool_name=request.tool_name,
        input_data=request.tool_input,
        output_data=tool_output
    )
    
    # Return the tool output
    return ToolExecutionResponse(
        query_id=request.query_id,
        tool_name=request.tool_name,
        tool_output=tool_output,
        execution_time=execution_time
    )

@router.get("/available-tools", response_model=List[Dict[str, Any]])
async def list_available_tools(
    tool_registry: ToolRegistry = Depends()
):
    """
    List all available tools
    
    Returns:
        List of tool information dictionaries
    """
    return tool_registry.list_tools()

@router.get("/tool-examples/{tool_name}", response_model=List[Dict[str, Any]])
async def get_tool_examples(
    tool_name: str,
    tool_registry: ToolRegistry = Depends()
):
    """
    Get examples for a specific tool
    
    Args:
        tool_name: Tool name
        
    Returns:
        List of example input/output pairs
    """
    examples = tool_registry.get_tool_examples(tool_name)
    if not examples:
        raise HTTPException(status_code=404, detail=f"No examples found for tool: {tool_name}")
    
    return examples

@router.get("/logs/{query_id}", response_model=Dict[str, Any])
async def get_query_logs(
    query_id: str,
    process_logger: ProcessLogger = Depends()
):
    """
    Get the process log for a query
    
    Args:
        query_id: Query ID
        
    Returns:
        Process log
    """
    log = process_logger.get_process_log(query_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"No log found for query: {query_id}")
    
    return log