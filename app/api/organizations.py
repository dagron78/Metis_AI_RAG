from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.db.repositories.organization_repository import OrganizationRepository
from app.models.organization import Organization, OrganizationCreate, OrganizationUpdate, OrganizationMember
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter()


@router.get("/organizations", response_model=List[Organization])
async def get_organizations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all organizations the current user is a member of
    
    Args:
        skip: Number of organizations to skip
        limit: Maximum number of organizations to return
        
    Returns:
        List of organizations
    """
    org_repo = OrganizationRepository(db)
    organizations = await org_repo.get_user_organizations(current_user.id)
    
    # Apply pagination
    start = min(skip, len(organizations))
    end = min(start + limit, len(organizations))
    
    return organizations[start:end]


@router.post("/organizations", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization with the current user as owner
    
    Args:
        organization: Organization creation data
        
    Returns:
        Created organization
    """
    try:
        org_repo = OrganizationRepository(db)
        created_org = await org_repo.create_organization(organization, current_user.id)
        return created_org
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/organizations/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get an organization by ID
    
    Args:
        organization_id: Organization ID
        
    Returns:
        Organization if found
    """
    org_repo = OrganizationRepository(db)
    
    # Check if user is a member of the organization
    is_member = await org_repo.user_is_member(organization_id, current_user.id)
    if not is_member and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this organization"
        )
    
    organization = await org_repo.get_by_id(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {organization_id} not found"
        )
    
    return organization


@router.put("/organizations/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: str,
    organization_update: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an organization
    
    Args:
        organization_id: Organization ID
        organization_update: Organization update data
        
    Returns:
        Updated organization
    """
    org_repo = OrganizationRepository(db)
    
    # Check if user is an admin or owner of the organization
    is_admin_or_owner = await org_repo.user_is_admin_or_owner(organization_id, current_user.id)
    if not is_admin_or_owner and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this organization"
        )
    
    try:
        updated_org = await org_repo.update_organization(organization_id, organization_update)
        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with ID {organization_id} not found"
            )
        
        return updated_org
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an organization
    
    Args:
        organization_id: Organization ID
    """
    org_repo = OrganizationRepository(db)
    
    # Check if user is an owner of the organization
    is_owner = await org_repo.user_is_owner(organization_id, current_user.id)
    if not is_owner and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this organization"
        )
    
    success = await org_repo.delete_organization(organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {organization_id} not found"
        )
    
    return None


@router.get("/organizations/{organization_id}/members", response_model=List[OrganizationMember])
async def get_organization_members(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all members of an organization
    
    Args:
        organization_id: Organization ID
        
    Returns:
        List of organization members
    """
    org_repo = OrganizationRepository(db)
    
    # Check if user is a member of the organization
    is_member = await org_repo.user_is_member(organization_id, current_user.id)
    if not is_member and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this organization"
        )
    
    members = await org_repo.get_organization_members(organization_id)
    return members


@router.post("/organizations/{organization_id}/members", response_model=OrganizationMember, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    organization_id: str,
    user_id: str,
    role: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a member to an organization
    
    Args:
        organization_id: Organization ID
        user_id: User ID
        role: Member role ('owner', 'admin', 'member')
        
    Returns:
        Organization member
    """
    org_repo = OrganizationRepository(db)
    
    # Check if user is an admin or owner of the organization
    is_admin_or_owner = await org_repo.user_is_admin_or_owner(organization_id, current_user.id)
    if not is_admin_or_owner and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add members to this organization"
        )
    
    # Only owners can add other owners
    if role == 'owner':
        is_owner = await org_repo.user_is_owner(organization_id, current_user.id)
        if not is_owner and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can add other owners to the organization"
            )
    
    try:
        member = await org_repo.add_member(organization_id, user_id, role)
        return member
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/organizations/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    organization_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a member from an organization
    
    Args:
        organization_id: Organization ID
        user_id: User ID
    """
    org_repo = OrganizationRepository(db)
    
    # Check if user is an admin or owner of the organization
    is_admin_or_owner = await org_repo.user_is_admin_or_owner(organization_id, current_user.id)
    
    # Users can remove themselves
    is_self = current_user.id == user_id
    
    if not is_admin_or_owner and not is_self and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove members from this organization"
        )
    
    # Get the role of the user to be removed
    user_role = await org_repo.get_user_role_in_organization(organization_id, user_id)
    
    # Only owners can remove other owners
    if user_role == 'owner':
        is_owner = await org_repo.user_is_owner(organization_id, current_user.id)
        if not is_owner and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can remove other owners from the organization"
            )
    
    try:
        success = await org_repo.remove_member(organization_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} is not a member of this organization"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/organizations/{organization_id}/role", response_model=str)
async def get_user_role_in_organization(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's role in an organization
    
    Args:
        organization_id: Organization ID
        
    Returns:
        User's role in the organization
    """
    org_repo = OrganizationRepository(db)
    role = await org_repo.get_user_role_in_organization(organization_id, current_user.id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this organization"
        )
    
    return role