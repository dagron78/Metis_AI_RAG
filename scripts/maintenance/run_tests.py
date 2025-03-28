#!/usr/bin/env python3
"""
Test runner for Metis RAG testing strategy.
This script executes all test suites and generates a comprehensive report.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_runner")

# Test suites
TEST_SUITES = [
    {
        "name": "RAG Quality Tests",
        "module": "tests.test_rag_quality",
        "description": "Tests for factual accuracy, relevance, and citation quality",
        "report_files": [
            "test_quality_results.json",
            "test_multi_doc_results.json",
            "test_citation_results.json",
            "test_api_integration_results.json"
        ]
    },
    {
        "name": "File Handling Tests",
        "module": "tests.test_file_handling",
        "description": "Tests for different file types, multiple file uploads, and large files",
        "report_files": [
            "test_file_type_results.json",
            "test_chunking_strategy_results.json",
            "test_large_file_results.json",
            "test_api_upload_results.json",
            "test_multiple_upload_results.json"
        ]
    },
    {
        "name": "Performance Tests",
        "module": "tests.test_performance",
        "description": "Tests for response time, throughput, and resource utilization",
        "report_files": [
            "test_response_time_results.json",
            "test_throughput_results.json",
            "test_resource_utilization_results.json",
            "test_api_performance_results.json",
            "performance_benchmark_report.json",
            "performance_benchmark_report.html"
        ]
    },
    {
        "name": "Edge Case Tests",
        "module": "tests.test_edge_cases",
        "description": "Tests for unusual inputs, error handling, and system resilience",
        "report_files": [
            "test_special_queries_results.json",
            "test_concurrent_processing_results.json",
            "test_invalid_files_results.json",
            "test_malformed_requests_results.json",
            "test_vector_store_resilience_results.json",
            "edge_case_test_report.json",
            "edge_case_test_report.html"
        ]
    }
]

def run_test_suite(suite, args):
    """Run a test suite using pytest"""
    logger.info(f"Running {suite['name']}...")
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", "-xvs"]
    
    # Add specific test options
    if args.failfast:
        cmd.append("-xvs")
    
    # Add the module to test
    cmd.append(suite["module"])
    
    # Run the command
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    # Log the result
    if result.returncode == 0:
        logger.info(f"{suite['name']} completed successfully in {end_time - start_time:.2f} seconds")
    else:
        logger.error(f"{suite['name']} failed with return code {result.returncode}")
        logger.error(f"STDOUT: {result.stdout}")
        logger.error(f"STDERR: {result.stderr}")
    
    return {
        "name": suite["name"],
        "success": result.returncode == 0,
        "duration_seconds": end_time - start_time,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": result.returncode
    }

def collect_reports(suite):
    """Collect report files for a test suite"""
    reports = {}
    
    for report_file in suite["report_files"]:
        if os.path.exists(report_file):
            try:
                with open(report_file, "r") as f:
                    reports[report_file] = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse {report_file} as JSON")
                with open(report_file, "r") as f:
                    reports[report_file] = f.read()
        else:
            logger.warning(f"Report file {report_file} not found")
    
    return reports

def generate_master_report(results, args):
    """Generate a master report from all test results"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_suites": results
    }
    
    # Save report
    report_path = "metis_rag_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Master report saved to {os.path.abspath(report_path)}")
    
    # Generate HTML report
    html_report = generate_html_report(report)
    html_report_path = "metis_rag_test_report.html"
    
    with open(html_report_path, "w") as f:
        f.write(html_report)
    
    logger.info(f"HTML report saved to {os.path.abspath(html_report_path)}")
    
    # Open the report in a browser if requested
    if args.open_report:
        webbrowser.open(f"file://{os.path.abspath(html_report_path)}")
    
    return report_path, html_report_path

def generate_html_report(report):
    """Generate an HTML report from the test results"""
    # Count successful test suites
    success_count = sum(1 for suite in report["test_suites"] if suite["result"]["success"])
    total_count = len(report["test_suites"])
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    # Calculate total duration
    total_duration = sum(suite["result"]["duration_seconds"] for suite in report["test_suites"])
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Metis RAG Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .section {{ margin-bottom: 30px; }}
        .summary {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
        .summary-box {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; width: 30%; text-align: center; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .details {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 10px; }}
        .details pre {{ white-space: pre-wrap; overflow-x: auto; }}
        .toggle-btn {{ background-color: #4CAF50; color: white; padding: 5px 10px; border: none; border-radius: 3px; cursor: pointer; }}
        .toggle-btn:hover {{ background-color: #45a049; }}
    </style>
    <script>
        function toggleDetails(id) {{
            var details = document.getElementById(id);
            if (details.style.display === "none") {{
                details.style.display = "block";
            }} else {{
                details.style.display = "none";
            }}
        }}
    </script>
</head>
<body>
    <h1>Metis RAG Test Report</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <div class="summary-box">
            <h3>Test Suites</h3>
            <p class="{('success' if success_rate == 100 else 'failure')}">{success_count}/{total_count} ({success_rate:.1f}%)</p>
        </div>
        <div class="summary-box">
            <h3>Total Duration</h3>
            <p>{total_duration:.2f} seconds</p>
        </div>
        <div class="summary-box">
            <h3>Timestamp</h3>
            <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Test Suite Results</h2>
        <table>
            <tr>
                <th>Test Suite</th>
                <th>Description</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Details</th>
            </tr>
            {"".join([f'''
            <tr>
                <td>{suite["name"]}</td>
                <td>{suite["description"]}</td>
                <td class="{'success' if suite['result']['success'] else 'failure'}">{('Success' if suite['result']['success'] else 'Failure')}</td>
                <td>{suite["result"]["duration_seconds"]:.2f} seconds</td>
                <td><button class="toggle-btn" onclick="toggleDetails('details-{i}')">Toggle Details</button></td>
            </tr>
            <tr>
                <td colspan="5">
                    <div id="details-{i}" class="details" style="display: none;">
                        <h4>Output:</h4>
                        <pre>{suite["result"]["stdout"]}</pre>
                        <h4>Error Output:</h4>
                        <pre>{suite["result"]["stderr"]}</pre>
                        <h4>Reports:</h4>
                        <ul>
                            {"".join([f'<li><a href="{report_file}">{report_file}</a></li>' for report_file in suite["reports"].keys()])}
                        </ul>
                    </div>
                </td>
            </tr>
            ''' for i, suite in enumerate(report["test_suites"])])}
        </table>
    </div>
    
    <div class="section">
        <h2>Individual Test Reports</h2>
        <p>The following reports were generated by the test suites:</p>
        <ul>
            {"".join([f'<li><a href="{report_file}">{report_file}</a></li>' for suite in report["test_suites"] for report_file in suite["reports"].keys()])}
        </ul>
    </div>
    
    <div class="section">
        <h2>Specific Report Links</h2>
        <h3>Performance Report</h3>
        <p><a href="performance_benchmark_report.html">Performance Benchmark Report</a></p>
        
        <h3>Edge Case Report</h3>
        <p><a href="edge_case_test_report.html">Edge Case Test Report</a></p>
    </div>
</body>
</html>
"""
    
    return html

def create_reports_directory():
    """Create a directory for test reports"""
    reports_dir = "test_reports"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = f"{reports_dir}_{timestamp}"
    
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def copy_reports_to_directory(reports_dir):
    """Copy all report files to the reports directory"""
    report_files = []
    for suite in TEST_SUITES:
        report_files.extend(suite["report_files"])
    
    report_files.extend(["metis_rag_test_report.json", "metis_rag_test_report.html"])
    
    for file in report_files:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(reports_dir, file))
            logger.info(f"Copied {file} to {reports_dir}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run Metis RAG tests")
    parser.add_argument("--suite", type=str, help="Run a specific test suite (rag_quality, file_handling, performance, edge_cases)")
    parser.add_argument("--failfast", action="store_true", help="Stop on first failure")
    parser.add_argument("--open-report", action="store_true", help="Open the HTML report in a browser")
    parser.add_argument("--save-reports", action="store_true", help="Save reports to a timestamped directory")
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    
    # Run tests
    results = []
    
    # Filter test suites if a specific one is requested
    suites_to_run = TEST_SUITES
    if args.suite:
        suite_map = {
            "rag_quality": "RAG Quality Tests",
            "file_handling": "File Handling Tests",
            "performance": "Performance Tests",
            "edge_cases": "Edge Case Tests"
        }
        if args.suite in suite_map:
            suite_name = suite_map[args.suite]
            suites_to_run = [suite for suite in TEST_SUITES if suite["name"] == suite_name]
            if not suites_to_run:
                logger.error(f"Test suite {args.suite} not found")
                return 1
        else:
            logger.error(f"Unknown test suite: {args.suite}")
            logger.info(f"Available suites: {', '.join(suite_map.keys())}")
            return 1
    
    # Run each test suite
    for suite in suites_to_run:
        # Run the test suite
        result = run_test_suite(suite, args)
        
        # Collect reports
        reports = collect_reports(suite)
        
        # Store results
        results.append({
            "name": suite["name"],
            "description": suite["description"],
            "result": result,
            "reports": reports
        })
        
        # Stop on first failure if requested
        if args.failfast and not result["success"]:
            logger.error(f"Stopping due to failure in {suite['name']}")
            break
    
    # Generate master report
    report_path, html_report_path = generate_master_report(results, args)
    
    # Save reports to a directory if requested
    if args.save_reports:
        reports_dir = create_reports_directory()
        copy_reports_to_directory(reports_dir)
        logger.info(f"Reports saved to {reports_dir}")
    
    # Return success if all test suites passed
    return 0 if all(suite["result"]["success"] for suite in results) else 1

if __name__ == "__main__":
    sys.exit(main())