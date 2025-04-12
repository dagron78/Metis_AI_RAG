import asyncio
import sys
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("process_pending_documents")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import AsyncSessionLocal
from app.db.models import Document
from sqlalchemy import select, update
from app.rag.document_processor import DocumentProcessor
from app.rag.vector_store import VectorStore

async def process_pending_documents():
    """Process documents that are stuck in 'pending' or 'processing' status"""
    logger.info("Looking for documents to process...")
    
    try:
        # Create a session
        async with AsyncSessionLocal() as session:
            # Query documents in pending or processing status
            result = await session.execute(
                select(Document).where(
                    Document.processing_status.in_(["pending", "processing"])
                )
            )
            documents = result.scalars().all()
            
            if not documents:
                logger.info("No pending or processing documents found.")
                return
            
            logger.info(f"Found {len(documents)} documents to process.")
            
            # Create document processor
            document_processor = DocumentProcessor(session=session)
            
            # Process each document
            for document in documents:
                logger.info(f"Processing document: {document.id} - {document.filename}")
                
                try:
                    # Reset status to pending
                    document.processing_status = "pending"
                    await session.commit()
                    
                    # Process the document
                    processed_document = await document_processor.process_document(document)
                    
                    logger.info(f"Document processed successfully: {document.id}")
                    
                    # Verify document was added to vector store
                    vector_store = VectorStore()
                    stats = await vector_store.get_statistics()
                    logger.info(f"Vector store statistics after processing: {stats}")
                    
                except Exception as e:
                    logger.error(f"Error processing document {document.id}: {str(e)}")
                    # Update status to failed
                    document.processing_status = "failed"
                    await session.commit()
    
    except Exception as e:
        logger.error(f"Error in process_pending_documents: {str(e)}")

if __name__ == "__main__":
    asyncio.run(process_pending_documents())