"""Add user_id columns to documents and conversations tables

Revision ID: add_user_id_columns
Revises: add_background_tasks
Create Date: 2025-03-21 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'add_user_id_columns'
down_revision = 'add_background_tasks'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist
    from sqlalchemy import inspect
    
    # Get inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if user_id column exists in documents table
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