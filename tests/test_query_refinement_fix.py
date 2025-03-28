#!/usr/bin/env python3
"""
Test script to verify the query refinement fixes.

This script tests the following fixes:
1. Entity preservation in query refinement
2. Minimum context requirements
3. Chunk ID validation in citations
"""

import asyncio
import logging
import sys
import os
import uuid
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("test_query_refinement_fix")

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from app.rag.rag_engine import RAGEngine
from app.rag.agents.retrieval_judge import RetrievalJudge
from app.rag.ollama_client import OllamaClient
from app.models.chat import Message

async def test_entity_preservation():
    """Test entity preservation in query refinement"""
    logger.info("Testing entity preservation in query refinement...")
    
    # Create a retrieval judge
    ollama_client = OllamaClient()
    retrieval_judge = RetrievalJudge(ollama_client=ollama_client)
    
    # Test queries with entity names
    test_queries = [
        "tell me about Stabilium",
        "what is Quantum Resonance Modulation",
        "explain the Heisenberg Uncertainty Principle",
        "information about Microsoft Azure",
        "details on SpaceX Starship"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: {query}")
        
        # Create a mock chunks list for testing
        mock_chunks = [
            {
                "chunk_id": str(uuid.uuid4()),
                "content": f"This is a document about {query.split()[-1]}.",
                "metadata": {"filename": "test.txt"},
                "distance": 0.2
            }
        ]
        
        # Test query refinement
        refined_query = await retrieval_judge.refine_query(query, mock_chunks)
        
        # Check if the entity name is preserved
        entity_name = query.split()[-1]
        if entity_name in refined_query:
            logger.info(f"✅ Entity '{entity_name}' preserved in refined query: '{refined_query}'")
        else:
            logger.error(f"❌ Entity '{entity_name}' NOT preserved in refined query: '{refined_query}'")
            
        # Add a separator for readability
        logger.info("-" * 50)

async def test_minimum_context():
    """Test minimum context requirements"""
    logger.info("Testing minimum context requirements...")
    
    # Create a RAG engine
    rag_engine = RAGEngine()
    
    # Test query
    query = "tell me about Stabilium"
    
    # Execute the query
    response = await rag_engine.query(
        query=query,
        use_rag=True,
        stream=False
    )
    
    # Check the response
    if response and "answer" in response:
        answer = response["answer"]
        sources = response.get("sources", [])
        
        logger.info(f"Query: {query}")
        logger.info(f"Answer length: {len(answer)} characters")
        logger.info(f"Number of sources: {len(sources)}")
        
        # Check if we have a minimum number of sources
        if len(sources) >= 3:
            logger.info("✅ Minimum context requirement met")
        else:
            logger.warning(f"⚠️ Minimum context requirement not met: only {len(sources)} sources")
            
        # Log the first 100 characters of the answer
        logger.info(f"Answer preview: {answer[:100]}...")
    else:
        logger.error("❌ Failed to get a response from the RAG engine")
    
    # Add a separator for readability
    logger.info("-" * 50)

async def test_citation_handling():
    """Test citation handling with non-existent chunk IDs"""
    logger.info("Testing citation handling...")
    
    # Create a RAG engine
    rag_engine = RAGEngine()
    
    # Create a conversation with history
    conversation_id = str(uuid.uuid4())
    conversation_history = [
        Message(id=1, conversation_id=conversation_id, role="user", content="Hello"),
        Message(id=2, conversation_id=conversation_id, role="assistant", content="Hi there! How can I help you?")
    ]
    
    # Test query
    query = "tell me about Stabilium and Quantum Resonance"
    
    # Execute the query
    response = await rag_engine.query(
        query=query,
        use_rag=True,
        stream=False,
        conversation_history=conversation_history
    )
    
    # Check the response
    if response and "answer" in response:
        answer = response["answer"]
        sources = response.get("sources", [])
        
        logger.info(f"Query: {query}")
        logger.info(f"Answer length: {len(answer)} characters")
        logger.info(f"Number of sources: {len(sources)}")
        
        # Check if we have valid sources
        valid_sources = [s for s in sources if s.document_id]
        if len(valid_sources) > 0:
            logger.info(f"✅ Valid sources found: {len(valid_sources)}")
        else:
            logger.warning("⚠️ No valid sources found")
            
        # Log the first 100 characters of the answer
        logger.info(f"Answer preview: {answer[:100]}...")
    else:
        logger.error("❌ Failed to get a response from the RAG engine")
    
    # Add a separator for readability
    logger.info("-" * 50)

async def main():
    """Main function to run all tests"""
    logger.info("Starting query refinement fix tests...")
    
    # Test entity preservation
    await test_entity_preservation()
    
    # Test minimum context requirements
    await test_minimum_context()
    
    # Test citation handling
    await test_citation_handling()
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())