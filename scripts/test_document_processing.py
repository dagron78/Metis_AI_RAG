"""
Test script for document processing with adapter functions.

This script demonstrates the document processor working with the adapter functions by:
1. Creating a Pydantic Document
2. Processing the document
3. Converting the processed document to a SQLAlchemy Document
4. Converting it back to a Pydantic Document
5. Verifying that the data is preserved
"""
import sys
import os
import uuid
import asyncio
import tempfile
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.document import Document as PydanticDocument, Chunk as PydanticChunk
from app.db.models import Document as DBDocument, Chunk as DBChunk
from app.rag.document_processor import DocumentProcessor
from app.db.adapters import (
    pydantic_document_to_sqlalchemy,
    sqlalchemy_document_to_pydantic,
    pydantic_chunk_to_sqlalchemy,
    sqlalchemy_chunk_to_pydantic,
    to_str_id,
    to_uuid_or_str
)
from app.core.config import UPLOAD_DIR

async def test_document_processing():
    """Test document processing with adapter functions"""
    print("Testing document processing with adapter functions...")
    
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create a test document
            doc_id = str(uuid.uuid4())
            filename = "test.txt"
            
            # Create document directory
            document_dir = os.path.join(temp_dir, doc_id)
            os.makedirs(document_dir, exist_ok=True)
            
            # Create test file
            document_file_path = os.path.join(document_dir, filename)
            with open(document_file_path, 'w') as f:
                f.write("This is a test document.\n\n" * 10)
                
            print(f"Created test file at: {document_file_path}")
            
            # Create a Pydantic Document
            pydantic_doc = PydanticDocument(
                id=doc_id,
                filename=filename,
                content="",  # Content will be read during processing
                metadata={
                    "file_type": "txt",
                    "test_size": "small",
                    "processing_status": "pending"
                },
                folder="/test"
            )
            
            print(f"Created Pydantic Document: {pydantic_doc.id}")
            
            # Create a DocumentProcessor with simplified settings
            # Disable chunking judge and document analysis service
            import app.rag.document_processor
            original_use_chunking_judge = app.rag.document_processor.USE_CHUNKING_JUDGE
            app.rag.document_processor.USE_CHUNKING_JUDGE = False
            
            # Create a custom document processor that uses our temp directory
            class TestDocumentProcessor(DocumentProcessor):
                async def _load_document(self, file_path: str):
                    """Override to use the correct file path"""
                    print(f"Original file path: {file_path}")
                    
                    # Extract document ID and filename from the path
                    parts = file_path.split('/')
                    doc_id = parts[-2]
                    filename = parts[-1]
                    
                    # Use the temp directory instead
                    correct_path = os.path.join(temp_dir, doc_id, filename)
                    print(f"Corrected file path: {correct_path}")
                    
                    # Read the file content
                    with open(correct_path, 'r') as f:
                        content = f.read()
                    
                    # Return a LangchainDocument
                    from langchain.schema import Document as LangchainDocument
                    return [LangchainDocument(page_content=content, metadata={"source": correct_path})]
            
            try:
                processor = TestDocumentProcessor(
                    upload_dir=temp_dir,  # Use the temp directory directly
                    chunking_strategy="recursive",
                    chunk_size=1500,
                    chunk_overlap=150
                )
            finally:
                # Restore original settings
                app.rag.document_processor.USE_CHUNKING_JUDGE = original_use_chunking_judge
            
            # Process the document
            processed_doc = await processor.process_document(pydantic_doc)
            
            print(f"Processed document: {processed_doc.id}")
            print(f"Number of chunks: {len(processed_doc.chunks)}")
            
            # Convert to SQLAlchemy Document
            db_doc = pydantic_document_to_sqlalchemy(processed_doc)
            
            print(f"Converted to SQLAlchemy Document: {db_doc.id}")
            print(f"Number of chunks: {len(db_doc.chunks)}")
            
            # Convert back to Pydantic Document
            pydantic_doc2 = sqlalchemy_document_to_pydantic(db_doc)
            
            print(f"Converted back to Pydantic Document: {pydantic_doc2.id}")
            print(f"Number of chunks: {len(pydantic_doc2.chunks)}")
            
            # Verify that the data is preserved
            assert str(pydantic_doc2.id) == str(processed_doc.id)
            assert pydantic_doc2.filename == processed_doc.filename
            assert pydantic_doc2.content == processed_doc.content
            assert pydantic_doc2.metadata == processed_doc.metadata
            assert pydantic_doc2.folder == processed_doc.folder
            assert len(pydantic_doc2.chunks) == len(processed_doc.chunks)
            
            print("All tests passed!")
            
            return True
        finally:
            # No need to restore UPLOAD_DIR since we're using dependency injection
            pass

if __name__ == "__main__":
    asyncio.run(test_document_processing())