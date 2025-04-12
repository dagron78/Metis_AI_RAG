import asyncio
import sys
import os
import logging
import sqlite3
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("direct_process_document")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import SETTINGS
from app.rag.document_processor import DocumentProcessor
from app.rag.vector_store import VectorStore
from app.models.document import Document

async def direct_process_document():
    """Directly process a document and add it to the vector database"""
    logger.info("Directly processing a document...")
    
    # Extract database path from the URL
    db_path = SETTINGS.database_url.replace("sqlite+aiosqlite:///", "")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get a document to process
        cursor.execute("SELECT id, filename, doc_metadata FROM documents LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            logger.error("No documents found in the database")
            return
        
        doc_id = result[0]
        filename = result[1]
        metadata_str = result[2]
        
        logger.info(f"Processing document: {doc_id} - {filename}")
        
        # Parse metadata
        metadata = json.loads(metadata_str) if metadata_str else {}
        file_path = metadata.get("file_path", "")
        
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File path not found: {file_path}")
            return
        
        # Create a Document object (Pydantic model)
        document = Document(
            id=doc_id,
            filename=filename,
            content="",  # Will be populated by the processor
            metadata=metadata,
            folder="/"
        )
        
        # Create a document processor
        document_processor = DocumentProcessor()
        
        # Process the document
        logger.info(f"Processing document with file path: {file_path}")
        processed_document = await document_processor.process_document(document)
        
        # Check if the document was processed successfully
        if processed_document and processed_document.chunks:
            logger.info(f"Document processed successfully with {len(processed_document.chunks)} chunks")
            
            # Create a vector store
            vector_store = VectorStore()
            
            # Add the document to the vector store
            logger.info(f"Adding document to vector store")
            await vector_store.add_document(processed_document)
            
            # Get vector store statistics
            stats = await vector_store.get_statistics()
            logger.info(f"Vector store statistics: {stats}")
            
            # Update document status in the database
            cursor.execute(
                "UPDATE documents SET processing_status = 'completed' WHERE id = ?",
                (doc_id,)
            )
            conn.commit()
            
            logger.info(f"Document {doc_id} processed and added to vector store successfully")
        else:
            logger.error(f"Document processing failed: no chunks generated")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")

if __name__ == "__main__":
    asyncio.run(direct_process_document())