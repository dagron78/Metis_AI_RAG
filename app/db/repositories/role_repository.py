from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, and_, select, text, update
from sqlalchemy.dialects.postgresql import UUID as SQLUUID

from app.db.models import Role as DBRole, UserRole as DBUserRole, User as DBUser
from app.models.role import Role as PydanticRole, RoleCreate, RoleUpdate, UserRole as PydanticUserRole, UserRoleCreate
from app.db.repositories.base import BaseRepository


class RoleRepository(BaseRepository[DBRole]):
    """
    Repository for Role model
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DBRole)
    
    async def get_by_id(self, id: Union[str, UUID]) -> Optional[PydanticRole]:
        """
        Get a role by ID
        
        Args:
            id: Role ID
            
        Returns:
            Role if found, None otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(id, str):
            try:
                id = UUID(id)
            except ValueError:
                return None
        
        stmt = select(DBRole).where(DBRole.id == id)
        result = await self.session.execute(stmt)
        role = result.scalars().first()
        
        if not role:
            return None
        
        return self._db_role_to_pydantic(role)
    
    async def get_by_name(self, name: str) -> Optional[PydanticRole]:
        """
        Get a role by name
        
        Args:
            name: Role name
            
        Returns:
            Role if found, None otherwise
        """
        stmt = select(DBRole).where(DBRole.name == name)
        result = await self.session.execute(stmt)
        role = result.scalars().first()
        
        if not role:
            return None
        
        return self._db_role_to_pydantic(role)
    
    async def create_role(self, role_data: RoleCreate) -> PydanticRole:
        """
        Create a new role
        
        Args:
            role_data: Role creation data
            
        Returns:
            Created role
        """
        # Check if role name already exists
        existing_role = await self.get_by_name(role_data.name)
        if existing_role:
            raise ValueError(f"Role with name '{role_data.name}' already exists")
        
        # Create role
        role = DBRole(
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions,
            created_at=datetime.utcnow()
        )
        
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        
        return self._db_role_to_pydantic(role)
    
    async def update_role(self, role_id: Union[str, UUID], role_data: RoleUpdate) -> Optional[PydanticRole]:
        """
        Update a role
        
        Args:
            role_id: Role ID
            role_data: Role update data
            
        Returns:
            Updated role if found, None otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(role_id, str):
            try:
                role_id = UUID(role_id)
            except ValueError:
                return None
        
        # Get the role
        stmt = select(DBRole).where(DBRole.id == role_id)
        result = await self.session.execute(stmt)
        db_role = result.scalars().first()
        
        if not db_role:
            return None
        
        # Update fields if provided
        if role_data.name is not None:
            # Check if name already exists
            existing_role = await self.get_by_name(role_data.name)
            if existing_role and str(existing_role.id) != str(role_id):
                raise ValueError(f"Role with name '{role_data.name}' already exists")
            db_role.name = role_data.name
        
        if role_data.description is not None:
            db_role.description = role_data.description
        
        if role_data.permissions is not None:
            db_role.permissions = role_data.permissions
        
        await self.session.commit()
        await self.session.refresh(db_role)
        
        return self._db_role_to_pydantic(db_role)
    
    async def delete_role(self, role_id: Union[str, UUID]) -> bool:
        """
        Delete a role
        
        Args:
            role_id: Role ID
            
        Returns:
            True if role was deleted, False otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(role_id, str):
            try:
                role_id = UUID(role_id)
            except ValueError:
                return False
        
        # Get the role
        stmt = select(DBRole).where(DBRole.id == role_id)
        result = await self.session.execute(stmt)
        db_role = result.scalars().first()
        
        if not db_role:
            return False
        
        # Delete the role (cascade will handle user-role associations)
        await self.session.delete(db_role)
        await self.session.commit()
        
        return True
    
    async def get_all_roles(self, skip: int = 0, limit: int = 100) -> List[PydanticRole]:
        """
        Get all roles with pagination
        
        Args:
            skip: Number of roles to skip
            limit: Maximum number of roles to return
            
        Returns:
            List of roles
        """
        stmt = select(DBRole).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        roles = result.scalars().all()
        
        return [self._db_role_to_pydantic(role) for role in roles]
    
    async def assign_role_to_user(self, user_id: Union[str, UUID], role_id: Union[str, UUID]) -> PydanticUserRole:
        """
        Assign a role to a user
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            User-role association
        """
        # Convert string IDs to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                raise ValueError(f"Invalid user ID: {user_id}")
        
        if isinstance(role_id, str):
            try:
                role_id = UUID(role_id)
            except ValueError:
                raise ValueError(f"Invalid role ID: {role_id}")
        
        # Check if user exists
        user_stmt = select(DBUser).where(DBUser.id == user_id)
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalars().first()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if role exists
        role_stmt = select(DBRole).where(DBRole.id == role_id)
        role_result = await self.session.execute(role_stmt)
        role = role_result.scalars().first()
        
        if not role:
            raise ValueError(f"Role with ID {role_id} not found")
        
        # Check if user already has this role
        user_role_stmt = select(DBUserRole).where(
            and_(DBUserRole.user_id == user_id, DBUserRole.role_id == role_id)
        )
        user_role_result = await self.session.execute(user_role_stmt)
        existing_user_role = user_role_result.scalars().first()
        
        if existing_user_role:
            # User already has this role, return the existing association
            return PydanticUserRole(
                user_id=str(existing_user_role.user_id),
                role_id=str(existing_user_role.role_id),
                created_at=existing_user_role.created_at
            )
        
        # Create user-role association
        user_role = DBUserRole(
            user_id=user_id,
            role_id=role_id,
            created_at=datetime.utcnow()
        )
        
        self.session.add(user_role)
        await self.session.commit()
        
        return PydanticUserRole(
            user_id=str(user_role.user_id),
            role_id=str(user_role.role_id),
            created_at=user_role.created_at
        )
    
    async def remove_role_from_user(self, user_id: Union[str, UUID], role_id: Union[str, UUID]) -> bool:
        """
        Remove a role from a user
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            True if role was removed, False otherwise
        """
        # Convert string IDs to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        if isinstance(role_id, str):
            try:
                role_id = UUID(role_id)
            except ValueError:
                return False
        
        # Get the user-role association
        stmt = select(DBUserRole).where(
            and_(DBUserRole.user_id == user_id, DBUserRole.role_id == role_id)
        )
        result = await self.session.execute(stmt)
        user_role = result.scalars().first()
        
        if not user_role:
            return False
        
        # Delete the user-role association
        await self.session.delete(user_role)
        await self.session.commit()
        
        return True
    
    async def get_user_roles(self, user_id: Union[str, UUID]) -> List[PydanticRole]:
        """
        Get all roles assigned to a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of roles assigned to the user
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return []
        
        # Get all roles assigned to the user
        stmt = select(DBRole).join(DBUserRole, DBUserRole.role_id == DBRole.id).where(DBUserRole.user_id == user_id)
        result = await self.session.execute(stmt)
        roles = result.scalars().all()
        
        return [self._db_role_to_pydantic(role) for role in roles]
    
    async def get_role_users(self, role_id: Union[str, UUID]) -> List[str]:
        """
        Get all users assigned to a role
        
        Args:
            role_id: Role ID
            
        Returns:
            List of user IDs assigned to the role
        """
        # Convert string ID to UUID if needed
        if isinstance(role_id, str):
            try:
                role_id = UUID(role_id)
            except ValueError:
                return []
        
        # Get all users assigned to the role
        stmt = select(DBUserRole.user_id).where(DBUserRole.role_id == role_id)
        result = await self.session.execute(stmt)
        user_ids = result.scalars().all()
        
        return [str(user_id) for user_id in user_ids]
    
    async def user_has_role(self, user_id: Union[str, UUID], role_name: str) -> bool:
        """
        Check if a user has a specific role
        
        Args:
            user_id: User ID
            role_name: Role name
            
        Returns:
            True if user has the role, False otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        # Check if user has the role
        stmt = select(DBUserRole).join(DBRole, DBUserRole.role_id == DBRole.id).where(
            and_(DBUserRole.user_id == user_id, DBRole.name == role_name)
        )
        result = await self.session.execute(stmt)
        user_role = result.scalars().first()
        
        return user_role is not None
    
    async def user_has_permission(self, user_id: Union[str, UUID], permission: str) -> bool:
        """
        Check if a user has a specific permission through any of their roles
        
        Args:
            user_id: User ID
            permission: Permission name
            
        Returns:
            True if user has the permission, False otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        # Get all roles assigned to the user
        roles = await self.get_user_roles(user_id)
        
        # Check if any role has the permission
        for role in roles:
            if role.permissions and permission in role.permissions:
                return True
        
        return False
    
    def _db_role_to_pydantic(self, db_role: DBRole) -> PydanticRole:
        """
        Convert a database role to a Pydantic role
        
        Args:
            db_role: Database role
            
        Returns:
            Pydantic role
        """
        return PydanticRole(
            id=str(db_role.id),
            name=db_role.name,
            description=db_role.description,
            permissions=db_role.permissions,
            created_at=db_role.created_at
        )