from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.models import PasswordResetToken, User
from app.db.repositories.base import BaseRepository
from app.models.password_reset import PasswordResetToken as PydanticPasswordResetToken

class PasswordResetRepository(BaseRepository[PasswordResetToken]):
    """
    Repository for PasswordResetToken model
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PasswordResetToken)
    
    async def create_token(self, user_id: str, expires_in_hours: int = 24) -> PydanticPasswordResetToken:
        """
        Create a new password reset token
        
        Args:
            user_id: User ID
            expires_in_hours: Token expiration time in hours
            
        Returns:
            Created token (Pydantic model)
        """
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Create token
        token = PasswordResetToken(
            user_id=user_id,
            expires_at=expires_at
        )
        
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        
        # Convert to Pydantic model
        return self._db_token_to_pydantic(token)
    
    async def get_valid_token(self, token: str) -> Optional[PydanticPasswordResetToken]:
        """
        Get a valid token by token string
        
        Args:
            token: Token string
            
        Returns:
            Token if found and valid, None otherwise
        """
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.expires_at > datetime.utcnow(),
                PasswordResetToken.is_used == False
            )
        )
        result = await self.session.execute(stmt)
        db_token = result.scalars().first()
        
        if not db_token:
            return None
        
        return self._db_token_to_pydantic(db_token)
    
    async def invalidate_token(self, token: str) -> bool:
        """
        Invalidate a token by marking it as used
        
        Args:
            token: Token string
            
        Returns:
            True if token was invalidated, False otherwise
        """
        stmt = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.session.execute(stmt)
        db_token = result.scalars().first()
        
        if not db_token:
            return False
        
        db_token.is_used = True
        await self.session.commit()
        
        return True
    
    async def invalidate_all_user_tokens(self, user_id: str) -> int:
        """
        Invalidate all tokens for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of tokens invalidated
        """
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.is_used == False
            )
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            token.is_used = True
            count += 1
        
        if count > 0:
            await self.session.commit()
        
        return count
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Delete all expired tokens
        
        Returns:
            Number of tokens deleted
        """
        stmt = select(PasswordResetToken).where(PasswordResetToken.expires_at < datetime.utcnow())
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            await self.session.delete(token)
            count += 1
        
        if count > 0:
            await self.session.commit()
        
        return count
    
    def _db_token_to_pydantic(self, db_token: PasswordResetToken) -> PydanticPasswordResetToken:
        """
        Convert a database token to a Pydantic token
        
        Args:
            db_token: Database token
            
        Returns:
            Pydantic token
        """
        return PydanticPasswordResetToken(
            id=str(db_token.id),
            user_id=str(db_token.user_id),
            token=db_token.token,
            created_at=db_token.created_at,
            expires_at=db_token.expires_at,
            is_used=db_token.is_used
        )