#!/usr/bin/env python3
"""
Integration tests for database-level permissions (Row Level Security)
"""

import pytest
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.dependencies import get_db
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.document_repository import DocumentRepository
from app.models.user import UserCreate
from app.models.document import DocumentCreate, DocumentPermissionCreate


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
async def test_documents(test_users):
    """Create test documents in the database"""
    owner_user, collaborator_user, unrelated_user = test_users
    
    # Get database session
    db = await anext(get_db())
    
    try:
        # Set database context to owner user
        await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
        
        # Create document repository
        document_repository = DocumentRepository(db)
        
        # Create private document
        private_doc_data = {
            "title": "Private Document",
            "content": "This is a private document",
            "user_id": owner_user.id,
            "is_public": False
        }
        private_doc = await document_repository.create_document(DocumentCreate(**private_doc_data))
        
        # Create public document
        public_doc_data = {
            "title": "Public Document",
            "content": "This is a public document",
            "user_id": owner_user.id,
            "is_public": True
        }
        public_doc = await document_repository.create_document(DocumentCreate(**public_doc_data))
        
        # Create shared document (read permission)
        shared_read_doc_data = {
            "title": "Shared Read Document",
            "content": "This is a document shared with read permission",
            "user_id": owner_user.id,
            "is_public": False
        }
        shared_read_doc = await document_repository.create_document(DocumentCreate(**shared_read_doc_data))
        
        # Create shared document (write permission)
        shared_write_doc_data = {
            "title": "Shared Write Document",
            "content": "This is a document shared with write permission",
            "user_id": owner_user.id,
            "is_public": False
        }
        shared_write_doc = await document_repository.create_document(DocumentCreate(**shared_write_doc_data))
        
        # Create shared document (admin permission)
        shared_admin_doc_data = {
            "title": "Shared Admin Document",
            "content": "This is a document shared with admin permission",
            "user_id": owner_user.id,
            "is_public": False
        }
        shared_admin_doc = await document_repository.create_document(DocumentCreate(**shared_admin_doc_data))
        
        # Share documents with collaborator
        read_permission = DocumentPermissionCreate(
            document_id=shared_read_doc.id,
            user_id=collaborator_user.id,
            permission_level="read"
        )
        await document_repository.create_document_permission(read_permission)
        
        write_permission = DocumentPermissionCreate(
            document_id=shared_write_doc.id,
            user_id=collaborator_user.id,
            permission_level="write"
        )
        await document_repository.create_document_permission(write_permission)
        
        admin_permission = DocumentPermissionCreate(
            document_id=shared_admin_doc.id,
            user_id=collaborator_user.id,
            permission_level="admin"
        )
        await document_repository.create_document_permission(admin_permission)
        
        # Return documents
        yield {
            "private_doc": private_doc,
            "public_doc": public_doc,
            "shared_read_doc": shared_read_doc,
            "shared_write_doc": shared_write_doc,
            "shared_admin_doc": shared_admin_doc
        }
        
        # Clean up - delete documents
        await document_repository.delete_document(private_doc.id)
        await document_repository.delete_document(public_doc.id)
        await document_repository.delete_document(shared_read_doc.id)
        await document_repository.delete_document(shared_write_doc.id)
        await document_repository.delete_document(shared_admin_doc.id)
    finally:
        # Reset database context
        await db.execute(text("SET app.current_user_id = NULL"))
        await db.close()


class TestDatabasePermissions:
    """Tests for database-level permissions (Row Level Security)"""
    
    @pytest.mark.asyncio
    async def test_owner_access(self, test_users, test_documents):
        """Test that the owner can access their own documents"""
        owner_user, _, _ = test_users
        
        # Get database session
        db = await anext(get_db())
        
        try:
            # Set database context to owner user
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            
            # Create document repository
            document_repository = DocumentRepository(db)
            
            # Get all documents
            documents = await document_repository.get_all_documents()
            
            # Owner should see all their documents
            assert len(documents) == 5
            
            # Check specific documents
            private_doc = await document_repository.get_document_by_id(test_documents["private_doc"].id)
            assert private_doc is not None
            assert private_doc.title == "Private Document"
            
            public_doc = await document_repository.get_document_by_id(test_documents["public_doc"].id)
            assert public_doc is not None
            assert public_doc.title == "Public Document"
            
            shared_read_doc = await document_repository.get_document_by_id(test_documents["shared_read_doc"].id)
            assert shared_read_doc is not None
            assert shared_read_doc.title == "Shared Read Document"
            
            # Test update access
            updated_title = "Updated Private Document"
            updated_doc = await document_repository.update_document(
                test_documents["private_doc"].id,
                {"title": updated_title}
            )
            assert updated_doc is not None
            assert updated_doc.title == updated_title
            
            # Test delete access
            temp_doc_data = {
                "title": "Temporary Document",
                "content": "This document will be deleted",
                "user_id": owner_user.id,
                "is_public": False
            }
            temp_doc = await document_repository.create_document(DocumentCreate(**temp_doc_data))
            
            # Delete the document
            delete_result = await document_repository.delete_document(temp_doc.id)
            assert delete_result is True
            
            # Verify it's deleted
            deleted_doc = await document_repository.get_document_by_id(temp_doc.id)
            assert deleted_doc is None
            
        finally:
            # Reset database context
            await db.execute(text("SET app.current_user_id = NULL"))
            await db.close()
    
    @pytest.mark.asyncio
    async def test_public_document_access(self, test_users, test_documents):
        """Test that any user can access public documents"""
        _, _, unrelated_user = test_users
        
        # Get database session
        db = await anext(get_db())
        
        try:
            # Set database context to unrelated user
            await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
            
            # Create document repository
            document_repository = DocumentRepository(db)
            
            # Get all documents
            documents = await document_repository.get_all_documents()
            
            # Unrelated user should only see public documents
            assert len(documents) == 1
            assert documents[0].title == "Public Document"
            
            # Check specific documents
            private_doc = await document_repository.get_document_by_id(test_documents["private_doc"].id)
            assert private_doc is None  # Should not be accessible
            
            public_doc = await document_repository.get_document_by_id(test_documents["public_doc"].id)
            assert public_doc is not None
            assert public_doc.title == "Public Document"
            
            shared_read_doc = await document_repository.get_document_by_id(test_documents["shared_read_doc"].id)
            assert shared_read_doc is None  # Should not be accessible
            
            # Test update access (should fail)
            try:
                updated_doc = await document_repository.update_document(
                    test_documents["public_doc"].id,
                    {"title": "Attempted Update"}
                )
                assert False, "Should not be able to update public document"
            except Exception:
                # Expected to fail
                pass
            
            # Verify document was not updated
            public_doc = await document_repository.get_document_by_id(test_documents["public_doc"].id)
            assert public_doc.title == "Public Document"
            
        finally:
            # Reset database context
            await db.execute(text("SET app.current_user_id = NULL"))
            await db.close()
    
    @pytest.mark.asyncio
    async def test_shared_document_access(self, test_users, test_documents):
        """Test access to documents shared with different permission levels"""
        _, collaborator_user, _ = test_users
        
        # Get database session
        db = await anext(get_db())
        
        try:
            # Set database context to collaborator user
            await db.execute(text(f"SET app.current_user_id = '{collaborator_user.id}'"))
            
            # Create document repository
            document_repository = DocumentRepository(db)
            
            # Get all documents
            documents = await document_repository.get_all_documents()
            
            # Collaborator should see public document and shared documents
            assert len(documents) == 4  # Public + 3 shared docs
            
            # Check specific documents
            private_doc = await document_repository.get_document_by_id(test_documents["private_doc"].id)
            assert private_doc is None  # Should not be accessible
            
            public_doc = await document_repository.get_document_by_id(test_documents["public_doc"].id)
            assert public_doc is not None
            assert public_doc.title == "Public Document"
            
            shared_read_doc = await document_repository.get_document_by_id(test_documents["shared_read_doc"].id)
            assert shared_read_doc is not None
            assert shared_read_doc.title == "Shared Read Document"
            
            shared_write_doc = await document_repository.get_document_by_id(test_documents["shared_write_doc"].id)
            assert shared_write_doc is not None
            assert shared_write_doc.title == "Shared Write Document"
            
            shared_admin_doc = await document_repository.get_document_by_id(test_documents["shared_admin_doc"].id)
            assert shared_admin_doc is not None
            assert shared_admin_doc.title == "Shared Admin Document"
            
            # Test update access on read-only document (should fail)
            try:
                updated_doc = await document_repository.update_document(
                    test_documents["shared_read_doc"].id,
                    {"title": "Attempted Update"}
                )
                assert False, "Should not be able to update read-only document"
            except Exception:
                # Expected to fail
                pass
            
            # Test update access on write-permission document (should succeed)
            updated_title = "Updated Shared Write Document"
            updated_doc = await document_repository.update_document(
                test_documents["shared_write_doc"].id,
                {"title": updated_title}
            )
            assert updated_doc is not None
            assert updated_doc.title == updated_title
            
            # Test update access on admin-permission document (should succeed)
            updated_title = "Updated Shared Admin Document"
            updated_doc = await document_repository.update_document(
                test_documents["shared_admin_doc"].id,
                {"title": updated_title}
            )
            assert updated_doc is not None
            assert updated_doc.title == updated_title
            
        finally:
            # Reset database context
            await db.execute(text("SET app.current_user_id = NULL"))
            await db.close()
    
    @pytest.mark.asyncio
    async def test_document_permission_management(self, test_users, test_documents):
        """Test creating, updating, and revoking document permissions"""
        owner_user, collaborator_user, unrelated_user = test_users
        
        # Get database session
        db = await anext(get_db())
        
        try:
            # Set database context to owner user
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            
            # Create document repository
            document_repository = DocumentRepository(db)
            
            # Create a new document for testing permissions
            test_doc_data = {
                "title": "Permission Test Document",
                "content": "This document is for testing permissions",
                "user_id": owner_user.id,
                "is_public": False
            }
            test_doc = await document_repository.create_document(DocumentCreate(**test_doc_data))
            
            # Initially, unrelated user should not be able to access the document
            await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
            unrelated_access = await document_repository.get_document_by_id(test_doc.id)
            assert unrelated_access is None
            
            # Grant read permission to unrelated user
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            read_permission = DocumentPermissionCreate(
                document_id=test_doc.id,
                user_id=unrelated_user.id,
                permission_level="read"
            )
            await document_repository.create_document_permission(read_permission)
            
            # Now unrelated user should be able to read the document
            await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
            unrelated_access = await document_repository.get_document_by_id(test_doc.id)
            assert unrelated_access is not None
            assert unrelated_access.title == "Permission Test Document"
            
            # But should not be able to update it
            try:
                updated_doc = await document_repository.update_document(
                    test_doc.id,
                    {"title": "Attempted Update"}
                )
                assert False, "Should not be able to update with read permission"
            except Exception:
                # Expected to fail
                pass
            
            # Upgrade to write permission
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            write_permission = DocumentPermissionCreate(
                document_id=test_doc.id,
                user_id=unrelated_user.id,
                permission_level="write"
            )
            # This will update the existing permission
            await document_repository.create_document_permission(write_permission)
            
            # Now unrelated user should be able to update the document
            await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
            updated_title = "Updated by Unrelated User"
            updated_doc = await document_repository.update_document(
                test_doc.id,
                {"title": updated_title}
            )
            assert updated_doc is not None
            assert updated_doc.title == updated_title
            
            # Revoke permission
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            await document_repository.delete_document_permission(test_doc.id, unrelated_user.id)
            
            # Now unrelated user should not be able to access the document again
            await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
            unrelated_access = await document_repository.get_document_by_id(test_doc.id)
            assert unrelated_access is None
            
            # Clean up - delete test document
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            await document_repository.delete_document(test_doc.id)
            
        finally:
            # Reset database context
            await db.execute(text("SET app.current_user_id = NULL"))
            await db.close()
    
    @pytest.mark.asyncio
    async def test_document_chunks_access(self, test_users, test_documents):
        """Test that chunk access follows document access permissions"""
        owner_user, collaborator_user, unrelated_user = test_users
        
        # Get database session
        db = await anext(get_db())
        
        try:
            # Set database context to owner user
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            
            # Create document repository
            document_repository = DocumentRepository(db)
            
            # Create a document with chunks
            test_doc_data = {
                "title": "Document with Chunks",
                "content": "This document has multiple chunks for testing",
                "user_id": owner_user.id,
                "is_public": False
            }
            test_doc = await document_repository.create_document(DocumentCreate(**test_doc_data))
            
            # Add chunks to the document (directly using SQL for simplicity)
            for i in range(3):
                await db.execute(text(
                    f"""
                    INSERT INTO chunks (id, document_id, content, chunk_index, metadata)
                    VALUES ('{uuid.uuid4()}', '{test_doc.id}', 'Chunk {i} content', {i}, '{{"index": {i}}}'::jsonb)
                    """
                ))
            await db.commit()
            
            # Owner should see all chunks
            chunks_query = text(f"SELECT * FROM chunks WHERE document_id = '{test_doc.id}'")
            result = await db.execute(chunks_query)
            owner_chunks = result.fetchall()
            assert len(owner_chunks) == 3
            
            # Unrelated user should not see any chunks
            await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
            result = await db.execute(chunks_query)
            unrelated_chunks = result.fetchall()
            assert len(unrelated_chunks) == 0
            
            # Share document with collaborator
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            read_permission = DocumentPermissionCreate(
                document_id=test_doc.id,
                user_id=collaborator_user.id,
                permission_level="read"
            )
            await document_repository.create_document_permission(read_permission)
            
            # Collaborator should now see all chunks
            await db.execute(text(f"SET app.current_user_id = '{collaborator_user.id}'"))
            result = await db.execute(chunks_query)
            collaborator_chunks = result.fetchall()
            assert len(collaborator_chunks) == 3
            
            # Make document public
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            await document_repository.update_document(test_doc.id, {"is_public": True})
            
            # Now unrelated user should see all chunks
            await db.execute(text(f"SET app.current_user_id = '{unrelated_user.id}'"))
            result = await db.execute(chunks_query)
            unrelated_chunks = result.fetchall()
            assert len(unrelated_chunks) == 3
            
            # Clean up - delete test document
            await db.execute(text(f"SET app.current_user_id = '{owner_user.id}'"))
            await document_repository.delete_document(test_doc.id)
            
        finally:
            # Reset database context
            await db.execute(text("SET app.current_user_id = NULL"))
            await db.close()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])