import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import AsyncSessionLocal

async def create_password_reset_table():
    """Create the password_reset_tokens table"""
    
    # SQL statements for creating the password_reset_tokens table and indexes
    sql_statements = [
        """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            token VARCHAR NOT NULL UNIQUE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            is_used BOOLEAN DEFAULT FALSE
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_token ON password_reset_tokens(token)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens(user_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_expires_at ON password_reset_tokens(expires_at)
        """
    ]
    
    # Connect to the database and execute each SQL statement
    async with AsyncSessionLocal() as session:
        for sql in sql_statements:
            await session.execute(text(sql))
        await session.commit()
        print("Password reset tokens table created successfully")

if __name__ == "__main__":
    asyncio.run(create_password_reset_table())