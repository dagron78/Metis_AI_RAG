"""Initial database schema

Revision ID: initial_schema
Revises: 
Create Date: 2025-03-18 16:27:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create folders table
    op.create_table(
        'folders',
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('parent_path', sa.String(), nullable=True),
        sa.Column('document_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_path'], ['folders.path'], ),
        sa.PrimaryKeyConstraint('path')
    )
    op.create_index('ix_folders_parent_path', 'folders', ['parent_path'])

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('folder', sa.String(), nullable=True),
        sa.Column('uploaded', sa.DateTime(), nullable=True),
        sa.Column('processing_status', sa.String(), nullable=True),
        sa.Column('processing_strategy', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['folder'], ['folders.path'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_filename', 'documents', ['filename'])
    op.create_index('ix_documents_folder', 'documents', ['folder'])
    op.create_index('ix_documents_processing_status', 'documents', ['processing_status'])

    # Create chunks table
    op.create_table(
        'chunks',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('document_id', UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('index', sa.Integer(), nullable=False),
        sa.Column('embedding_quality', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_document_id_index', 'chunks', ['document_id', 'index'])

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_tags_name', 'tags', ['name'])

    # Create document_tags association table
    op.create_table(
        'document_tags',
        sa.Column('document_id', UUID(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'])
    op.create_index('ix_conversations_updated_at', 'conversations', ['updated_at'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_timestamp', 'messages', ['timestamp'])

    # Create citations table
    op.create_table(
        'citations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('document_id', UUID(), nullable=True),
        sa.Column('chunk_id', UUID(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('character_range_start', sa.Integer(), nullable=True),
        sa.Column('character_range_end', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_citations_chunk_id', 'citations', ['chunk_id'])
    op.create_index('ix_citations_document_id', 'citations', ['document_id'])
    op.create_index('ix_citations_message_id', 'citations', ['message_id'])

    # Create processing_jobs table
    op.create_table(
        'processing_jobs',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('document_count', sa.Integer(), nullable=True),
        sa.Column('processed_count', sa.Integer(), nullable=True),
        sa.Column('strategy', sa.String(), nullable=True),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_processing_jobs_created_at', 'processing_jobs', ['created_at'])
    op.create_index('ix_processing_jobs_status', 'processing_jobs', ['status'])

    # Create analytics_queries table
    op.create_table(
        'analytics_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('use_rag', sa.Boolean(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('document_ids', JSONB(), nullable=True),
        sa.Column('query_type', sa.String(), nullable=True),
        sa.Column('successful', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_queries_model', 'analytics_queries', ['model'])
    op.create_index('ix_analytics_queries_query_type', 'analytics_queries', ['query_type'])
    op.create_index('ix_analytics_queries_timestamp', 'analytics_queries', ['timestamp'])


def downgrade():
    op.drop_table('analytics_queries')
    op.drop_table('processing_jobs')
    op.drop_table('citations')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('document_tags')
    op.drop_table('tags')
    op.drop_table('chunks')
    op.drop_table('documents')
    op.drop_table('folders')