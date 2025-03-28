#!/usr/bin/env python3
"""
Analysis script for Retrieval Judge comparison results.
This script:
1. Loads the results from the comparison test
2. Performs detailed analysis on the effectiveness of the Retrieval Judge
3. Generates visualizations to highlight key findings
4. Provides recommendations for improving the Retrieval Judge
"""

import os
import json
import logging
import argparse
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("analyze_retrieval_judge_results")

def load_results(results_file: str) -> List[Dict[str, Any]]:
    """Load the comparison test results from file"""
    logger.info(f"Loading results from {results_file}")
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        logger.info(f"Loaded {len(results)} test results")
        return results
    except Exception as e:
        logger.error(f"Error loading results: {str(e)}")
        return []

def load_metrics(metrics_file: str) -> Dict[str, Any]:
    """Load the analysis metrics from file"""
    logger.info(f"Loading metrics from {metrics_file}")
    
    try:
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        logger.info(f"Loaded metrics for {metrics.get('total_queries', 0)} queries")
        return metrics
    except Exception as e:
        logger.error(f"Error loading metrics: {str(e)}")
        return {}

def analyze_source_relevance(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the relevance of sources retrieved by both methods"""
    logger.info("Analyzing source relevance...")
    
    relevance_analysis = {
        "avg_standard_relevance": 0,
        "avg_judge_relevance": 0,
        "relevance_improvement": 0,
        "by_complexity": {},
        "by_document": defaultdict(lambda: {"standard": 0, "judge": 0, "count": 0})
    }
    
    # Initialize complexity metrics
    for complexity in ["simple", "moderate", "complex", "ambiguous", "multi-part"]:
        relevance_analysis["by_complexity"][complexity] = {
            "count": 0,
            "avg_standard_relevance": 0,
            "avg_judge_relevance": 0,
            "improvement": 0
        }
    
    # Calculate average relevance scores
    total_standard_relevance = 0
    total_judge_relevance = 0
    total_sources = 0
    
    for result in results:
        complexity = result["complexity"]
        
        # Calculate average relevance for standard retrieval
        standard_sources = result["standard"]["sources"]
        standard_relevance = sum(s["relevance_score"] for s in standard_sources) if standard_sources else 0
        standard_avg_relevance = standard_relevance / len(standard_sources) if standard_sources else 0
        
        # Calculate average relevance for judge retrieval
        judge_sources = result["judge"]["sources"]
        judge_relevance = sum(s["relevance_score"] for s in judge_sources) if judge_sources else 0
        judge_avg_relevance = judge_relevance / len(judge_sources) if judge_sources else 0
        
        # Update totals
        total_standard_relevance += standard_avg_relevance
        total_judge_relevance += judge_avg_relevance
        total_sources += 1
        
        # Update complexity metrics
        if complexity in relevance_analysis["by_complexity"]:
            relevance_analysis["by_complexity"][complexity]["count"] += 1
            relevance_analysis["by_complexity"][complexity]["avg_standard_relevance"] += standard_avg_relevance
            relevance_analysis["by_complexity"][complexity]["avg_judge_relevance"] += judge_avg_relevance
        
        # Track relevance by document
        for source in standard_sources:
            doc_id = source["document_id"]
            relevance_analysis["by_document"][doc_id]["standard"] += source["relevance_score"]
            relevance_analysis["by_document"][doc_id]["count"] += 1
            
        for source in judge_sources:
            doc_id = source["document_id"]
            relevance_analysis["by_document"][doc_id]["judge"] += source["relevance_score"]
            # Don't increment count again as we're calculating averages
    
    # Calculate overall averages
    if total_sources > 0:
        relevance_analysis["avg_standard_relevance"] = total_standard_relevance / total_sources
        relevance_analysis["avg_judge_relevance"] = total_judge_relevance / total_sources
        
        # Calculate improvement percentage
        if relevance_analysis["avg_standard_relevance"] > 0:
            relevance_analysis["relevance_improvement"] = (
                (relevance_analysis["avg_judge_relevance"] - relevance_analysis["avg_standard_relevance"]) / 
                relevance_analysis["avg_standard_relevance"] * 100
            )
    
    # Calculate complexity averages and improvements
    for complexity, data in relevance_analysis["by_complexity"].items():
        if data["count"] > 0:
            data["avg_standard_relevance"] /= data["count"]
            data["avg_judge_relevance"] /= data["count"]
            
            # Calculate improvement percentage
            if data["avg_standard_relevance"] > 0:
                data["improvement"] = (
                    (data["avg_judge_relevance"] - data["avg_standard_relevance"]) / 
                    data["avg_standard_relevance"] * 100
                )
    
    # Calculate document averages
    for doc_id, data in relevance_analysis["by_document"].items():
        if data["count"] > 0:
            data["avg_standard"] = data["standard"] / data["count"]
            data["avg_judge"] = data["judge"] / data["count"]
            
            # Calculate improvement percentage
            if data["avg_standard"] > 0:
                data["improvement"] = (
                    (data["avg_judge"] - data["avg_standard"]) / 
                    data["avg_standard"] * 100
                )
    
    # Convert defaultdict to regular dict for JSON serialization
    relevance_analysis["by_document"] = dict(relevance_analysis["by_document"])
    
    return relevance_analysis

def analyze_query_refinement(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the effectiveness of query refinement"""
    logger.info("Analyzing query refinement effectiveness...")
    
    # This is a bit tricky since we don't have direct access to the refined queries
    # We'll infer effectiveness by comparing source relevance for ambiguous queries
    
    refinement_analysis = {
        "ambiguous_queries": [],
        "multi_part_queries": [],
        "avg_improvement_ambiguous": 0,
        "avg_improvement_multi_part": 0
    }
    
    # Extract ambiguous and multi-part queries
    ambiguous_queries = [r for r in results if r["complexity"] == "ambiguous"]
    multi_part_queries = [r for r in results if r["complexity"] == "multi-part"]
    
    # Calculate average improvement for ambiguous queries
    total_improvement_ambiguous = 0
    for query in ambiguous_queries:
        standard_sources = query["standard"]["sources"]
        judge_sources = query["judge"]["sources"]
        
        standard_relevance = sum(s["relevance_score"] for s in standard_sources) / len(standard_sources) if standard_sources else 0
        judge_relevance = sum(s["relevance_score"] for s in judge_sources) / len(judge_sources) if judge_sources else 0
        
        improvement = ((judge_relevance - standard_relevance) / standard_relevance * 100) if standard_relevance > 0 else 0
        
        refinement_analysis["ambiguous_queries"].append({
            "query": query["query"],
            "standard_relevance": standard_relevance,
            "judge_relevance": judge_relevance,
            "improvement": improvement
        })
        
        total_improvement_ambiguous += improvement
    
    # Calculate average improvement for multi-part queries
    total_improvement_multi_part = 0
    for query in multi_part_queries:
        standard_sources = query["standard"]["sources"]
        judge_sources = query["judge"]["sources"]
        
        standard_relevance = sum(s["relevance_score"] for s in standard_sources) / len(standard_sources) if standard_sources else 0
        judge_relevance = sum(s["relevance_score"] for s in judge_sources) / len(judge_sources) if judge_sources else 0
        
        improvement = ((judge_relevance - standard_relevance) / standard_relevance * 100) if standard_relevance > 0 else 0
        
        refinement_analysis["multi_part_queries"].append({
            "query": query["query"],
            "standard_relevance": standard_relevance,
            "judge_relevance": judge_relevance,
            "improvement": improvement
        })
        
        total_improvement_multi_part += improvement
    
    # Calculate averages
    if ambiguous_queries:
        refinement_analysis["avg_improvement_ambiguous"] = total_improvement_ambiguous / len(ambiguous_queries)
    
    if multi_part_queries:
        refinement_analysis["avg_improvement_multi_part"] = total_improvement_multi_part / len(multi_part_queries)
    
    return refinement_analysis

def analyze_context_optimization(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the effectiveness of context optimization"""
    logger.info("Analyzing context optimization effectiveness...")
    
    optimization_analysis = {
        "avg_standard_sources": 0,
        "avg_judge_sources": 0,
        "source_count_difference": 0,
        "source_count_difference_percent": 0,
        "by_complexity": {}
    }
    
    # Initialize complexity metrics
    for complexity in ["simple", "moderate", "complex", "ambiguous", "multi-part"]:
        optimization_analysis["by_complexity"][complexity] = {
            "count": 0,
            "avg_standard_sources": 0,
            "avg_judge_sources": 0,
            "difference": 0,
            "difference_percent": 0
        }
    
    # Calculate source counts
    total_standard_sources = 0
    total_judge_sources = 0
    total_queries = len(results)
    
    for result in results:
        complexity = result["complexity"]
        standard_source_count = len(result["standard"]["sources"])
        judge_source_count = len(result["judge"]["sources"])
        
        # Update totals
        total_standard_sources += standard_source_count
        total_judge_sources += judge_source_count
        
        # Update complexity metrics
        if complexity in optimization_analysis["by_complexity"]:
            optimization_analysis["by_complexity"][complexity]["count"] += 1
            optimization_analysis["by_complexity"][complexity]["avg_standard_sources"] += standard_source_count
            optimization_analysis["by_complexity"][complexity]["avg_judge_sources"] += judge_source_count
    
    # Calculate overall averages
    if total_queries > 0:
        optimization_analysis["avg_standard_sources"] = total_standard_sources / total_queries
        optimization_analysis["avg_judge_sources"] = total_judge_sources / total_queries
        
        # Calculate difference
        optimization_analysis["source_count_difference"] = optimization_analysis["avg_judge_sources"] - optimization_analysis["avg_standard_sources"]
        
        # Calculate percentage difference
        if optimization_analysis["avg_standard_sources"] > 0:
            optimization_analysis["source_count_difference_percent"] = (
                optimization_analysis["source_count_difference"] / optimization_analysis["avg_standard_sources"] * 100
            )
    
    # Calculate complexity averages and differences
    for complexity, data in optimization_analysis["by_complexity"].items():
        if data["count"] > 0:
            data["avg_standard_sources"] /= data["count"]
            data["avg_judge_sources"] /= data["count"]
            
            # Calculate difference
            data["difference"] = data["avg_judge_sources"] - data["avg_standard_sources"]
            
            # Calculate percentage difference
            if data["avg_standard_sources"] > 0:
                data["difference_percent"] = (
                    data["difference"] / data["avg_standard_sources"] * 100
                )
    
    return optimization_analysis

def analyze_performance_impact(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the performance impact of using the Retrieval Judge"""
    logger.info("Analyzing performance impact...")
    
    performance_analysis = {
        "avg_standard_time": 0,
        "avg_judge_time": 0,
        "time_difference": 0,
        "time_difference_percent": 0,
        "by_complexity": {}
    }
    
    # Initialize complexity metrics
    for complexity in ["simple", "moderate", "complex", "ambiguous", "multi-part"]:
        performance_analysis["by_complexity"][complexity] = {
            "count": 0,
            "avg_standard_time": 0,
            "avg_judge_time": 0,
            "difference": 0,
            "difference_percent": 0
        }
    
    # Calculate processing times
    total_standard_time = 0
    total_judge_time = 0
    total_queries = len(results)
    
    for result in results:
        complexity = result["complexity"]
        standard_time = result["standard"]["time"]
        judge_time = result["judge"]["time"]
        
        # Update totals
        total_standard_time += standard_time
        total_judge_time += judge_time
        
        # Update complexity metrics
        if complexity in performance_analysis["by_complexity"]:
            performance_analysis["by_complexity"][complexity]["count"] += 1
            performance_analysis["by_complexity"][complexity]["avg_standard_time"] += standard_time
            performance_analysis["by_complexity"][complexity]["avg_judge_time"] += judge_time
    
    # Calculate overall averages
    if total_queries > 0:
        performance_analysis["avg_standard_time"] = total_standard_time / total_queries
        performance_analysis["avg_judge_time"] = total_judge_time / total_queries
        
        # Calculate difference
        performance_analysis["time_difference"] = performance_analysis["avg_judge_time"] - performance_analysis["avg_standard_time"]
        
        # Calculate percentage difference
        if performance_analysis["avg_standard_time"] > 0:
            performance_analysis["time_difference_percent"] = (
                performance_analysis["time_difference"] / performance_analysis["avg_standard_time"] * 100
            )
    
    # Calculate complexity averages and differences
    for complexity, data in performance_analysis["by_complexity"].items():
        if data["count"] > 0:
            data["avg_standard_time"] /= data["count"]
            data["avg_judge_time"] /= data["count"]
            
            # Calculate difference
            data["difference"] = data["avg_judge_time"] - data["avg_standard_time"]
            
            # Calculate percentage difference
            if data["avg_standard_time"] > 0:
                data["difference_percent"] = (
                    data["difference"] / data["avg_standard_time"] * 100
                )
    
    return performance_analysis

def generate_visualizations(
    results: List[Dict[str, Any]], 
    relevance_analysis: Dict[str, Any],
    refinement_analysis: Dict[str, Any],
    optimization_analysis: Dict[str, Any],
    performance_analysis: Dict[str, Any]
):
    """Generate visualizations to highlight key findings"""
    logger.info("Generating visualizations...")
    
    # Create output directory for visualizations
    vis_dir = os.path.join("tests", "retrieval_judge", "visualizations")
    os.makedirs(vis_dir, exist_ok=True)
    
    # 1. Relevance improvement by complexity
    plt.figure(figsize=(10, 6))
    complexities = list(relevance_analysis["by_complexity"].keys())
    improvements = [relevance_analysis["by_complexity"][c]["improvement"] for c in complexities]
    
    plt.bar(complexities, improvements, color='skyblue')
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.title('Relevance Improvement by Query Complexity')
    plt.xlabel('Query Complexity')
    plt.ylabel('Improvement (%)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(vis_dir, 'relevance_by_complexity.png'))
    plt.close()
    
    # 2. Source count comparison
    plt.figure(figsize=(10, 6))
    complexities = list(optimization_analysis["by_complexity"].keys())
    standard_sources = [optimization_analysis["by_complexity"][c]["avg_standard_sources"] for c in complexities]
    judge_sources = [optimization_analysis["by_complexity"][c]["avg_judge_sources"] for c in complexities]
    
    x = np.arange(len(complexities))
    width = 0.35
    
    plt.bar(x - width/2, standard_sources, width, label='Standard Retrieval', color='lightcoral')
    plt.bar(x + width/2, judge_sources, width, label='Judge-Enhanced Retrieval', color='lightgreen')
    
    plt.title('Average Number of Sources by Query Complexity')
    plt.xlabel('Query Complexity')
    plt.ylabel('Average Number of Sources')
    plt.xticks(x, complexities)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(vis_dir, 'source_count_comparison.png'))
    plt.close()
    
    # 3. Processing time comparison
    plt.figure(figsize=(10, 6))
    complexities = list(performance_analysis["by_complexity"].keys())
    standard_times = [performance_analysis["by_complexity"][c]["avg_standard_time"] for c in complexities]
    judge_times = [performance_analysis["by_complexity"][c]["avg_judge_time"] for c in complexities]
    
    x = np.arange(len(complexities))
    width = 0.35
    
    plt.bar(x - width/2, standard_times, width, label='Standard Retrieval', color='lightcoral')
    plt.bar(x + width/2, judge_times, width, label='Judge-Enhanced Retrieval', color='lightgreen')
    
    plt.title('Average Processing Time by Query Complexity')
    plt.xlabel('Query Complexity')
    plt.ylabel('Average Time (seconds)')
    plt.xticks(x, complexities)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(vis_dir, 'processing_time_comparison.png'))
    plt.close()
    
    # 4. Query refinement effectiveness
    plt.figure(figsize=(10, 6))
    query_types = ['Ambiguous', 'Multi-part']
    improvements = [
        refinement_analysis["avg_improvement_ambiguous"],
        refinement_analysis["avg_improvement_multi_part"]
    ]
    
    plt.bar(query_types, improvements, color=['orange', 'purple'])
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.title('Query Refinement Effectiveness')
    plt.xlabel('Query Type')
    plt.ylabel('Average Relevance Improvement (%)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(vis_dir, 'query_refinement_effectiveness.png'))
    plt.close()
    
    logger.info(f"Visualizations saved to {os.path.abspath(vis_dir)}")

def generate_improvement_recommendations(
    relevance_analysis: Dict[str, Any],
    refinement_analysis: Dict[str, Any],
    optimization_analysis: Dict[str, Any],
    performance_analysis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate recommendations for improving the Retrieval Judge"""
    logger.info("Generating improvement recommendations...")
    
    recommendations = []
    
    # 1. Check relevance improvement
    overall_relevance_improvement = relevance_analysis.get("relevance_improvement", 0)
    if overall_relevance_improvement < 10:
        recommendations.append({
            "area": "Relevance Scoring",
            "issue": "Limited overall relevance improvement",
            "recommendation": "Enhance the relevance evaluation prompt to better distinguish between highly relevant and tangentially relevant content. Consider using a more fine-grained scoring system or incorporating domain-specific knowledge."
        })
    
    # 2. Check performance impact
    time_difference_percent = performance_analysis.get("time_difference_percent", 0)
    if time_difference_percent > 50:
        recommendations.append({
            "area": "Performance",
            "issue": "Significant processing time increase",
            "recommendation": "Optimize the judge's processing pipeline by: 1) Using a smaller, faster model for initial query analysis, 2) Implementing caching for similar queries, 3) Reducing the context size in prompts, or 4) Implementing parallel processing for independent judge operations."
        })
    
    # 3. Check query refinement effectiveness
    avg_improvement_ambiguous = refinement_analysis.get("avg_improvement_ambiguous", 0)
    if avg_improvement_ambiguous < 15:
        recommendations.append({
            "area": "Query Refinement",
            "issue": "Limited effectiveness for ambiguous queries",
            "recommendation": "Improve the query refinement prompt to better handle ambiguity by: 1) Adding examples of successful disambiguations, 2) Incorporating domain-specific terminology, 3) Implementing a clarification step that generates multiple possible interpretations before selecting the most likely one."
        })
    
    # 4. Check context optimization
    source_count_difference = optimization_analysis.get("source_count_difference", 0)
    if source_count_difference < 0:
        recommendations.append({
            "area": "Context Optimization",
            "issue": "Judge retrieves fewer sources on average",
            "recommendation": "Revise the context optimization logic to: 1) Focus more on diversity of information rather than just relevance, 2) Implement a minimum source count based on query complexity, 3) Add a post-processing step to ensure critical information isn't excluded."
        })
    
    # 5. Check complex query handling
    complex_improvement = relevance_analysis.get("by_complexity", {}).get("complex", {}).get("improvement", 0)
    if complex_improvement < 20:
        recommendations.append({
            "area": "Complex Query Handling",
            "issue": "Limited improvement for complex analytical queries",
            "recommendation": "Enhance complex query processing by: 1) Breaking down complex queries into sub-queries, 2) Implementing a multi-step retrieval process that builds context incrementally, 3) Adding a synthesis step that combines information from multiple sources."
        })
    
    # 6. Check multi-part query handling
    multi_part_improvement = relevance_analysis.get("by_complexity", {}).get("multi-part", {}).get("improvement", 0)
    if multi_part_improvement < 15:
        recommendations.append({
            "area": "Multi-part Query Handling",
            "issue": "Limited improvement for multi-part queries",
            "recommendation": "Improve multi-part query handling by: 1) Implementing a query decomposition step that identifies distinct sub-questions, 2) Retrieving information for each sub-question separately, 3) Merging the results with appropriate weighting, 4) Adding a final relevance check to ensure all parts of the query are addressed."
        })
    
    # Always recommend monitoring and feedback loop
    recommendations.append({
        "area": "Continuous Improvement",
        "issue": "Need for ongoing optimization",
        "recommendation": "Implement a feedback loop by: 1) Tracking user satisfaction with responses, 2) Logging cases where the judge significantly improves or degrades results, 3) Periodically retraining or fine-tuning the judge with examples of successful and unsuccessful retrievals."
    })
    
    return recommendations

def main():
    """Main analysis function"""
    parser = argparse.ArgumentParser(description="Analyze Retrieval Judge comparison results")
    parser.add_argument("--results", default=os.path.join("tests", "retrieval_judge", "results", "retrieval_judge_comparison_results.json"), 
                        help="Path to results JSON file")
    parser.add_argument("--metrics", default=os.path.join("tests", "retrieval_judge", "results", "retrieval_judge_metrics.json"), 
                        help="Path to metrics JSON file")
    parser.add_argument("--output", default=os.path.join("tests", "retrieval_judge", "results", "retrieval_judge_analysis_report.json"), 
                        help="Path to output analysis report")
    args = parser.parse_args()
    
    logger.info("Starting Retrieval Judge results analysis...")
    
    try:
        # Load results and metrics
        results = load_results(args.results)
        metrics = load_metrics(args.metrics)
        
        if not results:
            logger.error("No results to analyze. Please run the comparison test first.")
            return
        
        # Perform detailed analysis
        relevance_analysis = analyze_source_relevance(results)
        refinement_analysis = analyze_query_refinement(results)
        optimization_analysis = analyze_context_optimization(results)
        performance_analysis = analyze_performance_impact(results)
        
        # Generate visualizations
        generate_visualizations(
            results,
            relevance_analysis,
            refinement_analysis,
            optimization_analysis,
            performance_analysis
        )
        
        # Generate improvement recommendations
        recommendations = generate_improvement_recommendations(
            relevance_analysis,
            refinement_analysis,
            optimization_analysis,
            performance_analysis
        )
        
        # Compile analysis report
        analysis_report = {
            "summary": {
                "total_queries": len(results),
                "overall_relevance_improvement": relevance_analysis["relevance_improvement"],
                "performance_impact": performance_analysis["time_difference_percent"],
                "recommendation_count": len(recommendations)
            },
            "detailed_analysis": {
                "relevance": relevance_analysis,
                "query_refinement": refinement_analysis,
                "context_optimization": optimization_analysis,
                "performance": performance_analysis
            },
            "recommendations": recommendations
        }
        
        # Save analysis report
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(analysis_report, f, indent=2)
        
        # Print summary
        logger.info("\n=== RETRIEVAL JUDGE ANALYSIS SUMMARY ===")
        logger.info(f"Total queries analyzed: {len(results)}")
        logger.info(f"Overall relevance improvement: {relevance_analysis['relevance_improvement']:.2f}%")
        logger.info(f"Performance impact: {performance_analysis['time_difference_percent']:.2f}% increase in processing time")
        logger.info(f"Generated {len(recommendations)} improvement recommendations")
        logger.info(f"Analysis report saved to {os.path.abspath(args.output)}")
        logger.info(f"Visualizations saved to {os.path.abspath(os.path.join('tests', 'retrieval_judge', 'visualizations'))}")
        
        # Print top recommendations
        logger.info("\nTop improvement recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            logger.info(f"{i}. {rec['area']}: {rec['recommendation']}")
        
        logger.info("\nRetrieval Judge analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()