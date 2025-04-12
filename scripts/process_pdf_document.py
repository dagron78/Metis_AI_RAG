import asyncio
import sys
import os
import logging
import sqlite3
import json
from pathlib import Path
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("process_pdf_document")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.vector_store import VectorStore
from app.models.document import Document, Chunk
from app.rag.ollama_client import OllamaClient
from app.core.config import DEFAULT_EMBEDDING_MODEL
from langchain_community.document_loaders import PyPDFLoader

async def process_pdf_document():
    """Process a PDF document from the database and add it to the vector database"""
    logger.info("Processing a PDF document from the database...")
    
    # Extract database path from the URL
    from app.core.config import SETTINGS
    db_path = SETTINGS.database_url.replace("sqlite+aiosqlite:///", "")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the PDF document to process
        cursor.execute("SELECT id, filename, doc_metadata FROM documents WHERE filename LIKE '%.PDF'")
        result = cursor.fetchone()
        
        if not result:
            logger.error("PDF document not found in the database")
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
        
        # Extract text from PDF using LangChain's PyPDFLoader
        try:
            loader = PyPDFLoader(file_path)
            langchain_docs = loader.load()
            
            # Combine all pages into one content string
            content = "\n\n".join([doc.page_content for doc in langchain_docs])
            
            logger.info(f"Extracted text from PDF, length: {len(content)} characters")
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return
        
        # Create a Document object (Pydantic model)
        document = Document(
            id=doc_id,
            filename=filename,
            content=content,
            metadata=metadata,
            folder="/"
        )
        
        # Create Ollama client for embeddings
        ollama_client = OllamaClient()
        
        # Split content into chunks (simple splitting by paragraphs)
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        chunks = []
        
        # Limit to 20 chunks to avoid processing too much
        paragraphs = paragraphs[:20]
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            logger.info(f"Creating embedding for chunk {i+1}: '{paragraph[:50]}...'")
            
            # Create embedding
            embedding = await ollama_client.create_embedding(paragraph, model=DEFAULT_EMBEDDING_MODEL)
            
            # Create chunk
            chunk = Chunk(
                id=str(uuid4()),
                content=paragraph,
                embedding=embedding,
                metadata={
                    "document_id": document.id,
                    "index": i,
                    "folder": "/",
                    "is_public": True
                }
            )
            chunks.append(chunk)
        
        # Add chunks to document
        document.chunks = chunks
        
        # Create vector store
        vector_store = VectorStore()
        
        # Add document to vector store
        logger.info(f"Adding document {document.id} to vector store with {len(chunks)} chunks")
        await vector_store.add_document(document)
        
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
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")

if __name__ == "__main__":
    asyncio.run(process_pdf_document())