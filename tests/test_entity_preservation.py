#!/usr/bin/env python3
"""
Simplified test script to verify the entity preservation fix in the retrieval judge.
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

logger = logging.getLogger("test_entity_preservation")

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env.test
from dotenv import load_dotenv
load_dotenv(".env.test")

async def test_entity_preservation():
    """Test entity preservation in query refinement"""
    logger.info("Testing entity preservation in query refinement...")
    
    # Import the necessary modules
    from app.rag.agents.retrieval_judge import RetrievalJudge
    
    # Create a mock RetrievalJudge class that doesn't require external dependencies
    class MockRetrievalJudge(RetrievalJudge):
        def __init__(self):
            # Skip initialization that requires external dependencies
            pass
        
        async def refine_query(self, query: str, chunks: List[Dict[str, Any]]) -> str:
            # Simulate query refinement with a typo in entity names
            if "Stabilium" in query:
                refined = query.replace("Stabilium", "Stabilim")
                logger.info(f"Simulated refinement (with typo): '{query}' -> '{refined}'")
                # Now call our fixed _parse_refined_query method to fix the typo
                return self._parse_refined_query(refined, query)
            elif "Microsoft" in query:
                refined = query.replace("Microsoft", "Microsft")
                logger.info(f"Simulated refinement (with typo): '{query}' -> '{refined}'")
                return self._parse_refined_query(refined, query)
            elif "Quantum" in query:
                refined = query.replace("Quantum", "Quantom")
                logger.info(f"Simulated refinement (with typo): '{query}' -> '{refined}'")
                return self._parse_refined_query(refined, query)
            else:
                # No typo simulation for other queries
                logger.info(f"No typo simulation for: '{query}'")
                return self._parse_refined_query(query, query)
    
    # Create a mock retrieval judge
    retrieval_judge = MockRetrievalJudge()
    
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

async def main():
    """Main function to run all tests"""
    logger.info("Starting entity preservation test...")
    
    # Test entity preservation
    await test_entity_preservation()
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())