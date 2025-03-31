"""merge_heads_for_document_permissions

Revision ID: f7e702fc686e
Revises: enable_row_level_security, ensure_doc_metadata_column, merge_heads
Create Date: 2025-03-27 12:53:36.110083

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7e702fc686e'
down_revision = ('enable_row_level_security', 'ensure_doc_metadata_column', 'merge_heads')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass