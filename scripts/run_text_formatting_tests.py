#!/usr/bin/env python3
"""
Script to run text formatting tests and analyze the results.

This script:
1. Runs the text formatting tests
2. Analyzes the logs to identify formatting issues
3. Generates a report with recommendations
"""
import sys
import os
import logging
import json
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('text_formatting_tests.log')
    ]
)

logger = logging.getLogger("run_text_formatting_tests")

def setup_test_environment():
    """Set up the test environment."""
    logger.info("Setting up test environment")
    
    # Create test directories if they don't exist
    test_dirs = [
        Path("tests/test_cases/text_formatting"),
        Path("tests/results")
    ]
    
    for test_dir in test_dirs:
        test_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {test_dir}")
    
    # Check if test files exist
    test_formatting_py = Path("tests/test_text_formatting.py")
    test_marked_html = Path("tests/test_marked_config.html")
    
    if not test_formatting_py.exists():
        logger.error(f"Test file not found: {test_formatting_py}")
        return False
    
    if not test_marked_html.exists():
        logger.error(f"Test file not found: {test_marked_html}")
        return False
    
    logger.info("Test environment setup complete")
    return True

def run_text_formatting_tests():
    """Run the text formatting tests."""
    logger.info("Running text formatting tests")
    
    try:
        # Run the Python test script
        logger.info("Running test_text_formatting.py")
        result = subprocess.run(
            [sys.executable, "tests/test_text_formatting.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("Test output:")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("Test errors:")
            logger.warning(result.stderr)
        
        # Check if results file was created
        results_file = Path("tests/results/text_formatting_results.json")
        if not results_file.exists():
            logger.error("Test results file not found")
            return False
        
        logger.info(f"Test results saved to {results_file}")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running tests: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False

def open_marked_config_tester():
    """Open the marked.js configuration tester in a browser."""
    logger.info("Opening marked.js configuration tester")
    
    test_marked_html = Path("tests/test_marked_config.html").absolute()
    
    if not test_marked_html.exists():
        logger.error(f"Test file not found: {test_marked_html}")
        return False
    
    try:
        # Open the HTML file in the default browser
        webbrowser.open(f"file://{test_marked_html}")
        logger.info(f"Opened {test_marked_html} in browser")
        return True
    
    except Exception as e:
        logger.error(f"Error opening browser: {e}")
        return False

def analyze_test_results():
    """Analyze the test results and generate a report."""
    logger.info("Analyzing test results")
    
    results_file = Path("tests/results/text_formatting_results.json")
    if not results_file.exists():
        logger.error("Test results file not found")
        return False
    
    try:
        with open(results_file, "r", encoding="utf-8") as f:
            results = json.load(f)
        
        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_tests": sum(1 for r in results if r.get("success", False)),
            "failed_tests": sum(1 for r in results if not r.get("success", False)),
            "test_details": results,
            "recommendations": []
        }
        
        # Analyze results and add recommendations
        if report["failed_tests"] > 0:
            report["recommendations"].append(
                "Some tests failed. Check the logs for details."
            )
        
        # Check for paragraph preservation issues
        paragraph_issues = False
        for result in results:
            if not result.get("success", False):
                continue
            
            raw_text = result.get("raw_text", "")
            processed_text = result.get("processed_text", "")
            
            raw_paragraphs = raw_text.count("\n\n") + 1
            processed_paragraphs = processed_text.count("\n\n") + 1
            
            if raw_paragraphs != processed_paragraphs:
                paragraph_issues = True
                logger.warning(f"Paragraph count changed in test {result['name']}: {raw_paragraphs} -> {processed_paragraphs}")
        
        if paragraph_issues:
            report["recommendations"].append(
                "Paragraph structure is not being preserved. Consider modifying normalize_text() to better handle paragraph breaks."
            )
            report["recommendations"].append(
                "Experiment with marked.js breaks: false setting to see if it better preserves paragraph structure."
            )
        
        # Save report
        report_file = Path("tests/results/text_formatting_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Analysis report saved to {report_file}")
        
        # Print summary
        logger.info(f"Test summary: {report['successful_tests']}/{report['total_tests']} tests passed")
        for recommendation in report["recommendations"]:
            logger.info(f"Recommendation: {recommendation}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error analyzing test results: {e}")
        return False

def main():
    """Run the text formatting tests and analysis."""
    logger.info("Starting text formatting tests")
    
    # Setup test environment
    if not setup_test_environment():
        logger.error("Failed to set up test environment")
        return 1
    
    # Run tests
    if not run_text_formatting_tests():
        logger.error("Failed to run text formatting tests")
        return 1
    
    # Analyze results
    if not analyze_test_results():
        logger.error("Failed to analyze test results")
        return 1
    
    # Open marked.js configuration tester
    if not open_marked_config_tester():
        logger.warning("Failed to open marked.js configuration tester")
    
    logger.info("Text formatting tests completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())