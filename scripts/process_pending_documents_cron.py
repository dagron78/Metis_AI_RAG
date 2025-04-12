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
logger = logging.getLogger("process_pending_documents_cron")

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.vector_store import VectorStore
from app.models.document import Document, Chunk
from app.rag.ollama_client import OllamaClient
from app.core.config import DEFAULT_EMBEDDING_MODEL, SETTINGS

async def process_pending_documents():
    """Process all pending documents and add them to the vector database"""
    logger.info("Processing pending documents...")
    
    # Extract database path from the URL
    db_path = SETTINGS.database_url.replace("sqlite+aiosqlite:///", "")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all pending documents
        cursor.execute("SELECT id, filename, doc_metadata FROM documents WHERE processing_status = 'pending'")
        pending_documents = cursor.fetchall()
        
        if not pending_documents:
            logger.info("No pending documents found.")
            return
        
        logger.info(f"Found {len(pending_documents)} pending documents to process.")
        
        # Create Ollama client for embeddings
        ollama_client = OllamaClient()
        
        # Create vector store
        vector_store = VectorStore()
        
        # Process each document
        for doc_id, filename, metadata_str in pending_documents:
            try:
                logger.info(f"Processing document: {doc_id} - {filename}")
                
                # Update status to processing
                cursor.execute(
                    "UPDATE documents SET processing_status = 'processing' WHERE id = ?",
                    (doc_id,)
                )
                conn.commit()
                
                # Parse metadata
                metadata = json.loads(metadata_str) if metadata_str else {}
                file_path = metadata.get("file_path", "")
                
                if not file_path or not os.path.exists(file_path):
                    logger.error(f"File path not found: {file_path}")
                    
                    # Update status to failed
                    cursor.execute(
                        "UPDATE documents SET processing_status = 'failed' WHERE id = ?",
                        (doc_id,)
                    )
                    conn.commit()
                    continue
                
                # Read the file content
                try:
                    # Determine file type
                    _, ext = os.path.splitext(file_path.lower())
                    
                    if ext == ".pdf":
                        # Use PyPDFLoader for PDF files
                        from langchain_community.document_loaders import PyPDFLoader
                        loader = PyPDFLoader(file_path)
                        langchain_docs = loader.load()
                        content = "\n\n".join([doc.page_content for doc in langchain_docs])
                    else:
                        # Use simple text loading for other files
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    
                    logger.info(f"File content length: {len(content)} characters")
                except Exception as e:
                    logger.error(f"Error reading file: {str(e)}")
                    
                    # Update status to failed
                    cursor.execute(
                        "UPDATE documents SET processing_status = 'failed' WHERE id = ?",
                        (doc_id,)
                    )
                    conn.commit()
                    continue
                
                # Create a Document object (Pydantic model)
                document = Document(
                    id=doc_id,
                    filename=filename,
                    content=content,
                    metadata=metadata,
                    folder="/"
                )
                
                # Split content into chunks (simple splitting by paragraphs)
                paragraphs = [p for p in content.split('\n\n') if p.strip()]
                chunks = []
                
                # Limit to 30 chunks to avoid processing too much
                paragraphs = paragraphs[:30]
                
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
                
                # Add document to vector store
                logger.info(f"Adding document {document.id} to vector store with {len(chunks)} chunks")
                await vector_store.add_document(document)
                
                # Update status to completed
                cursor.execute(
                    "UPDATE documents SET processing_status = 'completed' WHERE id = ?",
                    (doc_id,)
                )
                conn.commit()
                
                logger.info(f"Document {doc_id} processed and added to vector store successfully")
                
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {str(e)}")
                
                # Update status to failed
                cursor.execute(
                    "UPDATE documents SET processing_status = 'failed' WHERE id = ?",
                    (doc_id,)
                )
                conn.commit()
        
        # Get vector store statistics
        stats = await vector_store.get_statistics()
        logger.info(f"Vector store statistics: {stats}")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error processing pending documents: {str(e)}")

if __name__ == "__main__":
    asyncio.run(process_pending_documents())