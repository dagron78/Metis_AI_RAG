#!/usr/bin/env python
"""
Script to run the most important Metis RAG tests in a logical order.
This script executes tests from core components to complete system testing.
"""

import os
import subprocess
import sys
import time
import argparse
from datetime import datetime

# Set up logging
LOG_FILE = "test_execution_log.txt"

# Global args variable that will be set in main()
args = None

def log_message(message, also_print=True, verbose_only=False):
    """Log a message to the log file and optionally print to console."""
    global args
    # Skip printing verbose messages if verbose mode is not enabled
    if verbose_only and args and not args.verbose and also_print:
        also_print = False
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")
    
    if also_print:
        print(log_entry)

def run_test(test_path, section_name=""):
    """Run a specific test and log the result."""
    global args
    if section_name:
        log_message(f"\n{'=' * 80}\n{section_name}\n{'=' * 80}")
    
    log_message(f"Running test: {test_path}")
    start_time = time.time()
    
    try:
        # Run the test using pytest
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Log the output
        duration = time.time() - start_time
        log_message(f"Test completed in {duration:.2f} seconds with exit code: {result.returncode}")
        
        # Print stdout and stderr
        if result.stdout:
            log_message(f"STDOUT:\n{result.stdout}", also_print=args and args.verbose)
        if result.stderr:
            log_message(f"STDERR:\n{result.stderr}", also_print=args and args.verbose)
        
        # Determine if the test passed or failed
        status = "PASSED" if result.returncode == 0 else "FAILED"
        log_message(f"Test {status}: {test_path}")
        
        return result.returncode == 0
    
    except Exception as e:
        log_message(f"Error running test {test_path}: {str(e)}")
        return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Metis RAG tests in a logical order")
    parser.add_argument("-s", "--section", type=int, choices=range(1, 6),
                        help="Run only a specific section (1-5)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show more detailed output")
    return parser.parse_args()

def main():
    """Main function to run all tests in the specified order."""
    # Parse command line arguments
    global args
    args = parse_arguments()
    
    # Initialize log file
    with open(LOG_FILE, "w") as f:
        f.write(f"Metis RAG Test Execution Log - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Define test sections and their tests
    test_sections = [
        {
            "name": "1. Core Component Unit Tests",
            "tests": [
                "tests/unit/rag/engine/test_rag_engine.py",
                "tests/unit/test_security_utils.py",
                "tests/unit/test_text_formatting.py",
                "tests/unit/db/test_db_connection.py",
                "tests/unit/db/repositories/test_document_repository.py",
                "tests/unit/rag/test_query_analyzer.py",
                "tests/unit/rag/tools/test_rag_tool.py",
                "tests/unit/middleware/test_authentication.py"
            ]
        },
        {
            "name": "2. Component Integration Tests",
            "tests": [
                "tests/integration/test_chunking_judge_integration.py",
                "tests/integration/rag_api/test_langgraph_rag_agent.py",
                "tests/integration/test_permissions_db.py",
                "tests/integration/test_auth_endpoints.py",
                "tests/integration/tasks_db/test_simplified_document_processing_with_db.py"
            ]
        },
        {
            "name": "3. Feature-Level Tests",
            "tests": [
                "tests/unit/utils/test_code_formatting.py",
                "tests/unit/api/test_chat_api.py",
                "tests/unit/api/test_document_upload.py",
                "tests/integration/test_permissions_vector.py"
            ]
        },
        {
            "name": "4. End-to-End Tests",
            "tests": [
                "tests/e2e/document_processing/test_document_processing_performance.py",
                "tests/e2e/auth/test_auth_flows.py",
                "tests/e2e/chat/test_metis_rag_e2e.py"
            ]
        },
        {
            "name": "5. Performance and Edge Case Tests",
            "tests": [
                "tests/unit/test_memory_buffer.py",
                "tests/e2e/chat/test_metis_rag_e2e_demo.py"
            ]
        }
    ]
    
    # Filter sections if a specific section was requested
    if args.section:
        section_index = args.section - 1  # Convert to 0-based index
        if 0 <= section_index < len(test_sections):
            test_sections = [test_sections[section_index]]
            log_message(f"Running only section {args.section}: {test_sections[0]['name']}")
        else:
            log_message(f"Error: Invalid section number {args.section}")
            return 1
    
    # Track overall success
    all_tests_passed = True
    failed_tests = []
    
    # Run all tests in order
    for section in test_sections:
        section_passed = True
        
        for test_path in section["tests"]:
            test_passed = run_test(test_path, section["name"] if test_path == section["tests"][0] else "")
            
            if not test_passed:
                section_passed = False
                all_tests_passed = False
                failed_tests.append(test_path)
                
                # If a core component test fails, we might want to stop the entire test run
                if section["name"] == "1. Core Component Unit Tests":
                    log_message(f"Critical test failure in core component: {test_path}")
                    log_message("Continuing with remaining tests in this section, but higher-level tests may fail.")
        
        # Log section summary
        if section_passed:
            log_message(f"\nSection {section['name']} PASSED")
        else:
            log_message(f"\nSection {section['name']} FAILED - Some tests did not pass")
    
    # Log overall summary
    log_message("\n" + "=" * 80)
    log_message("TEST EXECUTION SUMMARY")
    log_message("=" * 80)
    
    if all_tests_passed:
        log_message("All tests PASSED successfully!")
    else:
        log_message(f"Some tests FAILED. {len(failed_tests)} test(s) failed:")
        for test in failed_tests:
            log_message(f"  - {test}")
    
    log_message(f"\nTest execution completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"Detailed log available in: {os.path.abspath(LOG_FILE)}")
    
    # Return appropriate exit code
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())