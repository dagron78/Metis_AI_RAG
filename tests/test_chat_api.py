import requests
import json

# Test the chat API endpoint
url = "http://localhost:8000/api/chat/query"
payload = {
    "message": "Hello, how are you?",
    "use_rag": True,
    "stream": False
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")