from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.db.dependencies import get_db
from app.db.models import DocumentPermission
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.notification_repository import NotificationRepository
from app.db.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.document import DocumentInfo
from app.core.security import get_current_user
from app.core.permissions import has_permission, PERMISSION_SHARE

router = APIRouter()


class ShareDocumentRequest(BaseModel):
    """Request model for sharing a document"""
    user_id: str
    permission_level: str  # 'read', 'write', 'admin'


class DocumentCollaborator(BaseModel):
    """Model for document collaborator information"""
    user_id: str
    username: str
    permission_level: str
    shared_at: str


@router.post("/documents/{document_id}/share", status_code=status.HTTP_201_CREATED)
async def share_document(
    document_id: str,
    share_request: ShareDocumentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Share a document with another user
    
    Args:
        document_id: Document ID
        share_request: Share request with user_id and permission_level
        
    Returns:
        Success message
    """
    # Validate permission level
    valid_permissions = ["read", "write", "admin"]
    if share_request.permission_level not in valid_permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission level. Must be one of: {', '.join(valid_permissions)}"
        )
    
    # Get document
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    # Check if user has permission to share the document
    # User must be the owner or have admin permission on the document
    can_share = False
    
    # Check if user is the owner
    if str(document.user_id) == current_user.id:
        can_share = True
    else:
        # Check if user has admin permission on the document
        permission = await doc_repo.get_document_permission(document_id, current_user.id)
        if permission and permission.permission_level == "admin":
            can_share = True
        # Check if user has share permission through roles
        elif await has_permission(PERMISSION_SHARE)(current_user, db):
            can_share = True
    
    if not can_share:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to share this document"
        )
    
    # Share document
    try:
        await doc_repo.share_document(
            document_id=document_id,
            user_id=share_request.user_id,
            permission_level=share_request.permission_level
        )
        
        # Create notification for the user
        notification_repo = NotificationRepository(db)
        user_repo = UserRepository(db)
        
        # Get the target user's information
        target_user = await user_repo.get_by_id(share_request.user_id)
        if not target_user:
            # If user not found, still return success but don't create notification
            return {"message": "Document shared successfully, but user not found for notification"}
        
        # Create notification
        await notification_repo.create_document_shared_notification(
            user_id=share_request.user_id,
            document_id=document_id,
            document_name=document.filename,
            shared_by_username=current_user.username,
            permission_level=share_request.permission_level
        )
        
        return {"message": "Document shared successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/documents/{document_id}/share/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_document_access(
    document_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke a user's access to a document
    
    Args:
        document_id: Document ID
        user_id: User ID to revoke access from
        
    Returns:
        No content
    """
    # Get document
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    # Check if user has permission to revoke access
    # User must be the owner or have admin permission on the document
    can_revoke = False
    
    # Check if user is the owner
    if str(document.user_id) == current_user.id:
        can_revoke = True
    else:
        # Check if user has admin permission on the document
        permission = await doc_repo.get_document_permission(document_id, current_user.id)
        if permission and permission.permission_level == "admin":
            can_revoke = True
        # Check if user has share permission through roles
        elif await has_permission(PERMISSION_SHARE)(current_user, db):
            can_revoke = True
    
    if not can_revoke:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to revoke access to this document"
        )
    
    # Don't allow revoking access from the owner
    if str(document.user_id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke access from the document owner"
        )
    
    # Revoke access
    success = await doc_repo.revoke_document_access(document_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} does not have access to this document"
        )
    
    return None


@router.get("/documents/{document_id}/collaborators", response_model=List[DocumentCollaborator])
async def get_document_collaborators(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all collaborators for a document
    
    Args:
        document_id: Document ID
        
    Returns:
        List of collaborators
    """
    # Get document
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    # Check if user has permission to view collaborators
    # User must have at least read access to the document
    has_access = False
    
    # Check if user is the owner
    if str(document.user_id) == current_user.id:
        has_access = True
    else:
        # Check if user has permission on the document
        permission = await doc_repo.get_document_permission(document_id, current_user.id)
        if permission:
            has_access = True
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this document's collaborators"
        )
    
    # Get collaborators
    collaborators = await doc_repo.get_document_collaborators(document_id)
    
    return collaborators


@router.get("/documents/shared-with-me", response_model=List[DocumentInfo])
async def get_documents_shared_with_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all documents shared with the current user
    
    Returns:
        List of documents shared with the current user
    """
    doc_repo = DocumentRepository(db)
    documents = await doc_repo.get_documents_shared_with_user(current_user.id)
    
    return documents


@router.get("/documents/shared-by-me", response_model=List[DocumentInfo])
async def get_documents_shared_by_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all documents shared by the current user
    
    Returns:
        List of documents shared by the current user
    """
    doc_repo = DocumentRepository(db)
    documents = await doc_repo.get_documents_shared_by_user(current_user.id)
    
    return documents