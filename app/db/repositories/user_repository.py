from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, and_, select, text, update
from sqlalchemy.dialects.postgresql import UUID as SQLUUID

from app.db.models import User as DBUser, Document
from app.models.user import User as PydanticUser, UserCreate, UserUpdate, UserInDB
from app.db.repositories.base import BaseRepository
from app.core.security import get_password_hash, verify_password


class UserRepository(BaseRepository[DBUser]):
    """
    Repository for User model
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DBUser)
    
    async def get_by_id(self, id: Union[int, str, UUID]) -> Optional[PydanticUser]:
        """
        Get a user by ID with improved UUID handling
        
        Args:
            id: User ID (can be string, UUID, or int)
            
        Returns:
            User if found, None otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(id, str):
            try:
                id = UUID(id)
            except ValueError:
                return None
        
        # Use SQLAlchemy's native UUID handling
        stmt = select(DBUser).where(DBUser.id == id)
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        return self._db_user_to_pydantic(user)
    
    async def create_user(self, user_data: UserCreate) -> PydanticUser:
        """
        Create a new user
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user (Pydantic model)
        """
        # Check if username or email already exists
        existing_user = await self.get_by_username_or_email(user_data.username, user_data.email)
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Create password hash
        password_hash = get_password_hash(user_data.password)
        
        # Create user
        user = DBUser(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
            is_active=user_data.is_active,
            is_admin=user_data.is_admin,
            created_at=datetime.utcnow()
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        # Convert to Pydantic model
        return self._db_user_to_pydantic(user)
    
    async def get_by_username(self, username: str) -> Optional[PydanticUser]:
        """
        Get a user by username
        
        Args:
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        stmt = select(DBUser).where(DBUser.username == username)
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        return self._db_user_to_pydantic(user)
    
    async def get_by_email(self, email: str) -> Optional[PydanticUser]:
        """
        Get a user by email
        
        Args:
            email: Email
            
        Returns:
            User if found, None otherwise
        """
        stmt = select(DBUser).where(DBUser.email == email)
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        return self._db_user_to_pydantic(user)
    
    async def get_by_username_or_email(self, username: str, email: str) -> Optional[PydanticUser]:
        """
        Get a user by username or email
        
        Args:
            username: Username
            email: Email
            
        Returns:
            User if found, None otherwise
        """
        stmt = select(DBUser).where(or_(DBUser.username == username, DBUser.email == email))
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        return self._db_user_to_pydantic(user)
    
    async def update_user(self, user_id: Union[UUID, str], user_data: Union[UserUpdate, Dict[str, Any]]) -> Optional[PydanticUser]:
        """
        Update a user
        
        Args:
            user_id: User ID
            user_data: User update data
            
        Returns:
            Updated user if found, None otherwise
        """
        # Convert user_data to UserUpdate if it's a dict
        if isinstance(user_data, dict):
            user_data = UserUpdate(**user_data)
        
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Get the DB user
        stmt = select(DBUser).where(DBUser.id == user_id)
        result = await self.session.execute(stmt)
        db_user = result.scalars().first()
        
        if not db_user:
            return None
        
        # Update fields if provided
        if user_data.username is not None:
            # Check if username already exists
            existing_user = await self.get_by_username(user_data.username)
            if existing_user and str(existing_user.id) != str(user_id):
                raise ValueError("Username already exists")
            db_user.username = user_data.username
        
        if user_data.email is not None:
            # Check if email already exists
            existing_user = await self.get_by_email(user_data.email)
            if existing_user and str(existing_user.id) != str(user_id):
                raise ValueError("Email already exists")
            db_user.email = user_data.email
        
        if user_data.full_name is not None:
            db_user.full_name = user_data.full_name
        
        if user_data.password is not None:
            db_user.password_hash = get_password_hash(user_data.password)
        
        if user_data.is_active is not None:
            db_user.is_active = user_data.is_active
        
        if user_data.is_admin is not None:
            db_user.is_admin = user_data.is_admin
        
        await self.session.commit()
        await self.session.refresh(db_user)
        
        return self._db_user_to_pydantic(db_user)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[PydanticUser]:
        """
        Authenticate a user
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User if authentication successful, None otherwise
        """
        # Get user by username
        stmt = select(DBUser).where(DBUser.username == username)
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.session.commit()
        
        return self._db_user_to_pydantic(user)
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[PydanticUser]:
        """
        Get all users with pagination
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of users
        """
        stmt = select(DBUser).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        return [self._db_user_to_pydantic(user) for user in users]
    
    async def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> List[PydanticUser]:
        """
        Search users by username or email
        
        Args:
            search_term: Search term
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of users matching the search term
        """
        # Create a search pattern with wildcards
        search_pattern = f"%{search_term}%"
        
        # Search by username or email
        stmt = select(DBUser).where(
            or_(
                DBUser.username.ilike(search_pattern),
                DBUser.email.ilike(search_pattern),
                DBUser.full_name.ilike(search_pattern)
            )
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        return [self._db_user_to_pydantic(user) for user in users]
    
    async def delete_user(self, user_id: Union[UUID, str]) -> bool:
        """
        Delete a user and reassign their documents to the system user
        
        Args:
            user_id: User ID
            
        Returns:
            True if user was deleted, False otherwise
        """
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        # Get the system user
        system_user_stmt = select(DBUser).where(DBUser.username == 'system')
        system_user_result = await self.session.execute(system_user_stmt)
        system_user = system_user_result.scalars().first()
        
        if not system_user:
            # System user doesn't exist, create one
            raise ValueError("System user not found. Please run scripts/create_system_user.py first.")
        
        # First get all documents owned by this user
        docs_stmt = select(Document).where(Document.user_id == user_id)
        docs_result = await self.session.execute(docs_stmt)
        documents = docs_result.scalars().all()
        
        # Update each document individually
        for doc in documents:
            # Create updated metadata with previous owner info
            if not doc.doc_metadata:
                doc.doc_metadata = {}
            
            # Convert to dict if it's not already
            if not isinstance(doc.doc_metadata, dict):
                doc.doc_metadata = {}
                
            # Add previous owner info
            doc.doc_metadata['previous_owner'] = str(user_id)
            
            # Reassign to system user
            doc.user_id = system_user.id
            self.session.add(doc)
        
        # Get the DB user
        user_stmt = select(DBUser).where(DBUser.id == user_id)
        user_result = await self.session.execute(user_stmt)
        db_user = user_result.scalars().first()
        
        if not db_user:
            return False
        
        # Delete the user
        await self.session.delete(db_user)
        await self.session.commit()
        
        return True
    
    def _db_user_to_pydantic(self, db_user: DBUser) -> PydanticUser:
        """
        Convert a database user to a Pydantic user
        
        Args:
            db_user: Database user
            
        Returns:
            Pydantic user
        """
        # Check if user_metadata attribute exists
        metadata = {}
        if hasattr(db_user, 'user_metadata') and db_user.user_metadata is not None:
            metadata = db_user.user_metadata
            
        return PydanticUser(
            id=str(db_user.id),
            username=db_user.username,
            email=db_user.email,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            is_admin=db_user.is_admin,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            metadata=metadata
        )