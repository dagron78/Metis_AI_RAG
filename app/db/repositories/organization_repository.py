from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, and_, select, text, update, desc
from sqlalchemy.dialects.postgresql import UUID as SQLUUID

from app.db.models import Organization as DBOrganization, OrganizationMember as DBOrganizationMember, User as DBUser
from app.models.organization import Organization as PydanticOrganization, OrganizationCreate, OrganizationUpdate
from app.models.organization import OrganizationMember as PydanticOrganizationMember, OrganizationMemberCreate
from app.db.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[DBOrganization]):
    """
    Repository for Organization model
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DBOrganization)
    
    async def get_by_id(self, id: Union[str, UUID]) -> Optional[PydanticOrganization]:
        """
        Get an organization by ID
        
        Args:
            id: Organization ID
            
        Returns:
            Organization if found, None otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(id, str):
            try:
                id = UUID(id)
            except ValueError:
                return None
        
        stmt = select(DBOrganization).where(DBOrganization.id == id)
        result = await self.session.execute(stmt)
        organization = result.scalars().first()
        
        if not organization:
            return None
        
        return self._db_organization_to_pydantic(organization)
    
    async def get_by_name(self, name: str) -> Optional[PydanticOrganization]:
        """
        Get an organization by name
        
        Args:
            name: Organization name
            
        Returns:
            Organization if found, None otherwise
        """
        stmt = select(DBOrganization).where(DBOrganization.name == name)
        result = await self.session.execute(stmt)
        organization = result.scalars().first()
        
        if not organization:
            return None
        
        return self._db_organization_to_pydantic(organization)
    
    async def create_organization(self, organization_data: OrganizationCreate, owner_id: Union[str, UUID]) -> PydanticOrganization:
        """
        Create a new organization with the specified owner
        
        Args:
            organization_data: Organization creation data
            owner_id: User ID of the organization owner
            
        Returns:
            Created organization
        """
        # Check if organization name already exists
        existing_org = await self.get_by_name(organization_data.name)
        if existing_org:
            raise ValueError(f"Organization with name '{organization_data.name}' already exists")
        
        # Convert owner_id to UUID if needed
        if isinstance(owner_id, str):
            try:
                owner_id = UUID(owner_id)
            except ValueError:
                raise ValueError(f"Invalid owner ID: {owner_id}")
        
        # Create organization
        organization = DBOrganization(
            name=organization_data.name,
            description=organization_data.description,
            settings=organization_data.settings,
            created_at=datetime.utcnow()
        )
        
        self.session.add(organization)
        await self.session.flush()  # Flush to get the organization ID
        
        # Create owner membership
        owner_membership = DBOrganizationMember(
            organization_id=organization.id,
            user_id=owner_id,
            role='owner',
            created_at=datetime.utcnow()
        )
        
        self.session.add(owner_membership)
        await self.session.commit()
        await self.session.refresh(organization)
        
        return self._db_organization_to_pydantic(organization)
    
    async def update_organization(self, organization_id: Union[str, UUID], organization_data: OrganizationUpdate) -> Optional[PydanticOrganization]:
        """
        Update an organization
        
        Args:
            organization_id: Organization ID
            organization_data: Organization update data
            
        Returns:
            Updated organization if found, None otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(organization_id, str):
            try:
                organization_id = UUID(organization_id)
            except ValueError:
                return None
        
        # Get the organization
        stmt = select(DBOrganization).where(DBOrganization.id == organization_id)
        result = await self.session.execute(stmt)
        db_organization = result.scalars().first()
        
        if not db_organization:
            return None
        
        # Update fields if provided
        if organization_data.name is not None:
            # Check if name already exists
            existing_org = await self.get_by_name(organization_data.name)
            if existing_org and str(existing_org.id) != str(organization_id):
                raise ValueError(f"Organization with name '{organization_data.name}' already exists")
            db_organization.name = organization_data.name
        
        if organization_data.description is not None:
            db_organization.description = organization_data.description
        
        if organization_data.settings is not None:
            db_organization.settings = organization_data.settings
        
        await self.session.commit()
        await self.session.refresh(db_organization)
        
        return self._db_organization_to_pydantic(db_organization)
    
    async def delete_organization(self, organization_id: Union[str, UUID]) -> bool:
        """
        Delete an organization
        
        Args:
            organization_id: Organization ID
            
        Returns:
            True if organization was deleted, False otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(organization_id, str):
            try:
                organization_id = UUID(organization_id)
            except ValueError:
                return False
        
        # Get the organization
        stmt = select(DBOrganization).where(DBOrganization.id == organization_id)
        result = await self.session.execute(stmt)
        db_organization = result.scalars().first()
        
        if not db_organization:
            return False
        
        # Delete the organization (cascade will handle members)
        await self.session.delete(db_organization)
        await self.session.commit()
        
        return True
    
    async def get_all_organizations(self, skip: int = 0, limit: int = 100) -> List[PydanticOrganization]:
        """
        Get all organizations with pagination
        
        Args:
            skip: Number of organizations to skip
            limit: Maximum number of organizations to return
            
        Returns:
            List of organizations
        """
        stmt = select(DBOrganization).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        organizations = result.scalars().all()
        
        return [self._db_organization_to_pydantic(org) for org in organizations]
    
    async def add_member(self, organization_id: Union[str, UUID], user_id: Union[str, UUID], role: str) -> PydanticOrganizationMember:
        """
        Add a member to an organization
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            role: Member role ('owner', 'admin', 'member')
            
        Returns:
            Organization member
        """
        # Convert string IDs to UUID if needed
        if isinstance(organization_id, str):
            try:
                organization_id = UUID(organization_id)
            except ValueError:
                raise ValueError(f"Invalid organization ID: {organization_id}")
        
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                raise ValueError(f"Invalid user ID: {user_id}")
        
        # Validate role
        valid_roles = ['owner', 'admin', 'member']
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}. Must be one of: {', '.join(valid_roles)}")
        
        # Check if organization exists
        org_stmt = select(DBOrganization).where(DBOrganization.id == organization_id)
        org_result = await self.session.execute(org_stmt)
        organization = org_result.scalars().first()
        
        if not organization:
            raise ValueError(f"Organization with ID {organization_id} not found")
        
        # Check if user exists
        user_stmt = select(DBUser).where(DBUser.id == user_id)
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalars().first()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if user is already a member
        member_stmt = select(DBOrganizationMember).where(
            and_(
                DBOrganizationMember.organization_id == organization_id,
                DBOrganizationMember.user_id == user_id
            )
        )
        member_result = await self.session.execute(member_stmt)
        existing_member = member_result.scalars().first()
        
        if existing_member:
            # Update role if different
            if existing_member.role != role:
                existing_member.role = role
                await self.session.commit()
            
            return PydanticOrganizationMember(
                organization_id=str(existing_member.organization_id),
                user_id=str(existing_member.user_id),
                role=existing_member.role,
                created_at=existing_member.created_at
            )
        
        # Create new member
        member = DBOrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            created_at=datetime.utcnow()
        )
        
        self.session.add(member)
        await self.session.commit()
        
        return PydanticOrganizationMember(
            organization_id=str(member.organization_id),
            user_id=str(member.user_id),
            role=member.role,
            created_at=member.created_at
        )
    
    async def remove_member(self, organization_id: Union[str, UUID], user_id: Union[str, UUID]) -> bool:
        """
        Remove a member from an organization
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            True if member was removed, False otherwise
        """
        # Convert string IDs to UUID if needed
        if isinstance(organization_id, str):
            try:
                organization_id = UUID(organization_id)
            except ValueError:
                return False
        
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        # Get the member
        stmt = select(DBOrganizationMember).where(
            and_(
                DBOrganizationMember.organization_id == organization_id,
                DBOrganizationMember.user_id == user_id
            )
        )
        result = await self.session.execute(stmt)
        member = result.scalars().first()
        
        if not member:
            return False
        
        # Check if this is the last owner
        if member.role == 'owner':
            # Count owners
            owner_stmt = select(func.count()).where(
                and_(
                    DBOrganizationMember.organization_id == organization_id,
                    DBOrganizationMember.role == 'owner'
                )
            )
            owner_result = await self.session.execute(owner_stmt)
            owner_count = owner_result.scalar()
            
            if owner_count == 1:
                raise ValueError("Cannot remove the last owner of an organization")
        
        # Delete the member
        await self.session.delete(member)
        await self.session.commit()
        
        return True
    
    async def get_organization_members(self, organization_id: Union[str, UUID]) -> List[PydanticOrganizationMember]:
        """
        Get all members of an organization
        
        Args:
            organization_id: Organization ID
            
        Returns:
            List of organization members
        """
        # Convert string ID to UUID if needed
        if isinstance(organization_id, str):
            try:
                organization_id = UUID(organization_id)
            except ValueError:
                return []
        
        # Get all members
        stmt = select(DBOrganizationMember).where(DBOrganizationMember.organization_id == organization_id)
        result = await self.session.execute(stmt)
        members = result.scalars().all()
        
        return [
            PydanticOrganizationMember(
                organization_id=str(member.organization_id),
                user_id=str(member.user_id),
                role=member.role,
                created_at=member.created_at
            )
            for member in members
        ]
    
    async def get_user_organizations(self, user_id: Union[str, UUID]) -> List[PydanticOrganization]:
        """
        Get all organizations a user is a member of
        
        Args:
            user_id: User ID
            
        Returns:
            List of organizations
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return []
        
        # Get all organizations the user is a member of
        stmt = select(DBOrganization).join(
            DBOrganizationMember,
            DBOrganizationMember.organization_id == DBOrganization.id
        ).where(DBOrganizationMember.user_id == user_id)
        
        result = await self.session.execute(stmt)
        organizations = result.scalars().all()
        
        return [self._db_organization_to_pydantic(org) for org in organizations]
    
    async def get_user_role_in_organization(self, organization_id: Union[str, UUID], user_id: Union[str, UUID]) -> Optional[str]:
        """
        Get a user's role in an organization
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            User's role if they are a member, None otherwise
        """
        # Convert string IDs to UUID if needed
        if isinstance(organization_id, str):
            try:
                organization_id = UUID(organization_id)
            except ValueError:
                return None
        
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return None
        
        # Get the member
        stmt = select(DBOrganizationMember).where(
            and_(
                DBOrganizationMember.organization_id == organization_id,
                DBOrganizationMember.user_id == user_id
            )
        )
        result = await self.session.execute(stmt)
        member = result.scalars().first()
        
        if not member:
            return None
        
        return member.role
    
    async def user_is_member(self, organization_id: Union[str, UUID], user_id: Union[str, UUID]) -> bool:
        """
        Check if a user is a member of an organization
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            True if user is a member, False otherwise
        """
        role = await self.get_user_role_in_organization(organization_id, user_id)
        return role is not None
    
    async def user_is_admin_or_owner(self, organization_id: Union[str, UUID], user_id: Union[str, UUID]) -> bool:
        """
        Check if a user is an admin or owner of an organization
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            True if user is an admin or owner, False otherwise
        """
        role = await self.get_user_role_in_organization(organization_id, user_id)
        return role in ['admin', 'owner']
    
    async def user_is_owner(self, organization_id: Union[str, UUID], user_id: Union[str, UUID]) -> bool:
        """
        Check if a user is an owner of an organization
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            True if user is an owner, False otherwise
        """
        role = await self.get_user_role_in_organization(organization_id, user_id)
        return role == 'owner'
    
    def _db_organization_to_pydantic(self, db_organization: DBOrganization) -> PydanticOrganization:
        """
        Convert a database organization to a Pydantic organization
        
        Args:
            db_organization: Database organization
            
        Returns:
            Pydantic organization
        """
        return PydanticOrganization(
            id=str(db_organization.id),
            name=db_organization.name,
            description=db_organization.description,
            settings=db_organization.settings,
            created_at=db_organization.created_at
        )