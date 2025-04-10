"""
Test script for document processing end-to-end flow
"""
import os
import asyncio
import json
import uuid
import shutil
from pathlib import Path

# Add project root to path
import sys
sys.path.append(os.path.abspath('.'))

from app.rag.document_processor import DocumentProcessor
from app.rag.vector_store import VectorStore
from app.utils.file_utils import validate_file, save_upload_file
from app.core.config import UPLOAD_DIR

# Set up test document
TEST_DOCUMENT_PATH = os.path.join('data', 'test_docs', 'smart_home_user_guide.txt')
TEST_DOCUMENT_ID = str(uuid.uuid4())

async def test_document_processing():
    """Test document processing from start to finish"""
    print(f"Using test document: {TEST_DOCUMENT_PATH}")
    
    # Step 1: Copy test document to the uploads directory
    document_dir = os.path.join(UPLOAD_DIR, TEST_DOCUMENT_ID)
    os.makedirs(document_dir, exist_ok=True)
    
    dest_path = os.path.join(document_dir, os.path.basename(TEST_DOCUMENT_PATH))
    shutil.copy(TEST_DOCUMENT_PATH, dest_path)
    print(f"Copied test document to: {dest_path}")
    
    # Step 2: Initialize document processor with default settings
    processor = DocumentProcessor(
        upload_dir=UPLOAD_DIR,
        chunking_strategy="recursive"
    )
    print("Initialized document processor")
    
    # Step 3: Process the document
    print(f"Processing document with ID: {TEST_DOCUMENT_ID}")
    
    # Create a basic document object
    from app.models.document import Document, Chunk
    
    # Read the document content
    with open(dest_path, 'r') as f:
        document_content = f.read()
    
    document = Document(
        id=TEST_DOCUMENT_ID,
        filename=os.path.basename(TEST_DOCUMENT_PATH),
        content=document_content,
        folder="/test",
        tags=["test", "smart-home", "guide"]
    )
    
    # Process the document and get chunks
    print("Starting document processing...")
    processed_document = await processor.process_document(document)
    chunks = processed_document.chunks
    print(f"Document processed: {len(chunks)} chunks created")
    
    # Step 4: Initialize vector store
    vector_store = VectorStore()
    print("Initialized vector store")
    
    # Step 5: Store the chunks in the vector store
    print("Storing chunks in vector store...")
    
    # Update metadata for all chunks
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            "document_id": document.id,
            "test": True,
            "chunk_index": i,
            "user_id": "test-user"
        })
    
    # Add all chunks to the document
    document.chunks = chunks
    
    # Add document to vector store
    print(f"Adding document with {len(document.chunks)} chunks to vector store...")
    await vector_store.add_document(document)
    print("Document and chunks added to vector store successfully")
    
    # Step 6: Perform a test query
    print("\nPerforming test query...")
    query = "How do I reset my smart home device?"
    top_k = 3
    
    # Use the search method from VectorStore
    results = await vector_store.search(query, top_k=top_k)
    
    print(f"Query: {query}")
    print(f"Found {len(results)} relevant chunks:")
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Distance: {result.get('distance', 'N/A')}")
        print(f"Document ID: {result['metadata'].get('document_id', 'Unknown')}")
        print(f"Text: {result.get('content', '')[:150]}...")
    
    # Step 7: Clean up (optional)
    print("\nTest completed successfully")
    
    # Uncomment to clean up test document
    # if os.path.exists(document_dir):
    #     shutil.rmtree(document_dir)
    #     print(f"Cleaned up test document directory: {document_dir}")
    
    return "Document processing test completed successfully"

if __name__ == "__main__":
    result = asyncio.run(test_document_processing())
    print(result)