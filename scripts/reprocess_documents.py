import asyncio
import sys
import os
import logging
from pathlib import Path
from uuid import UUID

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import get_db
from app.db.repositories.basic_document_repository import BasicDocumentRepository
from app.rag.document_processor import DocumentProcessor
from app.rag.vector_store import VectorStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("reprocess_documents")

async def reprocess_documents():
    """Reprocess all documents to ensure they have the is_public flag set correctly"""
    logger.info("Starting document reprocessing")
    
    # Get database session
    async for session in get_db():
        try:
            # Create document repository
            document_repository = BasicDocumentRepository(session)
            
            # Get all documents
            documents = await document_repository.get_all_documents(limit=1000)
            logger.info(f"Found {len(documents)} documents to reprocess")
            
            # Create document processor
            document_processor = DocumentProcessor(session=session)
            
            # Process each document
            for document in documents:
                try:
                    logger.info(f"Reprocessing document {document.id}: {document.filename}")
                    
                    # Set is_public flag if not already set
                    if not hasattr(document, 'is_public') or document.is_public is None:
                        document.is_public = True
                        logger.info(f"Setting is_public=True for document {document.id}")
                        await session.commit()
                    
                    # Process document
                    await document_processor.process_document(document)
                    
                    logger.info(f"Successfully reprocessed document {document.id}")
                except Exception as e:
                    logger.error(f"Error reprocessing document {document.id}: {str(e)}")
            
            # Get vector store statistics
            vector_store = VectorStore()
            stats = await vector_store.get_statistics()
            logger.info(f"Vector store statistics after reprocessing: {stats}")
            
            logger.info("Document reprocessing completed")
            break  # Exit after processing with the first session
            
        except Exception as e:
            logger.error(f"Error in reprocess_documents: {str(e)}")

if __name__ == "__main__":
    asyncio.run(reprocess_documents())