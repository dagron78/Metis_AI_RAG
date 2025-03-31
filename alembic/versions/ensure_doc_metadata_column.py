"""ensure_doc_metadata_column

Revision ID: ensure_doc_metadata_column
Revises: rename_metadata_columns
Create Date: 2025-03-25 15:42:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'ensure_doc_metadata_column'
down_revision = 'rename_metadata_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Check if doc_metadata column exists in documents table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    # Add doc_metadata column if it doesn't exist
    if 'doc_metadata' not in columns:
        op.add_column('documents', 
                     sa.Column('doc_metadata', JSONB(), 
                              nullable=True, 
                              server_default=text("'{}'::jsonb")))
        
        # If metadata column exists, migrate data from metadata to doc_metadata
        if 'metadata' in columns:
            op.execute(text(
                "UPDATE documents SET doc_metadata = metadata::jsonb WHERE metadata IS NOT NULL"
            ))
            # Drop the old metadata column
            op.drop_column('documents', 'metadata')


def downgrade():
    # This is a safety migration, so downgrade does nothing
    pass