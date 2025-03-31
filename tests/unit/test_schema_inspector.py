"""
Unit tests for the schema inspector
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.db.schema_inspector import SchemaInspector
from app.rag.tools.postgresql_tool import PostgreSQLTool

@pytest.fixture
def schema_inspector():
    """Create a schema inspector instance for testing"""
    return SchemaInspector()

@pytest.fixture
def postgresql_tool():
    """Create a PostgreSQL tool instance for testing"""
    return PostgreSQLTool()

@pytest.mark.asyncio
async def test_get_schemas(schema_inspector):
    """Test getting schemas"""
    # Mock the connection manager
    with patch('app.db.schema_inspector.connection_manager') as mock_conn_manager:
        # Setup mock connection
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"schema_name": "public", "owner": "postgres", "description": "standard public schema"},
            {"schema_name": "app", "owner": "app_user", "description": "application schema"}
        ]
        
        # Setup connection manager mocks
        mock_conn_manager.get_connection_type.return_value = 'postgres'
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_conn_manager.release_postgres_connection = AsyncMock()
        
        # Call the method
        result = await schema_inspector.get_schemas("test_conn_id")
        
        # Verify results
        assert len(result) == 2
        assert result[0]["schema_name"] == "public"
        assert result[1]["schema_name"] == "app"
        
        # Verify mocks were called correctly
        mock_conn_manager.get_connection_type.assert_called_once_with("test_conn_id")
        mock_conn_manager.get_postgres_connection.assert_called_once_with("test_conn_id")
        mock_conn.fetch.assert_called_once()
        mock_conn_manager.release_postgres_connection.assert_called_once_with("test_conn_id", mock_conn)

@pytest.mark.asyncio
async def test_get_tables(schema_inspector):
    """Test getting tables"""
    # Mock the connection manager
    with patch('app.db.schema_inspector.connection_manager') as mock_conn_manager:
        # Setup mock connection
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                "table_name": "users", 
                "owner": "postgres", 
                "description": "User accounts",
                "row_estimate": 1000,
                "total_size": "1024 kB",
                "type": "table"
            },
            {
                "table_name": "documents", 
                "owner": "postgres", 
                "description": "Document storage",
                "row_estimate": 5000,
                "total_size": "8192 kB",
                "type": "table"
            }
        ]
        mock_conn.fetchval.return_value = 1042  # Exact count for first table
        
        # Setup connection manager mocks
        mock_conn_manager.get_connection_type.return_value = 'postgres'
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_conn_manager.release_postgres_connection = AsyncMock()
        
        # Call the method
        result = await schema_inspector.get_tables("test_conn_id", "public")
        
        # Verify results
        assert len(result) == 2
        assert result[0]["table_name"] == "users"
        assert result[1]["table_name"] == "documents"
        assert result[0]["exact_row_count"] == 1042
        
        # Verify mocks were called correctly
        mock_conn_manager.get_connection_type.assert_called_once_with("test_conn_id")
        mock_conn_manager.get_postgres_connection.assert_called_once_with("test_conn_id")
        assert mock_conn.fetch.call_count == 1
        assert mock_conn.fetchval.call_count == 1
        mock_conn_manager.release_postgres_connection.assert_called_once_with("test_conn_id", mock_conn)

@pytest.mark.asyncio
async def test_postgresql_tool_get_schemas(postgresql_tool):
    """Test PostgreSQL tool get_schemas operation"""
    # Mock the schema inspector
    with patch('app.rag.tools.postgresql_tool.schema_inspector') as mock_schema_inspector:
        # Setup mock schema inspector
        mock_schema_inspector.get_schemas = AsyncMock()
        mock_schema_inspector.get_schemas.return_value = [
            {"schema_name": "public", "owner": "postgres", "description": "standard public schema"},
            {"schema_name": "app", "owner": "app_user", "description": "application schema"}
        ]
        
        # Mock connection manager
        with patch('app.rag.tools.postgresql_tool.connection_manager') as mock_conn_manager:
            mock_conn_manager.get_connection_type.return_value = 'postgres'
            
            # Call the method
            result = await postgresql_tool.execute({
                "operation": "get_schemas",
                "connection_id": "test_conn_id"
            })
            
            # Verify results
            assert "schemas" in result
            assert len(result["schemas"]) == 2
            assert result["schemas"][0]["schema_name"] == "public"
            assert result["schemas"][1]["schema_name"] == "app"
            assert "execution_time" in result
            
            # Verify mocks were called correctly
            mock_conn_manager.get_connection_type.assert_called_once_with("test_conn_id")
            mock_schema_inspector.get_schemas.assert_called_once_with("test_conn_id")

@pytest.mark.asyncio
async def test_postgresql_tool_explain_query(postgresql_tool):
    """Test PostgreSQL tool explain_query operation"""
    # Mock the connection manager
    with patch('app.rag.tools.postgresql_tool.connection_manager') as mock_conn_manager:
        # Setup mock connection
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            ("Seq Scan on users  (cost=0.00..25.88 rows=6 width=90) (actual time=0.019..0.021 rows=3 loops=1)",),
            ("  Filter: ((email)::text ~~ '%example.com'::text)",),
            ("  Rows Removed by Filter: 7",),
            ("Planning Time: 0.066 ms",),
            ("Execution Time: 0.048 ms",)
        ]
        
        # Setup connection manager mocks
        mock_conn_manager.get_connection_type.return_value = 'postgres'
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_conn_manager.release_postgres_connection = AsyncMock()
        
        # Call the method
        result = await postgresql_tool.execute({
            "operation": "explain_query",
            "connection_id": "test_conn_id",
            "query": "SELECT * FROM users WHERE email LIKE '%example.com'",
            "explain_type": "analyze"
        })
        
        # Verify results
        assert "query" in result
        assert "plan_text" in result
        assert result["query"] == "SELECT * FROM users WHERE email LIKE '%example.com'"
        assert "Seq Scan on users" in result["plan_text"]
        assert "execution_time" in result
        
        # Verify mocks were called correctly
        mock_conn_manager.get_connection_type.assert_called_once_with("test_conn_id")
        mock_conn_manager.get_postgres_connection.assert_called_once_with("test_conn_id")
        mock_conn.fetch.assert_called_once()
        mock_conn_manager.release_postgres_connection.assert_called_once_with("test_conn_id", mock_conn)

@pytest.mark.asyncio
async def test_postgresql_tool_vector_search(postgresql_tool):
    """Test PostgreSQL tool vector_search operation"""
    # Mock the schema inspector and connection manager
    with patch('app.rag.tools.postgresql_tool.schema_inspector') as mock_schema_inspector, \
         patch('app.rag.tools.postgresql_tool.connection_manager') as mock_conn_manager:
        
        # Setup mock schema inspector
        mock_schema_inspector.get_pgvector_info = AsyncMock()
        mock_schema_inspector.get_pgvector_info.return_value = {
            "installed": True,
            "version": "0.5.0"
        }
        
        # Setup mock connection
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"id": 1, "text": "Sample text 1", "distance": 0.15},
            {"id": 2, "text": "Sample text 2", "distance": 0.25},
            {"id": 3, "text": "Sample text 3", "distance": 0.35}
        ]
        
        # Setup connection manager mocks
        mock_conn_manager.get_connection_type.return_value = 'postgres'
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_conn_manager.release_postgres_connection = AsyncMock()
        
        # Call the method
        result = await postgresql_tool.execute({
            "operation": "vector_search",
            "connection_id": "test_conn_id",
            "table_name": "embeddings",
            "column_name": "embedding",
            "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
            "distance_type": "cosine",
            "limit": 5
        })
        
        # Verify results
        assert "results" in result
        assert len(result["results"]) == 3
        assert result["results"][0]["id"] == 1
        assert result["results"][0]["text"] == "Sample text 1"
        assert result["results"][0]["distance"] == 0.15
        assert result["count"] == 3
        assert result["distance_type"] == "cosine"
        assert "execution_time" in result
        
        # Verify mocks were called correctly
        mock_conn_manager.get_connection_type.assert_called_once_with("test_conn_id")
        mock_schema_inspector.get_pgvector_info.assert_called_once_with("test_conn_id")
        mock_conn_manager.get_postgres_connection.assert_called_once_with("test_conn_id")
        mock_conn.fetch.assert_called_once()
        mock_conn_manager.release_postgres_connection.assert_called_once_with("test_conn_id", mock_conn)