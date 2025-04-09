"""
Fixtures for RAG tools tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.rag.tools import Tool

class MockTool(Tool):
    """Mock tool for testing"""
    
    def __init__(self, name="mock_tool", description="Mock tool"):
        super().__init__(name=name, description=description)
    
    async def execute(self, input_data):
        return {"result": f"Executed {self.name} with input: {input_data}"}
    
    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {
                "test_param": {
                    "type": "string",
                    "description": "Test parameter"
                }
            }
        }
    
    def get_output_schema(self):
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Test result"
                }
            }
        }
    
    def get_examples(self):
        return [
            {
                "input": {"test_param": "test_value"},
                "output": {"result": "Executed mock_tool with input: {'test_param': 'test_value'}"}
            }
        ]

@pytest.fixture
def mock_tool():
    """Create a mock tool"""
    return MockTool()

@pytest.fixture
def mock_rag_engine():
    """Create a mock RAG engine for tool tests"""
    mock = AsyncMock()
    mock.retrieve.return_value = [
        {
            "content": "Test content",
            "metadata": {"document_id": "doc123"},
            "score": 0.95
        }
    ]
    return mock