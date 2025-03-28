#!/usr/bin/env python3
"""
Python script to run the Retrieval Judge tests and analysis
"""

import os
import sys
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("run_tests")

def run_command(command, description):
    """Run a command and log the output"""
    logger.info(f"Running: {description}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        logger.info(f"Command completed in {time.time() - start_time:.2f} seconds")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.warning(result.stderr)
            
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False

def main():
    """Main function to run the tests"""
    logger.info("===== Metis RAG Retrieval Judge Test Suite =====")
    
    # Get the base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    
    # Run the comparison tests
    logger.info("Step 1: Running comparison tests...")
    if not run_command(
        [sys.executable, "-m", "tests.retrieval_judge.test_retrieval_judge_comparison"],
        "Comparison tests"
    ):
        logger.error("Comparison tests failed. Exiting.")
        return 1
    
    # Run the analysis
    logger.info("Step 2: Running analysis...")
    if not run_command(
        [sys.executable, "-m", "tests.retrieval_judge.analyze_retrieval_judge_results"],
        "Analysis"
    ):
        logger.error("Analysis failed. Exiting.")
        return 1
    
    logger.info("===== Test Suite Completed Successfully =====")
    logger.info("Results are available in: tests/retrieval_judge/results/")
    logger.info("Visualizations are available in: tests/retrieval_judge/visualizations/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())