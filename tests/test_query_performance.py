import os
import time
import asyncio
import pytest
import statistics
from typing import List, Dict, Any
from uuid import UUID

from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.db.session import SessionLocal
from app.core.config import SETTINGS

# Test configuration
TEST_QUERIES = [
    "What is the main purpose of the RAG system?",
    "How does the document analysis service work?",
    "What are the key components of the LangGraph integration?",
    "Explain the database schema for documents and chunks",
    "How does the memory integration enhance the system?",
    "What performance optimizations are implemented in the system?",
    "How does the response quality pipeline work?",
    "What is the purpose of the background task system?",
    "How are documents processed and analyzed?",
    "What are the main features of the Metis RAG system?"
]

# Number of times to run each query for averaging
NUM_RUNS = 3

# Maximum acceptable response time for simple queries (in seconds)
MAX_RESPONSE_TIME = 6.0

@pytest.fixture
def db_session():
    """Create a database session for testing"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def document_repository(db_session):
    """Create a document repository for testing"""
    return DocumentRepository(db_session)

@pytest.fixture
def analytics_repository(db_session):
    """Create an analytics repository for testing"""
    return AnalyticsRepository(db_session)

@pytest.fixture
def vector_store():
    """Create a vector store for testing"""
    return VectorStore()

@pytest.fixture
def rag_engine():
    """Create a RAG engine for testing"""
    return RAGEngine()

async def run_query(rag_engine, query: str, use_rag: bool = True):
    """Run a query and measure performance"""
    start_time = time.time()
    
    response = await rag_engine.query(
        query=query,
        model=SETTINGS.default_model,
        use_rag=use_rag,
        stream=False
    )
    
    elapsed_time = time.time() - start_time
    
    return {
        "query": query,
        "response": response.get("answer", ""),
        "elapsed_time": elapsed_time,
        "sources": response.get("sources", []),
        "token_count": response.get("token_count", 0)
    }

async def run_query_batch(rag_engine, queries: List[str], use_rag: bool = True, runs: int = 1):
    """Run a batch of queries multiple times and collect performance metrics"""
    results = []
    
    for query in queries:
        query_results = []
        for _ in range(runs):
            result = await run_query(rag_engine, query, use_rag)
            query_results.append(result)
        
        # Calculate average metrics
        avg_time = statistics.mean([r["elapsed_time"] for r in query_results])
        avg_token_count = statistics.mean([r["token_count"] for r in query_results])
        
        results.append({
            "query": query,
            "avg_elapsed_time": avg_time,
            "avg_token_count": avg_token_count,
            "num_runs": runs,
            "use_rag": use_rag,
            "response": query_results[0]["response"],  # Just use the first response
            "sources": query_results[0]["sources"]  # Just use the first sources
        })
    
    return results

def record_performance_results(analytics_repository, results: List[Dict[str, Any]]):
    """Record performance results in the analytics repository"""
    for result in results:
        analytics_repository.create_analytics_query(
            query=result["query"],
            model=SETTINGS.default_model,
            use_rag=result["use_rag"],
            response_time_ms=result["avg_elapsed_time"] * 1000,
            token_count=result["avg_token_count"],
            document_ids=[s.get("document_id") for s in result.get("sources", []) if s.get("document_id")],
            query_type="performance_test",
            successful=True
        )

@pytest.mark.asyncio
async def test_rag_query_performance(rag_engine, analytics_repository):
    """Test RAG query performance"""
    print(f"\nRunning RAG query performance test with {len(TEST_QUERIES)} queries, {NUM_RUNS} runs each")
    
    # Run queries with RAG
    results = await run_query_batch(rag_engine, TEST_QUERIES, use_rag=True, runs=NUM_RUNS)
    
    # Record results
    record_performance_results(analytics_repository, results)
    
    # Print results
    print("\nRAG Query Performance Results:")
    print(f"{'Query':<50} | {'Avg Time (s)':<12} | {'Avg Tokens':<10} | {'Sources':<10}")
    print("-" * 90)
    
    for result in results:
        query_display = result["query"][:47] + "..." if len(result["query"]) > 50 else result["query"].ljust(50)
        print(f"{query_display} | {result['avg_elapsed_time']:<12.2f} | {result['avg_token_count']:<10.0f} | {len(result['sources']):<10}")
    
    # Calculate overall metrics
    avg_time = statistics.mean([r["avg_elapsed_time"] for r in results])
    max_time = max([r["avg_elapsed_time"] for r in results])
    min_time = min([r["avg_elapsed_time"] for r in results])
    avg_tokens = statistics.mean([r["avg_token_count"] for r in results])
    
    print("-" * 90)
    print(f"Overall Average: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s, Avg Tokens: {avg_tokens:.0f}")
    
    # Assert performance requirements
    assert max_time <= MAX_RESPONSE_TIME, f"Maximum response time ({max_time:.2f}s) exceeds limit ({MAX_RESPONSE_TIME}s)"

@pytest.mark.asyncio
async def test_non_rag_query_performance(rag_engine, analytics_repository):
    """Test non-RAG query performance (LLM only)"""
    print(f"\nRunning non-RAG query performance test with {len(TEST_QUERIES)} queries, {NUM_RUNS} runs each")
    
    # Run queries without RAG
    results = await run_query_batch(rag_engine, TEST_QUERIES, use_rag=False, runs=NUM_RUNS)
    
    # Record results
    record_performance_results(analytics_repository, results)
    
    # Print results
    print("\nNon-RAG Query Performance Results:")
    print(f"{'Query':<50} | {'Avg Time (s)':<12} | {'Avg Tokens':<10}")
    print("-" * 80)
    
    for result in results:
        query_display = result["query"][:47] + "..." if len(result["query"]) > 50 else result["query"].ljust(50)
        print(f"{query_display} | {result['avg_elapsed_time']:<12.2f} | {result['avg_token_count']:<10.0f}")
    
    # Calculate overall metrics
    avg_time = statistics.mean([r["avg_elapsed_time"] for r in results])
    max_time = max([r["avg_elapsed_time"] for r in results])
    min_time = min([r["avg_elapsed_time"] for r in results])
    avg_tokens = statistics.mean([r["avg_token_count"] for r in results])
    
    print("-" * 80)
    print(f"Overall Average: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s, Avg Tokens: {avg_tokens:.0f}")

@pytest.mark.asyncio
async def test_performance_comparison():
    """Compare RAG vs non-RAG performance"""
    print("\nComparing RAG vs non-RAG performance")
    
    # This test will be implemented to analyze the results from the analytics repository
    # and compare the performance of RAG vs non-RAG queries
    
    # For now, we'll just print a placeholder message
    print("Performance comparison test will be implemented in a future update")

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_rag_query_performance(RAGEngine(), AnalyticsRepository(SessionLocal())))
    asyncio.run(test_non_rag_query_performance(RAGEngine(), AnalyticsRepository(SessionLocal())))
    asyncio.run(test_performance_comparison())