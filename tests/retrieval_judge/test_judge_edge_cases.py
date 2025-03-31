#!/usr/bin/env python3
"""
Test script to evaluate the Retrieval Judge's handling of edge cases.
This script:
1. Tests the judge with ambiguous queries
2. Tests the judge with queries containing typos
3. Tests the judge with domain-specific queries
4. Tests the judge with multi-part queries
5. Tests the judge with very short and very long queries
"""

import os
import sys
import json
import asyncio
import logging
import uuid
import time
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_judge_edge_cases")

# Import RAG components
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.rag.ollama_client import OllamaClient
from app.rag.agents.retrieval_judge import RetrievalJudge

# Define the model to use for the Retrieval Judge
JUDGE_MODEL = "gemma3:4b"

# Test queries for different edge cases
EDGE_CASE_QUERIES = [
    # Ambiguous queries
    {
        "query": "How does the system work?",
        "type": "ambiguous",
        "description": "Very general query without specific focus"
    },
    {
        "query": "Tell me about the API",
        "type": "ambiguous",
        "description": "Ambiguous query about the API without specifying which aspect"
    },
    
    # Queries with typos
    {
        "query": "How does the vektor store work?",
        "type": "typo",
        "description": "Typo in 'vector'"
    },
    {
        "query": "What is the documnet procesing pipeline?",
        "type": "typo",
        "description": "Multiple typos in 'document processing'"
    },
    
    # Domain-specific queries
    {
        "query": "How does the system handle context window optimization?",
        "type": "domain-specific",
        "description": "Domain-specific query about LLM context windows"
    },
    {
        "query": "What embedding models are supported for semantic search?",
        "type": "domain-specific",
        "description": "Domain-specific query about embedding models"
    },
    
    # Multi-part queries
    {
        "query": "What are the chunking strategies and how do they affect retrieval performance?",
        "type": "multi-part",
        "description": "Multi-part query about chunking strategies and their impact"
    },
    {
        "query": "How does the authentication work and what endpoints are available for document management?",
        "type": "multi-part",
        "description": "Multi-part query about authentication and document management endpoints"
    },
    
    # Very short queries
    {
        "query": "RAG?",
        "type": "short",
        "description": "Very short query with just an acronym"
    },
    {
        "query": "Embeddings?",
        "type": "short",
        "description": "Very short query with just a technical term"
    },
    
    # Very long queries
    {
        "query": "I'm trying to understand how the Metis RAG system works in detail, particularly how the document processing pipeline handles different file formats, how the chunking strategies are implemented, how the vector store manages embeddings efficiently, and how the retrieval judge optimizes the retrieval process to improve the relevance of the results. Can you explain all of these aspects in detail?",
        "type": "long",
        "description": "Very long query with multiple questions"
    }
]

# Sample chunks for testing
SAMPLE_CHUNKS = [
    {
        "chunk_id": "chunk1",
        "content": "The vector store is responsible for storing document embeddings, efficient similarity search, and metadata filtering. It uses a HNSW index for approximate nearest neighbor search and supports filtering by metadata such as tags, folder, and document ID.",
        "metadata": {
            "document_id": "doc1",
            "filename": "technical_documentation.md",
            "tags": "vector store,embeddings,search",
            "folder": "/docs"
        },
        "distance": 0.2
    },
    {
        "chunk_id": "chunk2",
        "content": "The document processing pipeline handles file validation and parsing, text extraction, chunking with configurable strategies, and metadata extraction. It supports various file formats including PDF, DOCX, TXT, and Markdown.",
        "metadata": {
            "document_id": "doc1",
            "filename": "technical_documentation.md",
            "tags": "document processing,chunking,extraction",
            "folder": "/docs"
        },
        "distance": 0.3
    },
    {
        "chunk_id": "chunk3",
        "content": "The API layer is implemented using FastAPI and provides endpoints for document upload and management, chat interactions, system configuration, and analytics data retrieval. All API requests require authentication using JWT tokens.",
        "metadata": {
            "document_id": "doc1",
            "filename": "technical_documentation.md",
            "tags": "api,fastapi,endpoints",
            "folder": "/docs"
        },
        "distance": 0.4
    },
    {
        "chunk_id": "chunk4",
        "content": "The LLM integration component connects to Ollama for local LLM inference, manages prompt templates, and handles context window optimization. It supports various models including Llama 3, Gemma, and Mistral.",
        "metadata": {
            "document_id": "doc1",
            "filename": "technical_documentation.md",
            "tags": "llm,inference,context window",
            "folder": "/docs"
        },
        "distance": 0.5
    },
    {
        "chunk_id": "chunk5",
        "content": "The Retrieval Judge is an LLM-based agent that enhances the RAG retrieval process by analyzing queries to determine optimal retrieval parameters, evaluating retrieved chunks for relevance, refining queries when needed to improve retrieval precision, and optimizing context assembly for better response generation.",
        "metadata": {
            "document_id": "doc2",
            "filename": "advanced_features.md",
            "tags": "retrieval judge,llm,optimization",
            "folder": "/docs/advanced"
        },
        "distance": 0.6
    }
]

async def test_query_analysis(retrieval_judge):
    """Test the judge's query analysis capabilities"""
    logger.info("Testing query analysis...")
    
    results = []
    
    for query_info in EDGE_CASE_QUERIES:
        query = query_info["query"]
        query_type = query_info["type"]
        description = query_info["description"]
        
        logger.info(f"\n=== Testing {query_type} query: {query} ===")
        logger.info(f"Description: {description}")
        
        # Analyze query
        start_time = time.time()
        analysis = await retrieval_judge.analyze_query(query)
        elapsed_time = time.time() - start_time
        
        # Log results
        logger.info(f"Query complexity: {analysis.get('complexity', 'unknown')}")
        logger.info(f"Recommended parameters: {analysis.get('parameters', {})}")
        logger.info(f"Analysis time: {elapsed_time:.2f}s")
        
        # Store results
        result = {
            "query": query,
            "type": query_type,
            "description": description,
            "analysis": analysis,
            "time": elapsed_time
        }
        
        results.append(result)
    
    # Save results to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "query_analysis_results.json")
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Query analysis results saved to {os.path.abspath(results_path)}")
    
    return results

async def test_chunk_evaluation(retrieval_judge):
    """Test the judge's chunk evaluation capabilities"""
    logger.info("Testing chunk evaluation...")
    
    results = []
    
    for query_info in EDGE_CASE_QUERIES:
        query = query_info["query"]
        query_type = query_info["type"]
        description = query_info["description"]
        
        logger.info(f"\n=== Testing {query_type} query: {query} ===")
        logger.info(f"Description: {description}")
        
        # Evaluate chunks
        start_time = time.time()
        evaluation = await retrieval_judge.evaluate_chunks(query, SAMPLE_CHUNKS)
        elapsed_time = time.time() - start_time
        
        # Log results
        logger.info(f"Needs refinement: {evaluation.get('needs_refinement', False)}")
        logger.info(f"Relevance scores: {evaluation.get('relevance_scores', {})}")
        logger.info(f"Evaluation time: {elapsed_time:.2f}s")
        
        # Store results
        result = {
            "query": query,
            "type": query_type,
            "description": description,
            "evaluation": evaluation,
            "time": elapsed_time
        }
        
        results.append(result)
    
    # Save results to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "chunk_evaluation_results.json")
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Chunk evaluation results saved to {os.path.abspath(results_path)}")
    
    return results

async def test_query_refinement(retrieval_judge):
    """Test the judge's query refinement capabilities"""
    logger.info("Testing query refinement...")
    
    results = []
    
    for query_info in EDGE_CASE_QUERIES:
        query = query_info["query"]
        query_type = query_info["type"]
        description = query_info["description"]
        
        logger.info(f"\n=== Testing {query_type} query: {query} ===")
        logger.info(f"Description: {description}")
        
        # Refine query
        start_time = time.time()
        refined_query = await retrieval_judge.refine_query(query, SAMPLE_CHUNKS)
        elapsed_time = time.time() - start_time
        
        # Log results
        logger.info(f"Original query: {query}")
        logger.info(f"Refined query: {refined_query}")
        logger.info(f"Refinement time: {elapsed_time:.2f}s")
        
        # Store results
        result = {
            "query": query,
            "type": query_type,
            "description": description,
            "refined_query": refined_query,
            "time": elapsed_time
        }
        
        results.append(result)
    
    # Save results to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "query_refinement_results.json")
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Query refinement results saved to {os.path.abspath(results_path)}")
    
    return results

async def test_context_optimization(retrieval_judge):
    """Test the judge's context optimization capabilities"""
    logger.info("Testing context optimization...")
    
    results = []
    
    for query_info in EDGE_CASE_QUERIES:
        query = query_info["query"]
        query_type = query_info["type"]
        description = query_info["description"]
        
        logger.info(f"\n=== Testing {query_type} query: {query} ===")
        logger.info(f"Description: {description}")
        
        # Optimize context
        start_time = time.time()
        optimized_chunks = await retrieval_judge.optimize_context(query, SAMPLE_CHUNKS)
        elapsed_time = time.time() - start_time
        
        # Log results
        logger.info(f"Original chunks: {len(SAMPLE_CHUNKS)}")
        logger.info(f"Optimized chunks: {len(optimized_chunks)}")
        logger.info(f"Optimization time: {elapsed_time:.2f}s")
        
        # Store results
        result = {
            "query": query,
            "type": query_type,
            "description": description,
            "original_chunk_count": len(SAMPLE_CHUNKS),
            "optimized_chunk_count": len(optimized_chunks),
            "optimized_chunk_ids": [chunk["chunk_id"] for chunk in optimized_chunks],
            "time": elapsed_time
        }
        
        results.append(result)
    
    # Save results to file
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "context_optimization_results.json")
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Context optimization results saved to {os.path.abspath(results_path)}")
    
    return results

async def analyze_results(query_analysis_results, chunk_evaluation_results, query_refinement_results, context_optimization_results):
    """Analyze the test results"""
    logger.info("\n=== ANALYSIS OF RETRIEVAL JUDGE EDGE CASE HANDLING ===")
    
    # Group results by query type
    query_types = set(r["type"] for r in query_analysis_results)
    
    # Analyze each query type
    for query_type in query_types:
        logger.info(f"\n--- {query_type.upper()} QUERIES ---")
        
        # Filter results for this query type
        qa_results = [r for r in query_analysis_results if r["type"] == query_type]
        ce_results = [r for r in chunk_evaluation_results if r["type"] == query_type]
        qr_results = [r for r in query_refinement_results if r["type"] == query_type]
        co_results = [r for r in context_optimization_results if r["type"] == query_type]
        
        # Query analysis metrics
        complexities = [r["analysis"].get("complexity", "unknown") for r in qa_results]
        complexity_counts = {}
        for complexity in complexities:
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        avg_qa_time = sum(r["time"] for r in qa_results) / len(qa_results) if qa_results else 0
        
        logger.info("Query Analysis:")
        logger.info(f"  Complexity distribution: {complexity_counts}")
        logger.info(f"  Average analysis time: {avg_qa_time:.2f}s")
        
        # Chunk evaluation metrics
        needs_refinement_count = sum(1 for r in ce_results if r["evaluation"].get("needs_refinement", False))
        avg_ce_time = sum(r["time"] for r in ce_results) / len(ce_results) if ce_results else 0
        
        logger.info("Chunk Evaluation:")
        logger.info(f"  Queries needing refinement: {needs_refinement_count}/{len(ce_results)}")
        logger.info(f"  Average evaluation time: {avg_ce_time:.2f}s")
        
        # Query refinement metrics
        avg_qr_time = sum(r["time"] for r in qr_results) / len(qr_results) if qr_results else 0
        
        # Calculate average change in query length
        original_lengths = [len(r["query"]) for r in qr_results]
        refined_lengths = [len(r["refined_query"]) for r in qr_results]
        avg_length_change = sum(refined - original for original, refined in zip(original_lengths, refined_lengths)) / len(qr_results) if qr_results else 0
        avg_length_change_percent = (sum(refined / original for original, refined in zip(original_lengths, refined_lengths) if original > 0) / len(qr_results) - 1) * 100 if qr_results else 0
        
        logger.info("Query Refinement:")
        logger.info(f"  Average refinement time: {avg_qr_time:.2f}s")
        logger.info(f"  Average change in query length: {avg_length_change:.2f} characters ({avg_length_change_percent:.2f}%)")
        
        # Context optimization metrics
        avg_co_time = sum(r["time"] for r in co_results) / len(co_results) if co_results else 0
        avg_chunk_reduction = sum(r["original_chunk_count"] - r["optimized_chunk_count"] for r in co_results) / len(co_results) if co_results else 0
        avg_chunk_reduction_percent = (1 - sum(r["optimized_chunk_count"] for r in co_results) / sum(r["original_chunk_count"] for r in co_results)) * 100 if sum(r["original_chunk_count"] for r in co_results) > 0 else 0
        
        logger.info("Context Optimization:")
        logger.info(f"  Average optimization time: {avg_co_time:.2f}s")
        logger.info(f"  Average chunk reduction: {avg_chunk_reduction:.2f} chunks ({avg_chunk_reduction_percent:.2f}%)")
    
    # Overall analysis
    logger.info("\n--- OVERALL ANALYSIS ---")
    
    # Query analysis metrics
    all_complexities = [r["analysis"].get("complexity", "unknown") for r in query_analysis_results]
    all_complexity_counts = {}
    for complexity in all_complexities:
        all_complexity_counts[complexity] = all_complexity_counts.get(complexity, 0) + 1
    
    avg_all_qa_time = sum(r["time"] for r in query_analysis_results) / len(query_analysis_results) if query_analysis_results else 0
    
    logger.info("Query Analysis:")
    logger.info(f"  Overall complexity distribution: {all_complexity_counts}")
    logger.info(f"  Overall average analysis time: {avg_all_qa_time:.2f}s")
    
    # Chunk evaluation metrics
    all_needs_refinement_count = sum(1 for r in chunk_evaluation_results if r["evaluation"].get("needs_refinement", False))
    avg_all_ce_time = sum(r["time"] for r in chunk_evaluation_results) / len(chunk_evaluation_results) if chunk_evaluation_results else 0
    
    logger.info("Chunk Evaluation:")
    logger.info(f"  Overall queries needing refinement: {all_needs_refinement_count}/{len(chunk_evaluation_results)}")
    logger.info(f"  Overall average evaluation time: {avg_all_ce_time:.2f}s")
    
    # Query refinement metrics
    avg_all_qr_time = sum(r["time"] for r in query_refinement_results) / len(query_refinement_results) if query_refinement_results else 0
    
    # Calculate overall average change in query length
    all_original_lengths = [len(r["query"]) for r in query_refinement_results]
    all_refined_lengths = [len(r["refined_query"]) for r in query_refinement_results]
    avg_all_length_change = sum(refined - original for original, refined in zip(all_original_lengths, all_refined_lengths)) / len(query_refinement_results) if query_refinement_results else 0
    avg_all_length_change_percent = (sum(refined / original for original, refined in zip(all_original_lengths, all_refined_lengths) if original > 0) / len(query_refinement_results) - 1) * 100 if query_refinement_results else 0
    
    logger.info("Query Refinement:")
    logger.info(f"  Overall average refinement time: {avg_all_qr_time:.2f}s")
    logger.info(f"  Overall average change in query length: {avg_all_length_change:.2f} characters ({avg_all_length_change_percent:.2f}%)")
    
    # Context optimization metrics
    avg_all_co_time = sum(r["time"] for r in context_optimization_results) / len(context_optimization_results) if context_optimization_results else 0
    avg_all_chunk_reduction = sum(r["original_chunk_count"] - r["optimized_chunk_count"] for r in context_optimization_results) / len(context_optimization_results) if context_optimization_results else 0
    avg_all_chunk_reduction_percent = (1 - sum(r["optimized_chunk_count"] for r in context_optimization_results) / sum(r["original_chunk_count"] for r in context_optimization_results)) * 100 if sum(r["original_chunk_count"] for r in context_optimization_results) > 0 else 0
    
    logger.info("Context Optimization:")
    logger.info(f"  Overall average optimization time: {avg_all_co_time:.2f}s")
    logger.info(f"  Overall average chunk reduction: {avg_all_chunk_reduction:.2f} chunks ({avg_all_chunk_reduction_percent:.2f}%)")
    
    # Identify query types where judge performs best/worst
    type_performance = {}
    for query_type in query_types:
        # Filter results for this query type
        qa_results = [r for r in query_analysis_results if r["type"] == query_type]
        ce_results = [r for r in chunk_evaluation_results if r["type"] == query_type]
        qr_results = [r for r in query_refinement_results if r["type"] == query_type]
        co_results = [r for r in context_optimization_results if r["type"] == query_type]
        
        # Calculate performance metrics
        needs_refinement_rate = sum(1 for r in ce_results if r["evaluation"].get("needs_refinement", False)) / len(ce_results) if ce_results else 0
        avg_length_change_percent = (sum(len(r["refined_query"]) / len(r["query"]) for r in qr_results if len(r["query"]) > 0) / len(qr_results) - 1) * 100 if qr_results else 0
        avg_chunk_reduction_percent = (1 - sum(r["optimized_chunk_count"] for r in co_results) / sum(r["original_chunk_count"] for r in co_results)) * 100 if sum(r["original_chunk_count"] for r in co_results) > 0 else 0
        
        type_performance[query_type] = {
            "needs_refinement_rate": needs_refinement_rate,
            "avg_length_change_percent": avg_length_change_percent,
            "avg_chunk_reduction_percent": avg_chunk_reduction_percent
        }
    
    # Sort by refinement rate (lower is better)
    refinement_sorted = sorted(type_performance.items(), key=lambda x: x[1]["needs_refinement_rate"])
    
    logger.info("\nQuery types by refinement rate (lower is better):")
    for query_type, metrics in refinement_sorted:
        logger.info(f"  {query_type}: {metrics['needs_refinement_rate']*100:.2f}% need refinement")
    
    # Sort by chunk reduction (higher is better)
    chunk_reduction_sorted = sorted(type_performance.items(), key=lambda x: x[1]["avg_chunk_reduction_percent"], reverse=True)
    
    logger.info("\nQuery types by chunk reduction (higher is better):")
    for query_type, metrics in chunk_reduction_sorted:
        logger.info(f"  {query_type}: {metrics['avg_chunk_reduction_percent']:.2f}% chunk reduction")
    
    # Save analysis to file
    analysis = {
        "by_type": {
            query_type: {
                "query_analysis": {
                    "complexity_distribution": {complexity: sum(1 for r in query_analysis_results if r["type"] == query_type and r["analysis"].get("complexity") == complexity) for complexity in set(all_complexities)},
                    "avg_time": sum(r["time"] for r in query_analysis_results if r["type"] == query_type) / len([r for r in query_analysis_results if r["type"] == query_type]) if [r for r in query_analysis_results if r["type"] == query_type] else 0
                },
                "chunk_evaluation": {
                    "needs_refinement_rate": sum(1 for r in chunk_evaluation_results if r["type"] == query_type and r["evaluation"].get("needs_refinement", False)) / len([r for r in chunk_evaluation_results if r["type"] == query_type]) if [r for r in chunk_evaluation_results if r["type"] == query_type] else 0,
                    "avg_time": sum(r["time"] for r in chunk_evaluation_results if r["type"] == query_type) / len([r for r in chunk_evaluation_results if r["type"] == query_type]) if [r for r in chunk_evaluation_results if r["type"] == query_type] else 0
                },
                "query_refinement": {
                    "avg_length_change_percent": (sum(len(r["refined_query"]) / len(r["query"]) for r in query_refinement_results if r["type"] == query_type and len(r["query"]) > 0) / len([r for r in query_refinement_results if r["type"] == query_type]) - 1) * 100 if [r for r in query_refinement_results if r["type"] == query_type] else 0,
                    "avg_time": sum(r["time"] for r in query_refinement_results if r["type"] == query_type) / len([r for r in query_refinement_results if r["type"] == query_type]) if [r for r in query_refinement_results if r["type"] == query_type] else 0
                },
                "context_optimization": {
                    "avg_chunk_reduction_percent": (1 - sum(r["optimized_chunk_count"] for r in context_optimization_results if r["type"] == query_type) / sum(r["original_chunk_count"] for r in context_optimization_results if r["type"] == query_type)) * 100 if sum(r["original_chunk_count"] for r in context_optimization_results if r["type"] == query_type) > 0 else 0,
                    "avg_time": sum(r["time"] for r in context_optimization_results if r["type"] == query_type) / len([r for r in context_optimization_results if r["type"] == query_type]) if [r for r in context_optimization_results if r["type"] == query_type] else 0
                }
            }
            for query_type in query_types
        },
        "overall": {
            "query_analysis": {
                "complexity_distribution": all_complexity_counts,
                "avg_time": avg_all_qa_time
            },
            "chunk_evaluation": {
                "needs_refinement_rate": all_needs_refinement_count / len(chunk_evaluation_results) if chunk_evaluation_results else 0,
                "avg_time": avg_all_ce_time
            },
            "query_refinement": {
                "avg_length_change_percent": avg_all_length_change_percent,
                "avg_time": avg_all_qr_time
            },
            "context_optimization": {
                "avg_chunk_reduction_percent": avg_all_chunk_reduction_percent,
                "avg_time": avg_all_co_time
            }
        },
        "type_performance_ranking": {
            "by_refinement_rate": [{"type": t, "rate": m["needs_refinement_rate"]} for t, m in refinement_sorted],
            "by_chunk_reduction": [{"type": t, "reduction": m["avg_chunk_reduction_percent"]} for t, m in chunk_reduction_sorted]
        }
    }
    
    results_dir = os.path.join("tests", "retrieval_judge", "results")
    analysis_path = os.path.join(results_dir, "judge_edge_case_analysis.json")
    
    with open(analysis_path, "w") as f:
        json.dump(analysis, f, indent=2)
    
    logger.info(f"Edge case analysis saved to {os.path.abspath(analysis_path)}")
    
    return analysis

async def main():
    """Main test function"""
    logger.info("Starting Retrieval Judge edge case tests...")
    logger.info(f"Using model {JUDGE_MODEL} for the Retrieval Judge")
    
    try:
        # Create OllamaClient
        ollama_client = OllamaClient()
        
        # Create Retrieval Judge
        retrieval_judge = RetrievalJudge(ollama_client=ollama_client, model=JUDGE_MODEL)
        
        # Test query analysis
        query_analysis_results = await test_query_analysis(retrieval_judge)
        
        # Test chunk evaluation
        chunk_evaluation_results = await test_chunk_evaluation(retrieval_judge)
        
        # Test query refinement
        query_refinement_results = await test_query_refinement(retrieval_judge)
        
        # Test context optimization
        context_optimization_results = await test_context_optimization(retrieval_judge)
        
        # Analyze results
        analysis = await analyze_results(
            query_analysis_results,
            chunk_evaluation_results,
            query_refinement_results,
            context_optimization_results
        )
        
        logger.info("Retrieval Judge edge case tests completed successfully")
        
    except Exception as e:
        logger.error(f"Error during Retrieval Judge edge case tests: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())