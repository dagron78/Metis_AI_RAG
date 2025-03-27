"""Fix RLS current_setting function

Revision ID: fix_rls_current_setting
Revises: enable_row_level_security
Create Date: 2025-03-27 17:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_rls_current_setting'
down_revision = 'enable_row_level_security'
branch_labels = None
depends_on = None


def upgrade():
    # Create a function to safely get the app.current_user_id setting
    # This function will return NULL if the setting doesn't exist
    op.execute("""
    CREATE OR REPLACE FUNCTION safe_get_current_user_id() RETURNS uuid AS $$
    DECLARE
        user_id uuid;
    BEGIN
        BEGIN
            -- Try to get the current user ID
            user_id := current_setting('app.current_user_id')::uuid;
        EXCEPTION WHEN OTHERS THEN
            -- If it fails, return NULL
            user_id := NULL;
        END;
        RETURN user_id;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Update the RLS policies to use the safe function
    # Update ownership RLS policy for documents (SELECT)
    op.execute('DROP POLICY IF EXISTS "Users can view their own documents" ON documents;')
    op.execute("""
    CREATE POLICY "Users can view their own documents"
    ON documents FOR SELECT
    USING (user_id = safe_get_current_user_id() OR is_public = true);
    """)
    
    # Update ownership RLS policy for documents (UPDATE)
    op.execute('DROP POLICY IF EXISTS "Users can update their own documents" ON documents;')
    op.execute("""
    CREATE POLICY "Users can update their own documents"
    ON documents FOR UPDATE
    USING (user_id = safe_get_current_user_id());
    """)
    
    # Update ownership RLS policy for documents (DELETE)
    op.execute('DROP POLICY IF EXISTS "Users can delete their own documents" ON documents;')
    op.execute("""
    CREATE POLICY "Users can delete their own documents"
    ON documents FOR DELETE
    USING (user_id = safe_get_current_user_id());
    """)
    
    # Update document sharing RLS policy (SELECT)
    op.execute('DROP POLICY IF EXISTS "Users can view documents shared with them" ON documents;')
    op.execute("""
    CREATE POLICY "Users can view documents shared with them"
    ON documents FOR SELECT
    USING (id IN (
      SELECT document_id FROM document_permissions WHERE user_id = safe_get_current_user_id()
    ));
    """)
    
    # Update document sharing RLS policy (UPDATE)
    op.execute('DROP POLICY IF EXISTS "Users can update documents shared with write permission" ON documents;')
    op.execute("""
    CREATE POLICY "Users can update documents shared with write permission"
    ON documents FOR UPDATE
    USING (id IN (
      SELECT document_id FROM document_permissions
      WHERE user_id = safe_get_current_user_id()
      AND permission_level IN ('write', 'admin')
    ));
    """)
    
    # Update policy for document sections (chunks) - SELECT
    op.execute('DROP POLICY IF EXISTS "Users can view their own document sections" ON chunks;')
    op.execute("""
    CREATE POLICY "Users can view their own document sections"
    ON chunks FOR SELECT
    USING (document_id IN (
      SELECT id FROM documents WHERE user_id = safe_get_current_user_id() OR is_public = true
    ));
    """)
    
    # Update policy for document sections shared with users - SELECT
    op.execute('DROP POLICY IF EXISTS "Users can view document sections shared with them" ON chunks;')
    op.execute("""
    CREATE POLICY "Users can view document sections shared with them"
    ON chunks FOR SELECT
    USING (document_id IN (
      SELECT document_id FROM document_permissions WHERE user_id = safe_get_current_user_id()
    ));
    """)
    
    # Update policy for document sections - UPDATE
    op.execute('DROP POLICY IF EXISTS "Users can update their own document sections" ON chunks;')
    op.execute("""
    CREATE POLICY "Users can update their own document sections"
    ON chunks FOR UPDATE
    USING (document_id IN (
      SELECT id FROM documents WHERE user_id = safe_get_current_user_id()
    ));
    """)
    
    # Update policy for document sections shared with write permission - UPDATE
    op.execute('DROP POLICY IF EXISTS "Users can update document sections shared with write permission" ON chunks;')
    op.execute("""
    CREATE POLICY "Users can update document sections shared with write permission"
    ON chunks FOR UPDATE
    USING (document_id IN (
      SELECT document_id FROM document_permissions
      WHERE user_id = safe_get_current_user_id()
      AND permission_level IN ('write', 'admin')
    ));
    """)


def downgrade():
    # Revert to the original RLS policies
    # Revert ownership RLS policy for documents (SELECT)
    op.execute('DROP POLICY IF EXISTS "Users can view their own documents" ON documents;')
    op.execute("""
    CREATE POLICY "Users can view their own documents"
    ON documents FOR SELECT
    USING (user_id = current_setting('app.current_user_id')::uuid OR is_public = true);
    """)
    
    # Revert ownership RLS policy for documents (UPDATE)
    op.execute('DROP POLICY IF EXISTS "Users can update their own documents" ON documents;')
    op.execute("""
    CREATE POLICY "Users can update their own documents"
    ON documents FOR UPDATE
    USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    # Revert ownership RLS policy for documents (DELETE)
    op.execute('DROP POLICY IF EXISTS "Users can delete their own documents" ON documents;')
    op.execute("""
    CREATE POLICY "Users can delete their own documents"
    ON documents FOR DELETE
    USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    # Revert document sharing RLS policy (SELECT)
    op.execute('DROP POLICY IF EXISTS "Users can view documents shared with them" ON documents;')
    op.execute("""
    CREATE POLICY "Users can view documents shared with them"
    ON documents FOR SELECT
    USING (id IN (
      SELECT document_id FROM document_permissions WHERE user_id = current_setting('app.current_user_id')::uuid
    ));
    """)
    
    # Revert document sharing RLS policy (UPDATE)
    op.execute('DROP POLICY IF EXISTS "Users can update documents shared with write permission" ON documents;')
    op.execute("""
    CREATE POLICY "Users can update documents shared with write permission"
    ON documents FOR UPDATE
    USING (id IN (
      SELECT document_id FROM document_permissions
      WHERE user_id = current_setting('app.current_user_id')::uuid
      AND permission_level IN ('write', 'admin')
    ));
    """)
    
    # Revert policy for document sections (chunks) - SELECT
    op.execute('DROP POLICY IF EXISTS "Users can view their own document sections" ON chunks;')
    op.execute("""
    CREATE POLICY "Users can view their own document sections"
    ON chunks FOR SELECT
    USING (document_id IN (
      SELECT id FROM documents WHERE user_id = current_setting('app.current_user_id')::uuid OR is_public = true
    ));
    """)
    
    # Revert policy for document sections shared with users - SELECT
    op.execute('DROP POLICY IF EXISTS "Users can view document sections shared with them" ON chunks;')
    op.execute("""
    CREATE POLICY "Users can view document sections shared with them"
    ON chunks FOR SELECT
    USING (document_id IN (
      SELECT document_id FROM document_permissions WHERE user_id = current_setting('app.current_user_id')::uuid
    ));
    """)
    
    # Revert policy for document sections - UPDATE
    op.execute('DROP POLICY IF EXISTS "Users can update their own document sections" ON chunks;')
    op.execute("""
    CREATE POLICY "Users can update their own document sections"
    ON chunks FOR UPDATE
    USING (document_id IN (
      SELECT id FROM documents WHERE user_id = current_setting('app.current_user_id')::uuid
    ));
    """)
    
    # Revert policy for document sections shared with write permission - UPDATE
    op.execute('DROP POLICY IF EXISTS "Users can update document sections shared with write permission" ON chunks;')
    op.execute("""
    CREATE POLICY "Users can update document sections shared with write permission"
    ON chunks FOR UPDATE
    USING (document_id IN (
      SELECT document_id FROM document_permissions
      WHERE user_id = current_setting('app.current_user_id')::uuid
      AND permission_level IN ('write', 'admin')
    ));
    """)
    
    # Drop the safe function
    op.execute("DROP FUNCTION IF EXISTS safe_get_current_user_id();")