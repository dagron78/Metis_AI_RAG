"""
API endpoints for database schema introspection
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.connection_manager import connection_manager
from app.db.schema_inspector import schema_inspector
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/schema",
    tags=["schema"],
    responses={404: {"description": "Not found"}},
)

@router.get("/connections")
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all PostgreSQL connections available to the user
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view database connections")
    
    # Get all connections
    connections = []
    for conn_id, conn_string in connection_manager._connection_map.items():
        conn_type = connection_manager.get_connection_type(conn_id)
        if conn_type == 'postgres':
            # Mask password in connection string for security
            masked_conn_string = mask_connection_string(conn_string)
            connections.append({
                "id": conn_id,
                "connection_string": masked_conn_string,
                "type": conn_type
            })
    
    return {"connections": connections}

@router.get("/schemas")
async def get_schemas(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of schemas in the database
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view database schemas")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get schemas
        schemas = await schema_inspector.get_schemas(connection_id)
        return {"schemas": schemas}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schemas: {str(e)}")

@router.get("/tables")
async def get_tables(
    connection_id: str,
    schema: str = "public",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of tables in the specified schema
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view database tables")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get tables
        tables = await schema_inspector.get_tables(connection_id, schema)
        return {"tables": tables, "schema": schema}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tables: {str(e)}")

@router.get("/columns")
async def get_columns(
    connection_id: str,
    table_name: str,
    schema: str = "public",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of columns for the specified table
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view table columns")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get columns
        columns = await schema_inspector.get_columns(connection_id, table_name, schema)
        return {"columns": columns, "table_name": table_name, "schema": schema}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving columns: {str(e)}")

@router.get("/indexes")
async def get_indexes(
    connection_id: str,
    table_name: str,
    schema: str = "public",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of indexes for the specified table
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view table indexes")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get indexes
        indexes = await schema_inspector.get_indexes(connection_id, table_name, schema)
        return {"indexes": indexes, "table_name": table_name, "schema": schema}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving indexes: {str(e)}")

@router.get("/constraints")
async def get_constraints(
    connection_id: str,
    table_name: str,
    schema: str = "public",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of constraints for the specified table
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view table constraints")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get constraints
        constraints = await schema_inspector.get_constraints(connection_id, table_name, schema)
        return {"constraints": constraints, "table_name": table_name, "schema": schema}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving constraints: {str(e)}")

@router.get("/foreign-keys")
async def get_foreign_keys(
    connection_id: str,
    table_name: str,
    schema: str = "public",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of foreign keys for the specified table
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view foreign keys")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get foreign keys
        foreign_keys = await schema_inspector.get_foreign_keys(connection_id, table_name, schema)
        return {"foreign_keys": foreign_keys, "table_name": table_name, "schema": schema}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving foreign keys: {str(e)}")

@router.get("/table-structure")
async def get_table_structure(
    connection_id: str,
    table_name: str,
    schema: str = "public",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive structure information for a table
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view table structure")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get table structure
        table_structure = await schema_inspector.get_table_structure(connection_id, table_name, schema)
        return {"table_structure": table_structure}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving table structure: {str(e)}")

@router.get("/database-structure")
async def get_database_structure(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive structure information for the entire database
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view database structure")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get database structure
        database_structure = await schema_inspector.get_database_structure(connection_id)
        return {"database_structure": database_structure}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving database structure: {str(e)}")

@router.get("/extensions")
async def get_extensions(
    connection_id: str,
    extension_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about installed PostgreSQL extensions
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view extensions")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get extensions
        extensions = await schema_inspector.get_extension_info(connection_id, extension_name)
        return {"extensions": extensions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving extensions: {str(e)}")

@router.get("/pgvector-info")
async def get_pgvector_info(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about pgvector extension if installed
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can view pgvector information")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get pgvector info
        pgvector_info = await schema_inspector.get_pgvector_info(connection_id)
        return {"pgvector_info": pgvector_info}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving pgvector information: {str(e)}")

@router.post("/explain-query")
async def explain_query(
    connection_id: str,
    query: str,
    explain_type: str = "simple",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Explain a SQL query execution plan
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can explain queries")
    
    try:
        # Validate connection
        conn_type = connection_manager.get_connection_type(connection_id)
        if conn_type != 'postgres':
            raise HTTPException(status_code=400, detail="Connection is not a PostgreSQL connection")
        
        # Get connection
        conn = await connection_manager.get_postgres_connection(connection_id)
        
        try:
            # Build EXPLAIN command based on type
            explain_options = ""
            if explain_type == "analyze":
                explain_options = "ANALYZE"
            elif explain_type == "verbose":
                explain_options = "VERBOSE"
            elif explain_type == "analyze_verbose":
                explain_options = "ANALYZE, VERBOSE"
            elif explain_type == "analyze_verbose_buffers":
                explain_options = "ANALYZE, VERBOSE, BUFFERS"
            elif explain_type == "json":
                explain_options = "FORMAT JSON"
            elif explain_type == "analyze_json":
                explain_options = "ANALYZE, FORMAT JSON"
            
            # Execute EXPLAIN
            explain_query = f"EXPLAIN ({explain_options}) {query}"
            rows = await conn.fetch(explain_query)
            
            # Format result
            if explain_type in ["json", "analyze_json"]:
                # For JSON format, return the parsed JSON
                plan = rows[0][0]
                return {
                    "query": query,
                    "plan": plan
                }
            else:
                # For text format, concatenate the rows
                plan_lines = [row[0] for row in rows]
                plan_text = "\n".join(plan_lines)
                
                return {
                    "query": query,
                    "plan_text": plan_text
                }
        finally:
            # Release connection back to pool
            await connection_manager.release_postgres_connection(connection_id, conn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error explaining query: {str(e)}")

def mask_connection_string(connection_string: str) -> str:
    """
    Mask password in connection string for security
    
    Args:
        connection_string: Database connection string
        
    Returns:
        Masked connection string
    """
    import re
    
    # Mask password in PostgreSQL connection string
    if connection_string.startswith('postgresql://'):
        # Find the password part
        match = re.search(r'postgresql://([^:]+):([^@]+)@', connection_string)
        if match:
            username = match.group(1)
            password = match.group(2)
            masked_password = '*' * len(password)
            masked_conn_string = connection_string.replace(
                f"{username}:{password}@", 
                f"{username}:{masked_password}@"
            )
            return masked_conn_string
    
    return connection_string