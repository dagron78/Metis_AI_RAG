"""
Integration test for the Enhanced LangGraph RAG Agent
"""
import pytest
import logging
import uuid
from typing import Dict, Any, List, Optional

from app.rag.agents.enhanced_langgraph_rag_agent import EnhancedLangGraphRAGAgent
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.tools import ToolRegistry
from app.rag.process_logger import ProcessLogger

# Configure logging
logger = logging.getLogger("tests.integration.test_enhanced_langgraph_rag_integration")

class MockProcessLogger:
    """Mock ProcessLogger for testing"""
    def __init__(self):
        self.process_log = {}
        self.logger = logging.getLogger("tests.mock_process_logger")
    
    def log_step(self, query_id: str, step_name: str, step_data: Dict[str, Any]) -> None:
        """Log a step without requiring the query_id to be registered first"""
        if query_id not in self.process_log:
            self.process_log[query_id] = {
                "query": step_data.get("query", ""),
                "steps": [],
                "final_response": None
            }
        
        self.process_log[query_id]["steps"].append({
            "step_name": step_name,
            "step_data": step_data
        })
    
    def log_final_response(self, query_id: str, response: str, metadata: Dict[str, Any]) -> None:
        """Log the final response without requiring the query_id to be registered first"""
        if query_id not in self.process_log:
            self.process_log[query_id] = {
                "query": "",
                "steps": [],
                "final_response": None
            }
        
        self.process_log[query_id]["final_response"] = {
            "response": response,
            "metadata": metadata
        }
    
    def get_process_log(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get the process log for a query"""
        return self.process_log.get(query_id)

class MockOllamaClient:
    """Mock OllamaClient for testing"""
    async def generate(self, prompt, model=None, system_prompt=None, stream=False, parameters=None):
        # Check if this is an error query
        is_error = "Error:" in prompt
        
        if stream:
            # For streaming, return an async generator
            async def mock_stream():
                if is_error:
                    yield "Error: This is a mock error response."
                else:
                    for token in ["This", " is", " a", " mock", " response", "."]:
                        yield token
            return mock_stream()
        else:
            # For non-streaming, return a dict with the response
            if is_error:
                return {"response": "Error: This is a mock error response."}
            else:
                return {"response": "This is a mock response."}

class MockVectorStore:
    """Mock VectorStore for testing"""
    async def search(self, query, top_k=10, filter_criteria=None):
        # Return mock search results
        return [
            {
                "chunk_id": f"chunk_{i}",
                "content": f"This is mock content for chunk {i}.",
                "metadata": {
                    "document_id": f"doc_{i}",
                    "filename": f"test_file_{i}.txt",
                    "tags": ["test", "mock"],
                    "folder": "/test"
                },
                "distance": 0.1 + (i * 0.05)  # Increasing distance (lower relevance)
            }
            for i in range(3)
        ]
    
    def get_stats(self):
        return {"count": 10}

class MockQueryAnalyzer:
    """Mock QueryAnalyzer for testing"""
    async def analyze(self, query):
        # Return mock analysis based on query content
        if "complex" in query.lower() or "tool" in query.lower():
            return {
                "complexity": "complex",
                "requires_tools": ["calculator"] if "calculate" in query.lower() else [],
                "sub_queries": ["What is the meaning of life?"] if "meaning" in query.lower() else [],
                "parameters": {"k": 5, "threshold": 0.5, "reranking": True},
                "justification": "This is a complex query that requires multiple steps."
            }
        else:
            return {
                "complexity": "simple",
                "requires_tools": [],
                "sub_queries": [],
                "parameters": {"k": 3, "threshold": 0.4, "reranking": False},
                "justification": "This is a simple query that can be answered directly."
            }

class MockToolRegistry:
    """Mock ToolRegistry for testing"""
    def list_tools(self):
        return ["rag", "calculator", "database"]
    
    def get_tool(self, tool_name):
        if tool_name in ["rag", "calculator", "database"]:
            return MockTool(tool_name)
        return None

class MockTool:
    """Mock Tool for testing"""
    def __init__(self, name):
        self.name = name
    
    async def execute(self, input_data):
        if self.name == "calculator" and "expression" in input_data:
            return {"result": 42}
        elif self.name == "rag" and "query" in input_data:
            return {"chunks": [{"content": "This is a mock RAG result."}]}
        elif self.name == "database" and "query" in input_data:
            return {"results": [{"id": 1, "name": "Test"}]}
        else:
            return {"error": "Invalid input"}

@pytest.mark.asyncio
async def test_enhanced_langgraph_rag_agent_initialization():
    """Test that the Enhanced LangGraph RAG Agent can be initialized"""
    # Initialize components
    vector_store = MockVectorStore()
    ollama_client = MockOllamaClient()
    query_analyzer = MockQueryAnalyzer()
    tool_registry = MockToolRegistry()
    process_logger = MockProcessLogger()
    
    # Initialize Enhanced LangGraph RAG Agent
    agent = EnhancedLangGraphRAGAgent(
        vector_store=vector_store,
        ollama_client=ollama_client,
        query_analyzer=query_analyzer,
        tool_registry=tool_registry,
        process_logger=process_logger
    )
    
    # Verify that the agent was initialized
    assert agent is not None
    assert agent.graph is not None
    assert agent.vector_store is not None
    assert agent.ollama_client is not None
    assert agent.query_analyzer is not None
    assert agent.query_planner is not None
    assert agent.plan_executor is not None
    assert agent.tool_registry is not None
    assert agent.process_logger is not None

@pytest.mark.asyncio
async def test_enhanced_langgraph_rag_agent_simple_query():
    """Test that the Enhanced LangGraph RAG Agent can process a simple query"""
    # Initialize components with mocks
    vector_store = MockVectorStore()
    ollama_client = MockOllamaClient()
    query_analyzer = MockQueryAnalyzer()
    tool_registry = MockToolRegistry()
    process_logger = MockProcessLogger()
    
    # Initialize Enhanced LangGraph RAG Agent
    agent = EnhancedLangGraphRAGAgent(
        vector_store=vector_store,
        ollama_client=ollama_client,
        query_analyzer=query_analyzer,
        tool_registry=tool_registry,
        process_logger=process_logger
    )
    
    # Test simple query
    query = "What is artificial intelligence?"
    
    # Query the Enhanced LangGraph RAG Agent
    response = await agent.query(
        query=query,
        stream=False
    )
    
    # Verify the response structure
    assert response is not None
    assert "query" in response
    assert response["query"] == query
    assert "answer" in response
    assert response["answer"] == "This is a mock response."
    assert "sources" in response
    assert isinstance(response["sources"], list)
    assert "execution_trace" not in response or response["execution_trace"] is None

@pytest.mark.asyncio
async def test_enhanced_langgraph_rag_agent_complex_query():
    """Test that the Enhanced LangGraph RAG Agent can process a complex query"""
    # Initialize components with mocks
    vector_store = MockVectorStore()
    ollama_client = MockOllamaClient()
    query_analyzer = MockQueryAnalyzer()
    tool_registry = MockToolRegistry()
    process_logger = MockProcessLogger()
    
    # Initialize Enhanced LangGraph RAG Agent
    agent = EnhancedLangGraphRAGAgent(
        vector_store=vector_store,
        ollama_client=ollama_client,
        query_analyzer=query_analyzer,
        tool_registry=tool_registry,
        process_logger=process_logger
    )
    
    # Test complex query that requires tools
    query = "Calculate the meaning of life and explain it in a complex way"
    
    # Query the Enhanced LangGraph RAG Agent
    response = await agent.query(
        query=query,
        stream=False
    )
    
    # Verify the response structure
    assert response is not None
    assert "query" in response
    assert response["query"] == query
    assert "answer" in response
    assert response["answer"] == "This is a mock response."
    assert "sources" in response
    assert isinstance(response["sources"], list)
    assert "execution_trace" in response
    assert isinstance(response["execution_trace"], list)

@pytest.mark.asyncio
async def test_enhanced_langgraph_rag_agent_streaming():
    """Test that the Enhanced LangGraph RAG Agent can stream responses"""
    # Initialize components with mocks
    vector_store = MockVectorStore()
    ollama_client = MockOllamaClient()
    query_analyzer = MockQueryAnalyzer()
    tool_registry = MockToolRegistry()
    process_logger = MockProcessLogger()
    
    # Initialize Enhanced LangGraph RAG Agent
    agent = EnhancedLangGraphRAGAgent(
        vector_store=vector_store,
        ollama_client=ollama_client,
        query_analyzer=query_analyzer,
        tool_registry=tool_registry,
        process_logger=process_logger
    )
    
    # Test query with streaming
    query = "What is artificial intelligence?"
    
    # Query the Enhanced LangGraph RAG Agent with streaming
    response = await agent.query(
        query=query,
        stream=True
    )
    
    # Verify the response structure
    assert response is not None
    assert "query" in response
    assert response["query"] == query
    assert "stream" in response
    
    # Collect tokens from the stream
    tokens = []
    async for token in response["stream"]:
        tokens.append(token)
    
    # Verify the tokens
    assert len(tokens) > 0
    assert "".join(tokens) == "This is a mock response."
    
    # Verify sources are included
    assert "sources" in response
    assert isinstance(response["sources"], list)

@pytest.mark.asyncio
async def test_enhanced_langgraph_rag_agent_error_handling():
    """Test that the Enhanced LangGraph RAG Agent handles errors gracefully"""
    # Initialize components with mocks
    vector_store = MockVectorStore()
    ollama_client = MockOllamaClient()
    query_analyzer = MockQueryAnalyzer()
    tool_registry = MockToolRegistry()
    process_logger = MockProcessLogger()
    
    # Initialize Enhanced LangGraph RAG Agent
    agent = EnhancedLangGraphRAGAgent(
        vector_store=vector_store,
        ollama_client=ollama_client,
        query_analyzer=query_analyzer,
        tool_registry=tool_registry,
        process_logger=process_logger
    )
    
    # Test query that triggers an error
    query = "Error: This should trigger an error response"
    
    try:
        # Query the Enhanced LangGraph RAG Agent
        response = await agent.query(
            query=query,
            stream=False
        )
        
        # If we get here, the agent handled the error
        assert response is not None
        assert "query" in response
        assert "answer" in response
        assert "Error" in response["answer"]
    except Exception as e:
        # The test fails if an unhandled exception is raised
        assert False, f"Enhanced LangGraph RAG Agent did not handle the error: {str(e)}"