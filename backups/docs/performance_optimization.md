# Metis RAG Performance Testing and Optimization

This document provides an overview of the performance testing and optimization tools available for the Metis RAG system, focusing on database performance, chunking strategies, and deployment configurations.

## Table of Contents

1. [Database Performance Testing](#database-performance-testing)
2. [Chunking Strategy Optimization](#chunking-strategy-optimization)
3. [Database-Specific Enhancements](#database-specific-enhancements)
4. [Deployment Configuration](#deployment-configuration)
5. [Running the Scripts](#running-the-scripts)

## Database Performance Testing

The `benchmark_database_performance.py` script provides comprehensive benchmarking of SQLite vs PostgreSQL performance for various operations:

- Document CRUD operations
- Chunk storage and retrieval
- Query performance
- Batch processing

### Usage

```bash
# Benchmark SQLite performance
python scripts/benchmark_database_performance.py --db-type sqlite

# Benchmark PostgreSQL performance
python scripts/benchmark_database_performance.py --db-type postgresql

# Generate HTML comparison report (after running both benchmarks)
python scripts/benchmark_database_performance.py --db-type sqlite --html --postgres-results path/to/postgres/results.json
```

### Key Metrics

The benchmark measures the following metrics:

- **Document Operations**: Create, read, update, and delete performance for documents of different sizes
- **Chunk Operations**: Insertion, retrieval, and update performance for chunks with different chunking strategies
- **Query Performance**: Response time for different types of queries
- **Batch Processing**: Processing time for batches of documents of different sizes

### Output

The script generates a detailed JSON report with all benchmark results and can also generate an HTML report with visualizations comparing SQLite and PostgreSQL performance.

## Chunking Strategy Optimization

The `optimize_chunking_strategy.py` script tests different chunking strategies and parameters to find the optimal configuration for each database backend:

- Compares different chunking strategies (recursive, token, markdown, semantic)
- Optimizes chunk size parameters
- Optimizes chunk overlap parameters

### Usage

```bash
# Optimize chunking strategies for SQLite
python scripts/optimize_chunking_strategy.py --db-type sqlite

# Optimize chunking strategies for PostgreSQL
python scripts/optimize_chunking_strategy.py --db-type postgresql

# Generate HTML report
python scripts/optimize_chunking_strategy.py --db-type sqlite --html
```

### Key Metrics

The optimization process measures:

- Processing time for different chunking strategies
- Storage and retrieval performance for different chunk sizes
- Query performance with different chunk configurations

### Output

The script generates recommendations for optimal chunking strategies, chunk sizes, and chunk overlaps for different file types and sizes, along with an HTML report visualizing the results.

## Database-Specific Enhancements

### PostgreSQL Enhancements

The `implement_postgres_enhancements.py` script implements PostgreSQL-specific optimizations:

- JSONB operators for metadata queries
- Full-text search capabilities
- Connection pooling configuration
- Index optimization

```bash
# View planned enhancements
python scripts/implement_postgres_enhancements.py

# Apply enhancements
python scripts/implement_postgres_enhancements.py --apply
```

### SQLite Optimizations

The `optimize_sqlite_for_concurrency.py` script implements SQLite-specific optimizations:

- WAL (Write-Ahead Logging) mode for better concurrency
- PRAGMA settings for performance
- Index optimization
- Connection pooling configuration

```bash
# View planned optimizations
python scripts/optimize_sqlite_for_concurrency.py

# Apply optimizations
python scripts/optimize_sqlite_for_concurrency.py --apply
```

## Deployment Configuration

The `update_docker_for_postgres.py` script updates the Docker configuration for PostgreSQL support:

- Updates docker-compose.yml to include a PostgreSQL service
- Updates Dockerfile to install PostgreSQL client libraries
- Creates database initialization scripts
- Updates environment configuration

```bash
# View planned changes
python scripts/update_docker_for_postgres.py

# Apply changes
python scripts/update_docker_for_postgres.py --apply
```

## Running the Scripts

### Prerequisites

- Python 3.10 or higher
- SQLite 3.9 or higher (for JSON support)
- PostgreSQL 12 or higher (for JSONB and full-text search)
- Docker and Docker Compose (for deployment configuration)

### Environment Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Configure the database connection:

For SQLite:
```
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./test.db
```

For PostgreSQL:
```
DATABASE_TYPE=postgresql
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=metis_rag
```

### Performance Testing Workflow

For a comprehensive performance evaluation, follow these steps:

1. Benchmark both database backends:
```bash
python scripts/benchmark_database_performance.py --db-type sqlite
python scripts/benchmark_database_performance.py --db-type postgresql --html --sqlite-results path/to/sqlite/results.json
```

2. Optimize chunking strategies for your chosen database:
```bash
python scripts/optimize_chunking_strategy.py --db-type postgresql --html
```

3. Apply database-specific enhancements:
```bash
# For PostgreSQL
python scripts/implement_postgres_enhancements.py --apply

# For SQLite
python scripts/optimize_sqlite_for_concurrency.py --apply
```

4. Update deployment configuration:
```bash
python scripts/update_docker_for_postgres.py --apply
```

### Interpreting Results

The HTML reports provide detailed visualizations and comparisons of performance metrics. Key considerations when interpreting results:

- **Document Size Impact**: Larger documents may perform differently than smaller ones
- **Chunking Strategy Tradeoffs**: Different strategies balance processing speed vs. retrieval quality
- **Concurrency Requirements**: PostgreSQL generally handles concurrent access better than SQLite
- **Resource Utilization**: Monitor CPU, memory, and disk usage during benchmarks

## Best Practices

### SQLite Optimization

- Use WAL mode for better concurrency
- Increase cache size for better performance
- Use appropriate indexes for common queries
- Consider connection pooling for web applications

### PostgreSQL Optimization

- Use JSONB operators for efficient metadata queries
- Implement full-text search for content queries
- Configure connection pooling for high-traffic applications
- Use appropriate indexes for common query patterns

### Chunking Optimization

- Use different chunking strategies for different file types
- Adjust chunk size based on content complexity
- Balance chunk overlap for context preservation vs. storage efficiency
- Consider database performance when choosing chunking parameters

## Conclusion

Performance optimization is an ongoing process. Regularly benchmark your system as your data and usage patterns evolve, and adjust your configuration accordingly.

For production deployments, consider:

- Regular database maintenance (VACUUM, ANALYZE)
- Monitoring database performance
- Scaling resources based on usage patterns
- Implementing caching for frequently accessed data