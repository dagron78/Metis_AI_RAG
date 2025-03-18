from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.db.models import Document, Chunk, Tag, Folder, document_tags
from app.db.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """
    Repository for Document model
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Document)
    
    def create_document(self, 
                       filename: str, 
                       content: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None, 
                       tags: Optional[List[str]] = None, 
                       folder: str = "/") -> Document:
        """
        Create a new document
        
        Args:
            filename: Document filename
            content: Document content
            metadata: Document metadata
            tags: List of tag names
            folder: Document folder path
            
        Returns:
            Created document
        """
        # Ensure folder exists
        self._ensure_folder_exists(folder)
        
        # Create document
        document = Document(
            filename=filename,
            content=content,
            metadata=metadata or {},
            folder=folder,
            uploaded=datetime.utcnow(),
            processing_status="pending"
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
                       document_id: UUID, 
                       filename: Optional[str] = None, 
                       content: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None, 
                       folder: Optional[str] = None) -> Optional[Document]:
        """
        Update a document
        
        Args:
            document_id: Document ID
            filename: New filename
            content: New content
            metadata: New metadata
            folder: New folder path
            
        Returns:
            Updated document if found, None otherwise
        """
        document = self.get_by_id(document_id)
        if not document:
            return None
        
        # Update fields if provided
        if filename:
            document.filename = filename
        
        if content is not None:  # Allow empty content
            document.content = content
        
        if metadata:
            # Merge metadata instead of replacing
            document.metadata = {**document.metadata, **metadata}
        
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
    
    def update_document_tags(self, document_id: UUID, tags: List[str]) -> Optional[Document]:
        """
        Update document tags
        
        Args:
            document_id: Document ID
            tags: New list of tag names
            
        Returns:
            Updated document if found, None otherwise
        """
        document = self.get_by_id(document_id)
        if not document:
            return None
        
        # Remove existing tags
        document.tags = []
        self.session.flush()
        
        # Add new tags
        self._add_tags_to_document(document, tags)
        
        self.session.commit()
        self.session.refresh(document)
        return document
    
    def get_document_with_chunks(self, document_id: UUID) -> Optional[Document]:
        """
        Get a document with its chunks
        
        Args:
            document_id: Document ID
            
        Returns:
            Document with chunks if found, None otherwise
        """
        return self.session.query(Document).filter(Document.id == document_id).first()
    
    def search_documents(self, 
                        query: str, 
                        tags: Optional[List[str]] = None, 
                        folder: Optional[str] = None, 
                        skip: int = 0, 
                        limit: int = 100) -> List[Document]:
        """
        Search documents by content, filename, or metadata
        
        Args:
            query: Search query
            tags: Filter by tags
            folder: Filter by folder
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching documents
        """
        # Base query
        db_query = self.session.query(Document)
        
        # Apply search filter
        if query:
            search_filter = or_(
                Document.filename.ilike(f"%{query}%"),
                Document.content.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
        
        # Apply tag filter
        if tags:
            tag_subquery = (
                self.session.query(document_tags.c.document_id)
                .join(Tag, Tag.id == document_tags.c.tag_id)
                .filter(Tag.name.in_(tags))
                .group_by(document_tags.c.document_id)
                .having(func.count(document_tags.c.tag_id) == len(tags))
                .subquery()
            )
            db_query = db_query.join(tag_subquery, Document.id == tag_subquery.c.document_id)
        
        # Apply folder filter
        if folder:
            db_query = db_query.filter(Document.folder == folder)
        
        # Apply pagination
        return db_query.order_by(Document.uploaded.desc()).offset(skip).limit(limit).all()
    
    def get_document_by_filename(self, filename: str, folder: str = "/") -> Optional[Document]:
        """
        Get a document by filename and folder
        
        Args:
            filename: Document filename
            folder: Document folder path
            
        Returns:
            Document if found, None otherwise
        """
        return self.session.query(Document).filter(
            and_(Document.filename == filename, Document.folder == folder)
        ).first()
    
    def get_documents_by_folder(self, folder: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get documents in a folder
        
        Args:
            folder: Folder path
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of documents in the folder
        """
        return self.session.query(Document).filter(
            Document.folder == folder
        ).order_by(Document.uploaded.desc()).offset(skip).limit(limit).all()
    
    def get_documents_by_tag(self, tag: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get documents with a specific tag
        
        Args:
            tag: Tag name
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of documents with the tag
        """
        return self.session.query(Document).join(
            document_tags, Document.id == document_tags.c.document_id
        ).join(
            Tag, Tag.id == document_tags.c.tag_id
        ).filter(
            Tag.name == tag
        ).order_by(Document.uploaded.desc()).offset(skip).limit(limit).all()
    
    def update_processing_status(self, document_id: UUID, status: str, strategy: Optional[str] = None) -> Optional[Document]:
        """
        Update document processing status
        
        Args:
            document_id: Document ID
            status: New processing status
            strategy: Processing strategy used
            
        Returns:
            Updated document if found, None otherwise
        """
        document = self.get_by_id(document_id)
        if not document:
            return None
        
        document.processing_status = status
        if strategy:
            document.processing_strategy = strategy
        
        self.session.commit()
        self.session.refresh(document)
        return document
    
    def _ensure_folder_exists(self, folder_path: str) -> Folder:
        """
        Ensure a folder exists, creating it and its parents if needed
        
        Args:
            folder_path: Folder path
            
        Returns:
            Folder object
        """
        # Root folder always exists
        if folder_path == "/":
            folder = self.session.query(Folder).filter(Folder.path == "/").first()
            if not folder:
                folder = Folder(path="/", name="Root", parent_path=None)
                self.session.add(folder)
                self.session.flush()
            return folder
        
        # Check if folder exists
        folder = self.session.query(Folder).filter(Folder.path == folder_path).first()
        if folder:
            return folder
        
        # Create folder and its parents
        parts = folder_path.strip("/").split("/")
        current_path = "/"
        parent_path = None
        
        # Ensure root folder exists
        self._ensure_folder_exists("/")
        
        # Create each folder in the path
        for i, part in enumerate(parts):
            current_path = f"{current_path}{part}/" if i > 0 else f"/{part}/"
            
            folder = self.session.query(Folder).filter(Folder.path == current_path).first()
            if not folder:
                folder = Folder(
                    path=current_path,
                    name=part,
                    parent_path=parent_path,
                    document_count=0,
                    created_at=datetime.utcnow()
                )
                self.session.add(folder)
                self.session.flush()
            
            parent_path = current_path
        
        return folder
    
    def _add_tags_to_document(self, document: Document, tag_names: List[str]) -> None:
        """
        Add tags to a document, creating tags if they don't exist
        
        Args:
            document: Document object
            tag_names: List of tag names
        """
        for tag_name in tag_names:
            # Get or create tag
            tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, created_at=datetime.utcnow(), usage_count=1)
                self.session.add(tag)
                self.session.flush()
            else:
                tag.usage_count += 1
            
            # Add tag to document
            document.tags.append(tag)