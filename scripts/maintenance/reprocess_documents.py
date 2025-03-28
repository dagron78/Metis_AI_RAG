#!/usr/bin/env python3
"""
Script to reprocess all documents in the Metis RAG system with updated chunking settings.
This is useful after changing chunking parameters to ensure all documents use the new settings.
"""

import os
import asyncio
import logging
from pathlib import Path

from app.models.document import Document
from app.rag.document_processor import DocumentProcessor
from app.rag.vector_store import VectorStore
from app.core.config import UPLOAD_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("reprocess_documents")

async def reprocess_documents():
    """Reprocess all documents with updated chunking settings"""
    logger.info("Starting document reprocessing")
    
    # Initialize document processor with updated settings
    processor = DocumentProcessor(
        chunking_strategy="recursive"  # This will use the updated chunk size for text files
    )
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Get all document directories in the uploads folder
    upload_path = Path(UPLOAD_DIR)
    if not upload_path.exists():
        logger.error(f"Uploads directory {UPLOAD_DIR} does not exist")
        return
    
    document_dirs = [d for d in upload_path.iterdir() if d.is_dir()]
    logger.info(f"Found {len(document_dirs)} document directories")
    
    # Process each document
    for doc_dir in document_dirs:
        try:
            # Get the document ID from the directory name
            document_id = doc_dir.name
            
            # Find the document file(s) in the directory
            files = list(doc_dir.iterdir())
            if not files:
                logger.warning(f"No files found in document directory {document_id}")
                continue
            
            # Assume the first file is the document (in a real system, you might need to be more sophisticated)
            document_file = files[0]
            
            logger.info(f"Reprocessing document: {document_file.name} (ID: {document_id})")
            
            # Read the file content
            try:
                with open(document_file, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')
            except Exception as e:
                logger.error(f"Error reading file {document_file}: {str(e)}")
                continue
                
            # Create a Document object
            document = Document(
                id=document_id,
                filename=document_file.name,
                content=content,  # Add the content field
                size=document_file.stat().st_size,
                folder="/",  # Default folder
                tags=[]  # No tags by default
            )
            
            # Delete existing document from vector store
            try:
                vector_store.delete_document(document_id)
                logger.info(f"Deleted existing document {document_id} from vector store")
            except Exception as e:
                logger.warning(f"Error deleting document {document_id} from vector store: {str(e)}")
            
            # Process the document with new chunking settings
            processed_document = await processor.process_document(document)
            
            # Add the document to the vector store
            await vector_store.add_document(processed_document)
            
            logger.info(f"Successfully reprocessed document {document_id} with {len(processed_document.chunks)} chunks")
        
        except Exception as e:
            logger.error(f"Error reprocessing document in directory {doc_dir}: {str(e)}")
    
    logger.info("Document reprocessing complete")

if __name__ == "__main__":
    asyncio.run(reprocess_documents())