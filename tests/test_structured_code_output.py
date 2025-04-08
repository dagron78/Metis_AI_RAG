"""
Test the structured code output functionality
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.structured_output import FormattedResponse, CodeBlock, TextBlock
from app.rag.rag_engine import RAGEngine
from app.rag.system_prompts import STRUCTURED_CODE_OUTPUT_PROMPT


@pytest.fixture
def mock_rag_engine():
    """Create a mock RAG engine for testing"""
    engine = MagicMock(spec=RAGEngine)
    engine._is_code_related_query = MagicMock(return_value=True)
    engine._create_system_prompt = MagicMock(return_value=STRUCTURED_CODE_OUTPUT_PROMPT)
    engine.ollama_client = AsyncMock()
    engine.cache_manager = MagicMock()
    engine.cache_manager.llm_response_cache.get_response = MagicMock(return_value=None)
    engine._record_analytics = AsyncMock()
    engine._cleanup_memory = AsyncMock()
    return engine


@pytest.mark.asyncio
async def test_structured_code_output_processing():
    """Test that structured code output is processed correctly"""
    # Create a sample structured output response
    structured_response = {
        "text": "Here's a Python function to calculate prime numbers: {CODE_BLOCK_0}",
        "code_blocks": [
            {
                "language": "python",
                "code": "def is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n\nprime_numbers = [n for n in range(101) if is_prime(n)]\nprint(prime_numbers)"
            }
        ],
        "preserve_paragraphs": True
    }
    
    # Create a FormattedResponse object
    formatted_response = FormattedResponse(**structured_response)
    
    # Verify the object is created correctly
    assert formatted_response.text == "Here's a Python function to calculate prime numbers: {CODE_BLOCK_0}"
    assert len(formatted_response.code_blocks) == 1
    assert formatted_response.code_blocks[0].language == "python"
    assert "def is_prime(n):" in formatted_response.code_blocks[0].code
    
    # Test the JSON schema
    schema = FormattedResponse.model_json_schema()
    assert "text" in schema["properties"]
    assert "code_blocks" in schema["properties"]


@pytest.mark.asyncio
async def test_rag_engine_structured_output():
    """Test that the RAG engine uses structured output for code queries"""
    with patch('app.rag.rag_generation.GenerationMixin._process_response_text') as mock_process:
        # Create a mock RAG engine
        engine = RAGEngine()
        engine._is_code_related_query = MagicMock(return_value=True)
        engine._create_system_prompt = MagicMock(return_value=STRUCTURED_CODE_OUTPUT_PROMPT)
        engine.ollama_client = AsyncMock()
        engine.ollama_client.generate = AsyncMock(return_value={"response": "{}"})
        engine.cache_manager = MagicMock()
        engine.cache_manager.llm_response_cache.get_response = MagicMock(return_value=None)
        engine._record_analytics = AsyncMock()
        engine._cleanup_memory = AsyncMock()
        
        # Mock the process_response_text method
        mock_process.return_value = "Processed response"
        
        # Call the query method with a code-related query
        response = await engine.query(
            query="Write a Python function to calculate prime numbers",
            model="test-model",
            stream=False
        )
        
        # Verify that the format parameter was included in the model parameters
        call_args = engine.ollama_client.generate.call_args[1]
        assert "parameters" in call_args
        assert "format" in call_args["parameters"]
        
        # Verify that the temperature was set to 0
        assert call_args["parameters"]["temperature"] == 0.0
        
        # Verify that the system prompt was set to the structured output prompt
        assert engine._create_system_prompt.called
        
        # Verify that the response was processed
        assert mock_process.called


@pytest.mark.asyncio
async def test_structured_output_integration():
    """Test the full integration of structured output processing"""
    # Create a sample JSON response
    json_response = json.dumps({
        "text": "Here's a Python function to calculate prime numbers: {CODE_BLOCK_0}",
        "code_blocks": [
            {
                "language": "python",
                "code": "def is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n\nprime_numbers = [n for n in range(101) if is_prime(n)]\nprint(prime_numbers)"
            }
        ],
        "preserve_paragraphs": True
    })
    
    # Create a mock response object
    mock_response = {"response": json_response}
    
    # Import the processing function
    from app.rag.rag_generation import GenerationMixin
    
    # Create an instance of GenerationMixin
    mixin = GenerationMixin()
    
    # Process the response
    processed_text = mixin._process_response_text(mock_response)
    
    # Verify that the code block was properly formatted
    assert "```python" in processed_text
    assert "def is_prime(n):" in processed_text
    assert "```" in processed_text
    
    # Verify that the placeholder was replaced
    assert "{CODE_BLOCK_0}" not in processed_text


@pytest.mark.asyncio
async def test_structured_output_with_text_blocks():
    """Test structured output processing with text blocks"""
    # Create a sample JSON response with text blocks
    json_response = json.dumps({
        "text": "This is a fallback text that shouldn't be used when text_blocks are provided.",
        "code_blocks": [
            {
                "language": "python",
                "code": "def example():\n    return 'Hello World'"
            }
        ],
        "text_blocks": [
            {
                "content": "Example Function",
                "format_type": "heading"
            },
            {
                "content": "Here's a simple Python function: {CODE_BLOCK_0}",
                "format_type": "paragraph"
            },
            {
                "content": "This function returns a greeting message.",
                "format_type": "paragraph"
            }
        ],
        "preserve_paragraphs": True
    })
    
    # Create a mock response object
    mock_response = {"response": json_response}
    
    # Import the processing function
    from app.rag.rag_generation import GenerationMixin
    
    # Create an instance of GenerationMixin
    mixin = GenerationMixin()
    
    # Process the response
    processed_text = mixin._process_response_text(mock_response)
    
    # Verify that the heading is properly formatted
    assert "## Example Function" in processed_text
    
    # Verify that the code block was properly formatted
    assert "```python" in processed_text
    assert "def example():" in processed_text
    assert "```" in processed_text
    
    # Verify that the placeholder was replaced
    assert "{CODE_BLOCK_0}" not in processed_text
    
    # Verify that paragraphs are properly separated
    assert "Here's a simple Python function:" in processed_text
    assert "This function returns a greeting message." in processed_text
    
    # Verify that the fallback text was not used
    assert "This is a fallback text" not in processed_text


if __name__ == "__main__":
    pytest.main(["-xvs", "test_structured_code_output.py"])