#!/bin/bash

# Script to run the query refinement test and verify the fixes

# Set the working directory to the project root
cd "$(dirname "$0")/.."

# Print header
echo "====================================================="
echo "  Metis RAG Query Refinement Fix Test"
echo "====================================================="
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Check if the virtual environment exists
if [ -d "venv_py310" ]; then
    echo "Activating virtual environment..."
    source venv_py310/bin/activate
else
    echo "Warning: Virtual environment not found. Using system Python."
fi

# Check if the test file exists
if [ ! -f "tests/test_query_refinement_fix.py" ]; then
    echo "Error: Test file not found: tests/test_query_refinement_fix.py"
    exit 1
fi

# Run the test
echo "Running query refinement test..."
echo
python3 tests/test_query_refinement_fix.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo
    echo "Test completed successfully!"
    echo
    echo "For more information about the fixes, see:"
    echo "docs/technical/query_refinement_fix.md"
else
    echo
    echo "Test failed. Please check the output for errors."
fi

echo
echo "====================================================="