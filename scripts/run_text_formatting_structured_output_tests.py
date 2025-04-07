#!/usr/bin/env python3
"""
Script to test the structured output approach for text formatting
"""
import os
import sys
import pytest
import logging
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('text_formatting_structured_output_tests.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the text formatting structured output tests"""
    logger.info("Running text formatting structured output tests...")
    
    # Run the tests
    test_file = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_text_formatting_structured_output.py')
    result = pytest.main(["-xvs", test_file])
    
    if result == 0:
        logger.info("All structured output tests passed!")
    else:
        logger.error(f"Structured output tests failed with exit code: {result}")
        sys.exit(result)
    
    # Run a manual test with a sample structured output
    logger.info("\nRunning manual test with sample structured output...")
    try:
        # Create a sample structured output
        structured_output = {
            "text": "This is a sample text with multiple paragraphs.\n\nThis is the second paragraph.\n\nHere's a Python example: {CODE_BLOCK_0}",
            "code_blocks": [
                {
                    "language": "python",
                    "code": "def hello():\n    print('Hello, world!')"
                }
            ],
            "text_blocks": [
                {
                    "content": "Structured Output Example",
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
        }
        
        # Import the necessary modules
        from app.models.structured_output import FormattedResponse
        from app.rag.rag_generation import GenerationMixin
        
        # Create a FormattedResponse object
        formatted_response = FormattedResponse.model_validate(structured_output)
        
        # Create a mock response object
        mock_response = {"response": json.dumps(structured_output)}
        
        # Create an instance of GenerationMixin
        mixin = GenerationMixin()
        
        # Process the response
        processed_text = mixin._process_response_text(mock_response)
        
        # Check the results
        logger.info("Manual test results:")
        logger.info(f"Processed text length: {len(processed_text)}")
        logger.info(f"Processed text preview: {processed_text[:200]}...")
        
        # Check for expected elements
        if "## Structured Output Example" in processed_text:
            logger.info("✅ Heading properly formatted")
        else:
            logger.warning("⚠️ Heading not properly formatted")
        
        if "```python" in processed_text and "```" in processed_text:
            logger.info("✅ Code block properly formatted")
        else:
            logger.warning("⚠️ Code block not properly formatted")
        
        if "{CODE_BLOCK_0}" not in processed_text:
            logger.info("✅ Code block placeholder properly replaced")
        else:
            logger.warning("⚠️ Code block placeholder not replaced")
        
        # Count paragraphs
        paragraphs = processed_text.split("\n\n")
        logger.info(f"Paragraph count: {len(paragraphs)}")
        
        logger.info("Manual test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in manual test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()