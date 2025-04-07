#!/usr/bin/env python3
"""
Script to run the structured output tests
"""
import os
import sys
import pytest
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('structured_output_tests.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the structured output tests"""
    logger.info("Running structured output tests...")
    
    # Run the tests
    test_file = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_structured_output_monitoring.py')
    result = pytest.main(["-xvs", test_file])
    
    if result == 0:
        logger.info("All structured output tests passed!")
    else:
        logger.error(f"Structured output tests failed with exit code: {result}")
        sys.exit(result)

if __name__ == "__main__":
    main()