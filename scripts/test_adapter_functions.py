"""
Test script for adapter functions.

This script demonstrates the adapter functions working correctly by:
1. Creating a Pydantic Document
2. Converting it to a SQLAlchemy Document
3. Converting it back to a Pydantic Document
4. Verifying that the data is preserved
"""
import sys
import os
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.document import Document as PydanticDocument, Chunk as PydanticChunk
from app.db.models import Document as DBDocument, Chunk as DBChunk
from app.db.adapters import (
    pydantic_document_to_sqlalchemy,
    sqlalchemy_document_to_pydantic,
    pydantic_chunk_to_sqlalchemy,
    sqlalchemy_chunk_to_pydantic,
    to_str_id,
    to_uuid_or_str
)

def test_adapter_functions():
    """Test the adapter functions"""
    print("Testing adapter functions...")
    
    # Create a Pydantic Document with Chunks
    doc_id = str(uuid.uuid4())
    pydantic_doc = PydanticDocument(
        id=doc_id,
        filename="test.txt",
        content="This is a test document.",
        metadata={
            "file_type": "txt",
            "test_size": "small",
            "processing_status": "pending"
        },
        folder="/test",
        chunks=[
            PydanticChunk(
                id=str(uuid.uuid4()),
                content="This is chunk 1.",
                metadata={"index": 0}
            ),
            PydanticChunk(
                id=str(uuid.uuid4()),
                content="This is chunk 2.",
                metadata={"index": 1}
            )
        ]
    )
    
    print(f"Created Pydantic Document: {pydantic_doc.id}")
    print(f"Number of chunks: {len(pydantic_doc.chunks)}")
    
    # Convert to SQLAlchemy Document
    db_doc = pydantic_document_to_sqlalchemy(pydantic_doc)
    
    print(f"Converted to SQLAlchemy Document: {db_doc.id}")
    print(f"Number of chunks: {len(db_doc.chunks)}")
    print(f"Metadata: {db_doc.doc_metadata}")
    
    # Verify that the data is preserved
    # For SQLite, the ID might be a string, while for PostgreSQL it might be a UUID
    # So we convert both to strings for comparison
    assert str(db_doc.id) == str(pydantic_doc.id)
    assert db_doc.filename == pydantic_doc.filename
    assert db_doc.content == pydantic_doc.content
    assert db_doc.doc_metadata == pydantic_doc.metadata
    assert db_doc.folder == pydantic_doc.folder
    assert len(db_doc.chunks) == len(pydantic_doc.chunks)
    
    # Convert back to Pydantic Document
    pydantic_doc2 = sqlalchemy_document_to_pydantic(db_doc)
    
    print(f"Converted back to Pydantic Document: {pydantic_doc2.id}")
    print(f"Number of chunks: {len(pydantic_doc2.chunks)}")
    print(f"Metadata: {pydantic_doc2.metadata}")
    
    # Verify that the data is preserved
    # For SQLite, the ID might be a string, while for PostgreSQL it might be a UUID
    # So we convert both to strings for comparison
    assert str(pydantic_doc2.id) == str(pydantic_doc.id)
    assert pydantic_doc2.filename == pydantic_doc.filename
    assert pydantic_doc2.content == pydantic_doc.content
    assert pydantic_doc2.metadata == pydantic_doc.metadata
    assert pydantic_doc2.folder == pydantic_doc.folder
    assert len(pydantic_doc2.chunks) == len(pydantic_doc.chunks)
    
    print("All tests passed!")
    
    return True

if __name__ == "__main__":
    test_adapter_functions()