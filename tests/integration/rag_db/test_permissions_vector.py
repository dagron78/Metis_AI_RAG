#!/usr/bin/env python3
"""
Integration tests for vector database security (metadata filtering)
"""

import pytest
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import os
from pathlib import Path
import tempfile
import shutil

from app.db.dependencies import get_db
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.document_repository import DocumentRepository
from app.models.user import UserCreate
from app.models.document import DocumentCreate, DocumentPermissionCreate
from app.rag.vector_store import VectorStore
from app.core.security import get_password_hash


@pytest.fixture
def event_loop():
    """Create an event loop for each test"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_users():
    """Create test users in the database"""
    # Get database session
    db = await anext(get_db())
    
    try:
        # Create user repository
        user_repository = UserRepository(db)
        
        # Create owner user
        owner_data = {
            "username": f"owner_{uuid.uuid4().hex[:8]}",
            "email": f"owner_{uuid.uuid4().hex[:8]}@example.com",
            "password": "testpassword123",
            "full_name": "Owner User",
            "is_active": True,
            "is_admin": False
        }
        owner_user = await user_repository.create_user(UserCreate(**owner_data))
        
        # Create collaborator user
        collaborator_data = {
            "username": f"collaborator_{uuid.uuid4().hex[:8]}",
            "email": f"collaborator_{uuid.uuid4().hex[:8]}@example.com",
            "password": "testpassword123",
            "full_name": "Collaborator User",
            "is_active": True,
            "is_admin": False
        }
        collaborator_user = await user_repository.create_user(UserCreate(**collaborator_data))
        
        # Create unrelated user
        unrelated_data = {
            "username": f"unrelated_{uuid.uuid4().hex[:8]}",
            "email": f"unrelated_{uuid.uuid4().hex[:8]}@example.com",
            "password": "testpassword123",
            "full_name": "Unrelated User",
            "is_active": True,
            "is_admin": False
        }
        unrelated_user = await user_repository.create_user(UserCreate(**unrelated_data))
        
        # Return users
        yield owner_user, collaborator_user, unrelated_user
        
        # Clean up - delete users
        await user_repository.delete_user(owner_user.id)
        await user_repository.delete_user(collaborator_user.id)
        await user_repository.delete_user(unrelated_user.id)
    finally:
        await db.close()


@pytest.fixture
async def test_vector_store():
    """Create a temporary vector store for testing"""
    # Create a temporary directory for the vector store
    temp_dir = tempfile.mkdtemp()
    vector_store_path = Path(temp_dir) / "test_vector_store"
    
    # Create vector store
    vector_store = VectorStore(str(vector_store_path))
    await vector_store.initialize()
    
    yield vector_store
    
    # Clean up
    await vector_store.close()
    shutil.rmtree(temp_dir)


@pytest.fixture
async def test_documents_with_vectors(test_users, test_vector_store):
    """Create test documents with vector embeddings"""
    owner_user, collaborator_user, unrelated_user = test_users
    
    # Get database session
    db = await anext(get_db())
    
    try:
        # Set database context to owner user
        await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
        
        # Create document repository
        document_repository = DocumentRepository(db)
        
        # Create documents
        documents = []
        
        # Private document
        private_doc_data = {
            "title": "Private Vector Document",
            "content": "This is a private document with vector embeddings",
            "user_id": owner_user.id,
            "is_public": False
        }
        private_doc = await document_repository.create_document(DocumentCreate(**private_doc_data))
        documents.append(private_doc)
        
        # Public document
        public_doc_data = {
            "title": "Public Vector Document",
            "content": "This is a public document with vector embeddings",
            "user_id": owner_user.id,
            "is_public": True
        }
        public_doc = await document_repository.create_document(DocumentCreate(**public_doc_data))
        documents.append(public_doc)
        
        # Shared document
        shared_doc_data = {
            "title": "Shared Vector Document",
            "content": "This is a document shared with collaborator with vector embeddings",
            "user_id": owner_user.id,
            "is_public": False
        }
        shared_doc = await document_repository.create_document(DocumentCreate(**shared_doc_data))
        documents.append(shared_doc)
        
        # Share document with collaborator
        share_permission = DocumentPermissionCreate(
            document_id=shared_doc.id,
            user_id=collaborator_user.id,
            permission_level="read"
        )
        await document_repository.create_document_permission(share_permission)
        
        # Collaborator's document
        collab_doc_data = {
            "title": "Collaborator Vector Document",
            "content": "This is a document owned by collaborator with vector embeddings",
            "user_id": collaborator_user.id,
            "is_public": False
        }
        # Set context to collaborator to create their document
        await db.execute(text(f"SET app.current_user_id = '{collaborator_user.id}'"))
        collab_doc = await document_repository.create_document(DocumentCreate(**collab_doc_data))
        documents.append(collab_doc)
        
        # Unrelated user's document
        unrelated_doc_data = {
            "title": "Unrelated Vector Document",
            "content": "This is a document owned by unrelated user with vector embeddings",
            "user_id": unrelated_user.id,
            "is_public": False
        }
        # Set context to unrelated user to create their document
        await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
        unrelated_doc = await document_repository.create_document(DocumentCreate(**unrelated_doc_data))
        documents.append(unrelated_doc)
        
        # Add vector embeddings for each document
        for doc in documents:
            # Create chunks with vector embeddings
            chunks = []
            for i in range(2):  # 2 chunks per document
                chunk_id = str(uuid.uuid4())
                chunk_content = f"Chunk {i} of document {doc.title}"
                chunk_embedding = [0.1] * 384  # Simple mock embedding
                
                # Create metadata with security information
                metadata = {
                    "document_id": doc.id,
                    "user_id": doc.user_id,
                    "is_public": doc.is_public,
                    "chunk_index": i,
                    "title": doc.title
                }
                
                # Add to vector store
                await test_vector_store.add_texts(
                    texts=[chunk_content],
                    metadatas=[metadata],
                    ids=[chunk_id]
                )
                
                chunks.append({
                    "id": chunk_id,
                    "content": chunk_content,
                    "metadata": metadata
                })
            
            # Add chunks to document
            doc.chunks = chunks
        
        # Return documents
        yield {
            "private_doc": private_doc,
            "public_doc": public_doc,
            "shared_doc": shared_doc,
            "collab_doc": collab_doc,
            "unrelated_doc": unrelated_doc
        }
        
        # Clean up - delete documents
        await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
        await document_repository.delete_document(private_doc.id)
        await document_repository.delete_document(public_doc.id)
        await document_repository.delete_document(shared_doc.id)
        
        await db.execute(text(f"SET app.current_user_id = '{collaborator_user.id}'"))
        await document_repository.delete_document(collab_doc.id)
        
        await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
        await document_repository.delete_document(unrelated_doc.id)
    finally:
        # Reset database context
        await db.execute(text("SET app.current_user_id = NULL"))
        await db.close()


class TestVectorDatabaseSecurity:
    """Tests for vector database security (metadata filtering)"""
    
    @pytest.mark.asyncio
    async def test_owner_vector_search(self, test_users, test_documents_with_vectors, test_vector_store):
        """Test that owner can search their own documents"""
        owner_user, _, _ = test_users
        docs = test_documents_with_vectors
        
        # Search as owner
        results = await test_vector_store.similarity_search(
            query="vector document",
            user_id=owner_user.id,
            k=10
        )
        
        # Owner should see their own documents (private, public, shared)
        assert len(results) >= 6  # At least 6 chunks (3 docs * 2 chunks)
        
        # Check document IDs in results
        result_doc_ids = {doc.metadata["document_id"] for doc in results}
        assert docs["private_doc"].id in result_doc_ids
        assert docs["public_doc"].id in result_doc_ids
        assert docs["shared_doc"].id in result_doc_ids
    
    @pytest.mark.asyncio
    async def test_collaborator_vector_search(self, test_users, test_documents_with_vectors, test_vector_store):
        """Test that collaborator can search their own and shared documents"""
        _, collaborator_user, _ = test_users
        docs = test_documents_with_vectors
        
        # Search as collaborator
        results = await test_vector_store.similarity_search(
            query="vector document",
            user_id=collaborator_user.id,
            k=10
        )
        
        # Collaborator should see their own documents, shared documents, and public documents
        assert len(results) >= 6  # At least 6 chunks (3 docs * 2 chunks)
        
        # Check document IDs in results
        result_doc_ids = {doc.metadata["document_id"] for doc in results}
        assert docs["collab_doc"].id in result_doc_ids  # Own document
        assert docs["shared_doc"].id in result_doc_ids  # Shared document
        assert docs["public_doc"].id in result_doc_ids  # Public document
        assert docs["private_doc"].id not in result_doc_ids  # Should not see owner's private document
        assert docs["unrelated_doc"].id not in result_doc_ids  # Should not see unrelated user's document
    
    @pytest.mark.asyncio
    async def test_unrelated_user_vector_search(self, test_users, test_documents_with_vectors, test_vector_store):
        """Test that unrelated user can only search public documents"""
        _, _, unrelated_user = test_users
        docs = test_documents_with_vectors
        
        # Search as unrelated user
        results = await test_vector_store.similarity_search(
            query="vector document",
            user_id=unrelated_user.id,
            k=10
        )
        
        # Unrelated user should see their own documents and public documents
        assert len(results) >= 4  # At least 4 chunks (2 docs * 2 chunks)
        
        # Check document IDs in results
        result_doc_ids = {doc.metadata["document_id"] for doc in results}
        assert docs["unrelated_doc"].id in result_doc_ids  # Own document
        assert docs["public_doc"].id in result_doc_ids  # Public document
        assert docs["private_doc"].id not in result_doc_ids  # Should not see owner's private document
        assert docs["shared_doc"].id not in result_doc_ids  # Should not see shared document
        assert docs["collab_doc"].id not in result_doc_ids  # Should not see collaborator's document
    
    @pytest.mark.asyncio
    async def test_post_retrieval_filtering(self, test_users, test_documents_with_vectors, test_vector_store):
        """Test post-retrieval filtering for additional security"""
        owner_user, collaborator_user, _ = test_users
        docs = test_documents_with_vectors
        
        # Simulate a scenario where metadata filtering might miss something
        # by directly adding a document with incorrect metadata
        
        # Create a document with incorrect metadata (missing user_id)
        bad_chunk_id = str(uuid.uuid4())
        bad_chunk_content = "This chunk has incorrect metadata"
        bad_metadata = {
            "document_id": docs["private_doc"].id,
            # Missing user_id field
            "is_public": False,
            "chunk_index": 99,
            "title": "Bad Metadata Document"
        }
        
        # Add to vector store
        await test_vector_store.add_texts(
            texts=[bad_chunk_content],
            metadatas=[bad_metadata],
            ids=[bad_chunk_id]
        )
        
        # Search as collaborator
        results = await test_vector_store.similarity_search(
            query="incorrect metadata",
            user_id=collaborator_user.id,
            k=10
        )
        
        # The bad chunk should be filtered out in post-retrieval filtering
        for doc in results:
            assert doc.page_content != bad_chunk_content
            
        # Double check by searching for the exact content
        exact_results = await test_vector_store.similarity_search(
            query="This chunk has incorrect metadata",
            user_id=collaborator_user.id,
            k=10
        )
        
        # Should not find the bad chunk
        for doc in exact_results:
            assert doc.page_content != bad_chunk_content
    
    @pytest.mark.asyncio
    async def test_password_reset_vector_persistence(self, test_users, test_documents_with_vectors, test_vector_store):
        """Test that vector metadata links persist after password reset"""
        owner_user, _, _ = test_users
        docs = test_documents_with_vectors
        
        # Initial search as owner
        initial_results = await test_vector_store.similarity_search(
            query="vector document",
            user_id=owner_user.id,
            k=10
        )
        
        # Get initial document IDs
        initial_doc_ids = {doc.metadata["document_id"] for doc in initial_results}
        
        # Simulate password reset by updating password hash
        db = await anext(get_db())
        try:
            user_repository = UserRepository(db)
            new_password = "newpassword456"
            new_password_hash = get_password_hash(new_password)
            await user_repository.update_user(owner_user.id, {"password_hash": new_password_hash})
            
            # Get updated user
            updated_user = await user_repository.get_by_id(owner_user.id)
            
            # Search again with updated user
            post_reset_results = await test_vector_store.similarity_search(
                query="vector document",
                user_id=updated_user.id,
                k=10
            )
            
            # Get post-reset document IDs
            post_reset_doc_ids = {doc.metadata["document_id"] for doc in post_reset_results}
            
            # Should see the same documents
            assert initial_doc_ids == post_reset_doc_ids
            
        finally:
            await db.close()
    
    @pytest.mark.asyncio
    async def test_cross_user_access_prevention(self, test_users, test_documents_with_vectors, test_vector_store):
        """Test prevention of cross-user access in vector search"""
        owner_user, _, unrelated_user = test_users
        docs = test_documents_with_vectors
        
        # Try to access owner's private document by directly searching for its content
        private_doc_query = "This is a private document with vector embeddings"
        
        # Search as unrelated user
        results = await test_vector_store.similarity_search(
            query=private_doc_query,
            user_id=unrelated_user.id,
            k=10
        )
        
        # Should not find owner's private document
        for doc in results:
            assert doc.metadata["document_id"] != docs["private_doc"].id
        
        # Now search as owner
        owner_results = await test_vector_store.similarity_search(
            query=private_doc_query,
            user_id=owner_user.id,
            k=10
        )
        
        # Should find owner's private document
        found_private = False
        for doc in owner_results:
            if doc.metadata["document_id"] == docs["private_doc"].id:
                found_private = True
                break
        
        assert found_private, "Owner should be able to find their private document"
    
    @pytest.mark.asyncio
    async def test_document_sharing_vector_access(self, test_users, test_documents_with_vectors, test_vector_store):
        """Test that document sharing affects vector search results"""
        owner_user, collaborator_user, unrelated_user = test_users
        docs = test_documents_with_vectors
        
        # Get database session
        db = await anext(get_db())
        
        try:
            # Set database context to owner user
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            
            # Create document repository
            document_repository = DocumentRepository(db)
            
            # Initial search as unrelated user
            initial_results = await test_vector_store.similarity_search(
                query="private vector document",
                user_id=unrelated_user.id,
                k=10
            )
            
            # Should not find owner's private document
            initial_doc_ids = {doc.metadata["document_id"] for doc in initial_results}
            assert docs["private_doc"].id not in initial_doc_ids
            
            # Share private document with unrelated user
            share_permission = DocumentPermissionCreate(
                document_id=docs["private_doc"].id,
                user_id=unrelated_user.id,
                permission_level="read"
            )
            await document_repository.create_document_permission(share_permission)
            
            # Search again as unrelated user
            post_share_results = await test_vector_store.similarity_search(
                query="private vector document",
                user_id=unrelated_user.id,
                k=10
            )
            
            # Now should find owner's private document
            post_share_doc_ids = {doc.metadata["document_id"] for doc in post_share_results}
            assert docs["private_doc"].id in post_share_doc_ids
            
            # Revoke permission
            await document_repository.delete_document_permission(docs["private_doc"].id, unrelated_user.id)
            
            # Search again as unrelated user
            post_revoke_results = await test_vector_store.similarity_search(
                query="private vector document",
                user_id=unrelated_user.id,
                k=10
            )
            
            # Should not find owner's private document again
            post_revoke_doc_ids = {doc.metadata["document_id"] for doc in post_revoke_results}
            assert docs["private_doc"].id not in post_revoke_doc_ids
            
        finally:
            # Reset database context
            await db.execute(text("SET app.current_user_id = NULL"))
            await db.close()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])