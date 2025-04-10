# Metis RAG Performance Testing and Optimization Guide

This guide explains how to use the performance testing and optimization scripts for the Metis RAG system.

## Overview

The Metis RAG system supports both SQLite and PostgreSQL databases. These scripts help you:

1. Benchmark database performance
2. Optimize chunking strategies
3. Implement database-specific enhancements
4. Update Docker configuration for PostgreSQL support
5. Migrate data between databases

## 1. Database Performance Benchmarking

The `benchmark_database_performance.py` script benchmarks SQLite vs PostgreSQL performance for various operations:

```bash
# Run benchmark for SQLite
python scripts/benchmark_database_performance.py --db-type sqlite

# Run benchmark for PostgreSQL
python scripts/benchmark_database_performance.py --db-type postgresql

# Generate HTML comparison report
python scripts/benchmark_database_performance.py --report-only \
  --sqlite-results tests/results/db_benchmark_sqlite_YYYYMMDD_HHMMSS.json \
  --postgres-results tests/results/db_benchmark_postgresql_YYYYMMDD_HHMMSS.json
```

This script tests:
- Document operations (create, retrieve, update, delete)
- Chunk operations (insert, retrieve, update)
- Query performance
- Batch processing

The HTML report provides a detailed comparison between SQLite and PostgreSQL, including:
- Performance metrics for each operation
- Charts comparing the two databases
- Recommendations based on the benchmark results

## 2. Chunking Strategy Optimization

The `optimize_chunking_strategy.py` script tests different chunking strategies and parameters to find the optimal configuration for each database backend:

```bash
# Optimize chunking strategies for SQLite
python scripts/optimize_chunking_strategy.py --db-type sqlite

# Optimize chunking strategies for PostgreSQL
python scripts/optimize_chunking_strategy.py --db-type postgresql
```

This script tests combinations of:
- Chunking strategies (recursive, token, markdown, semantic)
- Chunk sizes (500, 1000, 2000, 4000 characters)
- Chunk overlaps (50, 100, 200, 400 characters)
- File sizes (small, medium, large, xlarge)
- File types (txt, md)

The output includes recommendations for the optimal chunking strategy for each file type and size.

## 3. Database-Specific Enhancements

The `implement_database_enhancements.py` script implements database-specific enhancements for PostgreSQL and SQLite:

```bash
# Check enhancements for SQLite (dry run)
python scripts/implement_database_enhancements.py --db-type sqlite

# Apply enhancements for SQLite
python scripts/implement_database_enhancements.py --db-type sqlite --apply

# Check enhancements for PostgreSQL (dry run)
python scripts/implement_database_enhancements.py --db-type postgresql

# Apply enhancements for PostgreSQL
python scripts/implement_database_enhancements.py --db-type postgresql --apply
```

### PostgreSQL Enhancements

- GIN indexes on JSONB metadata fields
- Full-text search indexes on document and chunk content
- Semantic search function using vector embeddings
- Connection pooling optimization
- Materialized views for frequently accessed data

### SQLite Enhancements

- WAL mode for better concurrency
- Busy timeout for concurrent access
- Foreign key constraints
- Optimized synchronous mode
- Indexes for text search and JSON queries

## 4. Docker Configuration Update

The `update_docker_config.py` script updates the Docker configuration to support both SQLite and PostgreSQL:

```bash
# Check updates (dry run)
python scripts/update_docker_config.py

# Apply updates
python scripts/update_docker_config.py --apply
```

This script:
- Updates docker-compose.yml to include PostgreSQL service
- Updates Dockerfile to install PostgreSQL client libraries
- Creates database initialization scripts
- Creates environment-based configuration switching
- Creates deployment scripts for both SQLite and PostgreSQL
- Creates deployment documentation

After running this script, you can start the system with either SQLite or PostgreSQL:

```bash
# Start with SQLite
cd config
./start-sqlite.sh

# Start with PostgreSQL
cd config
./start-postgresql.sh
```

## 5. Database Migration

The `migrate_database.py` script migrates data between SQLite and PostgreSQL databases:

```bash
# Migrate from SQLite to PostgreSQL
python scripts/migrate_database.py --source sqlite --target postgresql

# Migrate from PostgreSQL to SQLite
python scripts/migrate_database.py --source postgresql --target sqlite

# Specify custom export file
python scripts/migrate_database.py --source sqlite --target postgresql --export-file data/my_export.json
```

This script:
1. Exports data from the source database to JSON
2. Imports data to the target database from JSON
3. Verifies data integrity after migration

## Performance Optimization Workflow

For optimal performance, follow this workflow:

1. **Benchmark both databases**:
   ```bash
   python scripts/benchmark_database_performance.py --db-type sqlite
   python scripts/benchmark_database_performance.py --db-type postgresql
   ```

2. **Generate comparison report**:
   ```bash
   python scripts/benchmark_database_performance.py --report-only \
     --sqlite-results tests/results/db_benchmark_sqlite_YYYYMMDD_HHMMSS.json \
     --postgres-results tests/results/db_benchmark_postgresql_YYYYMMDD_HHMMSS.json
   ```

3. **Optimize chunking strategies**:
   ```bash
   python scripts/optimize_chunking_strategy.py --db-type sqlite
   python scripts/optimize_chunking_strategy.py --db-type postgresql
   ```

4. **Implement database enhancements**:
   ```bash
   python scripts/implement_database_enhancements.py --db-type sqlite --apply
   python scripts/implement_database_enhancements.py --db-type postgresql --apply
   ```

5. **Update Docker configuration**:
   ```bash
   python scripts/update_docker_config.py --apply
   ```

6. **Migrate data if needed**:
   ```bash
   python scripts/migrate_database.py --source sqlite --target postgresql
   ```

## Performance Monitoring

After implementing optimizations, monitor system performance:

1. **Database Query Performance**:
   - Use the `EXPLAIN ANALYZE` SQL command to analyze query execution plans
   - Monitor slow queries in database logs

2. **API Response Times**:
   - Use the `/api/system/metrics` endpoint to view API performance metrics
   - Monitor response times for different endpoints

3. **Resource Usage**:
   - Monitor CPU, memory, and disk usage
   - Watch for database connection pool saturation

4. **Scaling Considerations**:
   - For larger deployments, consider using PostgreSQL with connection pooling
   - For smaller deployments, SQLite may be sufficient

## Conclusion

By using these performance testing and optimization scripts, you can:
- Make informed decisions about which database to use
- Optimize chunking strategies for your specific use case
- Implement database-specific enhancements for better performance
- Configure Docker for production deployment
- Migrate data between databases as needed

These optimizations will help ensure that your Metis RAG system performs efficiently at scale.