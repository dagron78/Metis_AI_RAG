# Row Level Security (RLS) Fix

## Issue

The Metis RAG application was experiencing errors related to PostgreSQL Row Level Security (RLS) policies. The application was trying to use `current_setting('app.current_user_id')` in PostgreSQL RLS policies, but this variable wasn't properly configured in the database, causing syntax errors like:

```
syntax error at or near "NULL"
[SQL: SET app.current_user_id = NULL]
```

## Solution

A new Alembic migration (`fix_rls_current_setting.py`) was created to address this issue. The migration:

1. Creates a custom PostgreSQL function `safe_get_current_user_id()` that safely handles the case when the `app.current_user_id` variable doesn't exist:

```sql
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
```

2. Updates all RLS policies to use this safe function instead of directly using `current_setting()`:

```sql
CREATE POLICY "Users can view their own documents" 
ON documents FOR SELECT 
USING (user_id = safe_get_current_user_id() OR is_public = true);
```

## Implementation Details

The migration modifies the following RLS policies:

- "Users can view their own documents"
- "Users can update their own documents"
- "Users can delete their own documents"
- "Users can view documents shared with them"
- "Users can update documents shared with write permission"
- "Users can view their own document sections"
- "Users can view document sections shared with them"
- "Users can update their own document sections"
- "Users can update document sections shared with write permission"

## How to Apply

The migration can be applied using the following command:

```bash
alembic upgrade heads
```

## Rollback

If needed, the migration can be rolled back using:

```bash
alembic downgrade fix_rls_current_setting-1
```

## Future Considerations

For a more permanent solution, consider:

1. Properly configuring the PostgreSQL database to support custom variables in the `app` namespace
2. Adding the following to your `postgresql.conf` file:
   ```
   custom_variable_classes = 'app'
   ```
3. Or using a different approach for RLS that doesn't rely on session variables