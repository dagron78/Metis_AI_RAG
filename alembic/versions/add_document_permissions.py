"""Add document_permissions table and is_public flag to documents

Revision ID: add_document_permissions
Revises: add_password_reset_tokens
Create Date: 2025-03-27 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'add_document_permissions'
down_revision = 'add_password_reset_tokens'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist
    from sqlalchemy import inspect
    
    # Get inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if document_permissions table exists
    tables = inspector.get_table_names()
    if 'document_permissions' not in tables:
        # Create document_permissions table
        op.create_table(
            'document_permissions',
            sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text("uuid_generate_v4()")),
            sa.Column('document_id', UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', UUID(as_uuid=True), nullable=False),
            sa.Column('permission_level', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('document_id', 'user_id', name='uq_document_permissions_document_user')
        )
        op.create_index('ix_document_permissions_document_id', 'document_permissions', ['document_id'])
        op.create_index('ix_document_permissions_user_id', 'document_permissions', ['user_id'])
    
    # Check if is_public column exists in documents table
    doc_columns = [col['name'] for col in inspector.get_columns('documents')]
    if 'is_public' not in doc_columns:
        # Add is_public column to documents table
        op.add_column('documents', sa.Column('is_public', sa.Boolean(), nullable=True, server_default='false'))
        op.create_index('ix_documents_is_public', 'documents', ['is_public'])


def downgrade():
    # Drop document_permissions table
    op.drop_index('ix_document_permissions_user_id', table_name='document_permissions')
    op.drop_index('ix_document_permissions_document_id', table_name='document_permissions')
    op.drop_table('document_permissions')
    
    # Drop is_public column from documents table
    op.drop_index('ix_documents_is_public', table_name='documents')
    op.drop_column('documents', 'is_public')