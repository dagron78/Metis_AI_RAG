"""
Integration tests for the response quality pipeline
"""
import pytest
import asyncio
import os
import json
from unittest.mock import MagicMock, AsyncMock, patch

from app.rag.response_quality_pipeline import ResponseQualityPipeline
from app.rag.process_logger import ProcessLogger
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient

class TestResponseQualityIntegration:
    """Integration tests for the response quality pipeline"""
    
    @pytest.fixture
    def process_logger(self):
        """Create a process logger"""
        log_dir = "tests/results/process_logs"
        os.makedirs(log_dir, exist_ok=True)
        return ProcessLogger(log_dir=log_dir)
    
    @pytest.fixture
    def ollama_client(self):
        """Create a mock Ollama client"""
        client = AsyncMock()
        
        # Mock the generate method to return different responses based on the prompt
        async def mock_generate(prompt, **kwargs):
            if "synthesize" in prompt.lower() or "context" in prompt.lower():
                return {
                    "response": "Paris is the capital of France. It is known for its art, culture, and the Eiffel Tower [1]."
                }
            elif "evaluate" in prompt.lower():
                evaluation = {
                    "factual_accuracy": 9,
                    "completeness": 7,
                    "relevance": 9,
                    "hallucination_detected": False,
                    "hallucination_details": "No hallucinations detected.",
                    "overall_score": 8,
                    "strengths": ["Accurate information", "Clear explanation", "Proper citation"],
                    "weaknesses": ["Could be more detailed"],
                    "improvement_suggestions": ["Add more context about Paris"]
                }
                return {"response": json.dumps(evaluation)}
            elif "refine" in prompt.lower():
                refinement = {
                    "refined_response": "Paris is the capital of France. It is known for its art, culture, and the Eiffel Tower [1]. As one of Europe's major centers for art, fashion, and culture, Paris is home to many famous landmarks including the Louvre Museum and Notre-Dame Cathedral.",
                    "improvement_summary": "Added more details about Paris as a cultural center and mentioned additional landmarks."
                }
                return {"response": json.dumps(refinement)}
            elif "analyze" in prompt.lower():
                analysis = {
                    "process_efficiency": {
                        "assessment": "The process was efficient.",
                        "issues_identified": [],
                        "recommendations": []
                    },
                    "retrieval_quality": {
                        "assessment": "Retrieval was effective.",
                        "issues_identified": [],
                        "recommendations": []
                    },
                    "response_quality": {
                        "assessment": "Response was accurate and well-structured.",
                        "issues_identified": [],
                        "recommendations": ["Could add more historical context"]
                    },
                    "overall_assessment": {
                        "strengths": ["Accurate information", "Good citations", "Clear structure"],
                        "weaknesses": ["Limited historical context"],
                        "recommendations": ["Add historical context in future responses"]
                    }
                }
                return {"response": json.dumps(analysis)}
            else:
                return {"response": "Default response"}
        
        client.generate = AsyncMock(side_effect=mock_generate)
        return client
    
    @pytest.fixture
    def vector_store(self):
        """Create a mock vector store"""
        store = AsyncMock()
        
        # Mock the search method to return sample chunks
        async def mock_search(query, **kwargs):
            return [
                {
                    "chunk_id": "chunk1",
                    "content": "Paris is the capital of France. It is known for the Eiffel Tower.",
                    "metadata": {
                        "document_id": "doc1",
                        "filename": "geography.txt",
                        "tags": ["geography", "europe"],
                        "folder": "/"
                    },
                    "distance": 0.1
                },
                {
                    "chunk_id": "chunk2",
                    "content": "France is a country in Western Europe. Its capital is Paris.",
                    "metadata": {
                        "document_id": "doc2",
                        "filename": "countries.txt",
                        "tags": ["geography", "europe"],
                        "folder": "/"
                    },
                    "distance": 0.2
                }
            ]
        
        store.search = AsyncMock(side_effect=mock_search)
        store.get_stats = MagicMock(return_value={"count": 100})
        return store
    
    @pytest.mark.asyncio
    async def test_response_quality_pipeline_standalone(self, ollama_client, process_logger):
        """Test the response quality pipeline as a standalone component"""
        # Create the pipeline
        pipeline = ResponseQualityPipeline(
            llm_provider=ollama_client,
            process_logger=process_logger,
            max_refinement_iterations=2,
            quality_threshold=8.0,
            enable_audit_reports=True
        )
        
        # Create test data
        query = "What is the capital of France?"
        query_id = "test-integration-id"
        context = "[1] Source: geography.txt, Tags: [geography, europe], Folder: /\n\nParis is the capital of France. It is known for the Eiffel Tower."
        sources = [
            {
                "document_id": "doc1",
                "chunk_id": "chunk1",
                "relevance_score": 0.9,
                "excerpt": "Paris is the capital of France. It is known for the Eiffel Tower.",
                "filename": "geography.txt",
                "tags": ["geography", "europe"],
                "folder": "/"
            }
        ]
        
        # Process the query
        result = await pipeline.process(
            query=query,
            context=context,
            sources=sources,
            query_id=query_id
        )
        
        # Check the result
        assert "response" in result
        assert "sources" in result
        assert "evaluation" in result
        assert "refinement_iterations" in result
        assert "execution_time" in result
        
        # Verify the response content
        assert "Paris" in result["response"]
        assert "France" in result["response"]
        
        # Verify the evaluation
        assert result["evaluation"]["overall_score"] >= 8.0
        assert not result["evaluation"]["hallucination_detected"]
        
        # Verify that refinement occurred
        assert "Louvre" in result["response"] or "Notre-Dame" in result["response"]
        
        # Check that the process logger was used
        log_file = os.path.join(process_logger.log_dir, f"query_{query_id}.json")
        assert os.path.exists(log_file)
    
    @pytest.mark.asyncio
    async def test_response_quality_with_rag_engine(self, ollama_client, vector_store, process_logger):
        """Test integrating the response quality pipeline with the RAG engine"""
        # Create the RAG engine
        rag_engine = RAGEngine(
            vector_store=vector_store,
            ollama_client=ollama_client
        )
        
        # Create the pipeline
        pipeline = ResponseQualityPipeline(
            llm_provider=ollama_client,
            process_logger=process_logger,
            max_refinement_iterations=1,
            quality_threshold=8.0,
            enable_audit_reports=True
        )
        
        # Mock the RAG engine's query method to use our pipeline
        original_query = rag_engine.query
        
        async def enhanced_query(query, **kwargs):
            # First, get the standard RAG result
            rag_result = await original_query(query, **kwargs)
            
            # Extract the necessary components
            response = rag_result.get("answer", "")
            sources = rag_result.get("sources", [])
            
            # Convert sources to the format expected by the pipeline
            formatted_sources = []
            for source in sources:
                formatted_sources.append({
                    "document_id": source.document_id,
                    "chunk_id": source.chunk_id,
                    "relevance_score": source.relevance_score,
                    "excerpt": source.excerpt,
                    "filename": source.filename,
                    "tags": source.tags,
                    "folder": source.folder
                })
            
            # Get the context from the RAG engine
            # In a real implementation, this would be extracted from the RAG engine's internal state
            context = "[1] Source: geography.txt, Tags: [geography, europe], Folder: /\n\nParis is the capital of France. It is known for the Eiffel Tower."
            
            # Process through the quality pipeline
            quality_result = await pipeline.process(
                query=query,
                context=context,
                sources=formatted_sources,
                conversation_context=kwargs.get("conversation_history")
            )
            
            # Return an enhanced result
            return {
                "query": query,
                "answer": quality_result["response"],
                "sources": sources,  # Keep the original source format for compatibility
                "evaluation": quality_result["evaluation"],
                "refinement_iterations": quality_result["refinement_iterations"],
                "quality_score": quality_result["evaluation"]["overall_score"]
            }
        
        # Replace the query method
        with patch.object(rag_engine, 'query', side_effect=enhanced_query):
            # Test the enhanced query
            result = await rag_engine.query(
                query="What is the capital of France?",
                model="llama3",
                use_rag=True
            )
            
            # Check the result
            assert "answer" in result
            assert "sources" in result
            assert "evaluation" in result
            assert "refinement_iterations" in result
            assert "quality_score" in result
            
            # Verify the response content
            assert "Paris" in result["answer"]
            assert "France" in result["answer"]
            
            # Verify the evaluation
            assert result["quality_score"] >= 8.0
            
            # Verify that the sources are included
            assert len(result["sources"]) > 0

if __name__ == "__main__":
    pytest.main(["-xvs", "test_response_quality_integration.py"])