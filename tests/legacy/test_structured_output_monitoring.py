"""
Test the structured output monitoring system
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import os
import shutil
from pathlib import Path

from app.rag.text_formatting_monitor import (
    TextFormattingMonitor,
    FormattingApproach,
    FormattingEvent,
    get_monitor
)
from app.models.structured_output import FormattedResponse, CodeBlock, TextBlock
from app.rag.rag_generation import GenerationMixin


@pytest.fixture
def test_monitor():
    """Create a test monitor with a temporary log directory"""
    # Create a temporary log directory
    test_log_dir = "test_logs/text_formatting"
    os.makedirs(test_log_dir, exist_ok=True)
    
    # Create a test monitor
    monitor = TextFormattingMonitor(log_dir=test_log_dir)
    
    yield monitor
    
    # Clean up the temporary log directory
    shutil.rmtree("test_logs", ignore_errors=True)


def test_record_event(test_monitor):
    """Test recording events"""
    # Record a success event
    test_monitor.record_event(
        approach=FormattingApproach.STRUCTURED_OUTPUT,
        event=FormattingEvent.SUCCESS,
        details={"response_size": 1000, "content_types": ["text", "code"]}
    )
    
    # Record a fallback event
    test_monitor.record_event(
        approach=FormattingApproach.STRUCTURED_OUTPUT,
        event=FormattingEvent.FALLBACK,
        details={"fallback_to": FormattingApproach.BACKEND_PROCESSING.value, "reason": "JSON parsing error"}
    )
    
    # Record an error event
    test_monitor.record_event(
        approach=FormattingApproach.STRUCTURED_OUTPUT,
        event=FormattingEvent.ERROR,
        error_message="Failed to parse JSON"
    )
    
    # Check that events were recorded
    assert len(test_monitor.events) == 3
    assert test_monitor.events[0]["approach"] == FormattingApproach.STRUCTURED_OUTPUT.value
    assert test_monitor.events[0]["event"] == FormattingEvent.SUCCESS.value
    assert test_monitor.events[1]["event"] == FormattingEvent.FALLBACK.value
    assert test_monitor.events[2]["event"] == FormattingEvent.ERROR.value
    assert "error_message" in test_monitor.events[2]


def test_save_events(test_monitor):
    """Test saving events to disk"""
    # Record some events
    test_monitor.record_event(
        approach=FormattingApproach.STRUCTURED_OUTPUT,
        event=FormattingEvent.SUCCESS,
        details={"response_size": 1000, "content_types": ["text", "code"]}
    )
    
    # Save events
    test_monitor.save_events()
    
    # Check that events were saved
    log_files = list(Path(test_monitor.log_dir).glob("text_formatting_events_*.json"))
    assert len(log_files) == 1
    
    # Check that events were cleared
    assert len(test_monitor.events) == 0
    
    # Check that the saved events are valid JSON
    with open(log_files[0], "r") as f:
        saved_events = json.load(f)
    
    assert len(saved_events) == 1
    assert saved_events[0]["approach"] == FormattingApproach.STRUCTURED_OUTPUT.value
    assert saved_events[0]["event"] == FormattingEvent.SUCCESS.value


def test_generate_report(test_monitor):
    """Test generating a report"""
    # Record some events
    test_monitor.record_event(
        approach=FormattingApproach.STRUCTURED_OUTPUT,
        event=FormattingEvent.SUCCESS,
        details={"response_size": 1000, "content_types": ["text", "code"]}
    )
    
    test_monitor.record_event(
        approach=FormattingApproach.STRUCTURED_OUTPUT,
        event=FormattingEvent.FALLBACK,
        details={"fallback_to": FormattingApproach.BACKEND_PROCESSING.value, "reason": "JSON parsing error"}
    )
    
    test_monitor.record_event(
        approach=FormattingApproach.BACKEND_PROCESSING,
        event=FormattingEvent.SUCCESS,
        details={"response_size": 800, "content_types": ["text"]}
    )
    
    # Save events
    test_monitor.save_events()
    
    # Mock _load_events to return our test events
    with open(list(Path(test_monitor.log_dir).glob("text_formatting_events_*.json"))[0], "r") as f:
        saved_events = json.load(f)
    
    test_monitor._load_events = MagicMock(return_value=saved_events)
    
    # Generate a report
    report = test_monitor.generate_report(time_period="day")
    
    # Check the report
    assert report["total_events"] == 3
    assert report["success_count"] == 2
    assert report["fallback_count"] == 1
    assert report["error_count"] == 0
    assert report["success_rate"] == (2/3) * 100
    assert "approach_usage" in report
    assert "structured_output" in report["approach_usage"]
    assert "backend_processing" in report["approach_usage"]


@pytest.mark.asyncio
async def test_process_response_text_with_monitoring():
    """Test that the process_response_text method uses the monitoring system"""
    # Create a mock monitor
    mock_monitor = MagicMock()
    mock_monitor.record_structured_output_success = MagicMock()
    mock_monitor.record_structured_output_error = MagicMock()
    mock_monitor.record_fallback = MagicMock()
    mock_monitor.record_event = MagicMock()
    
    # Patch get_monitor to return our mock
    with patch("app.rag.rag_generation.get_monitor", return_value=mock_monitor):
        # Create a GenerationMixin instance
        mixin = GenerationMixin()
        
        # Create a sample JSON response with text blocks and code blocks
        json_response = json.dumps({
            "text": "This is a sample text with code blocks.\n\nHere's a Python example: {CODE_BLOCK_0}",
            "code_blocks": [
                {
                    "language": "python",
                    "code": "def hello():\n    print('Hello, world!')"
                }
            ],
            "text_blocks": [
                {
                    "content": "Mixed Content Example",
                    "format_type": "heading"
                },
                {
                    "content": "This is a sample text with proper paragraph structure.",
                    "format_type": "paragraph"
                },
                {
                    "content": "Here's a Python example: {CODE_BLOCK_0}",
                    "format_type": "paragraph"
                },
                {
                    "content": "The function above prints a greeting message.",
                    "format_type": "paragraph"
                }
            ],
            "preserve_paragraphs": True
        })
        
        # Create a mock response object
        mock_response = {"response": json_response}
        
        # Process the response
        processed_text = mixin._process_response_text(mock_response)
        
        # Check that the monitoring methods were called
        mock_monitor.record_structured_output_success.assert_called_once()
        assert "code" in mock_monitor.record_structured_output_success.call_args[1]["content_types"]
        
        # Check that the text was processed correctly
        assert "## Mixed Content Example" in processed_text
        assert "```python" in processed_text
        assert "def hello():" in processed_text
        assert "```" in processed_text
        
        # Test error case
        mock_response = {"response": "{invalid json}"}
        processed_text = mixin._process_response_text(mock_response)
        
        # Check that the error monitoring methods were called
        mock_monitor.record_structured_output_error.assert_called_once()
        mock_monitor.record_fallback.assert_called_once()
        mock_monitor.record_event.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", "test_structured_output_monitoring.py"])