# Metis RAG Authentication Implementation Plan

## Overview

This document outlines the plan for adding authentication to the Metis RAG application. The goal is to implement a user authentication system where each user gets a unique ID that will be used to track their chats and documents.

## Current State Analysis

Based on the analysis of the codebase and database, the following observations were made:

1. The database already has a `users` table with the following schema:
   ```sql
   CREATE TABLE users (
       id UUID NOT NULL PRIMARY KEY,
       username VARCHAR NOT NULL UNIQUE,
       email VARCHAR NOT NULL UNIQUE,
       password_hash VARCHAR NOT NULL,
       full_name VARCHAR,
       is_active BOOLEAN,
       is_admin BOOLEAN,
       created_at TIMESTAMP WITHOUT TIME ZONE,
       last_login TIMESTAMP WITHOUT TIME ZONE,
       metadata JSONB
   );
   ```

2. However, the `documents` and `conversations` tables do not have a `user_id` column yet, which is needed to associate these resources with users.

3. The system has some concept of `user_id` in the `Conversation` model's metadata, but it's not properly integrated with a user authentication system.

4. The application doesn't have a proper authentication system implemented yet.

## Implementation Plan

### 1. Database Schema Updates

Since the `users` table already exists in the database, we only need to add the `user_id` columns to the `documents` and `conversations` tables.

#### 1.1 Update Documents Table

Add a user_id column to the documents table to associate documents with users:

```sql
ALTER TABLE documents ADD COLUMN user_id UUID REFERENCES users(id);
CREATE INDEX ix_documents_user_id ON documents(user_id);
```

#### 1.2 Update Conversations Table

Add a user_id column to the conversations table (instead of storing it in metadata):

```sql
ALTER TABLE conversations ADD COLUMN user_id UUID REFERENCES users(id);
CREATE INDEX ix_conversations_user_id ON conversations(user_id);
```

We attempted to create a migration for these changes, but encountered permission issues with the database. The migration file has been created at `alembic/versions/add_user_id_columns.py`, but it will need to be run by a user with appropriate database permissions.

### 2. Model Updates

#### 2.1 Create User Model

Create a new User model in `app/models/user.py`:

```python
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    
    class Config:
        arbitrary_types_allowed = True

class UserCreate(UserBase):
    """User creation model"""
    password: str
    
    class Config:
        arbitrary_types_allowed = True

class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    
    class Config:
        arbitrary_types_allowed = True

class User(UserBase):
    """User model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class UserInDB(User):
    """User model with password hash (for internal use)"""
    password_hash: str
    
    class Config:
        arbitrary_types_allowed = True
```

#### 2.2 Update Database Models

Update the database models in `app/db/models.py` to include the User model and relationships:

```python
class User(Base):
    """User model for database"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True) if DATABASE_TYPE == 'postgresql' else UUID, primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    user_metadata = Column('metadata', JSONType, default={})

    # Relationships
    documents = relationship("Document", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

    # Indexes
    __table_args__ = (
        Index('ix_users_username', username),
        Index('ix_users_email', email),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
```

Update the Document model:

```python
class Document(Base):
    # Existing fields...
    user_id = Column(UUID(as_uuid=True) if DATABASE_TYPE == 'postgresql' else UUID, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    # Existing relationships...
    user = relationship("User", back_populates="documents")
    
    # Indexes
    __table_args__ = (
        # Existing indexes...
        Index('ix_documents_user_id', user_id),
    )
```

Update the Conversation model:

```python
class Conversation(Base):
    # Existing fields...
    user_id = Column(UUID(as_uuid=True) if DATABASE_TYPE == 'postgresql' else UUID, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    # Existing relationships...
    user = relationship("User", back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        # Existing indexes...
        Index('ix_conversations_user_id', user_id),
    )
```

### 3. Security Implementation

#### 3.1 Update Security Module

Update the security module in `app/core/security.py` to include password hashing and JWT token generation:

```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user from a JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if username is None or user_id is None:
            raise credentials_exception
        
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    from app.db.dependencies import get_user_repository
    from app.db.session import AsyncSessionLocal
    
    db = AsyncSessionLocal()
    try:
        user_repository = get_user_repository(db)
        user = await user_repository.get_by_username(token_data.username)
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
    finally:
        await db.close()

async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Get the current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user

async def get_current_admin_user(current_user = Depends(get_current_user)):
    """
    Get the current admin user
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an admin user"
        )
    
    return current_user
```

#### 3.2 Update Config Module

Update the config module in `app/core/config.py` to include JWT settings:

```python
# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

### 4. Repository Implementation

#### 4.1 Create User Repository

Create a new user repository in `app/db/repositories/user_repository.py`:

```python
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, and_, select, text

from app.db.models import User as DBUser
from app.models.user import User as PydanticUser, UserCreate, UserUpdate, UserInDB
from app.db.repositories.base import BaseRepository
from app.core.security import get_password_hash, verify_password

class UserRepository(BaseRepository[DBUser]):
    """
    Repository for User model
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DBUser)
    
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
    
    async def update_user(self, user_id: Union[UUID, str], user_data: UserUpdate) -> Optional[PydanticUser]:
        """
        Update a user
        
        Args:
            user_id: User ID
            user_data: User update data
            
        Returns:
            Updated user if found, None otherwise
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Update fields if provided
        if user_data.username is not None:
            # Check if username already exists
            existing_user = await self.get_by_username(user_data.username)
            if existing_user and str(existing_user.id) != str(user_id):
                raise ValueError("Username already exists")
            user.username = user_data.username
        
        if user_data.email is not None:
            # Check if email already exists
            existing_user = await self.get_by_email(user_data.email)
            if existing_user and str(existing_user.id) != str(user_id):
                raise ValueError("Email already exists")
            user.email = user_data.email
        
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        if user_data.password is not None:
            user.password_hash = get_password_hash(user_data.password)
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        if user_data.is_admin is not None:
            user.is_admin = user_data.is_admin
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return self._db_user_to_pydantic(user)
    
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
    
    def _db_user_to_pydantic(self, db_user: DBUser) -> PydanticUser:
        """
        Convert a database user to a Pydantic user
        
        Args:
            db_user: Database user
            
        Returns:
            Pydantic user
        """
        return PydanticUser(
            id=str(db_user.id),
            username=db_user.username,
            email=db_user.email,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            is_admin=db_user.is_admin,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            metadata=db_user.user_metadata or {}
        )
```

#### 4.2 Update Dependencies

Update the dependencies in `app/db/dependencies.py` to include the user repository:

```python
from app.db.repositories.user_repository import UserRepository

def get_user_repository(db: AsyncSession) -> UserRepository:
    """
    Get a user repository
    
    Args:
        db: Database session
        
    Returns:
        User repository
    """
    return UserRepository(db)
```

### 5. API Implementation

#### 5.1 Create Authentication API

Create a new authentication API in `app/api/auth.py`:

```python
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserCreate, UserUpdate
from app.core.security import create_access_token, get_current_user, get_current_active_user, Token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.dependencies import get_db, get_user_repository
from app.db.repositories.user_repository import UserRepository

# Create router
router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Get an access token for a user
    """
    user = await user_repository.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Register a new user
    """
    try:
        user = await user_repository.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Update the current user
    """
    try:
        updated_user = await user_repository.update_user(current_user.id, user_data)
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

#### 5.2 Update Main App

Update the main app in `app/main.py` to include the authentication router:

```python
from app.api.auth import router as auth_router

# Include API routers
app.include_router(auth_router, prefix=f"{API_V1_STR}/auth", tags=["auth"])
```

### 6. Frontend Implementation

#### 6.1 Create Login Page

Create a login page template in `app/templates/login.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metis RAG - Login</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <style>
        /* Styles for login form */
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login to Metis RAG</h2>
        <div id="error-message" class="error-message"></div>
        <form id="login-form">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
        <div class="register-link">
            <p>Don't have an account? <a href="/register">Register</a></p>
        </div>
    </div>

    <script>
        // JavaScript for login form submission
    </script>
</body>
</html>
```

#### 6.2 Create Registration Page

Create a registration page template in `app/templates/register.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metis RAG - Register</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <style>
        /* Styles for registration form */
    </style>
</head>
<body>
    <div class="register-container">
        <h2>Register for Metis RAG</h2>
        <div id="error-message" class="error-message"></div>
        <form id="register-form">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="full_name">Full Name</label>
                <input type="text" id="full_name" name="full_name">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="confirm_password" required>
            </div>
            <button type="submit" class="btn">Register</button>
        </form>
        <div class="login-link">
            <p>Already have an account? <a href="/login">Login</a></p>
        </div>
    </div>

    <script>
        // JavaScript for registration form submission
    </script>
</body>
</html>
```

#### 6.3 Update Main App Routes

Update the main app in `app/main.py` to include routes for the login and registration pages:

```python
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Login page
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Registration page
    """
    return templates.TemplateResponse("register.html", {"request": request})
```

### 7. Migration Implementation

Create a new Alembic migration in `alembic/versions/add_users_table.py`:

```python
"""Add users table and update documents and conversations tables

Revision ID: add_users_table
Revises: initial_schema
Create Date: 2025-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'add_users_table'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Add user_id column to documents table
    op.add_column('documents', sa.Column('user_id', UUID(), nullable=True))
    op.create_foreign_key('fk_documents_user_id', 'documents', 'users', ['user_id'], ['id'])
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    
    # Add user_id column to conversations table
    op.add_column('conversations', sa.Column('user_id', UUID(), nullable=True))
    op.create_foreign_key('fk_conversations_user_id', 'conversations', 'users', ['user_id'], ['id'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])


def downgrade():
    # Drop foreign keys and indexes
    op.drop_constraint('fk_documents_user_id', 'documents', type_='foreignkey')
    op.drop_index('ix_documents_user_id', table_name='documents')
    op.drop_constraint('fk_conversations_user_id', 'conversations', type_='foreignkey')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    
    # Drop columns
    op.drop_column('documents', 'user_id')
    op.drop_column('conversations', 'user_id')
    
    # Drop users table
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
```

## Implementation Status

### Completed

1. ✅ Created the Pydantic User model in `app/models/user.py`
2. ✅ Updated the database models in `app/db/models.py` to include the User model relationships
3. ✅ Created the user repository in `app/db/repositories/user_repository.py`
4. ✅ Updated the security module in `app/core/security.py` (was already mostly implemented)
5. ✅ Created the authentication API in `app/api/auth.py`
6. ✅ Created login and registration templates in `app/templates/login.html` and `app/templates/register.html`
7. ✅ Updated the main app to include routes for login and registration pages
8. ✅ Created a migration file for adding user_id columns to documents and conversations tables

### Remaining Tasks

1. ⬜ Run the database migration with appropriate permissions
2. ⬜ Test the authentication system
3. ⬜ Update existing API endpoints to use the authentication system
4. ⬜ Update frontend components to use the authentication system

## Conclusion

This implementation plan provides a comprehensive approach to adding authentication to the Metis RAG application. We've discovered that the users table already exists in the database, which simplified part of our implementation. We've created all the necessary components for the authentication system, but we still need to run the database migration with appropriate permissions and integrate the authentication system with the existing application.

By completing this implementation, each user will get a unique ID that will be used to track their chats and documents, ensuring data privacy and personalized experiences.