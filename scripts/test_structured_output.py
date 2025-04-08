#!/usr/bin/env python3
"""
Script to test the structured code output functionality
"""
import os
import sys
import pytest
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def main():
    """Run the structured output tests"""
    logger.info("Running structured code output tests...")
    
    # Run the tests
    test_file = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_structured_code_output.py')
    result = pytest.main(["-xvs", test_file])
    
    if result == 0:
        logger.info("All tests passed!")
    else:
        logger.error(f"Tests failed with exit code: {result}")
        sys.exit(result)
    
    # Run a manual test with a sample query
    logger.info("\nRunning manual test with sample query...")
    try:
        from app.rag.rag_engine import RAGEngine
        from app.models.structured_output import FormattedResponse
        import asyncio
        import json
        
        async def test_query():
            engine = RAGEngine()
            response = await engine.query(
                query="Write a Python function to calculate prime numbers between 0 and 100",
                model="llama3:8b",  # Use an appropriate model
                stream=False
            )
            
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response keys: {response.keys()}")
            
            if "answer" in response:
                logger.info(f"Response preview: {response['answer'][:200]}...")
                
                # Check if the response contains properly formatted code blocks
                if "```python" in response["answer"] and "```" in response["answer"]:
                    logger.info("✅ Response contains properly formatted code blocks")
                else:
                    logger.warning("⚠️ Response may not contain properly formatted code blocks")
            else:
                logger.warning(f"Response does not contain 'answer' key: {response}")
        
        # Run the async test
        asyncio.run(test_query())
        
    except Exception as e:
        logger.error(f"Error in manual test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()