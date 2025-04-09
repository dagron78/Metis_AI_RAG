"""
Unit tests for the PlanExecutor
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from app.rag.plan_executor import PlanExecutor
from app.rag.query_planner import QueryPlan
from app.rag.tools import ToolRegistry, Tool
from app.rag.process_logger import ProcessLogger
from tests.unit.rag.tools.conftest import MockTool


class TestPlanExecutor:
    """Tests for the PlanExecutor class"""
    
    @pytest.mark.asyncio
    async def test_execute_simple_plan(self):
        """Test executing a simple plan"""
        # Create mock tool registry
        mock_registry = MagicMock()
        mock_registry.get_tool.return_value = MockTool(name="rag")
        
        # Create mock process logger
        mock_logger = MagicMock()
        
        # Create plan executor
        executor = PlanExecutor(
            tool_registry=mock_registry,
            process_logger=mock_logger
        )
        
        # Create a simple plan
        plan = QueryPlan(
            query_id="test_id",
            query="What is the capital of France?",
            steps=[
                {
                    "type": "tool",
                    "tool": "rag",
                    "input": {"query": "What is the capital of France?"},
                    "description": "Retrieve information using RAG"
                }
            ]
        )
        
        # Execute the plan
        result = await executor.execute_plan(plan)
        
        # Check result
        assert result["query_id"] == "test_id"
        assert "response" in result
        assert "steps" in result
        assert len(result["steps"]) == 1
        assert "execution_time" in result
        
        # Check that the tool was called
        mock_registry.get_tool.assert_called_once_with("rag")
        
        # Check that the process logger was called
        assert mock_logger.log_step.call_count >= 2  # At least start and complete
        assert mock_logger.log_final_response.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_complex_plan(self):
        """Test executing a complex plan"""
        # Create mock tools
        mock_rag_tool = AsyncMock()
        mock_rag_tool.execute.return_value = {
            "chunks": [
                {
                    "content": "Paris is the capital of France.",
                    "metadata": {"document_id": "doc1"},
                    "score": 0.95
                }
            ],
            "sources": ["doc1"]
        }
        
        mock_calc_tool = AsyncMock()
        mock_calc_tool.execute.return_value = {
            "result": 42
        }
        
        # Create mock tool registry
        mock_registry = MagicMock()
        mock_registry.get_tool.side_effect = lambda name: {
            "rag": mock_rag_tool,
            "calculator": mock_calc_tool
        }.get(name)
        
        # Create mock process logger
        mock_logger = MagicMock()
        
        # Create plan executor
        executor = PlanExecutor(
            tool_registry=mock_registry,
            process_logger=mock_logger
        )
        
        # Create a complex plan
        plan = QueryPlan(
            query_id="test_id",
            query="What is the capital of France and what is 6 * 7?",
            steps=[
                {
                    "type": "tool",
                    "tool": "rag",
                    "input": {"query": "What is the capital of France?"},
                    "description": "Retrieve information about France's capital"
                },
                {
                    "type": "tool",
                    "tool": "calculator",
                    "input": {"expression": "6 * 7"},
                    "description": "Calculate 6 * 7"
                },
                {
                    "type": "synthesize",
                    "description": "Synthesize results"
                }
            ]
        )
        
        # Execute the plan
        result = await executor.execute_plan(plan)
        
        # Check result
        assert result["query_id"] == "test_id"
        assert "response" in result
        assert "steps" in result
        assert len(result["steps"]) == 3  # All steps should be executed
        assert "execution_time" in result
        
        # Check that the tools were called
        mock_registry.get_tool.assert_any_call("rag")
        mock_registry.get_tool.assert_any_call("calculator")
        mock_rag_tool.execute.assert_called_once()
        mock_calc_tool.execute.assert_called_once()
        
        # Check that the process logger was called
        assert mock_logger.log_step.call_count >= 6  # At least start and complete for each step
        assert mock_logger.log_final_response.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing a tool"""
        # Create mock tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {"result": "test result"}
        
        # Create mock tool registry
        mock_registry = MagicMock()
        mock_registry.get_tool.return_value = mock_tool
        
        # Create plan executor
        executor = PlanExecutor(
            tool_registry=mock_registry
        )
        
        # Execute the tool
        result = await executor._execute_tool("test_tool", {"query": "test query"})
        
        # Check result
        assert result["result"] == "test result"
        
        # Check that the tool was called correctly
        mock_registry.get_tool.assert_called_once_with("test_tool")
        mock_tool.execute.assert_called_once_with({"query": "test query"})
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing a nonexistent tool"""
        # Create mock tool registry that returns None
        mock_registry = MagicMock()
        mock_registry.get_tool.return_value = None
        
        # Create plan executor
        executor = PlanExecutor(
            tool_registry=mock_registry
        )
        
        # Execute the nonexistent tool
        result = await executor._execute_tool("nonexistent_tool", {"query": "test query"})
        
        # Check result
        assert "error" in result
        assert "Tool not found" in result["error"]
        
        # Check that the tool registry was called correctly
        mock_registry.get_tool.assert_called_once_with("nonexistent_tool")
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_error(self):
        """Test executing a tool that raises an error"""
        # Create mock tool that raises an exception
        mock_tool = AsyncMock()
        mock_tool.execute.side_effect = Exception("Test error")
        
        # Create mock tool registry
        mock_registry = MagicMock()
        mock_registry.get_tool.return_value = mock_tool
        
        # Create plan executor
        executor = PlanExecutor(
            tool_registry=mock_registry
        )
        
        # Execute the tool
        result = await executor._execute_tool("test_tool", {"query": "test query"})
        
        # Check result
        assert "error" in result
        assert "Test error" in result["error"]
        
        # Check that the tool was called correctly
        mock_registry.get_tool.assert_called_once_with("test_tool")
        mock_tool.execute.assert_called_once_with({"query": "test query"})
    
    @pytest.mark.asyncio
    async def test_generate_response_with_llm(self):
        """Test generating a response with an LLM"""
        # Create mock LLM provider
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = {"response": "This is a test response"}
        
        # Create plan executor with LLM
        executor = PlanExecutor(
            tool_registry=MagicMock(),
            llm_provider=mock_llm
        )
        
        # Create a plan with results
        plan = QueryPlan(
            query_id="test_id",
            query="test query",
            steps=[
                {"type": "tool", "tool": "rag", "description": "RAG step"}
            ]
        )
        plan.record_step_result({"chunks": [{"content": "Test content"}]})
        
        # Generate response
        response = await executor._generate_response(plan)
        
        # Check response
        assert response == "This is a test response"
        
        # Check that the LLM was called
        mock_llm.generate.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_generate_simple_response(self):
        """Test generating a simple response without an LLM"""
        # Create plan executor without LLM
        executor = PlanExecutor(
            tool_registry=MagicMock()
        )
        
        # Create a plan with RAG results
        rag_plan = QueryPlan(
            query_id="test_id",
            query="What is the capital of France?",
            steps=[{"type": "tool", "tool": "rag"}]
        )
        rag_plan.record_step_result({
            "chunks": [{"content": "Paris is the capital of France."}]
        })
        
        # Generate response for RAG plan
        rag_response = executor._generate_simple_response(rag_plan)
        assert "Paris is the capital of France" in rag_response
        
        # Create a plan with calculator results
        calc_plan = QueryPlan(
            query_id="test_id",
            query="What is 2 + 2?",
            steps=[{"type": "tool", "tool": "calculator"}]
        )
        calc_plan.record_step_result({"result": 4})
        
        # Generate response for calculator plan
        calc_response = executor._generate_simple_response(calc_plan)
        assert "4" in calc_response
        
        # Create a plan with database results
        db_plan = QueryPlan(
            query_id="test_id",
            query="Query the database",
            steps=[{"type": "tool", "tool": "database"}]
        )
        db_plan.record_step_result({"results": [{"id": 1}, {"id": 2}]})
        
        # Generate response for database plan
        db_response = executor._generate_simple_response(db_plan)
        assert "2 records" in db_response
        
        # Create a plan with an error
        error_plan = QueryPlan(
            query_id="test_id",
            query="Error query",
            steps=[{"type": "tool", "tool": "rag"}]
        )
        error_plan.record_step_result({"error": "Test error"})
        
        # Generate response for error plan
        error_response = executor._generate_simple_response(error_plan)
        assert "error" in error_response.lower()
        assert "Test error" in error_response