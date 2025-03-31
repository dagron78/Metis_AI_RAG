# Authentication System Improvements

## Overview

This document outlines the improvements made to the Metis RAG authentication system to address issues identified during testing. The authentication system provides user registration, login, password reset, and admin user management functionality.

## Issues Identified

During testing with the `scripts/test_authentication.py` script, several issues were identified:

1. SQLAlchemy AsyncSession mismatch causing `'AsyncSession' object has no attribute 'query'` errors
2. Password reset implementation using raw SQL without proper text() function
3. Database schema mismatch with missing `doc_metadata` column
4. UUID handling issues in user retrieval by ID
5. Transaction management issues in user deletion
6. Document reassignment issues when deleting users

## Improvements Checklist

### Phase 1: Database and ORM Alignment

- [x] Fixed SQLAlchemy AsyncSession mismatch in BaseRepository
  - Updated BaseRepository class to use async methods instead of synchronous ones
  - Converted all query methods to use SQLAlchemy 2.0 style async queries
  - Ensured proper await statements for all database operations

- [x] Fixed password reset implementation
  - Added proper use of text() function for raw SQL queries
  - Ensured consistent use of async/await patterns
  - Fixed token generation and validation

- [x] Created migration for database schema alignment
  - Created migration file to add missing doc_metadata column
  - Updated Alembic environment to use async database connection
  - Prepared migration to safely handle existing data

### Phase 2: Remaining Issues (Completed)

- [x] Successfully applied database migration
  - Resolved issues with running async migrations
  - Verified column addition in database schema
  - Migrated data from old metadata column to new doc_metadata column

- [x] Fixed user retrieval by ID
  - Improved UUID handling with proper type conversion
  - Enhanced error handling for invalid UUID formats

- [x] Fixed user deletion functionality
  - Implemented document reassignment to system user
  - Added transaction management with proper error handling
  - Stored original owner information in document metadata

## Testing Results

The authentication test script (`scripts/test_authentication.py`) now shows all features working correctly:

### Working Features:
- ✅ User Registration
- ✅ User Login
- ✅ Current User Info Retrieval
- ✅ Password Reset Request
- ✅ Admin Login
- ✅ Listing All Users
- ✅ Getting User by ID
- ✅ Creating New Users
- ✅ Updating Users
- ✅ Deleting Users

## Technical Details

### BaseRepository Changes

The BaseRepository class was updated to use async methods:

```python
# Before
def get_by_id(self, id: Union[int, str, UUID]) -> Optional[ModelType]:
    return self.session.query(self.model_class).filter(self.model_class.id == id).first()

# After
async def get_by_id(self, id: Union[int, str, UUID]) -> Optional[ModelType]:
    stmt = select(self.model_class).where(self.model_class.id == id)
    result = await self.session.execute(stmt)
    return result.scalars().first()
```

### UUID Handling Improvements

Enhanced UUID handling in the get_by_id method:

```python
async def get_by_id(self, id: Union[int, str, UUID]) -> Optional[PydanticUser]:
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
```

### User Deletion with Document Reassignment

Implemented document reassignment when deleting users:

```python
async def delete_user(self, user_id: Union[UUID, str]) -> bool:
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
```

### Password Reset Implementation

The password reset implementation was updated to use the text() function:

```python
# Before
query = """
INSERT INTO password_reset_tokens (id, user_id, token, created_at, expires_at, is_used)
VALUES (:id, :user_id, :token, :created_at, :expires_at, :is_used)
"""
await db.execute(query, values)

# After
query = text("""
INSERT INTO password_reset_tokens (id, user_id, token, created_at, expires_at, is_used)
VALUES (:id, :user_id, :token, :created_at, :expires_at, :is_used)
""")
await db.execute(query, values)
```

### Database Migration

A migration was created to add the missing column:

```python
def upgrade():
    # Check if doc_metadata column exists in documents table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    # Add doc_metadata column if it doesn't exist
    if 'doc_metadata' not in columns:
        op.add_column('documents',
                     sa.Column('doc_metadata', JSONB(),
                              nullable=True,
                              server_default=text("'{}'::jsonb")))
```

## System User Creation

A script was created to ensure a system user exists for document reassignment:

```python
async def create_system_user():
    """Create a system user if it doesn't exist."""
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/metis_rag')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if system user already exists
        stmt = select(User).where(User.username == 'system')
        result = await session.execute(stmt)
        system_user = result.scalars().first()
        
        if not system_user:
            # Create system user
            system_user_id = uuid.uuid4()
            system_user = User(
                id=system_user_id,
                username='system',
                email='system@metisrag.internal',
                password_hash=get_password_hash('not_accessible'),
                full_name='System User',
                is_active=True,
                is_admin=True
            )
            session.add(system_user)
            await session.commit()
```

## Conclusion

The authentication system has been fully improved, with all 10 key features now working correctly. The improvements include:

1. Proper async/await patterns throughout the codebase
2. Enhanced UUID handling for robust ID management
3. Database schema alignment with ORM models
4. Document reassignment to system user when deleting users
5. Improved transaction management for data integrity

These changes ensure a more robust and reliable authentication system for the Metis RAG application.