"""
Unit tests for the QueryAnalyzer
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.rag.query_analyzer import QueryAnalyzer


class TestQueryAnalyzer:
    """Tests for the QueryAnalyzer class"""
    
    @pytest.mark.asyncio
    async def test_analyze_simple_query(self):
        """Test analyzing a simple query"""
        # Create mock LLM provider
        mock_llm_provider = AsyncMock()
        mock_llm_provider.generate.return_value = {
            "response": """
            {
              "complexity": "simple",
              "requires_tools": ["rag"],
              "sub_queries": [],
              "reasoning": "This is a simple factual query that can be answered with a single RAG lookup."
            }
            """
        }
        
        # Create query analyzer
        query_analyzer = QueryAnalyzer(llm_provider=mock_llm_provider)
        
        # Analyze query
        result = await query_analyzer.analyze("What is the capital of France?")
        
        # Check result
        assert result["complexity"] == "simple"
        assert result["requires_tools"] == ["rag"]
        assert result["sub_queries"] == []
        assert "reasoning" in result
        
        # Check LLM provider was called
        mock_llm_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_complex_query(self):
        """Test analyzing a complex query"""
        # Create mock LLM provider
        mock_llm_provider = AsyncMock()
        mock_llm_provider.generate.return_value = {
            "response": """
            {
              "complexity": "complex",
              "requires_tools": ["rag", "calculator"],
              "sub_queries": [
                "What is the population of France?",
                "What is the population of Germany?",
                "Calculate the population difference between France and Germany"
              ],
              "reasoning": "This query requires retrieving population data and performing a calculation."
            }
            """
        }
        
        # Create query analyzer
        query_analyzer = QueryAnalyzer(llm_provider=mock_llm_provider)
        
        # Analyze query
        result = await query_analyzer.analyze("What is the population difference between France and Germany?")
        
        # Check result
        assert result["complexity"] == "complex"
        assert "rag" in result["requires_tools"]
        assert "calculator" in result["requires_tools"]
        assert len(result["sub_queries"]) == 3
        assert "reasoning" in result
        
        # Check LLM provider was called
        mock_llm_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_with_json_parsing_failure(self):
        """Test analyzing a query with JSON parsing failure"""
        # Create mock LLM provider
        mock_llm_provider = AsyncMock()
        mock_llm_provider.generate.return_value = {
            "response": """
            The query "What is the capital of France?" is a simple factual query.
            It requires the rag tool to retrieve information.
            complexity: simple
            requires_tools: rag
            """
        }
        
        # Create query analyzer
        query_analyzer = QueryAnalyzer(llm_provider=mock_llm_provider)
        
        # Analyze query
        result = await query_analyzer.analyze("What is the capital of France?")
        
        # Check result - should use fallback parsing
        assert "complexity" in result
        assert "requires_tools" in result
        assert "sub_queries" in result
        assert "reasoning" in result
        
        # Check LLM provider was called
        mock_llm_provider.generate.assert_called_once()