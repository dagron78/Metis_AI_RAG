"""
Unit tests for the async DatabaseTool under concurrent load
"""
import os
import pytest
import pytest_asyncio
import asyncio
import tempfile
import json
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import uuid
import random

# Import the connection manager directly
from app.db.connection_manager import connection_manager
from app.rag.tools.database_tool_async import DatabaseTool

class TestDatabaseToolAsyncConcurrent:
    """Test class for async DatabaseTool under concurrent load"""
    
    @pytest_asyncio.fixture
    async def sqlite_temp_db(self):
        """Create a temporary SQLite database for testing"""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create a test table and insert data
        import aiosqlite
        async with aiosqlite.connect(path) as conn:
            await conn.execute("""
                CREATE TABLE test_users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    email TEXT
                )
            """)
            
            # Insert 1000 test records
            for i in range(1000):
                await conn.execute(
                    "INSERT INTO test_users (name, age, email) VALUES (?, ?, ?)",
                    (f"User {i}", random.randint(18, 80), f"user{i}@example.com")
                )
            
            await conn.commit()
        
        # Return the path
        yield path
        
        # Clean up
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest_asyncio.fixture
    async def temp_csv_file(self):
        """Create a temporary CSV file for testing"""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        # Create test data with 1000 records
        data = {
            'product_id': list(range(1, 1001)),
            'product_name': [f"Product {i}" for i in range(1, 1001)],
            'price': [round(random.uniform(10, 1000), 2) for _ in range(1000)],
            'category': random.choices(['Electronics', 'Clothing', 'Books', 'Home', 'Sports'], k=1000)
        }
        df = pd.DataFrame(data)
        
        # Write to CSV
        df.to_csv(path, index=False)
        
        # Return the path
        yield path
        
        # Clean up
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest_asyncio.fixture
    async def temp_json_file(self):
        """Create a temporary JSON file for testing"""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        # Create test data with 1000 records
        data = []
        for i in range(1000):
            data.append({
                'id': i,
                'name': f"Item {i}",
                'value': random.randint(1, 1000),
                'tags': random.sample(['tag1', 'tag2', 'tag3', 'tag4', 'tag5'], k=random.randint(1, 3))
            })
        
        # Write to JSON
        with open(path, 'w') as f:
            json.dump(data, f)
        
        # Return the path
        yield path
        
        # Clean up
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest_asyncio.fixture
    async def database_tool(self):
        """Create a DatabaseTool instance for testing"""
        tool = DatabaseTool()
        yield tool
        # Ensure all connections are closed
        for conn_id in list(tool.connection_manager._pools.keys()):
            try:
                await tool.connection_manager.close(conn_id)
            except Exception:
                pass
    
    async def run_concurrent_queries(self, database_tool, source, queries, num_concurrent=10):
        """Run multiple queries concurrently and measure performance"""
        start_time = time.time()
        
        async def run_query(query, params=None):
            try:
                result = await database_tool.execute({
                    'query': query,
                    'source': source,
                    'params': params
                })
                return result
            except Exception as e:
                print(f"Error executing query: {str(e)}")
                return {"error": f"Error executing query: {str(e)}"}
        
        # Create tasks for all queries
        tasks = [run_query(query['query'], query.get('params')) for query in queries]
        
        # Run queries in batches of num_concurrent to avoid overwhelming the connection pool
        results = []
        for i in range(0, len(tasks), num_concurrent):
            batch = tasks[i:i+num_concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=False)
            results.extend(batch_results)
            
            # Add a small delay between batches to allow connections to be properly released
            if i + num_concurrent < len(tasks):
                await asyncio.sleep(0.1)
        
        end_time = time.time()
        
        return {
            'results': results,
            'total_time': end_time - start_time,
            'avg_time_per_query': (end_time - start_time) / len(queries),
            'queries_per_second': len(queries) / (end_time - start_time)
        }
    
    @pytest.mark.asyncio
    async def test_sqlite_concurrent_queries(self, database_tool, sqlite_temp_db):
        """Test concurrent queries on SQLite database"""
        print(f"\nTesting concurrent SQLite queries...")
        
        # Create a list of 100 different queries
        queries = []
        for i in range(100):
            min_age = random.randint(18, 60)
            queries.append({
                'query': f"SELECT * FROM test_users WHERE age > :min_age LIMIT 10",
                'params': {'min_age': min_age}
            })
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        results = {}
        
        for concurrency in concurrency_levels:
            print(f"  Testing with concurrency level: {concurrency}")
            result = await self.run_concurrent_queries(
                database_tool, 
                sqlite_temp_db, 
                queries, 
                concurrency
            )
            results[concurrency] = result
            print(f"    Completed {len(queries)} queries in {result['total_time']:.2f}s")
            print(f"    Average time per query: {result['avg_time_per_query'] * 1000:.2f}ms")
            print(f"    Queries per second: {result['queries_per_second']:.2f}")
        
        # Verify results
        for concurrency, result in results.items():
            # Check that all queries returned results
            assert len(result['results']) == len(queries)
            
            # Check that most results have data (allow some errors)
            successful_results = [r for r in result['results'] if 'error' not in r]
            assert len(successful_results) >= len(result['results']) * 0.9, "Too many failed queries"
            
            for query_result in successful_results:
                assert 'results' in query_result
                assert 'row_count' in query_result
                assert query_result['row_count'] > 0
        
        # Check that higher concurrency levels generally improve throughput
        # (up to a point, as SQLite has limitations)
        throughputs = [results[c]['queries_per_second'] for c in concurrency_levels]
        print(f"\n  Throughput by concurrency level:")
        for i, c in enumerate(concurrency_levels):
            print(f"    Concurrency {c}: {throughputs[i]:.2f} queries/second")
        
        # The throughput should not collapse under load
        # Note: SQLite may not scale linearly due to its design
        assert throughputs[-1] >= throughputs[0] * 0.5, "Throughput collapsed under load"
    
    @pytest.mark.asyncio
    async def test_csv_concurrent_queries(self, database_tool, temp_csv_file):
        """Test concurrent queries on CSV file"""
        print(f"\nTesting concurrent CSV queries...")
        
        # Create a list of 50 different queries
        queries = []
        for i in range(50):
            min_price = random.randint(100, 800)
            queries.append({
                'query': f"SELECT * FROM data WHERE price > {min_price} LIMIT 10",
            })
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        results = {}
        
        for concurrency in concurrency_levels:
            print(f"  Testing with concurrency level: {concurrency}")
            result = await self.run_concurrent_queries(
                database_tool, 
                temp_csv_file, 
                queries, 
                concurrency
            )
            results[concurrency] = result
            print(f"    Completed {len(queries)} queries in {result['total_time']:.2f}s")
            print(f"    Average time per query: {result['avg_time_per_query'] * 1000:.2f}ms")
            print(f"    Queries per second: {result['queries_per_second']:.2f}")
        
        # Verify results
        for concurrency, result in results.items():
            # Check that all queries returned results
            assert len(result['results']) == len(queries)
            
            # Check that most results have data (allow some errors)
            successful_results = [r for r in result['results'] if 'error' not in r]
            assert len(successful_results) >= len(result['results']) * 0.8, "Too many failed queries"
            
            for query_result in successful_results:
                assert 'results' in query_result
                assert 'row_count' in query_result
    
    @pytest.mark.asyncio
    async def test_json_concurrent_queries(self, database_tool, temp_json_file):
        """Test concurrent queries on JSON file"""
        print(f"\nTesting concurrent JSON queries...")
        
        # Create a list of 50 different queries
        queries = []
        for i in range(50):
            min_value = random.randint(100, 800)
            queries.append({
                'query': f"SELECT * FROM data WHERE value > {min_value} LIMIT 10",
            })
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        results = {}
        
        for concurrency in concurrency_levels:
            print(f"  Testing with concurrency level: {concurrency}")
            result = await self.run_concurrent_queries(
                database_tool, 
                temp_json_file, 
                queries, 
                concurrency
            )
            results[concurrency] = result
            print(f"    Completed {len(queries)} queries in {result['total_time']:.2f}s")
            print(f"    Average time per query: {result['avg_time_per_query'] * 1000:.2f}ms")
            print(f"    Queries per second: {result['queries_per_second']:.2f}")
        
        # Verify results
        for concurrency, result in results.items():
            # Check that all queries returned results
            assert len(result['results']) == len(queries)
            
            # Check that most results have data (allow some errors)
            successful_results = [r for r in result['results'] if 'error' not in r]
            assert len(successful_results) >= len(result['results']) * 0.8, "Too many failed queries"
            
            for query_result in successful_results:
                assert 'results' in query_result
                assert 'row_count' in query_result
    
    @pytest.mark.asyncio
    async def test_mixed_source_concurrent_queries(self, database_tool, sqlite_temp_db, temp_csv_file, temp_json_file):
        """Test concurrent queries on mixed data sources"""
        print(f"\nTesting concurrent queries on mixed data sources...")
        
        # Create a list of queries for different data sources
        queries = []
        
        # SQLite queries
        for i in range(20):
            min_age = random.randint(18, 60)
            queries.append({
                'source': sqlite_temp_db,
                'query': f"SELECT * FROM test_users WHERE age > :min_age LIMIT 5",
                'params': {'min_age': min_age}
            })
        
        # CSV queries
        for i in range(15):
            min_price = random.randint(100, 800)
            queries.append({
                'source': temp_csv_file,
                'query': f"SELECT * FROM data WHERE price > {min_price} LIMIT 5",
            })
        
        # JSON queries
        for i in range(15):
            min_value = random.randint(100, 800)
            queries.append({
                'source': temp_json_file,
                'query': f"SELECT * FROM data WHERE value > {min_value} LIMIT 5",
            })
        
        # Shuffle the queries to mix data sources
        random.shuffle(queries)
        
        # Run mixed queries concurrently
        concurrency = 20
        print(f"  Testing with concurrency level: {concurrency}")
        
        async def run_query(query):
            result = await database_tool.execute({
                'query': query['query'],
                'source': query['source'],
                'params': query.get('params')
            })
            return result
        
        # Create tasks for all queries
        tasks = [run_query(query) for query in queries]
        
        # Run queries concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / len(queries)
        qps = len(queries) / total_time
        
        print(f"    Completed {len(queries)} mixed queries in {total_time:.2f}s")
        print(f"    Average time per query: {avg_time * 1000:.2f}ms")
        print(f"    Queries per second: {qps:.2f}")
        
        # Verify results
        assert len(results) == len(queries)
        
        # Check that most results have data (allow some errors)
        successful_results = [r for r in results if 'error' not in r]
        assert len(successful_results) >= len(results) * 0.8, "Too many failed queries"
        
        for result in successful_results:
            assert 'results' in result
            assert 'row_count' in result
    
    @pytest.mark.asyncio
    async def test_connection_pool_under_load(self, database_tool, sqlite_temp_db):
        """Test connection pool behavior under load"""
        print(f"\nTesting connection pool behavior under load...")
        
        # Register the connection with the connection manager
        conn_id = connection_manager.register_connection(sqlite_temp_db)
        
        # Function to get and release a connection
        async def get_and_release_connection():
            conn = await connection_manager.get_sqlite_connection(conn_id)
            # Simulate some work
            cursor = await conn.execute("SELECT COUNT(*) FROM test_users")
            row = await cursor.fetchone()
            await cursor.close()
            # No explicit release for SQLite connections
            return row[0]
        
        # Run many connection operations concurrently
        concurrency = 50
        tasks = [get_and_release_connection() for _ in range(concurrency)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        print(f"    Completed {concurrency} concurrent connection operations in {total_time:.2f}s")
        print(f"    All operations returned correct count: {all(r == 1000 for r in results)}")
        
        # Verify all operations returned the correct count
        assert all(r == 1000 for r in results)
        
        # Clean up
        await connection_manager.close(conn_id)