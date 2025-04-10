#!/bin/bash
# Script to run the most important Metis RAG tests in a logical order

# Set script to exit on error
set -e

# Display help message
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  echo "Usage: ./run_important_tests.sh [options]"
  echo ""
  echo "Options:"
  echo "  -h, --help     Show this help message"
  echo "  -s, --section  Run only a specific section (1-5)"
  echo "  -v, --verbose  Show more detailed output"
  echo ""
  echo "Examples:"
  echo "  ./run_important_tests.sh              # Run all tests"
  echo "  ./run_important_tests.sh -s 1         # Run only core component tests (section 1)"
  echo "  ./run_important_tests.sh -v           # Run all tests with verbose output"
  exit 0
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate the virtual environment
echo "Activating Python virtual environment..."
source "$PROJECT_ROOT/venv_py310/bin/activate"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not available. Make sure the virtual environment is properly set up."
    exit 1
fi

# Run the Python test script with any provided arguments
echo "Running Metis RAG tests in logical order..."
python "$SCRIPT_DIR/run_important_tests.py" "$@"

# Store the exit code
EXIT_CODE=$?

# Display completion message
if [ $EXIT_CODE -eq 0 ]; then
    echo "All tests completed successfully!"
else
    echo "Some tests failed. Check the log file for details."
fi

# Exit with the same code as the Python script
exit $EXIT_CODE