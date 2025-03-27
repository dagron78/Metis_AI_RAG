"""add_notifications_table

Revision ID: add_notifications_table
Revises: add_roles_tables
Create Date: 2025-03-27 16:12:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'add_notifications_table'
down_revision = 'add_roles_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])


def downgrade():
    op.drop_table('notifications')