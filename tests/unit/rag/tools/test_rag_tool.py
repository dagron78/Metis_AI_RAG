"""
Unit tests for the RAGTool
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.rag.tools import RAGTool


class TestRAGTool:
    """Tests for the RAGTool implementation"""
    
    @pytest.mark.asyncio
    async def test_rag_tool_execute(self, mock_rag_engine):
        """Test executing the RAG tool"""
        # Configure mock RAG engine
        mock_rag_engine.retrieve.return_value = [
            {
                "content": "Test content",
                "metadata": {"document_id": "doc123"},
                "score": 0.95
            }
        ]
        
        # Create RAG tool
        rag_tool = RAGTool(rag_engine=mock_rag_engine)
        
        # Execute tool
        result = await rag_tool.execute({
            "query": "Test query",
            "top_k": 3
        })
        
        # Check result
        assert "chunks" in result
        assert len(result["chunks"]) == 1
        assert result["chunks"][0]["content"] == "Test content"
        assert result["chunks"][0]["metadata"] == {"document_id": "doc123"}
        assert result["chunks"][0]["score"] == 0.95
        assert "sources" in result
        assert "doc123" in result["sources"]
        assert "execution_time" in result
        
        # Check RAG engine was called correctly
        mock_rag_engine.retrieve.assert_called_once_with(
            query="Test query",
            top_k=3,
            filters={}
        )
    
    def test_rag_tool_schemas(self, mock_rag_engine):
        """Test RAG tool schemas"""
        # Create RAG tool
        rag_tool = RAGTool(rag_engine=mock_rag_engine)
        
        # Check input schema
        input_schema = rag_tool.get_input_schema()
        assert input_schema["type"] == "object"
        assert "query" in input_schema["properties"]
        assert "top_k" in input_schema["properties"]
        assert "filters" in input_schema["properties"]
        assert input_schema["required"] == ["query"]
        
        # Check output schema
        output_schema = rag_tool.get_output_schema()
        assert output_schema["type"] == "object"
        assert "chunks" in output_schema["properties"]
        assert "sources" in output_schema["properties"]
        assert "execution_time" in output_schema["properties"]
        
        # Check examples
        examples = rag_tool.get_examples()
        assert len(examples) > 0
        assert "input" in examples[0]
        assert "output" in examples[0]