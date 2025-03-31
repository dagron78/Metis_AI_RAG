from typing import List, Optional, Dict, Any, Union, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, select, exists, String

from app.db.models import Document, Chunk, Tag, Folder, document_tags, DocumentPermission, User
from app.db.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """
    Repository for Document model with user context and permission handling
    """
    
    def __init__(self, session: Session, user_id: Optional[UUID] = None):
        super().__init__(session, Document)
        self.user_id = user_id
    
    def create_document(self,
                       filename: str,
                       content: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None,
                       tags: Optional[List[str]] = None,
                       folder: str = "/",
                       is_public: bool = False,
                       organization_id: Optional[Union[str, UUID]] = None) -> Document:
        """
        Create a new document
        
        Args:
            filename: Document filename
            content: Document content
            metadata: Document metadata
            tags: List of tag names
            folder: Document folder path
            is_public: Whether the document is publicly accessible
            organization_id: Organization ID (if the document belongs to an organization)
            
        Returns:
            Created document
        """
        # Ensure folder exists
        self._ensure_folder_exists(folder)
        
        # Convert organization_id to UUID if provided as string
        if organization_id and isinstance(organization_id, str):
            try:
                organization_id = UUID(organization_id)
            except ValueError:
                organization_id = None
        
        # Create document
        document = Document(
            filename=filename,
            content=content,
            doc_metadata=metadata or {},  # Changed from metadata to doc_metadata
            folder=folder,
            uploaded=datetime.utcnow(),
            processing_status="pending",
            user_id=self.user_id,  # Set the user ID from context
            is_public=is_public,
            organization_id=organization_id
        )
        
        self.session.add(document)
        self.session.flush()  # Flush to get the document ID
        
        # Add tags if provided
        if tags:
            self._add_tags_to_document(document, tags)
        
        # Update folder document count
        folder_obj = self.session.query(Folder).filter(Folder.path == folder).first()
        if folder_obj:
            folder_obj.document_count += 1
        
        self.session.commit()
        self.session.refresh(document)
        return document
    
    def update_document(self, 
                        document_id: Union[str, UUID], 
                        filename: Optional[str] = None, 
                        content: Optional[str] = None, 
                        metadata: Optional[Dict[str, Any]] = None, 
                        folder: Optional[str] = None,
                        is_public: Optional[bool] = None) -> Optional[Document]:
        """
        Update a document
        
        Args:
            document_id: Document ID
            filename: New filename
            content: New content
            metadata: New metadata
            folder: New folder path
            is_public: Whether the document is publicly accessible
            
        Returns:
            Updated document or None if not found
        """
        document = self.get_document(document_id)
        if not document:
            return None
        
        # Check if user has permission to update the document
        if not self._can_modify_document(document):
            return None
        
        # Update fields if provided
        if filename:
            document.filename = filename
        
        if content is not None:  # Allow empty content
            document.content = content
        
        if metadata:
            # Merge metadata instead of replacing
            document.doc_metadata = {**document.doc_metadata, **metadata}  # Changed from metadata to doc_metadata
        
        if is_public is not None:
            document.is_public = is_public
        
        if folder and folder != document.folder:
            # Ensure new folder exists
            self._ensure_folder_exists(folder)
            
            # Update folder document counts
            old_folder = self.session.query(Folder).filter(Folder.path == document.folder).first()
            if old_folder:
                old_folder.document_count -= 1
            
            new_folder = self.session.query(Folder).filter(Folder.path == folder).first()
            if new_folder:
                new_folder.document_count += 1
            
            document.folder = folder
        
        document.last_accessed = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(document)
        return document
    
    def get_document(self, document_id: Union[str, UUID]) -> Optional[Document]:
        """
        Get a document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None if not found
        """
        if isinstance(document_id, str):
            try:
                document_id = UUID(document_id)
            except ValueError:
                return None
        
        document = self.session.query(Document).filter(Document.id == document_id).first()
        
        # Check if user has permission to view the document
        if document and not self._can_view_document(document):
            return None
        
        if document:
            document.last_accessed = datetime.utcnow()
            self.session.commit()
        
        return document
    
    def delete_document(self, document_id: Union[str, UUID]) -> bool:
        """
        Delete a document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if isinstance(document_id, str):
            try:
                document_id = UUID(document_id)
            except ValueError:
                return False
        
        document = self.session.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # Check if user has permission to delete the document
        if not self._can_delete_document(document):
            return False
        
        # Update folder document count
        folder_obj = self.session.query(Folder).filter(Folder.path == document.folder).first()
        if folder_obj:
            folder_obj.document_count -= 1
        
        # Delete document (and chunks via cascade)
        self.session.delete(document)
        self.session.commit()
        
        return True
    
    def search_documents(self, 
                         query: Optional[str] = None, 
                         folder: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         limit: int = 100,
                         offset: int = 0,
                         include_public: bool = True) -> List[Document]:
        """
        Search documents by content, filename, or metadata
        
        Args:
            query: Search query (searches in content, filename, and metadata)
            folder: Filter by folder
            tags: Filter by tags
            limit: Maximum number of results
            offset: Offset for pagination
            include_public: Whether to include public documents
            
        Returns:
            List of documents
        """
        # Start with base query
        query_obj = self.session.query(Document)
        
        # Apply filters
        filters = []
        
        # Filter by user permissions
        if self.user_id:
            # Documents owned by the user
            user_filter = Document.user_id == self.user_id
            
            # Documents shared with the user
            shared_subquery = self.session.query(DocumentPermission.document_id).filter(
                DocumentPermission.user_id == self.user_id
            ).subquery()
            shared_filter = Document.id.in_(shared_subquery)
            
            # Public documents if requested
            if include_public:
                public_filter = Document.is_public == True
                filters.append(or_(user_filter, shared_filter, public_filter))
            else:
                filters.append(or_(user_filter, shared_filter))
        else:
            # Only public documents for anonymous users
            filters.append(Document.is_public == True)
        
        if query:
            filters.append(or_(
                Document.content.ilike(f"%{query}%"),
                Document.filename.ilike(f"%{query}%"),
                func.cast(Document.doc_metadata, type_=String).ilike(f"%{query}%")  # Changed from metadata to doc_metadata
            ))
        
        if folder:
            if folder.endswith('*'):
                # Folder path prefix search
                prefix = folder[:-1]
                filters.append(Document.folder.like(f"{prefix}%"))
            else:
                # Exact folder match
                filters.append(Document.folder == folder)
        
        if tags:
            # Filter by tags using a subquery
            for tag in tags:
                tag_subquery = self.session.query(document_tags.c.document_id).join(
                    Tag, Tag.id == document_tags.c.tag_id
                ).filter(Tag.name == tag).subquery()
                
                filters.append(Document.id.in_(tag_subquery))
        
        # Apply all filters
        if filters:
            query_obj = query_obj.filter(and_(*filters))
        
        # Order by last accessed (most recent first)
        query_obj = query_obj.order_by(Document.last_accessed.desc())
        
        # Apply pagination
        query_obj = query_obj.limit(limit).offset(offset)
        
        # Execute query
        documents = query_obj.all()
        
        # Update last_accessed for all returned documents
        for doc in documents:
            doc.last_accessed = datetime.utcnow()
        
        self.session.commit()
        
        return documents
    
    def get_documents_by_folder(self, folder: str, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        Get documents by folder
        
        Args:
            folder: Folder path
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of documents
        """
        query = self.session.query(Document).filter(Document.folder == folder)
        
        # Apply permission filtering
        if self.user_id:
            # Documents owned by the user
            user_filter = Document.user_id == self.user_id
            
            # Documents shared with the user
            shared_subquery = self.session.query(DocumentPermission.document_id).filter(
                DocumentPermission.user_id == self.user_id
            ).subquery()
            shared_filter = Document.id.in_(shared_subquery)
            
            # Public documents
            public_filter = Document.is_public == True
            
            # Documents in organizations the user is a member of
            org_subquery = self.session.query(
                Document.id
            ).join(
                "organization"  # Join using the relationship name
            ).join(
                "members"  # Join using the relationship name
            ).filter(
                Document.organization_id.isnot(None),
                Document.organization_id == Document.organization.id,
                Document.organization.members.user_id == self.user_id
            ).subquery()
            org_filter = Document.id.in_(org_subquery)
            
            query = query.filter(or_(user_filter, shared_filter, public_filter, org_filter))
        else:
            # Only public documents for anonymous users
            query = query.filter(Document.is_public == True)
        
        query = query.order_by(Document.uploaded.desc())
        query = query.limit(limit).offset(offset)
        
        documents = query.all()
        
        # Update last_accessed for all returned documents
        for doc in documents:
            doc.last_accessed = datetime.utcnow()
        
        self.session.commit()
        
        return documents
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        Get all documents accessible to the current user
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of documents
        """
        query = self.session.query(Document)
        
        # Apply permission filtering
        if self.user_id:
            # Documents owned by the user
            user_filter = Document.user_id == self.user_id
            
            # Documents shared with the user
            shared_subquery = self.session.query(DocumentPermission.document_id).filter(
                DocumentPermission.user_id == self.user_id
            ).subquery()
            shared_filter = Document.id.in_(shared_subquery)
            
            # Public documents
            public_filter = Document.is_public == True
            
            # Documents in organizations the user is a member of
            org_subquery = self.session.query(
                Document.id
            ).join(
                "organization"  # Join using the relationship name
            ).join(
                "members"  # Join using the relationship name
            ).filter(
                Document.organization_id.isnot(None),
                Document.organization_id == Document.organization.id,
                Document.organization.members.user_id == self.user_id
            ).subquery()
            org_filter = Document.id.in_(org_subquery)
            
            query = query.filter(or_(user_filter, shared_filter, public_filter, org_filter))
        else:
            # Only public documents for anonymous users
            query = query.filter(Document.is_public == True)
        
        query = query.order_by(Document.uploaded.desc())
        query = query.limit(limit).offset(offset)
        
        documents = query.all()
        
        return documents
    
    def count_documents(self, folder: Optional[str] = None, tag: Optional[str] = None) -> int:
        """
        Count documents
        
        Args:
            folder: Filter by folder
            tag: Filter by tag
            
        Returns:
            Number of documents
        """
        query = self.session.query(func.count(Document.id))
        
        # Apply permission filtering
        if self.user_id:
            # Documents owned by the user
            user_filter = Document.user_id == self.user_id
            
            # Documents shared with the user
            shared_subquery = self.session.query(DocumentPermission.document_id).filter(
                DocumentPermission.user_id == self.user_id
            ).subquery()
            shared_filter = Document.id.in_(shared_subquery)
            
            # Public documents
            public_filter = Document.is_public == True
            
            # Documents in organizations the user is a member of
            org_subquery = self.session.query(
                Document.id
            ).join(
                "organization"  # Join using the relationship name
            ).join(
                "members"  # Join using the relationship name
            ).filter(
                Document.organization_id.isnot(None),
                Document.organization_id == Document.organization.id,
                Document.organization.members.user_id == self.user_id
            ).subquery()
            org_filter = Document.id.in_(org_subquery)
            
            query = query.filter(or_(user_filter, shared_filter, public_filter, org_filter))
        else:
            # Only public documents for anonymous users
            query = query.filter(Document.is_public == True)
        
        if folder:
            query = query.filter(Document.folder == folder)
        
        if tag:
            tag_subquery = self.session.query(document_tags.c.document_id).join(
                Tag, Tag.id == document_tags.c.tag_id
            ).filter(Tag.name == tag).subquery()
            
            query = query.filter(Document.id.in_(tag_subquery))
        
        return query.scalar()
    
    def get_document_chunks(self, document_id: Union[str, UUID]) -> List[Chunk]:
        """
        Get all chunks for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            List of chunks
        """
        if isinstance(document_id, str):
            try:
                document_id = UUID(document_id)
            except ValueError:
                return []
        
        # Check if user has permission to view the document
        document = self.session.query(Document).filter(Document.id == document_id).first()
        if not document or not self._can_view_document(document):
            return []
        
        return self.session.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.index).all()
    
    def update_document_chunks(self, document_id: Union[str, UUID], chunks: List[Dict[str, Any]]) -> Optional[Document]:
        """
        Update document chunks
        
        Args:
            document_id: Document ID
            chunks: List of chunk data
            
        Returns:
            Updated document or None if not found
        """
        document = self.get_document(document_id)
        if not document:
            return None
        
        # Check if user has permission to modify the document
        if not self._can_modify_document(document):
            return None
        
        # Delete existing chunks
        self.session.query(Chunk).filter(Chunk.document_id == document.id).delete()
        
        # Create new chunks
        for i, chunk_data in enumerate(chunks):
            content = chunk_data.get('content', '')
            metadata = chunk_data.get('metadata', {})
            
            chunk = Chunk(
                document_id=document.id,
                content=content,
                chunk_metadata=metadata,  # Changed from metadata to chunk_metadata
                index=i
            )
            
            self.session.add(chunk)
        
        # Update document status
        document.processing_status = "completed"
        document.last_accessed = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(document)
        
        return document
    
    def add_tags_to_document(self, document_id: Union[str, UUID], tags: List[str]) -> Optional[Document]:
        """
        Add tags to a document
        
        Args:
            document_id: Document ID
            tags: List of tag names
            
        Returns:
            Updated document or None if not found
        """
        document = self.get_document(document_id)
        if not document:
            return None
        
        # Check if user has permission to modify the document
        if not self._can_modify_document(document):
            return None
        
        self._add_tags_to_document(document, tags)
        
        self.session.commit()
        self.session.refresh(document)
        
        return document
    
    def share_document(self, document_id: Union[str, UUID], user_id: Union[str, UUID], permission_level: str = "read") -> bool:
        """
        Share a document with another user
        
        Args:
            document_id: Document ID
            user_id: User ID to share with
            permission_level: Permission level (read, write, admin)
            
        Returns:
            True if shared successfully, False otherwise
        """
        if isinstance(document_id, str):
            try:
                document_id = UUID(document_id)
            except ValueError:
                return False
        
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        # Check if document exists
        document = self.session.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # Check if user has permission to share the document
        if not self._can_share_document(document):
            return False
        
        # Check if user exists
        user_exists = self.session.query(exists().where(User.id == user_id)).scalar()
        if not user_exists:
            return False
        
        # Check if permission already exists
        existing_permission = self.session.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user_id
        ).first()
        
        if existing_permission:
            # Update existing permission
            existing_permission.permission_level = permission_level
        else:
            # Create new permission
            permission = DocumentPermission(
                document_id=document_id,
                user_id=user_id,
                permission_level=permission_level
            )
            self.session.add(permission)
        
        self.session.commit()
        return True
    
    def revoke_document_access(self, document_id: Union[str, UUID], user_id: Union[str, UUID]) -> bool:
        """
        Revoke a user's access to a document
        
        Args:
            document_id: Document ID
            user_id: User ID to revoke access from
            
        Returns:
            True if revoked successfully, False otherwise
        """
        if isinstance(document_id, str):
            try:
                document_id = UUID(document_id)
            except ValueError:
                return False
        
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        # Check if document exists
        document = self.session.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # Check if user has permission to modify document sharing
        if not self._can_share_document(document):
            return False
        
        # Delete permission
        result = self.session.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user_id
        ).delete()
        
        self.session.commit()
        return result > 0
    
    def get_document_permissions(self, document_id: Union[str, UUID]) -> List[Dict[str, Any]]:
        """
        Get all permissions for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            List of permissions with user information
        """
        if isinstance(document_id, str):
            try:
                document_id = UUID(document_id)
            except ValueError:
                return []
        
        # Check if document exists
        document = self.session.query(Document).filter(Document.id == document_id).first()
        if not document:
            return []
        
        # Check if user has permission to view document permissions
        if not self._can_view_permissions(document):
            return []
        
        # Get permissions with user information
        permissions = self.session.query(
            DocumentPermission, User.username, User.email
        ).join(
            User, User.id == DocumentPermission.user_id
        ).filter(
            DocumentPermission.document_id == document_id
        ).all()
        
        return [
            {
                "user_id": str(perm.DocumentPermission.user_id),
                "username": username,
                "email": email,
                "permission_level": perm.DocumentPermission.permission_level,
                "created_at": perm.DocumentPermission.created_at
            }
            for perm, username, email in permissions
        ]
    
    def get_shared_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        Get documents shared with the current user
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of documents
        """
        if not self.user_id:
            return []
        
        # Get documents shared with the user
        shared_subquery = self.session.query(DocumentPermission.document_id).filter(
            DocumentPermission.user_id == self.user_id
        ).subquery()
        
        query = self.session.query(Document).filter(Document.id.in_(shared_subquery))
        query = query.order_by(Document.last_accessed.desc())
        query = query.limit(limit).offset(offset)
        
        documents = query.all()
        
        # Update last_accessed for all returned documents
        for doc in documents:
            doc.last_accessed = datetime.utcnow()
        
        self.session.commit()
        
        return documents
    
    def _can_view_document(self, document: Document) -> bool:
        """
        Check if the current user can view a document
        
        Args:
            document: Document to check
            
        Returns:
            True if user can view the document, False otherwise
        """
        # Public documents can be viewed by anyone
        if document.is_public:
            return True
        
        # If no user context, only public documents can be viewed
        if not self.user_id:
            return False
        
        # Document owner can view
        if document.user_id == self.user_id:
            return True
        
        # Check if document is shared with user
        permission = self.session.query(DocumentPermission).filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == self.user_id
        ).first()
        
        return permission is not None
    
    def _can_modify_document(self, document: Document) -> bool:
        """
        Check if the current user can modify a document
        
        Args:
            document: Document to check
            
        Returns:
            True if user can modify the document, False otherwise
        """
        # If no user context, no modifications allowed
        if not self.user_id:
            return False
        
        # Document owner can modify
        if document.user_id == self.user_id:
            return True
        
        # Check if document is shared with user with write or admin permission
        permission = self.session.query(DocumentPermission).filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == self.user_id,
            DocumentPermission.permission_level.in_(["write", "admin"])
        ).first()
        
        return permission is not None
    
    def _can_delete_document(self, document: Document) -> bool:
        """
        Check if the current user can delete a document
        
        Args:
            document: Document to check
            
        Returns:
            True if user can delete the document, False otherwise
        """
        # If no user context, no deletions allowed
        if not self.user_id:
            return False
        
        # Document owner can delete
        if document.user_id == self.user_id:
            return True
        
        # Check if document is shared with user with admin permission
        permission = self.session.query(DocumentPermission).filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == self.user_id,
            DocumentPermission.permission_level == "admin"
        ).first()
        
        return permission is not None
    
    def _can_share_document(self, document: Document) -> bool:
        """
        Check if the current user can share a document
        
        Args:
            document: Document to check
            
        Returns:
            True if user can share the document, False otherwise
        """
        # Same as delete permissions - only owner or admin can share
        return self._can_delete_document(document)
    
    def _can_view_permissions(self, document: Document) -> bool:
        """
        Check if the current user can view document permissions
        
        Args:
            document: Document to check
            
        Returns:
            True if user can view document permissions, False otherwise
        """
        # Same as share permissions - only owner or admin can view permissions
        return self._can_share_document(document)
    
    def _add_tags_to_document(self, document: Document, tags: List[str]) -> None:
        """
        Add tags to a document (helper method)
        
        Args:
            document: Document
            tags: List of tag names
        """
        for tag_name in tags:
            # Get or create tag
            tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                self.session.add(tag)
                self.session.flush()
            
            # Add tag to document if not already present
            if tag not in document.tags:
                document.tags.append(tag)
                tag.usage_count += 1
    
    def _ensure_folder_exists(self, folder_path: str) -> None:
        """
        Ensure a folder exists (create if not)
        
        Args:
            folder_path: Folder path
        """
        # Skip for root folder
        if folder_path == "/":
            # Ensure root folder exists
            root_folder = self.session.query(Folder).filter(Folder.path == "/").first()
            if not root_folder:
                root_folder = Folder(path="/", name="Root", parent_path=None)
                self.session.add(root_folder)
                self.session.flush()
            return
        
        # Check if folder already exists
        folder = self.session.query(Folder).filter(Folder.path == folder_path).first()
        if folder:
            return
        
        # Split path components
        parts = folder_path.strip('/').split('/')
        name = parts[-1]  # Last component is the folder name
        
        # Determine parent path
        if len(parts) == 1:
            parent_path = "/"
        else:
            parent_path = "/" + "/".join(parts[:-1])
        
        # Ensure parent folder exists
        self._ensure_folder_exists(parent_path)
        
        # Create folder
        folder = Folder(
            path=folder_path,
            name=name,
            parent_path=parent_path
        )
        
        self.session.add(folder)
        self.session.flush()
        
    def get_organization_documents(self, organization_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[Document]:
        """
        Get all documents in an organization
        
        Args:
            organization_id: Organization ID
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of documents
        """
        # Convert string ID to UUID if needed
        if isinstance(organization_id, str):
            try:
                organization_id = UUID(organization_id)
            except ValueError:
                return []
        
        query = self.session.query(Document).filter(Document.organization_id == organization_id)
        
        # Apply permission filtering
        if self.user_id:
            # Check if user is a member of the organization
            is_member_subquery = self.session.query(
                func.count()
            ).filter(
                and_(
                    Document.organization_id == organization_id,
                    Document.organization.has(
                        members=self.user_id
                    )
                )
            ).scalar_subquery()
            
            # If user is not a member, they can only see their own documents or documents shared with them
            user_filter = Document.user_id == self.user_id
            
            # Documents shared with the user
            shared_subquery = self.session.query(DocumentPermission.document_id).filter(
                DocumentPermission.user_id == self.user_id
            ).subquery()
            shared_filter = Document.id.in_(shared_subquery)
            
            # Public documents
            public_filter = Document.is_public == True
            
            # User is a member of the organization
            member_filter = is_member_subquery > 0
            
            query = query.filter(or_(user_filter, shared_filter, public_filter, member_filter))
        else:
            # Only public documents for anonymous users
            query = query.filter(Document.is_public == True)
        
        query = query.order_by(Document.uploaded.desc())
        query = query.limit(limit).offset(offset)
        
        documents = query.all()
        
        return documents