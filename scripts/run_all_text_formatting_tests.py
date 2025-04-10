#!/usr/bin/env python3
"""
Script to run all text formatting tests
"""
import os
import sys
import subprocess
import logging
import webbrowser
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('all_text_formatting_tests.log')
    ]
)

logger = logging.getLogger(__name__)

def run_test_script(script_path, description):
    """Run a test script and log the results"""
    logger.info(f"Running {description}...")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f"{description} completed successfully")
            logger.debug(f"Output: {result.stdout}")
        else:
            logger.error(f"{description} failed with exit code: {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            logger.debug(f"Standard output: {result.stdout}")
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running {description}: {str(e)}")
        return False

def open_html_test(html_path, description):
    """Open an HTML test file in the default browser"""
    logger.info(f"Opening {description} in browser...")
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(html_path)
        
        # Use file:// protocol for local files
        url = f"file://{abs_path}"
        
        # Open in browser
        webbrowser.open(url)
        
        logger.info(f"Opened {description} in browser")
        return True
    except Exception as e:
        logger.error(f"Error opening {description}: {str(e)}")
        return False

def main():
    """Run all text formatting tests"""
    logger.info("Starting all text formatting tests...")
    
    # Define test scripts and HTML files
    tests = [
        {
            "type": "script",
            "path": os.path.join(os.path.dirname(__file__), 'run_text_formatting_tests.py'),
            "description": "Basic Text Formatting Tests"
        },
        {
            "type": "script",
            "path": os.path.join(os.path.dirname(__file__), 'run_text_formatting_structured_output_tests.py'),
            "description": "Structured Output Text Formatting Tests"
        },
        {
            "type": "html",
            "path": os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_marked_config.html'),
            "description": "Marked.js Configuration Test"
        },
        {
            "type": "html",
            "path": os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_structured_output_format.html'),
            "description": "Structured Output Format Test"
        }
    ]
    
    # Run all tests
    results = []
    for test in tests:
        if test["type"] == "script":
            success = run_test_script(test["path"], test["description"])
        elif test["type"] == "html":
            success = open_html_test(test["path"], test["description"])
        else:
            logger.error(f"Unknown test type: {test['type']}")
            success = False
        
        results.append({
            "description": test["description"],
            "success": success
        })
    
    # Print summary
    logger.info("\nTest Summary:")
    success_count = sum(1 for r in results if r["success"])
    for i, result in enumerate(results):
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        logger.info(f"{i+1}. {result['description']}: {status}")
    
    logger.info(f"\nOverall: {success_count}/{len(results)} tests passed")
    
    if success_count < len(results):
        logger.warning("Some tests failed. Check the log for details.")
        return 1
    else:
        logger.info("All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())