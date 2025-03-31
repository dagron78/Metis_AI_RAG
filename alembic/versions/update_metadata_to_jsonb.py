"""Update metadata columns to use JSONB

Revision ID: update_metadata_to_jsonb
Revises: initial_schema
Create Date: 2025-03-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'update_metadata_to_jsonb'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    # For PostgreSQL, convert JSON to JSONB
    if op.get_bind().dialect.name == 'postgresql':
        # Update documents table
        op.alter_column('documents', 'metadata', 
                        type_=JSONB, 
                        postgresql_using='metadata::jsonb')
        
        # Update chunks table
        op.alter_column('chunks', 'metadata', 
                        type_=JSONB, 
                        postgresql_using='metadata::jsonb')
        
        # Update conversations table
        op.alter_column('conversations', 'metadata', 
                        type_=JSONB, 
                        postgresql_using='metadata::jsonb')
        
        # Update processing_jobs table
        op.alter_column('processing_jobs', 'metadata', 
                        type_=JSONB, 
                        postgresql_using='metadata::jsonb')
        
        # Update background_tasks table
        op.alter_column('background_tasks', 'metadata', 
                        type_=JSONB, 
                        postgresql_using='metadata::jsonb')
        
        # Update params column in background_tasks
        op.alter_column('background_tasks', 'params', 
                        type_=JSONB, 
                        postgresql_using='params::jsonb')
        
        # Update resource_usage column in background_tasks
        op.alter_column('background_tasks', 'resource_usage', 
                        type_=JSONB, 
                        postgresql_using='resource_usage::jsonb')
        
        # Update document_ids column in analytics_queries
        op.alter_column('analytics_queries', 'document_ids', 
                        type_=JSONB, 
                        postgresql_using='document_ids::jsonb')

def downgrade():
    # For PostgreSQL, convert JSONB back to JSON
    if op.get_bind().dialect.name == 'postgresql':
        # Update documents table
        op.alter_column('documents', 'metadata', 
                        type_=sa.JSON, 
                        postgresql_using='metadata::json')
        
        # Update chunks table
        op.alter_column('chunks', 'metadata', 
                        type_=sa.JSON, 
                        postgresql_using='metadata::json')
        
        # Update conversations table
        op.alter_column('conversations', 'metadata', 
                        type_=sa.JSON, 
                        postgresql_using='metadata::json')
        
        # Update processing_jobs table
        op.alter_column('processing_jobs', 'metadata', 
                        type_=sa.JSON, 
                        postgresql_using='metadata::json')
        
        # Update background_tasks table
        op.alter_column('background_tasks', 'metadata', 
                        type_=sa.JSON, 
                        postgresql_using='metadata::json')
        
        # Update params column in background_tasks
        op.alter_column('background_tasks', 'params', 
                        type_=sa.JSON, 
                        postgresql_using='params::json')
        
        # Update resource_usage column in background_tasks
        op.alter_column('background_tasks', 'resource_usage', 
                        type_=sa.JSON, 
                        postgresql_using='resource_usage::json')
        
        # Update document_ids column in analytics_queries
        op.alter_column('analytics_queries', 'document_ids', 
                        type_=sa.JSON, 
                        postgresql_using='document_ids::json')