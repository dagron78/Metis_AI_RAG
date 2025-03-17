"""
Unit tests for the Retrieval Judge
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.agents.retrieval_judge import RetrievalJudge
from app.rag.ollama_client import OllamaClient


@pytest.fixture
def mock_ollama_client():
    """Create a mock OllamaClient"""
    client = AsyncMock(spec=OllamaClient)
    return client


@pytest.fixture
def retrieval_judge(mock_ollama_client):
    """Create a RetrievalJudge with a mock OllamaClient"""
    return RetrievalJudge(ollama_client=mock_ollama_client, model="test-model")


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing"""
    return [
        {
            "chunk_id": "chunk1",
            "content": "This is a sample chunk about artificial intelligence and machine learning.",
            "metadata": {
                "document_id": "doc1",
                "filename": "ai_basics.md",
                "tags": "ai,machine learning",
                "folder": "/tech"
            },
            "distance": 0.2
        },
        {
            "chunk_id": "chunk2",
            "content": "Neural networks are a subset of machine learning and are at the core of deep learning algorithms.",
            "metadata": {
                "document_id": "doc1",
                "filename": "ai_basics.md",
                "tags": "ai,machine learning,neural networks",
                "folder": "/tech"
            },
            "distance": 0.3
        },
        {
            "chunk_id": "chunk3",
            "content": "Python is a popular programming language for data science and machine learning.",
            "metadata": {
                "document_id": "doc2",
                "filename": "programming.md",
                "tags": "python,programming",
                "folder": "/tech/programming"
            },
            "distance": 0.5
        }
    ]


class TestRetrievalJudge:
    """Tests for the RetrievalJudge class"""

    @pytest.mark.asyncio
    async def test_analyze_query(self, retrieval_judge, mock_ollama_client):
        """Test analyze_query method"""
        # Mock the LLM response
        mock_ollama_client.generate.return_value = {
            "response": json.dumps({
                "complexity": "moderate",
                "parameters": {
                    "k": 8,
                    "threshold": 0.5,
                    "reranking": True
                },
                "justification": "This is a moderately complex query that requires specific information about neural networks."
            })
        }

        # Call the method
        result = await retrieval_judge.analyze_query("How do neural networks work?")

        # Verify the result
        assert result["complexity"] == "moderate"
        assert result["parameters"]["k"] == 8
        assert result["parameters"]["threshold"] == 0.5
        assert result["parameters"]["reranking"] is True
        assert "justification" in result

        # Verify the LLM was called with the correct prompt
        mock_ollama_client.generate.assert_called_once()
        prompt = mock_ollama_client.generate.call_args[1]["prompt"]
        assert "How do neural networks work?" in prompt
        assert "analyze the query complexity" in prompt.lower()

    @pytest.mark.asyncio
    async def test_evaluate_chunks(self, retrieval_judge, mock_ollama_client, sample_chunks):
        """Test evaluate_chunks method"""
        # Mock the LLM response
        mock_ollama_client.generate.return_value = {
            "response": json.dumps({
                "relevance_scores": {
                    "1": 0.9,
                    "2": 0.8,
                    "3": 0.4
                },
                "needs_refinement": False,
                "justification": "The first two chunks are highly relevant to neural networks."
            })
        }

        # Call the method
        result = await retrieval_judge.evaluate_chunks("How do neural networks work?", sample_chunks)

        # Verify the result
        assert "relevance_scores" in result
        assert "chunk1" in result["relevance_scores"]
        assert result["relevance_scores"]["chunk1"] == 0.9
        assert result["relevance_scores"]["chunk2"] == 0.8
        assert result["relevance_scores"]["chunk3"] == 0.4
        assert result["needs_refinement"] is False
        assert "justification" in result

        # Verify the LLM was called with the correct prompt
        mock_ollama_client.generate.assert_called_once()
        prompt = mock_ollama_client.generate.call_args[1]["prompt"]
        assert "How do neural networks work?" in prompt
        assert "evaluate the relevance" in prompt.lower()
        assert "ai_basics.md" in prompt  # Sample chunk metadata

    @pytest.mark.asyncio
    async def test_refine_query(self, retrieval_judge, mock_ollama_client, sample_chunks):
        """Test refine_query method"""
        # Mock the LLM response
        mock_ollama_client.generate.return_value = {
            "response": "How do neural networks function in deep learning algorithms?"
        }

        # Call the method
        result = await retrieval_judge.refine_query("How do neural networks work?", sample_chunks)

        # Verify the result
        assert result == "How do neural networks function in deep learning algorithms?"

        # Verify the LLM was called with the correct prompt
        mock_ollama_client.generate.assert_called_once()
        prompt = mock_ollama_client.generate.call_args[1]["prompt"]
        assert "How do neural networks work?" in prompt
        assert "refine the user's query" in prompt.lower()

    @pytest.mark.asyncio
    async def test_optimize_context(self, retrieval_judge, mock_ollama_client, sample_chunks):
        """Test optimize_context method"""
        # Mock the LLM response
        mock_ollama_client.generate.return_value = {
            "response": json.dumps({
                "optimized_order": [2, 1],  # Chunk indices (1-based)
                "excluded_chunks": [3],  # Exclude chunk3
                "justification": "Ordered chunks for logical flow and excluded less relevant chunk."
            })
        }

        # Call the method
        result = await retrieval_judge.optimize_context("How do neural networks work?", sample_chunks)

        # Verify the result
        assert len(result) == 2
        assert result[0]["chunk_id"] == "chunk2"  # First in optimized order
        assert result[1]["chunk_id"] == "chunk1"  # Second in optimized order
        # chunk3 should be excluded

        # Verify the LLM was called with the correct prompt
        mock_ollama_client.generate.assert_called_once()
        prompt = mock_ollama_client.generate.call_args[1]["prompt"]
        assert "How do neural networks work?" in prompt
        assert "optimize the assembly" in prompt.lower()

    @pytest.mark.asyncio
    async def test_analyze_query_error_handling(self, retrieval_judge, mock_ollama_client):
        """Test error handling in analyze_query method"""
        # Mock the LLM response with invalid JSON
        mock_ollama_client.generate.return_value = {
            "response": "This is not valid JSON"
        }

        # Call the method
        result = await retrieval_judge.analyze_query("How do neural networks work?")

        # Verify default values are returned
        assert result["complexity"] == "moderate"
        assert result["parameters"]["k"] == 10
        assert result["parameters"]["threshold"] == 0.4
        assert result["parameters"]["reranking"] is True
        assert "Failed to parse" in result["justification"]

    @pytest.mark.asyncio
    async def test_extract_chunks_sample(self, retrieval_judge, sample_chunks):
        """Test _extract_chunks_sample method"""
        # Add more chunks to the sample
        extended_chunks = sample_chunks + [
            {
                "chunk_id": f"chunk{i}",
                "content": f"This is sample chunk {i} with some content that should be truncated if too long.",
                "metadata": {
                    "document_id": f"doc{i//2}",
                    "filename": f"file{i}.md",
                    "tags": "tag1,tag2",
                    "folder": "/folder"
                },
                "distance": 0.1 * i
            }
            for i in range(4, 10)
        ]

        # Call the method with max_chunks=3 and a small max_length
        result = retrieval_judge._extract_chunks_sample(extended_chunks, max_chunks=3, max_length=100)

        # Verify the result
        assert len(result) == 3  # Should only return 3 chunks
        assert all("chunk_id" in chunk for chunk in result)
        
        # Verify chunks are sorted by distance (ascending)
        distances = [chunk.get("distance", 1.0) for chunk in result]
        assert all(distances[i] <= distances[i+1] for i in range(len(distances)-1))
        
        # Verify content is truncated
        total_content_length = sum(len(chunk.get("content", "")) for chunk in result)
        assert total_content_length <= 100