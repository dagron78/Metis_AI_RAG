"""merge_heads_for_phase4

Revision ID: bb56459de93d
Revises: add_organizations_tables, f7e702fc686e
Create Date: 2025-03-27 16:22:33.920973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb56459de93d'
down_revision = ('add_organizations_tables', 'f7e702fc686e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass