import time
import asyncio
import pytest
import statistics
from typing import List, Dict, Any

# Test configuration
TEST_QUERIES = [
    "What is the main purpose of the RAG system?",
    "How does the document analysis service work?",
    "What are the key components of the LangGraph integration?",
    "Explain the database schema for documents and chunks",
    "How does the memory integration enhance the system?"
]

# Number of times to run each query for averaging
NUM_RUNS = 3

# Maximum acceptable response time for simple queries (in seconds)
MAX_RESPONSE_TIME = 6.0

class MockRAGEngine:
    """Mock RAG Engine for testing"""
    
    async def query(self, query: str, model: str = "gemma3:12b", use_rag: bool = True, stream: bool = False, **kwargs):
        """
        Mock query method that simulates response generation
        """
        # Simulate processing time based on query length and whether RAG is used
        base_time = 0.5 + (len(query) * 0.01)
        if use_rag:
            # RAG queries take longer
            processing_time = base_time * 2
            sources = [
                {"document_id": "doc1", "chunk_id": "chunk1", "relevance_score": 0.95, "excerpt": "Sample excerpt 1"},
                {"document_id": "doc2", "chunk_id": "chunk2", "relevance_score": 0.85, "excerpt": "Sample excerpt 2"}
            ]
        else:
            processing_time = base_time
            sources = []
        
        # Simulate processing
        await asyncio.sleep(processing_time)
        
        # Generate mock response
        response = {
            "answer": f"This is a mock response to: {query}",
            "sources": sources,
            "token_count": len(query) * 5
        }
        
        # Add stream if requested
        if stream:
            async def token_generator():
                tokens = response["answer"].split()
                for token in tokens:
                    await asyncio.sleep(0.1)
                    yield token + " "
            
            response["stream"] = token_generator()
        
        return response

async def run_query(rag_engine, query: str, use_rag: bool = True):
    """Run a query and measure performance"""
    start_time = time.time()
    
    response = await rag_engine.query(
        query=query,
        model="gemma3:12b",
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

@pytest.mark.asyncio
async def test_rag_query_performance():
    """Test RAG query performance"""
    print(f"\nRunning RAG query performance test with {len(TEST_QUERIES)} queries, {NUM_RUNS} runs each")
    
    # Create mock RAG engine
    rag_engine = MockRAGEngine()
    
    # Run queries with RAG
    results = await run_query_batch(rag_engine, TEST_QUERIES, use_rag=True, runs=NUM_RUNS)
    
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
async def test_non_rag_query_performance():
    """Test non-RAG query performance (LLM only)"""
    print(f"\nRunning non-RAG query performance test with {len(TEST_QUERIES)} queries, {NUM_RUNS} runs each")
    
    # Create mock RAG engine
    rag_engine = MockRAGEngine()
    
    # Run queries without RAG
    results = await run_query_batch(rag_engine, TEST_QUERIES, use_rag=False, runs=NUM_RUNS)
    
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
    
    # Create mock RAG engine
    rag_engine = MockRAGEngine()
    
    # Run queries with and without RAG
    rag_results = await run_query_batch(rag_engine, TEST_QUERIES, use_rag=True, runs=NUM_RUNS)
    non_rag_results = await run_query_batch(rag_engine, TEST_QUERIES, use_rag=False, runs=NUM_RUNS)
    
    # Calculate overall metrics
    rag_avg_time = statistics.mean([r["avg_elapsed_time"] for r in rag_results])
    non_rag_avg_time = statistics.mean([r["avg_elapsed_time"] for r in non_rag_results])
    
    # Print comparison
    print("\nPerformance Comparison:")
    print(f"RAG Average Response Time: {rag_avg_time:.2f}s")
    print(f"Non-RAG Average Response Time: {non_rag_avg_time:.2f}s")
    print(f"RAG Overhead: {rag_avg_time - non_rag_avg_time:.2f}s ({(rag_avg_time / non_rag_avg_time - 1) * 100:.1f}%)")

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_rag_query_performance())
    asyncio.run(test_non_rag_query_performance())
    asyncio.run(test_performance_comparison())