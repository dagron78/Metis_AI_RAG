"""rename_metadata_columns

Revision ID: rename_metadata_columns
Revises: update_metadata_to_jsonb
Create Date: 2025-03-25 14:34:44.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'rename_metadata_columns'
down_revision = 'update_metadata_to_jsonb'
branch_labels = None
depends_on = None


def upgrade():
    # Rename metadata column in documents table
    op.alter_column('documents', 'metadata', new_column_name='doc_metadata', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb"))
    
    # Rename metadata column in chunks table
    op.alter_column('chunks', 'metadata', new_column_name='chunk_metadata', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb"))
    
    # Rename metadata column in conversations table
    op.alter_column('conversations', 'metadata', new_column_name='conv_metadata', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb"))
    
    # Rename metadata column in processing_jobs table
    op.alter_column('processing_jobs', 'metadata', new_column_name='job_metadata', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb"))
    
    # Rename document_ids column in analytics_queries table
    op.alter_column('analytics_queries', 'document_ids', new_column_name='document_id_list', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb"))


def downgrade():
    # Revert column name changes
    op.alter_column('documents', 'doc_metadata', new_column_name='metadata', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb"))
    
    op.alter_column('chunks', 'chunk_metadata', new_column_name='metadata', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb"))
    
    op.alter_column('conversations', 'conv_metadata', new_column_name='metadata', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb"))
    
    op.alter_column('processing_jobs', 'job_metadata', new_column_name='metadata', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb"))
    
    op.alter_column('analytics_queries', 'document_id_list', new_column_name='document_ids', 
                   existing_type=JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb"))