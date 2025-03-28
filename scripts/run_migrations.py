#!/usr/bin/env python3
"""
Run Alembic migrations for the Background Task System
"""
import os
import sys
import subprocess

def run_migration():
    """
    Run Alembic migrations
    """
    print("Running Alembic migrations for the Background Task System...")
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Change to the project root directory
    os.chdir(project_root)
    
    # Run Alembic upgrade
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "heads"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("Migration completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running migration: {e}")
        print(e.stdout)
        print(e.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(run_migration())