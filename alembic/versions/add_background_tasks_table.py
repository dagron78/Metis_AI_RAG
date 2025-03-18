"""add background tasks table

Revision ID: add_background_tasks
Revises: initial_schema
Create Date: 2025-03-18 19:31:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'add_background_tasks'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create background_tasks table
    op.create_table(
        'background_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('task_type', sa.String(), nullable=False),
        sa.Column('params', JSONB(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, default=50),
        sa.Column('dependencies', sa.Text(), nullable=True),
        sa.Column('schedule_time', sa.DateTime(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True, default=0),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True, default=0.0),
        sa.Column('resource_usage', JSONB(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_background_tasks_status', 'background_tasks', ['status'])
    op.create_index('ix_background_tasks_task_type', 'background_tasks', ['task_type'])
    op.create_index('ix_background_tasks_created_at', 'background_tasks', ['created_at'])
    op.create_index('ix_background_tasks_schedule_time', 'background_tasks', ['schedule_time'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_background_tasks_schedule_time')
    op.drop_index('ix_background_tasks_created_at')
    op.drop_index('ix_background_tasks_task_type')
    op.drop_index('ix_background_tasks_status')
    
    # Drop table
    op.drop_table('background_tasks')