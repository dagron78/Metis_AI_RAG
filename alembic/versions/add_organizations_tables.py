"""add_organizations_tables

Revision ID: add_organizations_tables
Revises: add_notifications_table
Create Date: 2025-03-27 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'add_organizations_tables'
down_revision = 'add_notifications_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('settings', JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_organizations_name', 'organizations', ['name'])

    # Create organization_members table
    op.create_table(
        'organization_members',
        sa.Column('organization_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('organization_id', 'user_id')
    )
    op.create_index('ix_organization_members_organization_id', 'organization_members', ['organization_id'])
    op.create_index('ix_organization_members_user_id', 'organization_members', ['user_id'])

    # Add organization_id to documents table
    op.add_column('documents', sa.Column('organization_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_documents_organization_id', 'documents', 'organizations',
        ['organization_id'], ['id']
    )
    op.create_index('ix_documents_organization_id', 'documents', ['organization_id'])


def downgrade():
    # Remove organization_id from documents table
    op.drop_index('ix_documents_organization_id', table_name='documents')
    op.drop_constraint('fk_documents_organization_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'organization_id')

    # Drop organization_members table
    op.drop_table('organization_members')

    # Drop organizations table
    op.drop_table('organizations')