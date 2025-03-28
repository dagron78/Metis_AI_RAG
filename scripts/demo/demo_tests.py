#!/usr/bin/env python3
"""
Demonstration script for Metis RAG testing strategy.
This script runs a subset of tests and displays the results in a user-friendly way.
Ideal for presentations and demonstrations.
"""

import os
import sys
import json
import logging
import subprocess
import time
import argparse
from datetime import datetime
import webbrowser
import shutil
import threading
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("demo_tests")

# Demo test cases
DEMO_TESTS = [
    {
        "name": "Factual Accuracy Test",
        "description": "Tests if RAG responses contain expected facts from source documents",
        "command": ["pytest", "-xvs", "tests/test_rag_quality.py::test_factual_accuracy", "-v"],
        "report_file": "test_quality_results.json",
        "expected_duration": 10
    },
    {
        "name": "Multi-Document Retrieval Test",
        "description": "Tests retrieval across multiple documents",
        "command": ["pytest", "-xvs", "tests/test_rag_quality.py::test_multi_document_retrieval", "-v"],
        "report_file": "test_multi_doc_results.json",
        "expected_duration": 8
    },
    {
        "name": "File Type Support Test",
        "description": "Tests processing of different file types",
        "command": ["pytest", "-xvs", "tests/test_file_handling.py::test_file_type_support", "-v"],
        "report_file": "test_file_type_results.json",
        "expected_duration": 12
    },
    {
        "name": "Query Response Time Test",
        "description": "Measures response time for different query types",
        "command": ["pytest", "-xvs", "tests/test_performance.py::test_query_response_time", "-v"],
        "report_file": "test_response_time_results.json",
        "expected_duration": 15
    },
    {
        "name": "Special Characters Query Test",
        "description": "Tests queries with special characters, SQL injection, XSS, etc.",
        "command": ["pytest", "-xvs", "tests/test_edge_cases.py::test_special_characters_query", "-v"],
        "report_file": "test_special_queries_results.json",
        "expected_duration": 10
    }
]

def print_header(text):
    """Print a header with decoration"""
    width = 80
    print("\n" + "=" * width)
    print(f"{text.center(width)}")
    print("=" * width + "\n")

def print_test_info(test):
    """Print test information"""
    print(f"🧪 Test: {test['name']}")
    print(f"📝 Description: {test['description']}")
    print(f"⏱️  Expected Duration: {test['expected_duration']} seconds\n")

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Print a progress bar"""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()

def animate_progress(duration, stop_event):
    """Animate a progress bar for the given duration"""
    steps = 100
    for i in range(steps + 1):
        if stop_event.is_set():
            # Fill the progress bar completely when done
            print_progress_bar(steps, steps, prefix='Progress:', suffix='Complete', length=50)
            break
        print_progress_bar(i, steps, prefix='Progress:', suffix='Running...', length=50)
        time.sleep(duration / steps)

def run_test(test):
    """Run a test and display progress"""
    print_test_info(test)
    
    # Create a stop event for the animation thread
    stop_event = threading.Event()
    
    # Start the animation in a separate thread
    animation_thread = threading.Thread(target=animate_progress, args=(test["expected_duration"], stop_event))
    animation_thread.start()
    
    # Run the test
    start_time = time.time()
    result = subprocess.run(test["command"], capture_output=True, text=True)
    end_time = time.time()
    
    # Stop the animation
    stop_event.set()
    animation_thread.join()
    
    # Print the result
    actual_duration = end_time - start_time
    print(f"\n⏱️  Actual Duration: {actual_duration:.2f} seconds")
    
    if result.returncode == 0:
        print("✅ Test PASSED\n")
    else:
        print("❌ Test FAILED\n")
        print("Error details:")
        print(result.stderr)
    
    # Check if report file exists
    if os.path.exists(test["report_file"]):
        print(f"📊 Report generated: {test['report_file']}")
        try:
            with open(test["report_file"], "r") as f:
                report_data = json.load(f)
                print(f"📈 Report contains {len(report_data) if isinstance(report_data, list) else 'structured'} data points")
        except json.JSONDecodeError:
            print("⚠️  Report file is not valid JSON")
    else:
        print("⚠️  No report file generated")
    
    print("\n" + "-" * 80 + "\n")
    
    return {
        "name": test["name"],
        "success": result.returncode == 0,
        "duration_seconds": actual_duration,
        "report_file": test["report_file"] if os.path.exists(test["report_file"]) else None
    }

def generate_summary(results):
    """Generate a summary of test results"""
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    total_duration = sum(r["duration_seconds"] for r in results)
    
    print_header("TEST SUMMARY")
    print(f"Total Tests: {total_count}")
    print(f"Passed: {success_count}")
    print(f"Failed: {total_count - success_count}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Duration: {total_duration:.2f} seconds")
    
    # Print individual test results
    print("\nTest Results:")
    for i, result in enumerate(results):
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{i+1}. {result['name']}: {status} ({result['duration_seconds']:.2f}s)")
    
    # Print report files
    print("\nReport Files:")
    for result in results:
        if result["report_file"]:
            print(f"- {result['report_file']}")
    
    return {
        "success_count": success_count,
        "total_count": total_count,
        "success_rate": success_rate,
        "total_duration": total_duration
    }

def open_reports():
    """Open HTML reports in the browser"""
    report_files = [
        "performance_benchmark_report.html",
        "edge_case_test_report.html",
        "metis_rag_test_report.html"
    ]
    
    for file in report_files:
        if os.path.exists(file):
            print(f"Opening {file} in browser...")
            webbrowser.open(f"file://{os.path.abspath(file)}")
            time.sleep(1)  # Delay to prevent browser from being overwhelmed

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run Metis RAG demo tests")
    parser.add_argument("--test", type=int, help="Run a specific test (1-5)")
    parser.add_argument("--open-reports", action="store_true", help="Open HTML reports in browser")
    parser.add_argument("--random", action="store_true", help="Run tests in random order")
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    
    print_header("METIS RAG TESTING DEMONSTRATION")
    print("This demonstration will run a subset of tests to showcase the testing framework.")
    print("Each test will display progress and results, and generate a report file.")
    print("At the end, a summary of all test results will be displayed.")
    
    # Select tests to run
    tests_to_run = DEMO_TESTS
    if args.test:
        if 1 <= args.test <= len(DEMO_TESTS):
            tests_to_run = [DEMO_TESTS[args.test - 1]]
        else:
            print(f"Error: Test number must be between 1 and {len(DEMO_TESTS)}")
            return 1
    
    # Randomize test order if requested
    if args.random:
        random.shuffle(tests_to_run)
    
    # Run tests
    results = []
    for test in tests_to_run:
        result = run_test(test)
        results.append(result)
    
    # Generate summary
    summary = generate_summary(results)
    
    # Open reports if requested
    if args.open_reports:
        open_reports()
    
    return 0 if summary["success_count"] == summary["total_count"] else 1

if __name__ == "__main__":
    sys.exit(main())