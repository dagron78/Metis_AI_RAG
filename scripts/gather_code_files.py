#!/usr/bin/env python3
"""
Script to gather all code files into a single file for analysis.
This is similar to what repomix does but focused only on code files.
"""

import os
import fnmatch
from datetime import datetime

# Configuration
OUTPUT_FILE = "misc/metis_rag_code_only.txt"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# File extensions to include
INCLUDE_EXTENSIONS = ['.py', '.js', '.html', '.css', '.sql', '.mako']

# Directories to include
INCLUDE_DIRS = ['app', 'alembic']

# Patterns to exclude
EXCLUDE_PATTERNS = [
    '*test*.py',
    '*README*',
    '*__pycache__*',
    '.*',
]

def should_exclude(file_path):
    """Check if a file should be excluded based on patterns."""
    file_name = os.path.basename(file_path)
    
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(file_name, pattern):
            return True
    
    return False

def find_files():
    """Find all code files in the specified directories."""
    all_files = []
    
    for root_dir in INCLUDE_DIRS:
        dir_path = os.path.join(PROJECT_ROOT, root_dir)
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext in INCLUDE_EXTENSIONS and not should_exclude(file_path):
                    all_files.append(file_path)
    
    return all_files

def write_output(files):
    """Write all files to the output file."""
    os.makedirs(os.path.dirname(os.path.join(PROJECT_ROOT, OUTPUT_FILE)), exist_ok=True)
    
    with open(os.path.join(PROJECT_ROOT, OUTPUT_FILE), 'w') as out_file:
        # Write header
        out_file.write("This file is a merged representation of the Metis RAG codebase, combined into a single document.\n")
        out_file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        out_file.write("=" * 80 + "\n")
        out_file.write("File Summary\n")
        out_file.write("=" * 80 + "\n\n")
        
        # Write file list
        out_file.write("Files included:\n")
        for file in sorted(files):
            rel_path = os.path.relpath(file, PROJECT_ROOT)
            out_file.write(f"- {rel_path}\n")
        
        out_file.write("\n")
        
        # Write each file's content
        for file in sorted(files):
            rel_path = os.path.relpath(file, PROJECT_ROOT)
            out_file.write("=" * 80 + "\n")
            out_file.write(f"File: {rel_path}\n")
            out_file.write("=" * 80 + "\n")
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    out_file.write(content)
            except UnicodeDecodeError:
                out_file.write("[Binary file or encoding issue - content omitted]\n")
            except Exception as e:
                out_file.write(f"[Error reading file: {str(e)}]\n")
            
            out_file.write("\n\n")
    
    return os.path.join(PROJECT_ROOT, OUTPUT_FILE)

def main():
    """Main function."""
    print("Gathering code files...")
    files = find_files()
    print(f"Found {len(files)} files.")
    
    if files:
        output_path = write_output(files)
        print(f"Output written to {output_path}")
    else:
        print("No files found matching the criteria.")

if __name__ == "__main__":
    main()