#!/bin/bash
# Script to run the Retrieval Judge tests and analysis

echo "===== Metis RAG Retrieval Judge Test Suite ====="
echo ""

# Set the base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR/../.."

echo "Step 1: Running comparison tests..."
python -m tests.retrieval_judge.test_retrieval_judge_comparison
if [ $? -ne 0 ]; then
    echo "Error: Comparison tests failed."
    exit 1
fi

echo ""
echo "Step 2: Running analysis..."
python -m tests.retrieval_judge.analyze_retrieval_judge_results
if [ $? -ne 0 ]; then
    echo "Error: Analysis failed."
    exit 1
fi

echo ""
echo "===== Test Suite Completed Successfully ====="
echo "Results are available in: tests/retrieval_judge/results/"
echo "Visualizations are available in: tests/retrieval_judge/visualizations/"