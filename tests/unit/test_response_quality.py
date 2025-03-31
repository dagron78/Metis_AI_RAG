"""
Tests for the response quality components
"""
import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch

from app.rag.response_synthesizer import ResponseSynthesizer
from app.rag.response_evaluator import ResponseEvaluator
from app.rag.response_refiner import ResponseRefiner
from app.rag.audit_report_generator import AuditReportGenerator
from app.rag.process_logger import ProcessLogger

class TestResponseSynthesizer:
    """Tests for the ResponseSynthesizer class"""
    
    @pytest.fixture
    def llm_provider(self):
        """Create a mock LLM provider"""
        provider = AsyncMock()
        provider.generate = AsyncMock(return_value={"response": "This is a synthesized response with citation [1]."})
        return provider
    
    @pytest.fixture
    def process_logger(self):
        """Create a mock process logger"""
        logger = MagicMock(spec=ProcessLogger)
        logger.log_step = MagicMock()
        return logger
    
    @pytest.mark.asyncio
    async def test_synthesize(self, llm_provider, process_logger):
        """Test the synthesize method"""
        # Create a response synthesizer
        synthesizer = ResponseSynthesizer(
            llm_provider=llm_provider,
            process_logger=process_logger
        )
        
        # Create test data
        query = "What is the capital of France?"
        query_id = "test-query-id"
        context = "[1] Source: geography.txt, Tags: [geography, europe], Folder: /\n\nParis is the capital of France."
        sources = [
            {
                "document_id": "doc1",
                "chunk_id": "chunk1",
                "relevance_score": 0.95,
                "excerpt": "Paris is the capital of France.",
                "filename": "geography.txt",
                "tags": ["geography", "europe"],
                "folder": "/"
            }
        ]
        
        # Call the synthesize method
        result = await synthesizer.synthesize(
            query=query,
            query_id=query_id,
            context=context,
            sources=sources
        )
        
        # Check the result
        assert "response" in result
        assert "sources" in result
        assert "execution_time" in result
        assert result["response"] == "This is a synthesized response with citation [1]."
        assert len(result["sources"]) == 1
        assert result["sources"][0]["document_id"] == "doc1"
        
        # Check that the LLM provider was called
        llm_provider.generate.assert_called_once()
        
        # Check that the process logger was called
        process_logger.log_step.assert_called()

class TestResponseEvaluator:
    """Tests for the ResponseEvaluator class"""
    
    @pytest.fixture
    def llm_provider(self):
        """Create a mock LLM provider"""
        provider = AsyncMock()
        evaluation_json = {
            "factual_accuracy": 8,
            "completeness": 7,
            "relevance": 9,
            "hallucination_detected": False,
            "hallucination_details": "No hallucinations detected.",
            "overall_score": 8,
            "strengths": ["Accurate information", "Clear explanation"],
            "weaknesses": ["Could be more detailed"],
            "improvement_suggestions": ["Add more context about France"]
        }
        provider.generate = AsyncMock(return_value={"response": json.dumps(evaluation_json)})
        return provider
    
    @pytest.fixture
    def process_logger(self):
        """Create a mock process logger"""
        logger = MagicMock(spec=ProcessLogger)
        logger.log_step = MagicMock()
        return logger
    
    @pytest.mark.asyncio
    async def test_evaluate(self, llm_provider, process_logger):
        """Test the evaluate method"""
        # Create a response evaluator
        evaluator = ResponseEvaluator(
            llm_provider=llm_provider,
            process_logger=process_logger
        )
        
        # Create test data
        query = "What is the capital of France?"
        query_id = "test-query-id"
        response = "The capital of France is Paris."
        context = "[1] Source: geography.txt, Tags: [geography, europe], Folder: /\n\nParis is the capital of France."
        sources = [
            {
                "document_id": "doc1",
                "chunk_id": "chunk1",
                "relevance_score": 0.95,
                "excerpt": "Paris is the capital of France.",
                "filename": "geography.txt",
                "tags": ["geography", "europe"],
                "folder": "/"
            }
        ]
        
        # Call the evaluate method
        result = await evaluator.evaluate(
            query=query,
            query_id=query_id,
            response=response,
            context=context,
            sources=sources
        )
        
        # Check the result
        assert "factual_accuracy" in result
        assert "completeness" in result
        assert "relevance" in result
        assert "hallucination_detected" in result
        assert "overall_score" in result
        assert result["factual_accuracy"] == 8
        assert result["completeness"] == 7
        assert result["relevance"] == 9
        assert result["hallucination_detected"] is False
        assert result["overall_score"] == 8
        
        # Check that the LLM provider was called
        llm_provider.generate.assert_called_once()
        
        # Check that the process logger was called
        process_logger.log_step.assert_called()

class TestResponseRefiner:
    """Tests for the ResponseRefiner class"""
    
    @pytest.fixture
    def llm_provider(self):
        """Create a mock LLM provider"""
        provider = AsyncMock()
        refinement_json = {
            "refined_response": "The capital of France is Paris, a city known for its cultural heritage.",
            "improvement_summary": "Added more context about Paris."
        }
        provider.generate = AsyncMock(return_value={"response": json.dumps(refinement_json)})
        return provider
    
    @pytest.fixture
    def process_logger(self):
        """Create a mock process logger"""
        logger = MagicMock(spec=ProcessLogger)
        logger.log_step = MagicMock()
        return logger
    
    @pytest.mark.asyncio
    async def test_refine(self, llm_provider, process_logger):
        """Test the refine method"""
        # Create a response refiner
        refiner = ResponseRefiner(
            llm_provider=llm_provider,
            process_logger=process_logger
        )
        
        # Create test data
        query = "What is the capital of France?"
        query_id = "test-query-id"
        response = "The capital of France is Paris."
        evaluation = {
            "factual_accuracy": 8,
            "completeness": 7,
            "relevance": 9,
            "hallucination_detected": False,
            "hallucination_details": "No hallucinations detected.",
            "overall_score": 8,
            "strengths": ["Accurate information", "Clear explanation"],
            "weaknesses": ["Could be more detailed"],
            "improvement_suggestions": ["Add more context about France"]
        }
        context = "[1] Source: geography.txt, Tags: [geography, europe], Folder: /\n\nParis is the capital of France."
        sources = [
            {
                "document_id": "doc1",
                "chunk_id": "chunk1",
                "relevance_score": 0.95,
                "excerpt": "Paris is the capital of France.",
                "filename": "geography.txt",
                "tags": ["geography", "europe"],
                "folder": "/"
            }
        ]
        
        # Call the refine method
        result = await refiner.refine(
            query=query,
            query_id=query_id,
            response=response,
            evaluation=evaluation,
            context=context,
            sources=sources
        )
        
        # Check the result
        assert "refined_response" in result
        assert "improvement_summary" in result
        assert "execution_time" in result
        assert "iteration" in result
        assert result["refined_response"] == "The capital of France is Paris, a city known for its cultural heritage."
        assert result["improvement_summary"] == "Added more context about Paris."
        assert result["iteration"] == 1
        
        # Check that the LLM provider was called
        llm_provider.generate.assert_called_once()
        
        # Check that the process logger was called
        process_logger.log_step.assert_called()

class TestAuditReportGenerator:
    """Tests for the AuditReportGenerator class"""
    
    @pytest.fixture
    def process_logger(self):
        """Create a mock process logger"""
        logger = MagicMock(spec=ProcessLogger)
        logger.get_process_log = MagicMock(return_value={
            "query": "What is the capital of France?",
            "timestamp": "2025-03-18T18:00:00.000Z",
            "steps": [
                {
                    "step_name": "query_analysis",
                    "timestamp": "2025-03-18T18:00:01.000Z",
                    "data": {
                        "analysis": {
                            "complexity": "simple",
                            "requires_tools": [],
                            "sub_queries": []
                        }
                    }
                },
                {
                    "step_name": "retrieve_chunks",
                    "timestamp": "2025-03-18T18:00:02.000Z",
                    "data": {
                        "chunks": [
                            {
                                "content": "Paris is the capital of France.",
                                "metadata": {
                                    "document_id": "doc1",
                                    "chunk_id": "chunk1",
                                    "filename": "geography.txt",
                                    "tags": ["geography", "europe"],
                                    "folder": "/"
                                }
                            }
                        ]
                    }
                },
                {
                    "step_name": "response_synthesis",
                    "timestamp": "2025-03-18T18:00:03.000Z",
                    "data": {
                        "response": "The capital of France is Paris.",
                        "sources": [
                            {
                                "document_id": "doc1",
                                "chunk_id": "chunk1",
                                "relevance_score": 0.95,
                                "excerpt": "Paris is the capital of France.",
                                "filename": "geography.txt",
                                "tags": ["geography", "europe"],
                                "folder": "/"
                            }
                        ]
                    }
                },
                {
                    "step_name": "response_evaluation",
                    "timestamp": "2025-03-18T18:00:04.000Z",
                    "data": {
                        "evaluation": {
                            "factual_accuracy": 8,
                            "completeness": 7,
                            "relevance": 9,
                            "hallucination_detected": False,
                            "hallucination_details": "No hallucinations detected.",
                            "overall_score": 8,
                            "strengths": ["Accurate information", "Clear explanation"],
                            "weaknesses": ["Could be more detailed"],
                            "improvement_suggestions": ["Add more context about France"]
                        }
                    }
                }
            ],
            "final_response": {
                "text": "The capital of France is Paris.",
                "timestamp": "2025-03-18T18:00:05.000Z"
            }
        })
        logger.log_step = MagicMock()
        return logger
    
    @pytest.fixture
    def llm_provider(self):
        """Create a mock LLM provider"""
        provider = AsyncMock()
        analysis_json = {
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
                "assessment": "Response was accurate but could be more detailed.",
                "issues_identified": ["Limited detail"],
                "recommendations": ["Add more context"]
            },
            "overall_assessment": {
                "strengths": ["Accurate information", "Efficient process"],
                "weaknesses": ["Limited detail"],
                "recommendations": ["Add more context"]
            }
        }
        provider.generate = AsyncMock(return_value={"response": json.dumps(analysis_json)})
        return provider
    
    @pytest.mark.asyncio
    async def test_generate_report(self, process_logger, llm_provider):
        """Test the generate_report method"""
        # Create an audit report generator
        generator = AuditReportGenerator(
            process_logger=process_logger,
            llm_provider=llm_provider
        )
        
        # Call the generate_report method
        result = await generator.generate_report(
            query_id="test-query-id",
            include_llm_analysis=True
        )
        
        # Check the result
        assert "query_id" in result
        assert "query" in result
        assert "timestamp" in result
        assert "process_summary" in result
        assert "information_sources" in result
        assert "reasoning_trace" in result
        assert "verification_status" in result
        assert "execution_timeline" in result
        assert "response_quality" in result
        
        # Check that the process logger was called
        process_logger.get_process_log.assert_called_once_with("test-query-id")
        process_logger.log_step.assert_called_once()
        
        # Check that the LLM provider was called
        llm_provider.generate.assert_called_once()

if __name__ == "__main__":
    pytest.main(["-xvs", "test_response_quality.py"])