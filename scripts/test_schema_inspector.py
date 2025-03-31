"""
Test script for the PostgreSQL schema inspector and tool
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.connection_manager import connection_manager
from app.db.schema_inspector import schema_inspector
from app.rag.tools.postgresql_tool import PostgreSQLTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_schema_inspector")

async def test_schema_inspector(connection_string: str):
    """
    Test the schema inspector with a PostgreSQL connection
    
    Args:
        connection_string: PostgreSQL connection string
    """
    logger.info("Testing schema inspector with connection: %s", connection_string)
    
    # Register connection
    conn_id = connection_manager.register_connection(connection_string)
    logger.info("Registered connection with ID: %s", conn_id)
    
    try:
        # Test get_schemas
        logger.info("Testing get_schemas...")
        schemas = await schema_inspector.get_schemas(conn_id)
        logger.info("Found %d schemas:", len(schemas))
        for schema in schemas:
            logger.info("  - %s (owner: %s)", schema["schema_name"], schema["owner"])
        
        # Test get_tables for the public schema
        logger.info("\nTesting get_tables for 'public' schema...")
        tables = await schema_inspector.get_tables(conn_id, "public")
        logger.info("Found %d tables in 'public' schema:", len(tables))
        for table in tables:
            logger.info("  - %s (%s, ~%d rows, %s)", 
                       table["table_name"], 
                       table["type"], 
                       table["row_estimate"], 
                       table["total_size"])
        
        # If tables were found, test get_columns for the first table
        if tables:
            first_table = tables[0]["table_name"]
            logger.info("\nTesting get_columns for table '%s'...", first_table)
            columns = await schema_inspector.get_columns(conn_id, first_table)
            logger.info("Found %d columns in table '%s':", len(columns), first_table)
            for column in columns:
                logger.info("  - %s (%s, nullable: %s)", 
                           column["column_name"], 
                           column["data_type"], 
                           column["is_nullable"])
            
            # Test get_indexes
            logger.info("\nTesting get_indexes for table '%s'...", first_table)
            indexes = await schema_inspector.get_indexes(conn_id, first_table)
            logger.info("Found %d indexes in table '%s':", len(indexes), first_table)
            for index in indexes:
                logger.info("  - %s (%s, unique: %s)", 
                           index["index_name"], 
                           index["index_type"], 
                           index["is_unique"])
            
            # Test get_constraints
            logger.info("\nTesting get_constraints for table '%s'...", first_table)
            constraints = await schema_inspector.get_constraints(conn_id, first_table)
            logger.info("Found %d constraints in table '%s':", len(constraints), first_table)
            for constraint in constraints:
                logger.info("  - %s (%s)", 
                           constraint["constraint_name"], 
                           constraint["constraint_type"])
            
            # Test get_table_structure
            logger.info("\nTesting get_table_structure for table '%s'...", first_table)
            structure = await schema_inspector.get_table_structure(conn_id, first_table)
            logger.info("Retrieved table structure for '%s'", first_table)
            logger.info("  - %d columns, %d indexes, %d constraints", 
                       len(structure["columns"]), 
                       len(structure["indexes"]), 
                       len(structure["constraints"]))
        
        # Test get_extensions
        logger.info("\nTesting get_extensions...")
        extensions = await schema_inspector.get_extension_info(conn_id)
        logger.info("Found %d extensions:", len(extensions))
        for ext in extensions:
            logger.info("  - %s (version: %s)", ext["name"], ext["version"])
        
        # Test check_extension_installed for pgvector
        logger.info("\nTesting check_extension_installed for 'vector'...")
        has_pgvector = await schema_inspector.check_extension_installed(conn_id, "vector")
        logger.info("pgvector installed: %s", has_pgvector)
        
        # Test get_pgvector_info
        logger.info("\nTesting get_pgvector_info...")
        pgvector_info = await schema_inspector.get_pgvector_info(conn_id)
        logger.info("pgvector info: %s", pgvector_info)
        
        return True
    except Exception as e:
        logger.error("Error testing schema inspector: %s", str(e))
        return False
    finally:
        # Close connection
        await connection_manager.close(conn_id)
        logger.info("Closed connection")

async def test_postgresql_tool(connection_string: str):
    """
    Test the PostgreSQL tool with a PostgreSQL connection
    
    Args:
        connection_string: PostgreSQL connection string
    """
    logger.info("\n\nTesting PostgreSQL tool with connection: %s", connection_string)
    
    # Register connection
    conn_id = connection_manager.register_connection(connection_string)
    logger.info("Registered connection with ID: %s", conn_id)
    
    # Create PostgreSQL tool
    pg_tool = PostgreSQLTool()
    
    try:
        # Test get_schemas operation
        logger.info("Testing get_schemas operation...")
        result = await pg_tool.execute({
            "operation": "get_schemas",
            "connection_id": conn_id
        })
        logger.info("Found %d schemas in %.2f seconds", 
                   len(result["schemas"]), 
                   result["execution_time"])
        
        # Test get_tables operation
        logger.info("\nTesting get_tables operation...")
        result = await pg_tool.execute({
            "operation": "get_tables",
            "connection_id": conn_id,
            "schema": "public"
        })
        logger.info("Found %d tables in 'public' schema in %.2f seconds", 
                   len(result["tables"]), 
                   result["execution_time"])
        
        # If tables were found, test get_columns operation for the first table
        if result["tables"]:
            first_table = result["tables"][0]["table_name"]
            
            # Test get_columns operation
            logger.info("\nTesting get_columns operation for table '%s'...", first_table)
            result = await pg_tool.execute({
                "operation": "get_columns",
                "connection_id": conn_id,
                "table_name": first_table,
                "schema": "public"
            })
            logger.info("Found %d columns in table '%s' in %.2f seconds", 
                       len(result["columns"]), 
                       first_table, 
                       result["execution_time"])
            
            # Test explain_query operation
            logger.info("\nTesting explain_query operation...")
            result = await pg_tool.execute({
                "operation": "explain_query",
                "connection_id": conn_id,
                "query": f"SELECT * FROM {first_table} LIMIT 10",
                "explain_type": "analyze"
            })
            logger.info("Explained query in %.2f seconds", result["execution_time"])
            logger.info("Plan:\n%s", result.get("plan_text", ""))
        
        # Test get_extensions operation
        logger.info("\nTesting get_extensions operation...")
        result = await pg_tool.execute({
            "operation": "get_extensions",
            "connection_id": conn_id
        })
        logger.info("Found %d extensions in %.2f seconds", 
                   len(result["extensions"]), 
                   result["execution_time"])
        
        # Test check_extension operation for pgvector
        logger.info("\nTesting check_extension operation for 'vector'...")
        result = await pg_tool.execute({
            "operation": "check_extension",
            "connection_id": conn_id,
            "extension_name": "vector"
        })
        logger.info("pgvector installed: %s (checked in %.2f seconds)", 
                   result["installed"], 
                   result["execution_time"])
        
        # Test get_pgvector_info operation
        logger.info("\nTesting get_pgvector_info operation...")
        result = await pg_tool.execute({
            "operation": "get_pgvector_info",
            "connection_id": conn_id
        })
        logger.info("pgvector info retrieved in %.2f seconds", result["execution_time"])
        if result["pgvector_info"].get("installed", False):
            logger.info("pgvector version: %s", result["pgvector_info"].get("version", "unknown"))
            logger.info("Vector columns: %d", len(result["pgvector_info"].get("vector_columns", [])))
            logger.info("Vector indexes: %d", len(result["pgvector_info"].get("vector_indexes", [])))
        
        return True
    except Exception as e:
        logger.error("Error testing PostgreSQL tool: %s", str(e))
        return False
    finally:
        # Close connection
        await connection_manager.close(conn_id)
        logger.info("Closed connection")

async def main():
    """Main function"""
    # Get PostgreSQL connection string from environment variable or use a default
    connection_string = os.environ.get(
        "POSTGRES_CONNECTION_STRING", 
        "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    
    # Test schema inspector
    inspector_success = await test_schema_inspector(connection_string)
    
    # Test PostgreSQL tool
    tool_success = await test_postgresql_tool(connection_string)
    
    # Report results
    if inspector_success and tool_success:
        logger.info("\n\nAll tests passed successfully!")
        return 0
    else:
        logger.error("\n\nSome tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)