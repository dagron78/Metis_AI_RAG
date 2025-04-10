#!/usr/bin/env python3
"""
Script to move test files from the root directory to their appropriate locations
in the test directory structure.
"""
import os
import sys
import shutil
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Define mappings for where tests should go
TEST_MAPPINGS = {
    # API-related tests
    "test_chat_api.py": "unit/api/",
    
    # Authentication-related tests
    "test_auth_simple.py": "unit/middleware/",
    "test_authentication.py": "unit/middleware/",
    
    # Database-related tests
    "test_db_connection.py": "unit/db/",
    "test_db_connection_simple.py": "unit/db/",
    "test_db_simple.py": "unit/db/",
    "test_document_repository.py": "unit/db/repositories/",
    
    # Document processing tests
    "test_document_processing_performance.py": "e2e/document_processing/",
    "test_document_upload.py": "unit/api/",
    
    # RAG-related tests
    "test_chunking_judge_phase1.py": "unit/rag/",
    "test_chunking_judge_real.py": "integration/rag_api/",
    "test_entity_preservation.py": "unit/rag/",
    
    # E2E tests
    "test_metis_rag_e2e.py": "e2e/chat/",
    "test_metis_rag_e2e_demo.py": "e2e/chat/",
    
    # Task and document processing tests
    "test_background_tasks.py": "unit/tasks/",
    "test_simplified_document_processing.py": "unit/tasks/",
    "test_simplified_document_processing_with_db.py": "integration/tasks_db/",
    "test_simplified_performance.py": "unit/rag/engine/performance/",
    
    # Utility and formatting tests
    "test_code_formatting.py": "unit/utils/",
    "test_file_handling.py": "unit/utils/",
    "test_structured_code_output.py": "unit/utils/",
}

def move_test_file(file_name, source_dir, target_subdir):
    """Move a test file to its target directory."""
    source_path = os.path.join(source_dir, file_name)
    target_dir = os.path.join(source_dir, target_subdir)
    target_path = os.path.join(target_dir, file_name)
    
    # Check if the source file exists
    if not os.path.exists(source_path):
        print(f"  - Source file {source_path} does not exist, skipping")
        return False
    
    # Check if the target directory exists
    if not os.path.exists(target_dir):
        print(f"  - Creating target directory {target_dir}")
        os.makedirs(target_dir, exist_ok=True)
    
    # Check if the target file already exists
    if os.path.exists(target_path):
        print(f"  - Target file {target_path} already exists, skipping")
        return False
    
    # Move the file
    try:
        shutil.move(source_path, target_path)
        print(f"  ✓ Moved {file_name} to {target_subdir}")
        return True
    except Exception as e:
        print(f"  ! Error moving {file_name}: {str(e)}")
        return False

def main():
    """Main function."""
    # Get the tests directory
    tests_dir = os.path.join(project_root, 'tests')
    
    # Count statistics
    total_files = len(TEST_MAPPINGS)
    moved_files = 0
    skipped_files = 0
    
    print(f"Moving {total_files} test files to their appropriate directories...\n")
    
    # Process each mapping
    for file_name, target_subdir in TEST_MAPPINGS.items():
        print(f"Processing {file_name}...")
        if move_test_file(file_name, tests_dir, target_subdir):
            moved_files += 1
        else:
            skipped_files += 1
    
    # Print summary
    print(f"\nMoved {moved_files} files, skipped {skipped_files} files.")
    print(f"Total files processed: {moved_files + skipped_files} out of {total_files}.")

if __name__ == "__main__":
    main()