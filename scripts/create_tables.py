#!/usr/bin/env python3
"""
Create database tables directly using SQLAlchemy
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import Base, engine
from app.db.models import Document, Chunk, Tag, Folder, Conversation, Message, Citation, ProcessingJob, AnalyticsQuery, BackgroundTask
from app.models.memory import Memory

async def create_tables():
    """
    Create database tables
    """
    print("Creating database tables...")
    
    # Create tables using async engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(create_tables()))