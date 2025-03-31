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
down_revision = 'add_background_tasks'
branch_labels = None
depends_on = None


def upgrade():
    # Check if users table already exists
    from sqlalchemy import inspect
    from sqlalchemy.engine import reflection
    
    # Get inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if users table exists
    if 'users' not in inspector.get_table_names():
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
    
    # Check if user_id column exists in documents table
    inspector = inspect(conn)
    doc_columns = [col['name'] for col in inspector.get_columns('documents')]
    if 'user_id' not in doc_columns:
        # Add user_id column to documents table
        op.add_column('documents', sa.Column('user_id', UUID(), nullable=True))
        op.create_foreign_key('fk_documents_user_id', 'documents', 'users', ['user_id'], ['id'])
        op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    
    # Check if user_id column exists in conversations table
    conv_columns = [col['name'] for col in inspector.get_columns('conversations')]
    if 'user_id' not in conv_columns:
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