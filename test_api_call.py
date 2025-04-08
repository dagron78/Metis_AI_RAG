import requests
import json
import uuid

def test_query():
    """Test a simple query to check if our fixes work"""
    url = "http://localhost:8000/api/chat/query"
    
    # Generate a random conversation ID
    conversation_id = str(uuid.uuid4())
    
    # Create a test query
    data = {
        "query": "Tell me a brief fictional story about a robot",
        "conversation_id": conversation_id,
        "use_rag": False,
        "stream": False
    }
    
    # Send the request
    response = requests.post(url, json=data)
    
    # Print the response
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Query: {result.get('query')}")
        print(f"Answer length: {len(result.get('answer', ''))}")
        print(f"First 100 chars of answer: {result.get('answer', '')[:100]}...")
        print(f"Sources: {len(result.get('sources', []))}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

if __name__ == "__main__":
    print("Testing query...")
    success = test_query()
    print(f"Test {'succeeded' if success else 'failed'}")