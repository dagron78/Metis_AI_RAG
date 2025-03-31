#!/usr/bin/env python
"""
Migration script to transition from the old synchronous DatabaseTool to the new async version.

This script:
1. Renames the old DatabaseTool to DatabaseToolLegacy
2. Renames the new DatabaseToolAsync to DatabaseTool
3. Updates imports in the codebase

Usage:
    python scripts/migrate_to_async_database_tool.py

"""
import os
import re
import shutil
from pathlib import Path

def main():
    """Main migration function"""
    print("Starting migration to async DatabaseTool...")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Step 1: Rename the old DatabaseTool to DatabaseToolLegacy
    old_tool_path = project_root / "app" / "rag" / "tools" / "database_tool.py"
    legacy_tool_path = project_root / "app" / "rag" / "tools" / "database_tool_legacy.py"
    
    if old_tool_path.exists():
        print(f"Renaming {old_tool_path} to {legacy_tool_path}")
        
        # Read the old file
        with open(old_tool_path, "r") as f:
            content = f.read()
        
        # Update class name
        content = content.replace("class DatabaseTool(Tool):", "class DatabaseToolLegacy(Tool):")
        
        # Write to legacy file
        with open(legacy_tool_path, "w") as f:
            f.write(content)
        
        print(f"Created legacy version at {legacy_tool_path}")
    else:
        print(f"Warning: Old tool file {old_tool_path} not found")
    
    # Step 2: Rename the new DatabaseToolAsync to DatabaseTool
    new_tool_path = project_root / "app" / "rag" / "tools" / "database_tool_async.py"
    
    if new_tool_path.exists():
        print(f"Renaming {new_tool_path} to {old_tool_path}")
        
        # Read the new file
        with open(new_tool_path, "r") as f:
            content = f.read()
        
        # Write to the original location
        with open(old_tool_path, "w") as f:
            f.write(content)
        
        print(f"Installed new async version at {old_tool_path}")
    else:
        print(f"Error: New tool file {new_tool_path} not found")
        return
    
    # Step 3: Update imports in the codebase
    print("Updating imports in the codebase...")
    
    # Directories to search for imports
    dirs_to_search = [
        project_root / "app",
        project_root / "tests"
    ]
    
    # Files to exclude
    exclude_files = [
        str(legacy_tool_path),
        str(old_tool_path)
    ]
    
    # Patterns to search for
    import_patterns = [
        (r"from app\.rag\.tools\.database_tool import DatabaseTool", 
         "from app.rag.tools.database_tool import DatabaseTool  # Async version"),
        (r"from app\.rag\.tools import database_tool", 
         "from app.rag.tools import database_tool  # Contains async DatabaseTool")
    ]
    
    # Counter for modified files
    modified_files = 0
    
    # Walk through directories
    for directory in dirs_to_search:
        for root, _, files in os.walk(directory):
            for file in files:
                if not file.endswith(".py"):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Skip excluded files
                if file_path in exclude_files:
                    continue
                
                # Read file content
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Check if any pattern matches
                original_content = content
                for pattern, replacement in import_patterns:
                    content = re.sub(pattern, replacement, content)
                
                # If content changed, write back to file
                if content != original_content:
                    with open(file_path, "w") as f:
                        f.write(content)
                    print(f"Updated imports in {file_path}")
                    modified_files += 1
    
    print(f"Updated imports in {modified_files} files")
    
    # Step 4: Create a backup of the original file
    backup_dir = project_root / "backups" / "database_tool"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_path = backup_dir / "database_tool_original.py"
    if legacy_tool_path.exists():
        print(f"Creating backup at {backup_path}")
        shutil.copy2(legacy_tool_path, backup_path)
    
    print("\nMigration completed successfully!")
    print("\nNext steps:")
    print("1. Run tests to ensure everything works correctly:")
    print("   pytest tests/unit/test_database_tool_async.py")
    print("2. Update your code to use the new async features if needed")
    print("3. If you encounter any issues, the original implementation is available at:")
    print(f"   {legacy_tool_path}")
    print("   and a backup is stored at:")
    print(f"   {backup_path}")

if __name__ == "__main__":
    main()