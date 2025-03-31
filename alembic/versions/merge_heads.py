"""merge heads

Revision ID: merge_heads
Revises: add_user_id_columns, add_users_table
Create Date: 2025-03-21 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads'
down_revision = ('add_user_id_columns', 'add_users_table')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration, no schema changes needed
    pass


def downgrade():
    # This is a merge migration, no schema changes needed
    pass