#!/bin/bash
# Script to backup original test files that have duplicates in the structured directories

# Get the tests directory
TESTS_DIR="/Users/charleshoward/Metis_RAG/tests"
BACKUP_DIR="$TESTS_DIR/legacy_originals"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "Backing up original test files with duplicates..."
files_backed_up=0

# Find all test files at the root level
for file in $(find $TESTS_DIR -maxdepth 1 -name "test_*.py"); do
  filename=$(basename $file)
  
  # Check if this file exists elsewhere in the directory structure
  duplicates=$(find $TESTS_DIR -path "$TESTS_DIR/$filename" -prune -o -name "$filename" -print)
  
  if [ -n "$duplicates" ]; then
    # Move the original file to the backup directory
    echo "Moving $filename to backup directory..."
    mv "$file" "$BACKUP_DIR/"
    files_backed_up=$((files_backed_up + 1))
  fi
done

echo -e "\nBackup complete. Moved $files_backed_up files to $BACKUP_DIR."

# Count tests at different levels after backup
echo "Test file counts by directory after backup:"
echo "  Root level: $(find $TESTS_DIR -maxdepth 1 -name 'test_*.py' | wc -l)"
echo "  Unit tests: $(find $TESTS_DIR/unit -name 'test_*.py' | wc -l)"
echo "  Integration tests: $(find $TESTS_DIR/integration -name 'test_*.py' | wc -l)"
echo "  E2E tests: $(find $TESTS_DIR/e2e -name 'test_*.py' | wc -l)"
echo "  Legacy tests: $(find $TESTS_DIR/legacy -name 'test_*.py' | wc -l)"
echo "  Backed up originals: $(find $TESTS_DIR/legacy_originals -name 'test_*.py' | wc -l)"

echo "Done!"