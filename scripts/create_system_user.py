#!/usr/bin/env python3
"""
Create a system user for document ownership when users are deleted.
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.db.models import User
from app.core.security import get_password_hash


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
            print(f'System user created with ID: {system_user_id}')
        else:
            print(f'System user already exists with ID: {system_user.id}')


if __name__ == "__main__":
    asyncio.run(create_system_user())