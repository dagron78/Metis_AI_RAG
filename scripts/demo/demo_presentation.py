#!/usr/bin/env python3
"""
Metis RAG Demo Presentation Script

This script simulates a basic interaction with the Metis RAG system for demonstration purposes.
It shows the key steps in the RAG process, from query processing to response generation.
"""

import time
import json
import random
from datetime import datetime

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_step(step_num, step_name):
    """Print a formatted step header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}[Step {step_num}] {step_name}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'-' * 50}{Colors.ENDC}\n")

def simulate_typing(text, delay=0.03):
    """Simulate typing by printing characters with a delay."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def progress_bar(duration, description):
    """Display a progress bar for the given duration."""
    steps = 40
    for i in range(steps + 1):
        progress = i / steps
        bar = '█' * i + '░' * (steps - i)
        percentage = int(progress * 100)
        print(f"\r{Colors.CYAN}{description}: [{bar}] {percentage}%{Colors.ENDC}", end='')
        time.sleep(duration / steps)
    print()

def simulate_document_processing():
    """Simulate document processing."""
    print_step(1, "Document Processing")
    
    documents = [
        {"name": "quarterly_report.txt", "size": "245 KB", "pages": 12},
        {"name": "technical_documentation.md", "size": "189 KB", "pages": 8},
        {"name": "product_specifications.csv", "size": "78 KB", "rows": 156}
    ]
    
    print(f"{Colors.YELLOW}Available Documents:{Colors.ENDC}")
    for i, doc in enumerate(documents, 1):
        pages = doc.get('pages', doc.get('rows', 'N/A'))
        print(f"{i}. {doc['name']} ({doc['size']}, {pages} pages/rows)")
    
    print(f"\n{Colors.GREEN}Processing documents...{Colors.ENDC}")
    
    for doc in documents:
        print(f"\n{Colors.CYAN}Processing {doc['name']}...{Colors.ENDC}")
        
        # Determine chunking strategy based on file extension
        if doc['name'].endswith('.md'):
            strategy = "Markdown Header Chunking"
        elif doc['name'].endswith('.csv'):
            strategy = "Token-based Chunking"
        else:
            strategy = "Recursive Chunking"
        
        print(f"  Using {Colors.YELLOW}{strategy}{Colors.ENDC}")
        progress_bar(2, f"Extracting text from {doc['name']}")
        
        # Show chunking process
        chunk_count = random.randint(5, 20)
        print(f"  Created {Colors.GREEN}{chunk_count} chunks{Colors.ENDC}")
        progress_bar(1.5, "Generating embeddings")
        
        # Show vector storage
        print(f"  Stored in vector database with {Colors.GREEN}metadata{Colors.ENDC}")
    
    print(f"\n{Colors.GREEN}All documents processed successfully!{Colors.ENDC}")

def simulate_query_processing():
    """Simulate query processing."""
    print_step(2, "Query Processing")
    
    # User query
    query = "What are the key performance metrics for the new product line?"
    print(f"{Colors.YELLOW}User Query:{Colors.ENDC}")
    simulate_typing(f"{Colors.BOLD}{query}{Colors.ENDC}", 0.05)
    
    print(f"\n{Colors.CYAN}Processing query...{Colors.ENDC}")
    progress_bar(1, "Generating query embedding")
    
    # Vector search
    print(f"\n{Colors.CYAN}Searching vector database...{Colors.ENDC}")
    progress_bar(2, "Performing semantic search")
    
    # Retrieved chunks
    print(f"\n{Colors.GREEN}Retrieved relevant chunks:{Colors.ENDC}")
    chunks = [
        {"text": "The new product line demonstrated a 27% increase in efficiency metrics compared to previous generation...", "source": "quarterly_report.txt", "similarity": 0.89},
        {"text": "Key performance indicators include: processing speed (45 units/min), energy efficiency (0.8 kWh), and reliability score (98.7%)...", "source": "product_specifications.csv", "similarity": 0.87},
        {"text": "Performance testing revealed consistent results across all operational environments with metrics exceeding target thresholds...", "source": "technical_documentation.md", "similarity": 0.76}
    ]
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n{Colors.YELLOW}Chunk {i} (Similarity: {chunk['similarity']:.2f}){Colors.ENDC}")
        print(f"Source: {chunk['source']}")
        print(f"Text: \"{chunk['text']}\"")
    
    # Context assembly
    print(f"\n{Colors.CYAN}Assembling context for LLM...{Colors.ENDC}")
    progress_bar(1.5, "Building prompt with retrieved context")

def simulate_response_generation():
    """Simulate response generation."""
    print_step(3, "Response Generation")
    
    # Prompt construction
    print(f"{Colors.CYAN}Constructing prompt with retrieved context...{Colors.ENDC}")
    progress_bar(1, "Optimizing prompt")
    
    # LLM generation
    print(f"\n{Colors.CYAN}Generating response with Ollama (llama3)...{Colors.ENDC}")
    
    response = """Based on the provided documents, the key performance metrics for the new product line are:

1. **Efficiency**: 27% increase compared to the previous generation (source: quarterly_report.txt)

2. **Processing Speed**: 45 units per minute, which exceeds the industry standard (source: product_specifications.csv)

3. **Energy Efficiency**: 0.8 kWh consumption rate, representing a 15% improvement (source: product_specifications.csv)

4. **Reliability Score**: 98.7%, which surpasses the target threshold of 95% (source: product_specifications.csv)

5. **Environmental Performance**: Consistent results across all operational environments, with all metrics exceeding target thresholds (source: technical_documentation.md)

These metrics indicate that the new product line is performing exceptionally well, particularly in terms of efficiency and reliability. The consistent performance across different operational environments also suggests robust design and implementation."""
    
    # Stream the response
    print(f"\n{Colors.GREEN}Response:{Colors.ENDC}")
    simulate_typing(response, 0.01)
    
    # Show citations
    print(f"\n{Colors.YELLOW}Sources:{Colors.ENDC}")
    print("1. quarterly_report.txt (Section: Q2 Performance Review)")
    print("2. product_specifications.csv (Rows: 45-48)")
    print("3. technical_documentation.md (Section: Performance Testing)")

def simulate_analytics():
    """Simulate analytics dashboard."""
    print_step(4, "Analytics")
    
    print(f"{Colors.CYAN}Generating analytics data...{Colors.ENDC}")
    
    # Query statistics
    print(f"\n{Colors.YELLOW}Query Statistics:{Colors.ENDC}")
    stats = {
        "total_queries": 1245,
        "avg_response_time": 9.8,
        "rag_usage_percentage": 78,
        "avg_tokens_per_response": 512,
        "top_document": "technical_documentation.md (used in 34% of responses)"
    }
    
    for key, value in stats.items():
        key_formatted = key.replace("_", " ").title()
        print(f"  {key_formatted}: {Colors.GREEN}{value}{Colors.ENDC}")
    
    # Performance metrics
    print(f"\n{Colors.YELLOW}Performance Metrics:{Colors.ENDC}")
    print(f"  Vector Search Time: {Colors.GREEN}0.45s (avg){Colors.ENDC}")
    print(f"  Context Assembly Time: {Colors.GREEN}0.12s (avg){Colors.ENDC}")
    print(f"  LLM Generation Time: {Colors.GREEN}9.2s (avg){Colors.ENDC}")
    print(f"  Total Response Time: {Colors.GREEN}9.8s (avg){Colors.ENDC}")
    
    # Document usage
    print(f"\n{Colors.YELLOW}Document Usage:{Colors.ENDC}")
    print(f"  Most Used Document: {Colors.GREEN}technical_documentation.md{Colors.ENDC}")
    print(f"  Most Relevant Section: {Colors.GREEN}Performance Testing{Colors.ENDC}")
    print(f"  Cache Hit Ratio: {Colors.GREEN}68%{Colors.ENDC}")

def main():
    """Run the demo presentation."""
    print_header("METIS RAG TECHNICAL DEMONSTRATION")
    
    print(f"{Colors.BOLD}Date:{Colors.ENDC} {datetime.now().strftime('%B %d, %Y')}")
    print(f"{Colors.BOLD}System:{Colors.ENDC} Metis RAG v1.2.0")
    print(f"{Colors.BOLD}Models:{Colors.ENDC} llama3 (LLM), nomic-embed-text (Embeddings)")
    
    input(f"\n{Colors.YELLOW}Press Enter to start the demonstration...{Colors.ENDC}")
    
    simulate_document_processing()
    input(f"\n{Colors.YELLOW}Press Enter to continue to query processing...{Colors.ENDC}")
    
    simulate_query_processing()
    input(f"\n{Colors.YELLOW}Press Enter to continue to response generation...{Colors.ENDC}")
    
    simulate_response_generation()
    input(f"\n{Colors.YELLOW}Press Enter to view analytics...{Colors.ENDC}")
    
    simulate_analytics()
    
    print_header("DEMONSTRATION COMPLETE")
    print(f"{Colors.GREEN}{Colors.BOLD}Thank you for attending the Metis RAG technical demonstration!{Colors.ENDC}")

if __name__ == "__main__":
    main()