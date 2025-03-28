#!/usr/bin/env python3
"""
Run document processing performance tests and save results
"""
import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.session import SessionLocal
from app.db.repositories.document_repository import DocumentRepository
from app.rag.document_processor import DocumentProcessor
from app.rag.document_analysis_service import DocumentAnalysisService
from app.rag.vector_store import VectorStore
from tests.test_document_processing_performance import (
    run_processing_tests,
    run_analysis_tests,
    TEST_FILE_SIZES,
    TEST_CHUNKING_STRATEGIES,
    ensure_test_folder_exists
)

def save_results_to_file(results, test_type):
    """Save test results to a JSON file"""
    # Create results directory if it doesn't exist
    results_dir = os.path.join(project_root, "tests", "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_type}_results_{timestamp}.json"
    filepath = os.path.join(results_dir, filename)
    
    # Save results to file
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {filepath}")
    return filepath

def generate_html_report(processing_results, analysis_results, output_path):
    """Generate HTML report from test results"""
    # Create HTML report
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Document Processing Performance Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2, h3 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .chart-container { width: 100%; height: 400px; margin-bottom: 30px; }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>Document Processing Performance Report</h1>
        <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        
        <h2>Document Processing Performance</h2>
        <div class="chart-container">
            <canvas id="processingChart"></canvas>
        </div>
        
        <h3>Processing Results by File Size and Strategy</h3>
        <table>
            <tr>
                <th>File</th>
                <th>Size</th>
                <th>Strategy</th>
                <th>Avg Time (s)</th>
                <th>Avg Chunks</th>
            </tr>
    """
    
    # Add processing results to table
    for result in processing_results:
        html += f"""
            <tr>
                <td>{result['filename']}</td>
                <td>{result['size_kb']} KB</td>
                <td>{result['chunking_strategy']}</td>
                <td>{result['avg_elapsed_time']:.2f}</td>
                <td>{int(result['avg_chunk_count'])}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>Document Analysis Performance</h2>
        <div class="chart-container">
            <canvas id="analysisChart"></canvas>
        </div>
        
        <h3>Analysis Results by File Size</h3>
        <table>
            <tr>
                <th>File</th>
                <th>Size</th>
                <th>Avg Time (s)</th>
                <th>Recommended Strategy</th>
            </tr>
    """
    
    # Add analysis results to table
    for result in analysis_results:
        html += f"""
            <tr>
                <td>{result['filename']}</td>
                <td>{result['size_kb']} KB</td>
                <td>{result['avg_elapsed_time']:.2f}</td>
                <td>{result['recommended_strategy']}</td>
            </tr>
        """
    
    # Prepare data for charts
    strategies = list(set([r['chunking_strategy'] for r in processing_results]))
    file_sizes = list(set([r['size_name'] for r in processing_results]))
    
    # Create JavaScript for charts
    html += """
        </table>
        
        <script>
            // Processing chart
            const processingCtx = document.getElementById('processingChart').getContext('2d');
            const processingChart = new Chart(processingCtx, {
                type: 'bar',
                data: {
                    labels: """ + str(file_sizes) + """,
                    datasets: [
    """
    
    # Add datasets for each strategy
    for i, strategy in enumerate(strategies):
        strategy_results = [r for r in processing_results if r['chunking_strategy'] == strategy]
        data_by_size = {}
        for result in strategy_results:
            if result['size_name'] not in data_by_size:
                data_by_size[result['size_name']] = []
            data_by_size[result['size_name']].append(result['avg_elapsed_time'])
        
        # Average times for each size
        avg_times = []
        for size in file_sizes:
            if size in data_by_size and data_by_size[size]:
                avg_times.append(sum(data_by_size[size]) / len(data_by_size[size]))
            else:
                avg_times.append(0)
        
        # Generate random color
        color = f"hsl({i * 360 // len(strategies)}, 70%, 60%)"
        
        html += f"""
                        {{
                            label: '{strategy}',
                            data: {avg_times},
                            backgroundColor: '{color}',
                            borderColor: '{color}',
                            borderWidth: 1
                        }},
        """
    
    html += """
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Average Processing Time by File Size and Strategy'
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Time (seconds)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'File Size'
                            }
                        }
                    }
                }
            });
            
            // Analysis chart
            const analysisCtx = document.getElementById('analysisChart').getContext('2d');
            const analysisChart = new Chart(analysisCtx, {
                type: 'bar',
                data: {
                    labels: """ + str(file_sizes) + """,
                    datasets: [{
                        label: 'Analysis Time',
                        data: [
    """
    
    # Add analysis data
    analysis_data = {}
    for result in analysis_results:
        if result['size_name'] not in analysis_data:
            analysis_data[result['size_name']] = []
        analysis_data[result['size_name']].append(result['avg_elapsed_time'])
    
    for size in file_sizes:
        if size in analysis_data and analysis_data[size]:
            html += f"{sum(analysis_data[size]) / len(analysis_data[size])},"
        else:
            html += "0,"
    
    html += """
                        ],
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Average Analysis Time by File Size'
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Time (seconds)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'File Size'
                            }
                        }
                    }
                }
            });
        </script>
    </body>
    </html>
    """
    
    # Save HTML report
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"\nHTML report saved to: {output_path}")

async def run_tests(args):
    """Run the performance tests"""
    print(f"\nRunning document processing performance tests...")
    print(f"File sizes: {[size[0] for size in TEST_FILE_SIZES]}")
    print(f"Chunking strategies: {TEST_CHUNKING_STRATEGIES}")
    
    # Create database session
    db_session = SessionLocal()
    
    try:
        # Create repositories and services
        document_repository = DocumentRepository(db_session)
        document_processor = DocumentProcessor()
        document_analysis_service = DocumentAnalysisService()
        vector_store = VectorStore()
        
        # Ensure test folder exists
        ensure_test_folder_exists(document_repository)
        
        # Run processing tests
        print("\nRunning document processing tests...")
        processing_results = await run_processing_tests(
            document_repository, 
            document_processor, 
            vector_store
        )
        
        # Save processing results
        processing_file = save_results_to_file(processing_results, "document_processing")
        
        # Run analysis tests
        print("\nRunning document analysis tests...")
        analysis_results = await run_analysis_tests(
            document_repository, 
            document_analysis_service
        )
        
        # Save analysis results
        analysis_file = save_results_to_file(analysis_results, "document_analysis")
        
        # Generate HTML report
        if args.html:
            # Create results directory if it doesn't exist
            results_dir = os.path.join(project_root, "tests", "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # Create HTML report filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = os.path.join(results_dir, f"document_processing_report_{timestamp}.html")
            
            # Generate HTML report
            generate_html_report(processing_results, analysis_results, html_path)
        
        print("\nTests completed successfully!")
        return 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1
    finally:
        db_session.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run document processing performance tests")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    args = parser.parse_args()
    
    return asyncio.run(run_tests(args))

if __name__ == "__main__":
    sys.exit(main())