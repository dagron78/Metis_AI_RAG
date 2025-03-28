#!/usr/bin/env python3
"""
Run SQL script to grant permissions to the postgres user
"""
import os
import sys
import subprocess

def run_grant_permissions():
    """
    Run SQL script to grant permissions
    """
    print("Running SQL script to grant permissions to the postgres user...")
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Change to the project root directory
    os.chdir(project_root)
    
    # Path to the SQL script
    sql_script_path = os.path.join(project_root, "scripts", "grant_permissions.sql")
    
    # Run psql command
    try:
        # Note: This should be run as the charleshoward user who owns the tables
        result = subprocess.run(
            ["psql", "-d", "metis_rag", "-f", sql_script_path],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("Permissions granted successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running SQL script: {e}")
        print(e.stdout)
        print(e.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(run_grant_permissions())