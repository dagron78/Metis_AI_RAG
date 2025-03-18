"""
Unit tests for the ProcessLogger
"""
import pytest
import os
import json
import tempfile
from datetime import datetime
from unittest.mock import MagicMock

from app.rag.process_logger import ProcessLogger


class TestProcessLogger:
    """Tests for the ProcessLogger class"""
    
    def test_start_process(self):
        """Test starting a new process"""
        # Create process logger
        process_logger = ProcessLogger()
        
        # Start process
        process_logger.start_process("query123", "What is the capital of France?")
        
        # Check process log
        log = process_logger.get_process_log("query123")
        assert log is not None
        assert log["query"] == "What is the capital of France?"
        assert "timestamp" in log
        assert log["steps"] == []
        assert log["final_response"] is None
        assert log["audit_report"] is None
    
    def test_log_step(self):
        """Test logging a step"""
        # Create process logger
        process_logger = ProcessLogger()
        
        # Start process
        process_logger.start_process("query123", "What is the capital of France?")
        
        # Log step
        process_logger.log_step("query123", "query_analysis", {
            "complexity": "simple",
            "requires_tools": ["rag"]
        })
        
        # Check process log
        log = process_logger.get_process_log("query123")
        assert len(log["steps"]) == 1
        assert log["steps"][0]["step_name"] == "query_analysis"
        assert log["steps"][0]["data"]["complexity"] == "simple"
        assert log["steps"][0]["data"]["requires_tools"] == ["rag"]
        assert "timestamp" in log["steps"][0]
    
    def test_log_tool_usage(self):
        """Test logging tool usage"""
        # Create process logger
        process_logger = ProcessLogger()
        
        # Start process
        process_logger.start_process("query123", "What is the capital of France?")
        
        # Log tool usage
        process_logger.log_tool_usage(
            query_id="query123",
            tool_name="rag",
            input_data={"query": "What is the capital of France?", "top_k": 3},
            output_data={"chunks": [{"content": "Paris is the capital of France."}]}
        )
        
        # Check process log
        log = process_logger.get_process_log("query123")
        assert len(log["steps"]) == 1
        assert log["steps"][0]["step_name"] == "tool_rag"
        assert log["steps"][0]["data"]["tool"] == "rag"
        assert log["steps"][0]["data"]["input"]["query"] == "What is the capital of France?"
        assert log["steps"][0]["data"]["output"]["chunks"][0]["content"] == "Paris is the capital of France."
    
    def test_log_final_response(self):
        """Test logging the final response"""
        # Create process logger
        process_logger = ProcessLogger()
        
        # Start process
        process_logger.start_process("query123", "What is the capital of France?")
        
        # Log final response
        process_logger.log_final_response(
            query_id="query123",
            response="The capital of France is Paris.",
            metadata={"confidence": 0.95}
        )
        
        # Check process log
        log = process_logger.get_process_log("query123")
        assert log["final_response"] is not None
        assert log["final_response"]["text"] == "The capital of France is Paris."
        assert log["final_response"]["metadata"]["confidence"] == 0.95
        assert "timestamp" in log["final_response"]
    
    def test_get_step_data(self):
        """Test getting step data"""
        # Create process logger
        process_logger = ProcessLogger()
        
        # Start process
        process_logger.start_process("query123", "What is the capital of France?")
        
        # Log steps
        process_logger.log_step("query123", "query_analysis", {"complexity": "simple"})
        process_logger.log_step("query123", "retrieval", {"chunks": [{"content": "Paris is the capital of France."}]})
        process_logger.log_step("query123", "retrieval", {"chunks": [{"content": "France's capital city is Paris."}]})
        
        # Get step data
        retrieval_steps = process_logger.get_step_data("query123", "retrieval")
        
        # Check step data
        assert len(retrieval_steps) == 2
        assert retrieval_steps[0]["chunks"][0]["content"] == "Paris is the capital of France."
        assert retrieval_steps[1]["chunks"][0]["content"] == "France's capital city is Paris."
    
    def test_get_tool_usage(self):
        """Test getting tool usage data"""
        # Create process logger
        process_logger = ProcessLogger()
        
        # Start process
        process_logger.start_process("query123", "What is the capital of France?")
        
        # Log tool usage
        process_logger.log_tool_usage(
            query_id="query123",
            tool_name="rag",
            input_data={"query": "What is the capital of France?"},
            output_data={"chunks": [{"content": "Paris is the capital of France."}]}
        )
        
        process_logger.log_tool_usage(
            query_id="query123",
            tool_name="rag",
            input_data={"query": "Where is Paris located?"},
            output_data={"chunks": [{"content": "Paris is located in northern France."}]}
        )
        
        # Get tool usage
        rag_usage = process_logger.get_tool_usage("query123", "rag")
        
        # Check tool usage
        assert len(rag_usage) == 2
        assert rag_usage[0]["input"]["query"] == "What is the capital of France?"
        assert rag_usage[1]["input"]["query"] == "Where is Paris located?"
    
    def test_clear_log(self):
        """Test clearing the process log"""
        # Create process logger
        process_logger = ProcessLogger()
        
        # Start processes
        process_logger.start_process("query123", "What is the capital of France?")
        process_logger.start_process("query456", "What is the population of Germany?")
        
        # Clear specific log
        process_logger.clear_log("query123")
        
        # Check logs
        assert process_logger.get_process_log("query123") is None
        assert process_logger.get_process_log("query456") is not None
        
        # Clear all logs
        process_logger.clear_log()
        
        # Check logs
        assert process_logger.get_process_log("query456") is None
    
    def test_save_to_file(self):
        """Test saving the process log to a file"""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create process logger with log directory
            process_logger = ProcessLogger(log_dir=temp_dir)
            
            # Start process
            process_logger.start_process("query123", "What is the capital of France?")
            
            # Log step
            process_logger.log_step("query123", "query_analysis", {"complexity": "simple"})
            
            # Log final response
            process_logger.log_final_response("query123", "The capital of France is Paris.")
            
            # Check that file was created
            log_file = os.path.join(temp_dir, "query_query123.json")
            assert os.path.exists(log_file)
            
            # Check file contents
            with open(log_file, 'r') as f:
                log_data = json.load(f)
                assert log_data["query"] == "What is the capital of France?"
                assert len(log_data["steps"]) == 1
                assert log_data["final_response"]["text"] == "The capital of France is Paris."