# Metis RAG PostgreSQL MCP Integration Plan

This document outlines a detailed implementation plan for enhancing Metis RAG with concepts from the pg-mcp project, focusing on creating a fully asynchronous database layer that leverages PostgreSQL capabilities while maintaining compatibility with SQLite for development and testing.

## Background

Metis RAG currently uses a mixed database architecture:
- Core database operations use SQLAlchemy's async features
- The DatabaseTool uses synchronous SQLite connections wrapped in async methods

This inconsistency creates potential performance bottlenecks as synchronous operations can block the event loop in an otherwise asynchronous application.

The pg-mcp project provides a Model Context Protocol server for PostgreSQL with:
- Fully asynchronous database operations using asyncpg
- Secure connection management with connection IDs
- Rich schema introspection capabilities
- Support for PostgreSQL extensions like pgvector

## Implementation Phases

### Phase 1: True Async DatabaseTool Implementation

This phase focuses on eliminating the synchronous bottleneck in the DatabaseTool by implementing true async database access for both SQLite and PostgreSQL.

#### 1.1 Create Async Database Connection Manager

- [x] Create a new `app/db/connection_manager.py` module
- [x] Implement a `DatabaseConnectionManager` class with:
  - [x] Connection pooling for both SQLite and PostgreSQL
  - [x] Secure connection ID generation (similar to pg-mcp)
  - [x] Methods to register and retrieve connections
  - [x] Connection lifecycle management (acquire, release, close)
- [x] Add configuration options for connection pools
- [x] Implement proper error handling and logging

#### 1.2 Refactor DatabaseTool for True Async Operation

- [x] Create a new `app/rag/tools/database_tool_async.py` file
- [x] Replace synchronous sqlite3 with aiosqlite for SQLite operations
- [x] Add asyncpg support for PostgreSQL operations
- [x] Implement database type detection (SQLite vs PostgreSQL)
- [x] Update query execution methods to use appropriate async driver
- [x] Maintain backward compatibility with existing tool usage patterns
- [x] Add proper error handling and performance logging

#### 1.3 Update CSV and JSON Data Source Handling

- [x] Refactor CSV file handling to use aiosqlite for in-memory database
- [x] Refactor JSON file handling to use aiosqlite for in-memory database
- [x] Implement async file reading for CSV and JSON sources
- [x] Optimize data loading for large files

#### 1.4 Add Unit Tests for Async Database Operations

- [x] Create test fixtures for both SQLite and PostgreSQL connections
- [x] Test connection pooling and lifecycle management
- [x] Test query execution with various parameter types
- [x] Test error handling and recovery
- [x] Test compatibility with existing code
- [x] Test performance under concurrent load

#### 1.5 Update Dependencies and Documentation

- [x] Add aiosqlite and asyncpg to requirements.txt
- [x] Add aiofiles to requirements.txt
- [x] Create documentation with new async database capabilities
- [x] Document connection string formats for different database types
- [x] Create examples of using the enhanced DatabaseTool
- [x] Create migration script to help users transition to the new implementation

### Phase 1 Status

- [x] Core functionality implemented and tested
- [x] SQLite database operations working correctly
- [x] CSV and JSON handling fixed and working correctly with async operations
- [x] All changes committed to feature branch and backed up
- [x] Documentation and migration tools created

### Phase 2: PostgreSQL-specific Capabilities

This phase adds PostgreSQL-specific features to Metis RAG, leveraging the async foundation built in Phase 1.

#### 2.1 Implement Schema Introspection

- [x] Create a new `app/db/schema_inspector.py` module
- [x] Implement methods to retrieve:
  - [x] Database schemas
  - [x] Tables with descriptions and row counts
  - [x] Columns with data types and descriptions
  - [x] Indexes and constraints
- [x] Add caching for schema information to improve performance
- [x] Create API endpoints to expose schema information

#### 2.2 Add Query Explanation Capabilities

- [x] Implement EXPLAIN query execution
- [x] Create visualization helpers for execution plans
- [x] Add query optimization suggestions based on execution plans
- [x] Integrate with existing query analysis tools

#### 2.3 Support PostgreSQL Extensions

- [x] Add support for pgvector extension
  - [x] Implement vector similarity search methods
  - [x] Optimize for RAG vector embeddings
- [ ] Add support for PostGIS (if geospatial data is relevant)
- [x] Create extension detection and configuration helpers
- [x] Document extension usage and best practices
#### 2.4 Create a Dedicated PostgreSQLTool

- [x] Implement a new `PostgreSQLTool` class extending the base `Tool`
- [x] Expose PostgreSQL-specific capabilities
- [x] Add methods for advanced query operations
- [x] Implement proper error handling and logging
- [x] Create comprehensive documentation and examples
- [ ] Create comprehensive documentation and examples
#### 2.5 Update Testing Infrastructure

- [x] Create PostgreSQL-specific test fixtures
- [x] Test schema introspection with various database structures
- [x] Test query explanation with complex queries
- [x] Test extension functionality
- [x] Benchmark performance against baseline
- [ ] Benchmark performance against baseline

### Phase 3: MCP Server Interface (Optional)

This optional phase creates an MCP server that exposes Metis RAG's database through the Model Context Protocol.

#### 3.1 Create MCP Server Foundation

- [ ] Set up MCP server structure
- [ ] Implement server configuration
- [ ] Create connection management
- [ ] Implement security controls
- [ ] Set up logging and monitoring

#### 3.2 Implement MCP Tools

- [ ] Create connect/disconnect tools
- [ ] Implement query execution tool
- [ ] Add query explanation tool
- [ ] Create schema introspection tools
- [ ] Implement proper error handling

#### 3.3 Implement MCP Resources

- [ ] Create schema resources
- [ ] Implement table and column resources
- [ ] Add index and constraint resources
- [ ] Create data sample resources
- [ ] Implement extension resources

#### 3.4 Add AI Agent Integration

- [ ] Create example prompts for AI agents
- [ ] Implement context providers for database schema
- [ ] Add documentation for AI agent integration
- [ ] Create demo applications

#### 3.5 Testing and Documentation

- [ ] Create comprehensive tests for MCP server
- [ ] Document server setup and configuration
- [ ] Create usage examples
- [ ] Benchmark performance

## Implementation Considerations

### Database Abstraction

- Maintain a clear abstraction layer between database-specific code and generic code
- Use factory patterns to create appropriate database handlers based on connection type
- Keep SQLite support for development and testing environments
- Document differences between SQLite and PostgreSQL behavior

### Connection Management

- Implement secure connection ID generation to avoid exposing credentials
- Use connection pooling for both SQLite and PostgreSQL
- Implement proper connection lifecycle management
- Add monitoring for connection usage and performance

### Error Handling

- Create specific error types for different database issues
- Implement proper error logging and reporting
- Add retry mechanisms for transient errors
- Ensure errors are propagated appropriately to callers

### Performance Optimization

- Implement connection pooling with appropriate pool sizes
- Add query result caching where appropriate
- Use prepared statements for frequently executed queries
- Implement proper transaction management
- Add performance monitoring and logging

### Migration Path

- Provide tools to migrate from SQLite to PostgreSQL
- Document migration process and potential issues
- Ensure backward compatibility with existing data
- Create validation tools to verify data integrity after migration

## Success Metrics

- Elimination of synchronous database operations in async context
- Improved application responsiveness under load
- Reduced query execution time for complex operations
- Successful integration with PostgreSQL-specific features
- Comprehensive test coverage for all database operations
- Clear documentation for developers and users

## Timeline

- Phase 1: 2-3 weeks
- Phase 2: 3-4 weeks
- Phase 3: 2-3 weeks (if implemented)

Total estimated time: 7-10 weeks