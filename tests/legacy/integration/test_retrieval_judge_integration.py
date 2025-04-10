"""
Integration tests for the Retrieval Judge with RAG Engine
"""
import pytest
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.agents.retrieval_judge import RetrievalJudge
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.models.document import Document, Chunk


@pytest.fixture
def mock_ollama_client():
    """Create a mock OllamaClient"""
    client = AsyncMock(spec=OllamaClient)
    
    # Mock generate method to return a valid response
    async def mock_generate(prompt, model=None, system_prompt=None, stream=False, parameters=None):
        if "analyze the query" in prompt.lower():
            return {
                "response": json.dumps({
                    "complexity": "moderate",
                    "parameters": {
                        "k": 5,
                        "threshold": 0.5,
                        "reranking": True
                    },
                    "justification": "This is a moderately complex query about machine learning."
                })
            }
        elif "evaluate the relevance" in prompt.lower():
            return {
                "response": json.dumps({
                    "relevance_scores": {
                        "1": 0.9,
                        "2": 0.7,
                        "3": 0.3
                    },
                    "needs_refinement": False,
                    "justification": "The first two chunks are highly relevant to the query."
                })
            }
        elif "refine the user's query" in prompt.lower():
            return {
                "response": "What are the key concepts and applications of machine learning?"
            }
        elif "optimize the assembly" in prompt.lower():
            return {
                "response": json.dumps({
                    "optimized_order": [1, 2],
                    "excluded_chunks": [3],
                    "justification": "Ordered chunks for logical flow and excluded less relevant chunk."
                })
            }
        else:
            return {
                "response": "This is a response from the mock LLM."
            }
    
    client.generate = mock_generate
    
    # Mock create_embedding method
    async def mock_create_embedding(text, model=None):
        # Return a simple mock embedding (10 dimensions)
        return [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    client.create_embedding = mock_create_embedding
    
    return client


@pytest.fixture
def mock_vector_store(mock_ollama_client):
    """Create a mock VectorStore"""
    store = AsyncMock(spec=VectorStore)
    
    # Mock get_stats method
    store.get_stats.return_value = {"count": 10, "embeddings_model": "test-model"}
    
    # Mock search method
    async def mock_search(query, top_k=5, filter_criteria=None):
        return [
            {
                "chunk_id": "chunk1",
                "content": "Machine learning is a subset of artificial intelligence that focuses on developing systems that learn from data.",
                "metadata": {
                    "document_id": "doc1",
                    "filename": "ml_basics.md",
                    "tags": "machine learning,ai",
                    "folder": "/tech"
                },
                "distance": 0.1
            },
            {
                "chunk_id": "chunk2",
                "content": "Common machine learning algorithms include linear regression, decision trees, and neural networks.",
                "metadata": {
                    "document_id": "doc1",
                    "filename": "ml_basics.md",
                    "tags": "machine learning,algorithms",
                    "folder": "/tech"
                },
                "distance": 0.2
            },
            {
                "chunk_id": "chunk3",
                "content": "Python is a popular programming language for data science and machine learning projects.",
                "metadata": {
                    "document_id": "doc2",
                    "filename": "programming.md",
                    "tags": "python,programming",
                    "folder": "/tech/programming"
                },
                "distance": 0.6
            }
        ]
    
    store.search = mock_search
    
    return store


@pytest.fixture
def retrieval_judge(mock_ollama_client):
    """Create a RetrievalJudge with a mock OllamaClient"""
    return RetrievalJudge(ollama_client=mock_ollama_client, model="test-model")


@pytest.fixture
def rag_engine(mock_vector_store, mock_ollama_client, retrieval_judge):
    """Create a RAGEngine with mock components"""
    with patch('app.rag.rag_engine.USE_RETRIEVAL_JUDGE', True):
        engine = RAGEngine(
            vector_store=mock_vector_store,
            ollama_client=mock_ollama_client,
            retrieval_judge=retrieval_judge
        )
        return engine


class TestRetrievalJudgeIntegration:
    """Integration tests for the RetrievalJudge with RAGEngine"""

    @pytest.mark.asyncio
    async def test_enhanced_retrieval(self, rag_engine):
        """Test the enhanced retrieval method"""
        # Call the enhanced retrieval method
        context, sources, document_ids = await rag_engine._enhanced_retrieval(
            query="What is machine learning?",
            top_k=5
        )
        
        # Verify the results
        assert context  # Context should not be empty
        assert "Machine learning is a subset of artificial intelligence" in context
        assert len(sources) > 0
        assert len(document_ids) > 0
        
        # Verify sources contain the expected information
        assert sources[0]["document_id"] == "doc1"
        assert sources[0]["chunk_id"] == "chunk1"
        assert sources[0]["filename"] == "ml_basics.md"
        
        # Verify document IDs were collected
        assert "doc1" in document_ids

    @pytest.mark.asyncio
    async def test_query_with_retrieval_judge(self, rag_engine):
        """Test the query method with Retrieval Judge enabled"""
        # Call the query method
        result = await rag_engine.query(
            query="What is machine learning?",
            model="test-model",
            use_rag=True,
            stream=False
        )
        
        # Verify the result
        assert "query" in result
        assert "answer" in result
        assert "sources" in result
        assert len(result["sources"]) > 0
        
        # Verify the query was processed
        assert result["query"] == "What is machine learning?"
        
        # Verify the answer is not empty
        assert result["answer"]
        
        # Verify sources are included
        assert result["sources"][0].document_id == "doc1"
        assert result["sources"][0].chunk_id == "chunk1"

    @pytest.mark.asyncio
    async def test_query_with_retrieval_judge_disabled(self, rag_engine):
        """Test the query method with Retrieval Judge disabled"""
        # Temporarily disable the Retrieval Judge
        rag_engine.retrieval_judge = None
        
        # Call the query method
        result = await rag_engine.query(
            query="What is machine learning?",
            model="test-model",
            use_rag=True,
            stream=False
        )
        
        # Verify the result
        assert "query" in result
        assert "answer" in result
        assert "sources" in result
        assert len(result["sources"]) > 0
        
        # Verify the query was processed
        assert result["query"] == "What is machine learning?"
        
        # Verify the answer is not empty
        assert result["answer"]
        
        # Verify sources are included
        assert result["sources"][0].document_id == "doc1"

    @pytest.mark.asyncio
    async def test_query_with_rag_disabled(self, rag_engine):
        """Test the query method with RAG disabled"""
        # Call the query method with use_rag=False
        result = await rag_engine.query(
            query="What is machine learning?",
            model="test-model",
            use_rag=False,
            stream=False
        )
        
        # Verify the result
        assert "query" in result
        assert "answer" in result
        assert "sources" in result
        
        # Verify no sources are included when RAG is disabled
        assert len(result["sources"]) == 0
        
        # Verify the query was processed
        assert result["query"] == "What is machine learning?"
        
        # Verify the answer is not empty
        assert result["answer"]