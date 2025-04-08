#!/usr/bin/env python3
"""
Script to check and compare Ollama raw output with processed output in logs.

This script:
1. Sets the logging level to DEBUG
2. Makes a request to the chat API with debug_raw=true
3. Displays the raw and processed outputs for comparison
"""
import os
import sys
import json
import logging
import httpx
import asyncio
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging to show DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ollama_debug_comparison.log")
    ]
)

# Create a logger for this script
logger = logging.getLogger("ollama_debug")

async def test_ollama_comparison(query: str, use_rag: bool = True):
    """
    Test the Ollama output comparison by making a request to the chat API
    with debug_raw=true and logging the results.
    
    Args:
        query: The query to send to the chat API
        use_rag: Whether to use RAG for the query
    """
    logger.info(f"Testing Ollama output comparison with query: {query}")
    
    # API endpoint
    url = "http://localhost:8000/api/chat/query"
    
    # Request payload
    payload = {
        "message": query,
        "use_rag": use_rag,
        "stream": False,
        "model_parameters": {
            "temperature": 0.1
        }
    }
    
    # Authentication credentials - using the test user
    auth = {
        "username": "cqhoward",
        "password": "Lasher2025"
    }
    
    # Add debug_raw=true to the URL
    params = {"debug_raw": "true"}
    
    try:
        # Make the request
        async with httpx.AsyncClient() as client:
            logger.info("Sending request to chat API...")
            
            # First, get a token
            token_url = "http://localhost:8000/api/auth/token"
            token_response = await client.post(
                token_url,
                data={
                    "username": auth["username"],
                    "password": auth["password"],
                    "grant_type": "password"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0
            )
            
            if token_response.status_code != 200:
                logger.error(f"Authentication failed: {token_response.text}")
                return None
                
            # Extract the token
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error("No access token in response")
                return None
                
            # Make the actual request with the token
            logger.info("Authentication successful, making query request...")
            response = await client.post(
                url,
                json=payload,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=60.0
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                logger.info("Request successful!")
                
                # Parse the response
                data = response.json()
                
                # Get the raw and processed outputs
                raw_output = data.get("raw_ollama_output", "No raw output available")
                processed_output = data.get("message", "No processed output available")
                
                # Log the outputs for comparison
                logger.info("=" * 80)
                logger.info("RAW OLLAMA OUTPUT:")
                logger.info("=" * 80)
                logger.info(raw_output)
                
                logger.info("\n" + "=" * 80)
                logger.info("PROCESSED OUTPUT:")
                logger.info("=" * 80)
                logger.info(processed_output)
                
                # Save the outputs to files for easier comparison
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                with open(f"raw_output_{timestamp}.txt", "w") as f:
                    f.write(raw_output)
                
                with open(f"processed_output_{timestamp}.txt", "w") as f:
                    f.write(processed_output)
                
                logger.info(f"Outputs saved to raw_output_{timestamp}.txt and processed_output_{timestamp}.txt")
                
                # Return the outputs
                return {
                    "raw_output": raw_output,
                    "processed_output": processed_output
                }
            else:
                logger.error(f"Request failed with status code {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return None

async def main():
    """
    Main function to run the test
    """
    # Example queries to test
    queries = [
        "Write a Python function to calculate the factorial of a number",
        "Explain the difference between REST and GraphQL"
    ]
    
    # Test each query
    for query in queries:
        await test_ollama_comparison(query)
        logger.info("\n\n")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())