"""Enable Row Level Security on document tables

Revision ID: enable_row_level_security
Revises: add_document_permissions
Create Date: 2025-03-27 12:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'enable_row_level_security'
down_revision = 'add_document_permissions'
branch_labels = None
depends_on = None


def upgrade():
    # Enable RLS on documents table
    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY;")
    
    # Enable RLS on chunks table (document sections)
    op.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;")
    
    # Create ownership RLS policy for documents (SELECT)
    op.execute("""
    CREATE POLICY "Users can view their own documents" 
    ON documents FOR SELECT 
    USING (user_id = current_setting('app.current_user_id')::uuid OR is_public = true);
    """)
    
    # Create ownership RLS policy for documents (UPDATE)
    op.execute("""
    CREATE POLICY "Users can update their own documents" 
    ON documents FOR UPDATE
    USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    # Create ownership RLS policy for documents (DELETE)
    op.execute("""
    CREATE POLICY "Users can delete their own documents" 
    ON documents FOR DELETE
    USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    # Create document sharing RLS policy (SELECT)
    op.execute("""
    CREATE POLICY "Users can view documents shared with them" 
    ON documents FOR SELECT 
    USING (id IN (
      SELECT document_id FROM document_permissions WHERE user_id = current_setting('app.current_user_id')::uuid
    ));
    """)
    
    # Create document sharing RLS policy (UPDATE)
    op.execute("""
    CREATE POLICY "Users can update documents shared with write permission" 
    ON documents FOR UPDATE
    USING (id IN (
      SELECT document_id FROM document_permissions 
      WHERE user_id = current_setting('app.current_user_id')::uuid
      AND permission_level IN ('write', 'admin')
    ));
    """)
    
    # Create policy for document sections (chunks) - SELECT
    op.execute("""
    CREATE POLICY "Users can view their own document sections" 
    ON chunks FOR SELECT 
    USING (document_id IN (
      SELECT id FROM documents WHERE user_id = current_setting('app.current_user_id')::uuid OR is_public = true
    ));
    """)
    
    # Create policy for document sections shared with users - SELECT
    op.execute("""
    CREATE POLICY "Users can view document sections shared with them" 
    ON chunks FOR SELECT 
    USING (document_id IN (
      SELECT document_id FROM document_permissions WHERE user_id = current_setting('app.current_user_id')::uuid
    ));
    """)
    
    # Create policy for document sections - UPDATE
    op.execute("""
    CREATE POLICY "Users can update their own document sections" 
    ON chunks FOR UPDATE
    USING (document_id IN (
      SELECT id FROM documents WHERE user_id = current_setting('app.current_user_id')::uuid
    ));
    """)
    
    # Create policy for document sections shared with write permission - UPDATE
    op.execute("""
    CREATE POLICY "Users can update document sections shared with write permission" 
    ON chunks FOR UPDATE
    USING (document_id IN (
      SELECT document_id FROM document_permissions 
      WHERE user_id = current_setting('app.current_user_id')::uuid
      AND permission_level IN ('write', 'admin')
    ));
    """)


def downgrade():
    # Drop RLS policies for documents
    op.execute('DROP POLICY IF EXISTS "Users can view their own documents" ON documents;')
    op.execute('DROP POLICY IF EXISTS "Users can update their own documents" ON documents;')
    op.execute('DROP POLICY IF EXISTS "Users can delete their own documents" ON documents;')
    op.execute('DROP POLICY IF EXISTS "Users can view documents shared with them" ON documents;')
    op.execute('DROP POLICY IF EXISTS "Users can update documents shared with write permission" ON documents;')
    
    # Drop RLS policies for chunks
    op.execute('DROP POLICY IF EXISTS "Users can view their own document sections" ON chunks;')
    op.execute('DROP POLICY IF EXISTS "Users can view document sections shared with them" ON chunks;')
    op.execute('DROP POLICY IF EXISTS "Users can update their own document sections" ON chunks;')
    op.execute('DROP POLICY IF EXISTS "Users can update document sections shared with write permission" ON chunks;')
    
    # Disable RLS
    op.execute("ALTER TABLE documents DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chunks DISABLE ROW LEVEL SECURITY;")