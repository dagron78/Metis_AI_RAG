"""Add memories table for explicit memory storage

Revision ID: add_memories_table
Revises: bb56459de93d
Create Date: 2025-03-31 18:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'add_memories_table'
down_revision = 'bb56459de93d'
branch_labels = None
depends_on = None

def upgrade():
    # Create memories table
    op.create_table(
        'memories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('label', sa.String(50), nullable=False, server_default='explicit_memory'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Add index for faster lookups by conversation_id
    op.create_index(
        'ix_memories_conversation_id',
        'memories',
        ['conversation_id']
    )
    
    # Add index for faster lookups by label
    op.create_index(
        'ix_memories_label',
        'memories',
        ['label']
    )

def downgrade():
    # Drop indexes
    op.drop_index('ix_memories_label')
    op.drop_index('ix_memories_conversation_id')
    
    # Drop memories table
    op.drop_table('memories')