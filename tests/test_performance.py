#!/usr/bin/env python3
"""
Performance benchmarking test suite for the Metis RAG system.
This test suite measures response time, throughput, and resource utilization.
"""

import os
import sys
import json
import asyncio
import logging
import uuid
import time
import psutil
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
import statistics
import concurrent.futures
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_performance")

# Import RAG components
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.document_processor import DocumentProcessor
from app.models.document import Document, Chunk
from app.models.chat import ChatQuery
from app.main import app

# Test client
client = TestClient(app)

# Test document content
TEST_DOCUMENT = """# Metis RAG Technical Documentation

## Introduction

This document provides technical documentation for the Metis RAG system, a Retrieval-Augmented Generation platform designed for enterprise knowledge management.

## Architecture Overview

Metis RAG follows a modular architecture with the following components:

### Frontend Layer

The frontend is built with HTML, CSS, and JavaScript, providing an intuitive interface for:
- Document management
- Chat interactions
- System configuration
- Analytics and monitoring

### API Layer

The API layer is implemented using FastAPI and provides endpoints for:
- Document upload and management
- Chat interactions
- System configuration
- Analytics data retrieval

### RAG Engine

The core RAG engine consists of:

#### Document Processing

The document processing pipeline handles:
- File validation and parsing
- Text extraction
- Chunking with configurable strategies
- Metadata extraction

#### Vector Store

The vector store is responsible for:
- Storing document embeddings
- Efficient similarity search
- Metadata filtering

#### LLM Integration

The LLM integration component:
- Connects to Ollama for local LLM inference
- Manages prompt templates
- Handles context window optimization
"""

# Test queries for benchmarking
BENCHMARK_QUERIES = [
    "What is the architecture of Metis RAG?",
    "How does the document processing pipeline work?",
    "What is the role of the vector store?",
    "How does the frontend interface with the API layer?",
    "What is the purpose of the LLM integration component?",
    "Explain the chunking strategies used in document processing.",
    "How does the system handle metadata filtering?",
    "What technologies are used in the frontend layer?",
    "How does the RAG engine retrieve relevant information?",
    "What is the overall purpose of the Metis RAG system?"
]

@pytest.fixture
def test_document_dir():
    """Create a temporary directory for test documents"""
    temp_dir = tempfile.mkdtemp(prefix="metis_rag_perf_")
    yield temp_dir
    # Clean up
    shutil.rmtree(temp_dir)

@pytest.fixture
def create_test_document(test_document_dir):
    """Create a test document for performance testing"""
    file_path = os.path.join(test_document_dir, "technical_doc.md")
    with open(file_path, "w") as f:
        f.write(TEST_DOCUMENT)
    return file_path

@pytest.fixture
async def setup_vector_store(create_test_document):
    """Set up vector store with test document"""
    # Use a separate directory for test ChromaDB
    test_chroma_dir = "test_perf_chroma"
    os.makedirs(test_chroma_dir, exist_ok=True)
    
    # Initialize vector store
    vector_store = VectorStore(persist_directory=test_chroma_dir)
    
    # Create Document object
    with open(create_test_document, "r") as f:
        content = f.read()
        
    doc = Document(
        id="test_doc",
        filename=os.path.basename(create_test_document),
        content=content,
        tags=["technical", "documentation"],
        folder="/test"
    )
    
    # Create a single chunk for simplicity
    doc.chunks = [
        Chunk(
            id="test_chunk_0",
            content=content,
            metadata={
                "index": 0,
                "source": os.path.basename(create_test_document)
            }
        )
    ]
    
    # Add document to vector store
    await vector_store.add_document(doc)
    
    return vector_store, doc

@pytest.fixture
async def setup_rag_engine(setup_vector_store):
    """Set up RAG engine with test vector store"""
    vector_store, document = await setup_vector_store
    rag_engine = RAGEngine(vector_store=vector_store)
    return rag_engine, document

def get_system_metrics():
    """Get current system resource utilization"""
    process = psutil.Process(os.getpid())
    return {
        "cpu_percent": process.cpu_percent(),
        "memory_percent": process.memory_percent(),
        "memory_mb": process.memory_info().rss / (1024 * 1024),  # Convert to MB
        "threads": process.num_threads(),
        "system_cpu_percent": psutil.cpu_percent(),
        "system_memory_percent": psutil.virtual_memory().percent
    }

@pytest.mark.asyncio
async def test_query_response_time(setup_rag_engine):
    """Benchmark query response time"""
    rag_engine, document = await setup_rag_engine
    
    results = []
    
    for query in BENCHMARK_QUERIES:
        # Warm-up query to initialize any lazy-loaded components
        await rag_engine.query(
            query="Warm-up query",
            use_rag=True,
            stream=False
        )
        
        # Measure response time
        start_time = time.time()
        
        response = await rag_engine.query(
            query=query,
            use_rag=True,
            stream=False
        )
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Get system metrics
        metrics = get_system_metrics()
        
        # Log results
        logger.info(f"Query: {query}")
        logger.info(f"Response time: {response_time_ms:.2f} ms")
        logger.info(f"CPU: {metrics['cpu_percent']:.1f}%, Memory: {metrics['memory_mb']:.1f} MB")
        
        # Store results
        results.append({
            "query": query,
            "response_time_ms": response_time_ms,
            "answer_length": len(response.get("answer", "")),
            "sources_count": len(response.get("sources", [])),
            **metrics
        })
    
    # Calculate statistics
    response_times = [r["response_time_ms"] for r in results]
    stats = {
        "min_response_time_ms": min(response_times),
        "max_response_time_ms": max(response_times),
        "avg_response_time_ms": statistics.mean(response_times),
        "median_response_time_ms": statistics.median(response_times),
        "stddev_response_time_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0,
        "total_queries": len(response_times)
    }
    
    # Save results to file
    results_path = "test_response_time_results.json"
    with open(results_path, "w") as f:
        json.dump({
            "results": results,
            "statistics": stats
        }, f, indent=2)
    
    logger.info(f"Response time test results saved to {os.path.abspath(results_path)}")
    logger.info(f"Average response time: {stats['avg_response_time_ms']:.2f} ms")
    
    # Assert reasonable response time (adjust threshold as needed)
    assert stats["avg_response_time_ms"] < 5000, f"Average response time too high: {stats['avg_response_time_ms']:.2f} ms"

@pytest.mark.asyncio
async def test_throughput(setup_rag_engine):
    """Benchmark system throughput with concurrent queries"""
    rag_engine, document = await setup_rag_engine
    
    results = []
    concurrency_levels = [1, 2, 5, 10]  # Number of concurrent queries
    
    for concurrency in concurrency_levels:
        logger.info(f"Testing throughput with concurrency level: {concurrency}")
        
        # Create a list of queries (repeat the benchmark queries if needed)
        queries = BENCHMARK_QUERIES * (concurrency // len(BENCHMARK_QUERIES) + 1)
        queries = queries[:concurrency]  # Limit to the desired concurrency level
        
        # Function to execute a single query
        async def execute_query(query):
            start_time = time.time()
            
            response = await rag_engine.query(
                query=query,
                use_rag=True,
                stream=False
            )
            
            end_time = time.time()
            return {
                "query": query,
                "response_time_ms": (end_time - start_time) * 1000,
                "answer_length": len(response.get("answer", "")),
                "sources_count": len(response.get("sources", []))
            }
        
        # Execute queries concurrently
        start_time = time.time()
        
        # Create tasks for all queries
        tasks = [execute_query(query) for query in queries]
        
        # Wait for all tasks to complete
        query_results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time_seconds = end_time - start_time
        
        # Calculate throughput
        throughput_qps = concurrency / total_time_seconds if total_time_seconds > 0 else 0
        
        # Get system metrics
        metrics = get_system_metrics()
        
        # Calculate statistics
        response_times = [r["response_time_ms"] for r in query_results]
        stats = {
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "avg_response_time_ms": statistics.mean(response_times),
            "median_response_time_ms": statistics.median(response_times),
            "stddev_response_time_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0
        }
        
        # Log results
        logger.info(f"Concurrency: {concurrency}, Throughput: {throughput_qps:.2f} queries/second")
        logger.info(f"Avg response time: {stats['avg_response_time_ms']:.2f} ms")
        logger.info(f"CPU: {metrics['cpu_percent']:.1f}%, Memory: {metrics['memory_mb']:.1f} MB")
        
        # Store results
        results.append({
            "concurrency": concurrency,
            "total_time_seconds": total_time_seconds,
            "throughput_queries_per_second": throughput_qps,
            "query_count": len(query_results),
            "response_time_stats": stats,
            "system_metrics": metrics,
            "query_results": query_results
        })
    
    # Save results to file
    results_path = "test_throughput_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Throughput test results saved to {os.path.abspath(results_path)}")
    
    # Assert reasonable throughput scaling
    throughputs = [r["throughput_queries_per_second"] for r in results]
    assert throughputs[-1] > 0, "Throughput should be greater than zero"
    
    # Ideally, throughput should scale with concurrency, but this depends on system resources
    # This is a simple check that throughput doesn't collapse under load
    assert throughputs[-1] >= throughputs[0] * 0.5, "Throughput collapsed under load"

@pytest.mark.asyncio
async def test_resource_utilization(setup_rag_engine):
    """Benchmark resource utilization during sustained load"""
    rag_engine, document = await setup_rag_engine
    
    results = []
    duration_seconds = 30  # Duration of the test
    query_interval_seconds = 1  # Time between queries
    
    logger.info(f"Testing resource utilization over {duration_seconds} seconds")
    
    # Function to execute queries at regular intervals
    async def query_task():
        start_time = time.time()
        query_count = 0
        
        while time.time() - start_time < duration_seconds:
            # Select a query
            query = BENCHMARK_QUERIES[query_count % len(BENCHMARK_QUERIES)]
            
            # Execute query
            await rag_engine.query(
                query=query,
                use_rag=True,
                stream=False
            )
            
            query_count += 1
            
            # Wait for the next interval
            await asyncio.sleep(query_interval_seconds)
            
        return query_count
    
    # Function to monitor system resources
    async def monitor_task():
        start_time = time.time()
        metrics_list = []
        
        while time.time() - start_time < duration_seconds:
            # Get system metrics
            metrics = get_system_metrics()
            metrics["timestamp"] = time.time() - start_time
            metrics_list.append(metrics)
            
            # Wait before next measurement
            await asyncio.sleep(1)
            
        return metrics_list
    
    # Run both tasks concurrently
    query_task_obj = asyncio.create_task(query_task())
    monitor_task_obj = asyncio.create_task(monitor_task())
    
    # Wait for both tasks to complete
    query_count = await query_task_obj
    metrics_list = await monitor_task_obj
    
    # Calculate statistics
    cpu_percentages = [m["cpu_percent"] for m in metrics_list]
    memory_mbs = [m["memory_mb"] for m in metrics_list]
    
    stats = {
        "avg_cpu_percent": statistics.mean(cpu_percentages),
        "max_cpu_percent": max(cpu_percentages),
        "avg_memory_mb": statistics.mean(memory_mbs),
        "max_memory_mb": max(memory_mbs),
        "query_count": query_count,
        "queries_per_second": query_count / duration_seconds
    }
    
    # Log results
    logger.info(f"Executed {query_count} queries over {duration_seconds} seconds")
    logger.info(f"Average CPU: {stats['avg_cpu_percent']:.1f}%, Max CPU: {stats['max_cpu_percent']:.1f}%")
    logger.info(f"Average Memory: {stats['avg_memory_mb']:.1f} MB, Max Memory: {stats['max_memory_mb']:.1f} MB")
    
    # Store results
    results = {
        "duration_seconds": duration_seconds,
        "query_interval_seconds": query_interval_seconds,
        "query_count": query_count,
        "queries_per_second": query_count / duration_seconds,
        "statistics": stats,
        "metrics_timeline": metrics_list
    }
    
    # Save results to file
    results_path = "test_resource_utilization_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Resource utilization test results saved to {os.path.abspath(results_path)}")
    
    # No specific assertions for resource utilization, as acceptable values depend on the system

@pytest.mark.asyncio
async def test_api_performance(create_test_document):
    """Benchmark API endpoint performance"""
    results = []
    
    # Test document upload and processing performance
    with open(create_test_document, "rb") as f:
        file_content = f.read()
    
    # Measure upload performance
    upload_times = []
    document_ids = []
    
    for i in range(5):  # Upload the same document 5 times
        file_obj = BytesIO(file_content)
        file_obj.name = f"perf_test_{i}.md"
        
        start_time = time.time()
        
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": (file_obj.name, file_obj, "text/markdown")}
        )
        
        end_time = time.time()
        upload_time_ms = (end_time - start_time) * 1000
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_ids.append(upload_data["document_id"])
        
        upload_times.append(upload_time_ms)
        
        logger.info(f"Upload {i+1}: {upload_time_ms:.2f} ms")
    
    # Measure processing performance
    start_time = time.time()
    
    process_response = client.post(
        "/api/documents/process",
        json={"document_ids": document_ids}
    )
    
    end_time = time.time()
    process_time_ms = (end_time - start_time) * 1000
    
    assert process_response.status_code == 200
    
    logger.info(f"Processing {len(document_ids)} documents: {process_time_ms:.2f} ms")
    
    # Measure query performance
    query_times = []
    
    for query in BENCHMARK_QUERIES[:5]:  # Use first 5 queries
        start_time = time.time()
        
        query_response = client.post(
            "/api/chat/query",
            json={
                "message": query,
                "use_rag": True,
                "stream": False
            }
        )
        
        end_time = time.time()
        query_time_ms = (end_time - start_time) * 1000
        
        assert query_response.status_code == 200
        
        query_times.append(query_time_ms)
        
        logger.info(f"Query: {query}")
        logger.info(f"Query time: {query_time_ms:.2f} ms")
    
    # Calculate statistics
    upload_stats = {
        "min_upload_time_ms": min(upload_times),
        "max_upload_time_ms": max(upload_times),
        "avg_upload_time_ms": statistics.mean(upload_times)
    }
    
    query_stats = {
        "min_query_time_ms": min(query_times),
        "max_query_time_ms": max(query_times),
        "avg_query_time_ms": statistics.mean(query_times)
    }
    
    # Store results
    results = {
        "upload_performance": {
            "document_count": len(document_ids),
            "upload_times_ms": upload_times,
            "statistics": upload_stats
        },
        "processing_performance": {
            "document_count": len(document_ids),
            "process_time_ms": process_time_ms,
            "process_time_per_document_ms": process_time_ms / len(document_ids)
        },
        "query_performance": {
            "query_count": len(query_times),
            "query_times_ms": query_times,
            "statistics": query_stats
        }
    }
    
    # Save results to file
    results_path = "test_api_performance_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"API performance test results saved to {os.path.abspath(results_path)}")
    
    # Clean up - delete all documents
    for doc_id in document_ids:
        client.delete(f"/api/documents/{doc_id}")

@pytest.mark.asyncio
async def test_generate_performance_report():
    """Generate a comprehensive performance report"""
    # Check if all result files exist
    result_files = [
        "test_response_time_results.json",
        "test_throughput_results.json",
        "test_resource_utilization_results.json",
        "test_api_performance_results.json"
    ]
    
    missing_files = [f for f in result_files if not os.path.exists(f)]
    
    if missing_files:
        logger.warning(f"Missing result files: {missing_files}")
        logger.warning("Run the individual performance tests first")
        return
    
    # Load all results
    results = {}
    
    for file_path in result_files:
        with open(file_path, "r") as f:
            results[file_path] = json.load(f)
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "response_time": {
                "avg_ms": results["test_response_time_results.json"]["statistics"]["avg_response_time_ms"],
                "min_ms": results["test_response_time_results.json"]["statistics"]["min_response_time_ms"],
                "max_ms": results["test_response_time_results.json"]["statistics"]["max_response_time_ms"]
            },
            "throughput": {
                "max_qps": max(r["throughput_queries_per_second"] for r in results["test_throughput_results.json"]),
                "concurrency_levels": [r["concurrency"] for r in results["test_throughput_results.json"]]
            },
            "resource_utilization": {
                "avg_cpu_percent": results["test_resource_utilization_results.json"]["statistics"]["avg_cpu_percent"],
                "max_cpu_percent": results["test_resource_utilization_results.json"]["statistics"]["max_cpu_percent"],
                "avg_memory_mb": results["test_resource_utilization_results.json"]["statistics"]["avg_memory_mb"],
                "max_memory_mb": results["test_resource_utilization_results.json"]["statistics"]["max_memory_mb"]
            },
            "api_performance": {
                "avg_upload_time_ms": results["test_api_performance_results.json"]["upload_performance"]["statistics"]["avg_upload_time_ms"],
                "avg_query_time_ms": results["test_api_performance_results.json"]["query_performance"]["statistics"]["avg_query_time_ms"],
                "process_time_per_document_ms": results["test_api_performance_results.json"]["processing_performance"]["process_time_per_document_ms"]
            }
        },
        "detailed_results": results
    }
    
    # Save report
    report_path = "performance_benchmark_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Performance benchmark report saved to {os.path.abspath(report_path)}")
    
    # Generate HTML report
    html_report = f"""<!DOCTYPE html>
<html>
<head>
    <title>Metis RAG Performance Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .section {{ margin-bottom: 30px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .chart {{ width: 100%; height: 300px; margin-top: 20px; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>Metis RAG Performance Benchmark Report</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="section">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Average Response Time</td>
                <td>{report["summary"]["response_time"]["avg_ms"]:.2f} ms</td>
            </tr>
            <tr>
                <td>Maximum Throughput</td>
                <td>{report["summary"]["throughput"]["max_qps"]:.2f} queries/second</td>
            </tr>
            <tr>
                <td>Average CPU Usage</td>
                <td>{report["summary"]["resource_utilization"]["avg_cpu_percent"]:.1f}%</td>
            </tr>
            <tr>
                <td>Average Memory Usage</td>
                <td>{report["summary"]["resource_utilization"]["avg_memory_mb"]:.1f} MB</td>
            </tr>
            <tr>
                <td>Average Upload Time</td>
                <td>{report["summary"]["api_performance"]["avg_upload_time_ms"]:.2f} ms</td>
            </tr>
            <tr>
                <td>Average Query Time (API)</td>
                <td>{report["summary"]["api_performance"]["avg_query_time_ms"]:.2f} ms</td>
            </tr>
            <tr>
                <td>Document Processing Time</td>
                <td>{report["summary"]["api_performance"]["process_time_per_document_ms"]:.2f} ms per document</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Response Time</h2>
        <p>Statistics for query response time across {len(results["test_response_time_results.json"]["results"])} test queries.</p>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Minimum</td>
                <td>{report["summary"]["response_time"]["min_ms"]:.2f} ms</td>
            </tr>
            <tr>
                <td>Maximum</td>
                <td>{report["summary"]["response_time"]["max_ms"]:.2f} ms</td>
            </tr>
            <tr>
                <td>Average</td>
                <td>{report["summary"]["response_time"]["avg_ms"]:.2f} ms</td>
            </tr>
        </table>
        
        <div class="chart">
            <canvas id="responseTimeChart"></canvas>
        </div>
    </div>
    
    <div class="section">
        <h2>Throughput</h2>
        <p>Throughput measurements at different concurrency levels.</p>
        <table>
            <tr>
                <th>Concurrency</th>
                <th>Throughput (queries/second)</th>
                <th>Average Response Time (ms)</th>
            </tr>
            {"".join(f"<tr><td>{r['concurrency']}</td><td>{r['throughput_queries_per_second']:.2f}</td><td>{r['response_time_stats']['avg_response_time_ms']:.2f}</td></tr>" for r in results["test_throughput_results.json"])}
        </table>
        
        <div class="chart">
            <canvas id="throughputChart"></canvas>
        </div>
    </div>
    
    <div class="section">
        <h2>Resource Utilization</h2>
        <p>Resource utilization during sustained load over {results["test_resource_utilization_results.json"]["duration_seconds"]} seconds.</p>
        <table>
            <tr>
                <th>Metric</th>
                <th>Average</th>
                <th>Maximum</th>
            </tr>
            <tr>
                <td>CPU Usage</td>
                <td>{report["summary"]["resource_utilization"]["avg_cpu_percent"]:.1f}%</td>
                <td>{report["summary"]["resource_utilization"]["max_cpu_percent"]:.1f}%</td>
            </tr>
            <tr>
                <td>Memory Usage</td>
                <td>{report["summary"]["resource_utilization"]["avg_memory_mb"]:.1f} MB</td>
                <td>{report["summary"]["resource_utilization"]["max_memory_mb"]:.1f} MB</td>
            </tr>
        </table>
        
        <div class="chart">
            <canvas id="resourceChart"></canvas>
        </div>
    </div>
    
    <div class="section">
        <h2>API Performance</h2>
        <p>Performance measurements for API endpoints.</p>
        <h3>Upload Performance</h3>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Average Upload Time</td>
                <td>{report["summary"]["api_performance"]["avg_upload_time_ms"]:.2f} ms</td>
            </tr>
            <tr>
                <td>Document Processing Time</td>
                <td>{report["summary"]["api_performance"]["process_time_per_document_ms"]:.2f} ms per document</td>
            </tr>
        </table>
        
        <h3>Query Performance</h3>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Average Query Time</td>
                <td>{report["summary"]["api_performance"]["avg_query_time_ms"]:.2f} ms</td>
            </tr>
        </table>
    </div>
    
    <script>
        // Response Time Chart
        const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
        const responseTimeChart = new Chart(responseTimeCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([r["query"][:20] + "..." for r in results["test_response_time_results.json"]["results"]])},
                datasets: [{{
                    label: 'Response Time (ms)',
                    data: {json.dumps([r["response_time_ms"] for r in results["test_response_time_results.json"]["results"]])},
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Response Time (ms)'
                        }}
                    }}
                }}
            }}
        }});
        
        // Throughput Chart
        const throughputCtx = document.getElementById('throughputChart').getContext('2d');
        const throughputChart = new Chart(throughputCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps([r["concurrency"] for r in results["test_throughput_results.json"]])},
                datasets: [
                    {{
                        label: 'Throughput (queries/second)',
                        data: {json.dumps([r["throughput_queries_per_second"] for r in results["test_throughput_results.json"]])},
                        backgroundColor: 'rgba(75, 192, 192, 0.5)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 2,
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'Avg Response Time (ms)',
                        data: {json.dumps([r["response_time_stats"]["avg_response_time_ms"] for r in results["test_throughput_results.json"]])},
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{
                            display: true,
                            text: 'Throughput (queries/second)'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{
                            display: true,
                            text: 'Response Time (ms)'
                        }},
                        grid: {{
                            drawOnChartArea: false
                        }}
                    }}
                }}
            }}
        }});
        
        // Resource Utilization Chart
        const resourceCtx = document.getElementById('resourceChart').getContext('2d');
        const resourceData = {json.dumps(results["test_resource_utilization_results.json"]["metrics_timeline"])};
        const resourceChart = new Chart(resourceCtx, {{
            type: 'line',
            data: {{
                labels: resourceData.map(m => m.timestamp.toFixed(1) + 's'),
                datasets: [
                    {{
                        label: 'CPU Usage (%)',
                        data: resourceData.map(m => m.cpu_percent),
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'Memory Usage (MB)',
                        data: resourceData.map(m => m.memory_mb),
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{
                            display: true,
                            text: 'CPU Usage (%)'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{
                            display: true,
                            text: 'Memory Usage (MB)'
                        }},
                        grid: {{
                            drawOnChartArea: false
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    html_report_path = "performance_benchmark_report.html"
    with open(html_report_path, "w") as f:
        f.write(html_report)
    
    logger.info(f"HTML performance report saved to {os.path.abspath(html_report_path)}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])