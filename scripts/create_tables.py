#!/usr/bin/env python3
"""
Create database tables directly using SQLAlchemy
"""
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import Base, engine
from app.db.models import Document, Chunk, Tag, Folder, Conversation, Message, Citation, ProcessingJob, AnalyticsQuery, BackgroundTask

def create_tables():
    """
    Create database tables
    """
    print("Creating database tables...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(create_tables())