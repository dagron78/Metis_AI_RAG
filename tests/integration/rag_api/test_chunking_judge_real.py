"""
Test script for Phase 1 of the LLM-enhanced RAG system: Chunking Judge component.
This script tests the Chunking Judge's ability to analyze different document types
and recommend appropriate chunking strategies using the real Ollama client.
"""
import asyncio
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("chunking_judge_test")

# Add the app directory to the Python path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.document import Document
from app.rag.agents.chunking_judge import ChunkingJudge
from app.rag.ollama_client import OllamaClient
from app.core.config import USE_CHUNKING_JUDGE, CHUNKING_JUDGE_MODEL

async def test_chunking_judge_with_real_ollama():
    """Test the Chunking Judge with different document types using the real Ollama client"""
    logger.info("\n===== Testing Chunking Judge Component with Real Ollama (Phase 1) =====\n")
    
    # Use real Ollama client
    logger.info(f"Using real Ollama client with model: {CHUNKING_JUDGE_MODEL}")
    ollama_client = OllamaClient()
    
    # Create Chunking Judge
    chunking_judge = ChunkingJudge(ollama_client=ollama_client)
    
    # Test documents - using files from the project root
    test_files = [
        "test_document.txt",
        "technical_documentation.md",
        "test_data.csv"
    ]
    
    results = []
    
    for filename in test_files:
        if not os.path.exists(filename):
            logger.warning(f"Warning: {filename} not found, skipping...")
            continue
            
        logger.info(f"\n----- Testing with {filename} -----\n")
        
        # Read document content
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Create document object
        document = Document(
            id=f"test-{filename}",
            filename=filename,
            content=content
        )
        
        # Analyze document with Chunking Judge
        logger.info(f"Analyzing document: {filename}")
        analysis_result = await chunking_judge.analyze_document(document)
        
        # Print analysis result
        logger.info("\nChunking Judge Analysis Result:")
        logger.info(f"Strategy: {analysis_result['strategy']}")
        logger.info(f"Parameters: chunk_size={analysis_result['parameters']['chunk_size']}, " +
              f"chunk_overlap={analysis_result['parameters']['chunk_overlap']}")
        logger.info(f"Justification: {analysis_result['justification']}")
        
        # Store results
        result = {
            "filename": filename,
            "strategy": analysis_result["strategy"],
            "parameters": analysis_result["parameters"],
            "justification": analysis_result["justification"]
        }
        results.append(result)
        
        logger.info("\n" + "="*50)
    
    # Save results to a JSON file
    results_file = "chunking_judge_real_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nTest results saved to {results_file}")
    
    return results

async def main():
    """Main function"""
    logger.info("Starting Chunking Judge Phase 1 test with real Ollama...")
    
    # Check if Chunking Judge is enabled
    if not USE_CHUNKING_JUDGE:
        logger.warning("Warning: Chunking Judge is disabled in configuration.")
        logger.warning("To enable it, set USE_CHUNKING_JUDGE=True in .env or app/core/config.py")
    
    results = await test_chunking_judge_with_real_ollama()
    
    # Print summary
    logger.info("\n===== Chunking Judge Test Summary =====")
    for result in results:
        logger.info(f"File: {result['filename']}")
        logger.info(f"Strategy: {result['strategy']}")
        logger.info(f"Parameters: chunk_size={result['parameters']['chunk_size']}, " +
              f"chunk_overlap={result['parameters']['chunk_overlap']}")
        logger.info("---")
    
    logger.info("\nChunking Judge Phase 1 test with real Ollama completed.")

if __name__ == "__main__":
    asyncio.run(main())