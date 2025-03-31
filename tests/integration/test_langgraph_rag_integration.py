"""
Integration test for the LangGraph RAG Agent
"""
import pytest
import logging
from typing import Dict, Any, List

from app.rag.agents.langgraph_rag_agent import LangGraphRAGAgent
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient

# Configure logging
logger = logging.getLogger("tests.integration.test_langgraph_rag_integration")

@pytest.mark.asyncio
async def test_langgraph_rag_agent_initialization():
    """Test that the LangGraph RAG Agent can be initialized"""
    # Initialize components
    vector_store = VectorStore()
    ollama_client = OllamaClient()
    
    # Initialize LangGraph RAG Agent
    langgraph_rag_agent = LangGraphRAGAgent(
        vector_store=vector_store,
        ollama_client=ollama_client
    )
    
    # Verify that the agent was initialized
    assert langgraph_rag_agent is not None
    assert langgraph_rag_agent.graph is not None
    assert langgraph_rag_agent.vector_store is not None
    assert langgraph_rag_agent.ollama_client is not None
    assert langgraph_rag_agent.chunking_judge is not None
    assert langgraph_rag_agent.retrieval_judge is not None
    assert langgraph_rag_agent.semantic_chunker is not None

@pytest.mark.asyncio
async def test_langgraph_rag_agent_query():
    """Test that the LangGraph RAG Agent can process a query"""
    # Initialize components with mock ollama client to avoid actual LLM calls
    vector_store = VectorStore()
    
    # Create a mock OllamaClient that returns predefined responses
    class MockOllamaClient:
        async def generate(self, prompt, model=None, system_prompt=None, stream=False, parameters=None):
            if stream:
                # For streaming, return an async generator
                async def mock_stream():
                    for token in ["This", " is", " a", " mock", " response", "."] if not prompt.startswith("Error") else ["Error"]:
                        yield token
                return mock_stream()
            else:
                # For non-streaming, return a dict with the response
                return {"response": "This is a mock response." if not prompt.startswith("Error") else "Error"}
    
    ollama_client = MockOllamaClient()
    
    # Initialize LangGraph RAG Agent with mock client
    langgraph_rag_agent = LangGraphRAGAgent(
        vector_store=vector_store,
        ollama_client=ollama_client
    )
    
    # Test query
    query = "What are the key features of the Metis RAG system?"
    
    # Query the LangGraph RAG Agent
    response = await langgraph_rag_agent.query(
        query=query,
        stream=False
    )
    
    # Verify the response structure
    assert response is not None
    assert "query" in response
    assert response["query"] == query
    assert "answer" in response or "stream" in response
    
    # If not streaming, verify the answer
    if "answer" in response:
        assert response["answer"] == "This is a mock response."
    
    # Verify sources are included (even if empty)
    assert "sources" in response

@pytest.mark.asyncio
async def test_langgraph_rag_agent_error_handling():
    """Test that the LangGraph RAG Agent handles errors gracefully"""
    # Initialize components with mock ollama client that raises exceptions
    vector_store = VectorStore()
    
    # Create a mock OllamaClient that raises exceptions
    class ErrorOllamaClient:
        async def generate(self, prompt, model=None, system_prompt=None, stream=False, parameters=None):
            if prompt.startswith("Error"):
                raise Exception("Mock error")
            
            if stream:
                # For streaming, return an async generator
                async def mock_stream():
                    for token in ["This", " is", " a", " mock", " response", "."]:
                        yield token
                return mock_stream()
            else:
                # For non-streaming, return a dict with the response
                return {"response": "This is a mock response."}
    
    ollama_client = ErrorOllamaClient()
    
    # Initialize LangGraph RAG Agent with error client
    langgraph_rag_agent = LangGraphRAGAgent(
        vector_store=vector_store,
        ollama_client=ollama_client
    )
    
    # Test query that triggers an error
    query = "Error: This should trigger an exception"
    
    try:
        # Query the LangGraph RAG Agent
        response = await langgraph_rag_agent.query(
            query=query,
            stream=False
        )
        
        # If we get here, the agent handled the error
        assert response is not None
        assert "query" in response
        assert "error" in response or "answer" in response
    except Exception as e:
        # The test fails if an unhandled exception is raised
        assert False, f"LangGraph RAG Agent did not handle the error: {str(e)}"