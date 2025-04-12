from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, and_, select, exists, String

from app.db.models import Document, Chunk, Tag, Folder, document_tags, DocumentPermission, User
from app.db.repositories.base import BaseRepository


class BasicDocumentRepository(BaseRepository[Document]):
    """
    Repository for Document model with async methods for developer mode
    """
    
    def __init__(self, session: AsyncSession, user_id: Optional[UUID] = None):
        super().__init__(session, Document)
        self.user_id = user_id
    
    async def create_document(self,
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
        await self._ensure_folder_exists(folder)
        
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
            doc_metadata=metadata or {},  # Use doc_metadata instead of metadata
            folder=folder,
            uploaded=datetime.utcnow(),
            processing_status="pending",
            user_id=str(self.user_id) if self.user_id else None,  # Convert UUID to string for SQLite
            is_public=is_public,
            organization_id=organization_id
        )
        
        self.session.add(document)
        await self.session.flush()  # Flush to get the document ID
        
        # Add tags if provided
        if tags:
            await self._add_tags_to_document(document, tags)
        
        # Update folder document count
        stmt = select(Folder).where(Folder.path == folder)
        result = await self.session.execute(stmt)
        folder_obj = result.scalars().first()
        
        if folder_obj:
            folder_obj.document_count += 1
        
        await self.session.commit()
        await self.session.refresh(document)
        return document
    
    async def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        Get all documents accessible to the current user
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of documents
        """
        stmt = select(Document)
        
        # Apply permission filtering
        if self.user_id:
            # Documents owned by the user
            user_filter = Document.user_id == str(self.user_id) if self.user_id else None
            
            # Documents shared with the user
            shared_subquery = select(DocumentPermission.document_id).where(
                DocumentPermission.user_id == str(self.user_id) if self.user_id else None
            ).subquery()
            shared_filter = Document.id.in_(shared_subquery)
            
            # Public documents
            public_filter = Document.is_public == True
            
            stmt = stmt.where(or_(user_filter, shared_filter, public_filter))
        else:
            # Only public documents for anonymous users
            stmt = stmt.where(Document.is_public == True)
        
        stmt = stmt.order_by(Document.uploaded.desc())
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.session.execute(stmt)
        documents = result.scalars().all()
        
        return documents
    
    async def get_document(self, document_id: Union[str, UUID]) -> Optional[Document]:
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
        
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        document = result.scalars().first()
        
        if document:
            document.last_accessed = datetime.utcnow()
            await self.session.commit()
        
        return document
    
    async def delete_document(self, document_id: Union[str, UUID]) -> bool:
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
        
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        document = result.scalars().first()
        
        if not document:
            return False
        
        # Update folder document count
        folder_stmt = select(Folder).where(Folder.path == document.folder)
        folder_result = await self.session.execute(folder_stmt)
        folder_obj = folder_result.scalars().first()
        
        if folder_obj:
            folder_obj.document_count -= 1
        
        # Delete document (and chunks via cascade)
        await self.session.delete(document)
        await self.session.commit()
        
        return True
    
    async def update_document_tags(self, document_id: Union[str, UUID], tags: List[str]) -> Optional[Document]:
        """
        Update document tags
        
        Args:
            document_id: Document ID
            tags: List of tag names
            
        Returns:
            Updated document or None if not found
        """
        document = await self.get_document(document_id)
        if not document:
            return None
        
        # Clear existing tags
        document.tags = []
        await self.session.flush()
        
        # Add new tags
        await self._add_tags_to_document(document, tags)
        
        await self.session.commit()
        await self.session.refresh(document)
        
        return document
    
    async def update_document_folder(self, document_id: Union[str, UUID], folder: str) -> Optional[Document]:
        """
        Update document folder
        
        Args:
            document_id: Document ID
            folder: New folder path
            
        Returns:
            Updated document or None if not found
        """
        document = await self.get_document(document_id)
        if not document:
            return None
        
        # Ensure new folder exists
        await self._ensure_folder_exists(folder)
        
        # Update folder document counts
        old_folder_stmt = select(Folder).where(Folder.path == document.folder)
        old_folder_result = await self.session.execute(old_folder_stmt)
        old_folder = old_folder_result.scalars().first()
        
        if old_folder:
            old_folder.document_count -= 1
        
        new_folder_stmt = select(Folder).where(Folder.path == folder)
        new_folder_result = await self.session.execute(new_folder_stmt)
        new_folder = new_folder_result.scalars().first()
        
        if new_folder:
            new_folder.document_count += 1
        
        # Update document folder
        document.folder = folder
        
        await self.session.commit()
        await self.session.refresh(document)
        
        return document
    
    async def _add_tags_to_document(self, document: Document, tags: List[str]) -> None:
        """
        Add tags to a document (helper method)
        
        Args:
            document: Document
            tags: List of tag names
        """
        for tag_name in tags:
            # Get or create tag
            tag_stmt = select(Tag).where(Tag.name == tag_name)
            tag_result = await self.session.execute(tag_stmt)
            tag = tag_result.scalars().first()
            
            if not tag:
                tag = Tag(name=tag_name)
                self.session.add(tag)
                await self.session.flush()
            
            # Add tag to document if not already present
            if tag not in document.tags:
                document.tags.append(tag)
                tag.usage_count += 1
    
    async def _ensure_folder_exists(self, folder_path: str) -> None:
        """
        Ensure a folder exists (create if not)
        
        Args:
            folder_path: Folder path
        """
        # Skip for root folder
        if folder_path == "/":
            # Ensure root folder exists
            root_folder_stmt = select(Folder).where(Folder.path == "/")
            root_folder_result = await self.session.execute(root_folder_stmt)
            root_folder = root_folder_result.scalars().first()
            
            if not root_folder:
                root_folder = Folder(path="/", name="Root", parent_path=None)
                self.session.add(root_folder)
                await self.session.flush()
            return
        
        # Check if folder already exists
        folder_stmt = select(Folder).where(Folder.path == folder_path)
        folder_result = await self.session.execute(folder_stmt)
        folder = folder_result.scalars().first()
        
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
        await self._ensure_folder_exists(parent_path)
        
        # Create folder
        folder = Folder(
            path=folder_path,
            name=name,
            parent_path=parent_path
        )
        
        self.session.add(folder)
        await self.session.flush()