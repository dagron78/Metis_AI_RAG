"""
Fixtures for RAG API integration tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.agents.langgraph_rag_agent import LangGraphRAGAgent

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store"""
    mock = AsyncMock(spec=VectorStore)
    mock.search.return_value = [
        {
            "chunk_id": "chunk1",
            "content": "This is a test chunk",
            "metadata": {"document_id": "doc1"},
            "distance": 0.1
        },
        {
            "chunk_id": "chunk2",
            "content": "This is another test chunk",
            "metadata": {"document_id": "doc1"},
            "distance": 0.2
        }
    ]
    return mock

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client that returns predefined responses"""
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
    
    return MockOllamaClient()

@pytest.fixture
def mock_langgraph_rag_agent(mock_vector_store, mock_ollama_client):
    """Create a mock LangGraph RAG Agent"""
    agent = LangGraphRAGAgent(
        vector_store=mock_vector_store,
        ollama_client=mock_ollama_client
    )
    
    # Mock the internal components with AsyncMock
    agent.chunking_judge = AsyncMock()
    agent.chunking_judge.analyze_query.return_value = {"complexity": "simple"}
    
    agent.retrieval_judge = AsyncMock()
    agent.retrieval_judge.analyze_query.return_value = {"complexity": "simple", "top_k": 3}
    agent.retrieval_judge.evaluate_retrieval.return_value = {"relevant": True}
    
    agent.semantic_chunker = AsyncMock()
    agent.semantic_chunker.chunk_text.return_value = ["Chunk 1", "Chunk 2"]
    
    # Mock the graph
    agent.graph = MagicMock()
    agent.app = AsyncMock()
    
    # Mock the query method directly to avoid LangGraph complexities
    async def mock_query(query, stream=False, **kwargs):
        return {
            "query": query,
            "answer": "This is a mock response.",
            "sources": []
        }
    
    agent.query = mock_query
    
    return agent