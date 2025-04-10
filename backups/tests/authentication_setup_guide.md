# Metis RAG Authentication Testing Guide

This guide provides solutions for authentication issues when testing the Metis RAG system.

## Authentication Issues Identified

1. **TestClient Authentication Issues**: The FastAPI TestClient has limitations when working with async code and authentication, particularly with event loops.

2. **Database Connection Issues**: When using TestClient with async database connections, event loop conflicts can occur.

3. **Token Handling**: The TestClient doesn't maintain cookies/session state properly between requests.

## Solutions

### Solution 1: Direct API Testing

The most reliable approach is to use direct API calls with the `requests` library instead of TestClient. This approach:

- Avoids event loop conflicts
- Properly maintains authentication state
- Works with the actual running API

We've implemented this solution in `scripts/test_api_directly.py`, which successfully:
- Authenticates with the API
- Uploads and processes documents
- Executes queries against the RAG system
- Retrieves meaningful responses with citations

### Solution 2: TestClient with Session Fixation

If you need to use TestClient for integration with pytest, you can:

1. Use direct requests to obtain an authentication token
2. Manually set the token in the TestClient headers
3. Verify authentication before proceeding with tests

```python
# Example of TestClient with manual token setting
import requests
from fastapi.testclient import TestClient
from app.main import app

# Get token using direct requests
def get_auth_token():
    response = requests.post(
        "http://localhost:8000/api/auth/token",
        data={
            "username": "testuser",
            "password": "testpassword",
            "grant_type": "password"
        }
    )
    return response.json().get("access_token")

# Configure TestClient with token
def get_authenticated_client():
    client = TestClient(app)
    token = get_auth_token()
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

### Solution 3: Separate Authentication Service

For more complex testing scenarios:

1. Create a separate authentication service that runs independently
2. Use this service to generate tokens for testing
3. Configure your tests to use these pre-generated tokens

## Test User Management

For reliable testing:

1. **Create dedicated test users** with known credentials
2. Use a **unique test user for each test run** to avoid conflicts
3. Clean up test users after testing if possible

## API Endpoint Verification

Our testing confirmed the following endpoints work correctly:

- `/api/auth/register` - User registration
- `/api/auth/token` - Token acquisition
- `/api/auth/me` - User verification
- `/api/documents/upload` - Document upload
- `/api/documents/process` - Document processing
- `/api/chat/query` - RAG queries

Some endpoints returned 500 errors:
- `/api/documents/{id}` - Document info retrieval
- `/api/documents/{id}` - Document deletion

These errors suggest potential bugs in the document management endpoints, but they don't affect the core RAG functionality.

## Query Results

Our testing confirmed that the RAG system correctly:
- Retrieves relevant information from uploaded documents
- Provides accurate answers to queries
- Includes citations to source documents

Example query: "What is the battery life of the motion sensor?"
Response: "Based on the provided documents, I found information about the motion sensor's battery life. According to [1], the Motion Sensor (Device ID: SH-MS100) has a Battery Life of 2 years."

## Conclusion

The Metis RAG system's core functionality (authentication, document processing, and querying) works correctly. The authentication issues in the test suite are related to the testing approach rather than the system itself.

By using direct API calls or properly configuring TestClient, you can successfully test the entire system end-to-end.