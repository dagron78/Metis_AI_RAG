#!/bin/bash
# Script to check for duplicate test files between root and structured directories

# Get the tests directory
TESTS_DIR="/Users/charleshoward/Metis_RAG/tests"

# Find all test files at the root level
echo "Checking for duplicate test files..."
for file in $(find $TESTS_DIR -maxdepth 1 -name "test_*.py"); do
  filename=$(basename $file)
  
  # Check if this file exists elsewhere in the directory structure
  duplicates=$(find $TESTS_DIR -path "$TESTS_DIR/$filename" -prune -o -name "$filename" -print)
  
  if [ -n "$duplicates" ]; then
    echo "Found duplicate for $filename:"
    echo "  Original: $file"
    echo "  Duplicates:"
    for dup in $duplicates; do
      echo "    - $dup"
    done
    echo ""
  fi
done

# Count tests at different levels
echo "Test file counts by directory:"
echo "  Root level: $(find $TESTS_DIR -maxdepth 1 -name 'test_*.py' | wc -l)"
echo "  Unit tests: $(find $TESTS_DIR/unit -name 'test_*.py' | wc -l)"
echo "  Integration tests: $(find $TESTS_DIR/integration -name 'test_*.py' | wc -l)"
echo "  E2E tests: $(find $TESTS_DIR/e2e -name 'test_*.py' | wc -l)"
echo "  Legacy tests: $(find $TESTS_DIR/legacy -name 'test_*.py' | wc -l)"

echo "Done!"