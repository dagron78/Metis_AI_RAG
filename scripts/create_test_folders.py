#!/usr/bin/env python3
"""
Create test folders in the database
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.session import SessionLocal
from app.db.repositories.document_repository import DocumentRepository
from app.db.models import Folder

def create_test_folders():
    """Create test folders in the database"""
    # Create database session
    db_session = SessionLocal()
    
    try:
        # Create document repository
        document_repository = DocumentRepository(db_session)
        
        # Create root folder if it doesn't exist
        root_folder = db_session.query(Folder).filter(Folder.path == "/").first()
        if not root_folder:
            root_folder = Folder(path="/", name="Root", parent_path=None)
            db_session.add(root_folder)
            db_session.commit()
            print("Created root folder '/'")
        else:
            print("Root folder '/' already exists")
        
        # Create test folder if it doesn't exist (without trailing slash)
        test_folder = db_session.query(Folder).filter(Folder.path == "/test").first()
        if not test_folder:
            test_folder = Folder(
                path="/test",  # No trailing slash
                name="test",
                parent_path="/",
                document_count=0
            )
            db_session.add(test_folder)
            db_session.commit()
            print("Created test folder '/test'")
        else:
            print("Test folder '/test' already exists")
        
        return 0
    except Exception as e:
        print(f"Error creating test folders: {e}")
        return 1
    finally:
        db_session.close()

if __name__ == "__main__":
    sys.exit(create_test_folders())