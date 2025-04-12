import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.vector_store import VectorStore
from app.core.config import CHROMA_DB_DIR

async def check_vector_db_contents():
    """Check the contents of the vector database"""
    print(f"Checking vector store at: {CHROMA_DB_DIR}")
    
    try:
        # Create vector store
        vector_store = VectorStore()
        
        # Get statistics
        stats = await vector_store.get_statistics()
        print(f"Vector store statistics: {stats}")
        
        # Get more detailed information about documents
        if stats["total_documents"] > 0:
            print(f"\nFound {stats['total_documents']} documents with {stats['total_chunks']} chunks.")
            
            # Get all document IDs
            all_metadatas = vector_store.collection.get(
                include=["metadatas"]
            )
            
            # Extract unique document IDs and their metadata
            document_info = {}
            if all_metadatas and "metadatas" in all_metadatas and all_metadatas["metadatas"]:
                for metadata in all_metadatas["metadatas"]:
                    if metadata and "document_id" in metadata:
                        doc_id = metadata["document_id"]
                        if doc_id not in document_info:
                            document_info[doc_id] = {
                                "filename": metadata.get("filename", "Unknown"),
                                "chunks": 0,
                                "folder": metadata.get("folder", "/"),
                                "is_public": metadata.get("is_public", False)
                            }
                        document_info[doc_id]["chunks"] += 1
            
            # Print document information
            print("\nDocument details:")
            for doc_id, info in document_info.items():
                print(f"  Document ID: {doc_id}")
                print(f"    Filename: {info['filename']}")
                print(f"    Folder: {info['folder']}")
                print(f"    Chunks: {info['chunks']}")
                print(f"    Public: {info['is_public']}")
                print()
        else:
            print("\nNo documents found in the vector database.")
            print("This could be why your RAG system is not referencing any documents.")
            
    except Exception as e:
        print(f"Error checking vector store: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_vector_db_contents())