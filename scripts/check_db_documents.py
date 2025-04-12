import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import AsyncSessionLocal
from app.db.models import Document
from sqlalchemy import select

async def check_db_documents():
    """Check documents in the database and their processing status"""
    print("Checking documents in the database...")
    
    try:
        # Create a session directly using AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            # Query all documents
            result = await session.execute(select(Document.id, Document.filename, Document.processing_status))
            documents = result.all()
            
            print(f"Found {len(documents)} documents in the database:")
            
            if documents:
                for doc in documents:
                    print(f"ID: {doc[0]}, Filename: {doc[1]}, Status: {doc[2]}")
                
                # Count documents by status
                pending = sum(1 for doc in documents if doc[2] == "pending")
                processing = sum(1 for doc in documents if doc[2] == "processing")
                completed = sum(1 for doc in documents if doc[2] == "completed")
                failed = sum(1 for doc in documents if doc[2] == "failed")
                
                print(f"\nStatus summary:")
                print(f"  Pending: {pending}")
                print(f"  Processing: {processing}")
                print(f"  Completed: {completed}")
                print(f"  Failed: {failed}")
                
                if pending > 0 or processing > 0:
                    print("\nYou have documents that haven't been fully processed yet.")
                    print("This could be why your RAG system isn't referencing any documents.")
            else:
                print("No documents found in the database.")
    except Exception as e:
        print(f"Error checking documents: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_db_documents())