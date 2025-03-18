"""
Unit tests for the QueryPlanner
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from app.rag.query_planner import QueryPlanner, QueryPlan
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.tools import ToolRegistry, Tool

class MockTool(Tool):
    """Mock tool for testing"""
    
    def __init__(self, name="mock_tool", description="Mock tool"):
        super().__init__(name=name, description=description)
    
    async def execute(self, input_data):
        return {"result": f"Executed {self.name} with input: {input_data}"}
    
    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query string"
                }
            }
        }
    
    def get_output_schema(self):
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Result string"
                }
            }
        }
    
    def get_examples(self):
        return [
            {
                "input": {"query": "test query"},
                "output": {"result": "test result"}
            }
        ]


class TestQueryPlan:
    """Tests for the QueryPlan class"""
    
    def test_query_plan_initialization(self):
        """Test initializing a query plan"""
        plan = QueryPlan(
            query_id="test_id",
            query="test query",
            steps=[
                {"type": "tool", "tool": "rag", "input": {"query": "test query"}}
            ]
        )
        
        assert plan.query_id == "test_id"
        assert plan.query == "test query"
        assert len(plan.steps) == 1
        assert plan.current_step == 0
        assert not plan.is_completed()
    
    def test_get_next_step(self):
        """Test getting the next step in a plan"""
        plan = QueryPlan(
            query_id="test_id",
            query="test query",
            steps=[
                {"type": "tool", "tool": "rag", "input": {"query": "test query"}},
                {"type": "tool", "tool": "calculator", "input": {"expression": "1 + 1"}}
            ]
        )
        
        # Get first step
        step = plan.get_next_step()
        assert step["type"] == "tool"
        assert step["tool"] == "rag"
        
        # Record result and get next step
        plan.record_step_result({"chunks": []})
        step = plan.get_next_step()
        assert step["type"] == "tool"
        assert step["tool"] == "calculator"
        
        # Record result and check completion
        plan.record_step_result({"result": 2})
        assert plan.is_completed()
        assert plan.get_next_step() is None
    
    def test_to_dict_and_from_dict(self):
        """Test converting a plan to and from a dictionary"""
        original_plan = QueryPlan(
            query_id="test_id",
            query="test query",
            steps=[
                {"type": "tool", "tool": "rag", "input": {"query": "test query"}}
            ]
        )
        
        # Convert to dictionary
        plan_dict = original_plan.to_dict()
        
        # Create new plan from dictionary
        new_plan = QueryPlan.from_dict(plan_dict)
        
        # Check that the plans are equivalent
        assert new_plan.query_id == original_plan.query_id
        assert new_plan.query == original_plan.query
        assert new_plan.steps == original_plan.steps
        assert new_plan.current_step == original_plan.current_step
        assert new_plan.results == original_plan.results
        assert new_plan.completed == original_plan.completed


class TestQueryPlanner:
    """Tests for the QueryPlanner class"""
    
    @pytest.mark.asyncio
    async def test_create_simple_plan(self):
        """Test creating a simple plan"""
        # Create mock query analyzer
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze.return_value = {
            "complexity": "simple",
            "requires_tools": ["rag"],
            "sub_queries": [],
            "reasoning": "This is a simple factual query"
        }
        
        # Create mock tool registry
        mock_registry = MagicMock()
        mock_registry.get_tool.return_value = MockTool(name="rag")
        
        # Create query planner
        planner = QueryPlanner(
            query_analyzer=mock_analyzer,
            tool_registry=mock_registry
        )
        
        # Create plan
        plan = await planner.create_plan(
            query_id="test_id",
            query="What is the capital of France?"
        )
        
        # Check plan
        assert plan.query_id == "test_id"
        assert plan.query == "What is the capital of France?"
        assert len(plan.steps) == 1
        assert plan.steps[0]["type"] == "tool"
        assert plan.steps[0]["tool"] == "rag"
        
        # Check that the analyzer was called correctly
        mock_analyzer.analyze.assert_called_once_with("What is the capital of France?")
    
    @pytest.mark.asyncio
    async def test_create_complex_plan(self):
        """Test creating a complex plan"""
        # Create mock query analyzer
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze.return_value = {
            "complexity": "complex",
            "requires_tools": ["calculator", "rag"],
            "sub_queries": ["What is the population of France?", "What is the population of Germany?"],
            "reasoning": "This query requires calculation and retrieval"
        }
        
        # Create mock tool registry
        mock_registry = MagicMock()
        mock_registry.get_tool.side_effect = lambda name: MockTool(name=name)
        
        # Create query planner
        planner = QueryPlanner(
            query_analyzer=mock_analyzer,
            tool_registry=mock_registry
        )
        
        # Create plan
        plan = await planner.create_plan(
            query_id="test_id",
            query="What is the combined population of France and Germany?"
        )
        
        # Check plan
        assert plan.query_id == "test_id"
        assert plan.query == "What is the combined population of France and Germany?"
        
        # Should have 4 steps: calculator, rag, 2 sub-queries, and synthesize
        assert len(plan.steps) == 5
        
        # Check that the steps include the required tools
        tools = [step["tool"] for step in plan.steps if step["type"] == "tool"]
        assert "calculator" in tools
        assert "rag" in tools
        
        # Check that there's a synthesize step
        assert any(step["type"] == "synthesize" for step in plan.steps)
        
        # Check that the analyzer was called correctly
        mock_analyzer.analyze.assert_called_once_with("What is the combined population of France and Germany?")
    
    def test_create_tool_input(self):
        """Test creating tool input"""
        # Create mock query analyzer and tool registry
        mock_analyzer = MagicMock()
        mock_registry = MagicMock()
        
        # Create query planner
        planner = QueryPlanner(
            query_analyzer=mock_analyzer,
            tool_registry=mock_registry
        )
        
        # Test creating input for RAG tool
        rag_input = planner._create_tool_input("rag", "What is the capital of France?")
        assert rag_input["query"] == "What is the capital of France?"
        assert rag_input["top_k"] == 5
        
        # Test creating input for calculator tool
        calc_input = planner._create_tool_input("calculator", "Calculate 2 + 2")
        assert "expression" in calc_input
        
        # Test creating input for database tool
        db_input = planner._create_tool_input("database", "Query the database")
        assert "query" in db_input
        assert "source" in db_input