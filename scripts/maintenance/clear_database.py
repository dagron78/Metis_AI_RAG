#!/usr/bin/env python3
"""
Script to clear the Metis RAG database and start fresh.
This script will:
1. Delete the ChromaDB directory
2. Delete the uploads directory (optional)
"""

import os
import shutil
import argparse
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Default paths
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
UPLOAD_DIR = BASE_DIR / "uploads"

def clear_database(clear_uploads=False):
    """Clear the database and optionally the uploads directory"""
    print(f"Clearing ChromaDB directory: {CHROMA_DB_DIR}")
    
    if os.path.exists(CHROMA_DB_DIR):
        try:
            shutil.rmtree(CHROMA_DB_DIR)
            print("✅ ChromaDB directory deleted successfully")
        except Exception as e:
            print(f"❌ Error deleting ChromaDB directory: {str(e)}")
            print("   Make sure the application is not running")
            return False
    else:
        print("ℹ️ ChromaDB directory does not exist, nothing to delete")
    
    # Recreate the directory
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    print("✅ Created fresh ChromaDB directory")
    
    if clear_uploads:
        print(f"Clearing uploads directory: {UPLOAD_DIR}")
        if os.path.exists(UPLOAD_DIR):
            try:
                # Delete all contents but keep the directory
                for item in os.listdir(UPLOAD_DIR):
                    item_path = os.path.join(UPLOAD_DIR, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                print("✅ Uploads directory cleared successfully")
            except Exception as e:
                print(f"❌ Error clearing uploads directory: {str(e)}")
                return False
        else:
            print("ℹ️ Uploads directory does not exist, nothing to delete")
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            print("✅ Created fresh uploads directory")
    
    print("\n✅ Database cleared successfully!")
    print("\nYou can now restart the application with a fresh database.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clear the Metis RAG database and start fresh")
    parser.add_argument("--clear-uploads", action="store_true", help="Also clear the uploads directory")
    args = parser.parse_args()
    
    clear_database(args.clear_uploads)