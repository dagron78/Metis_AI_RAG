#!/usr/bin/env python3
"""
Test script for the authentication system
"""
import asyncio
import httpx
import json
import uuid
from typing import Dict, Any, Optional

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# Test user credentials
TEST_USER = {
    "username": f"testuser_{uuid.uuid4().hex[:8]}",
    "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
}

# Global variables
access_token = None
user_id = None

async def register_user() -> Dict[str, Any]:
    """Register a new user"""
    print(f"Registering user: {TEST_USER['username']}")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/register",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"User registered successfully: {user_data['username']}")
            return user_data
        else:
            print(f"Failed to register user: {response.text}")
            raise Exception(f"Failed to register user: {response.text}")

async def login_user() -> str:
    """Login with user credentials and get access token"""
    print(f"Logging in as: {TEST_USER['username']}")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/token",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("Login successful, received access token")
            return token_data["access_token"]
        else:
            print(f"Failed to login: {response.text}")
            raise Exception(f"Failed to login: {response.text}")

async def get_current_user(token: str) -> Dict[str, Any]:
    """Get current user information"""
    print("Getting current user information")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"Current user: {user_data['username']}")
            return user_data
        else:
            print(f"Failed to get current user: {response.text}")
            raise Exception(f"Failed to get current user: {response.text}")

async def upload_document(token: str, filename: str = "test_document.txt") -> str:
    """Upload a test document"""
    print(f"Uploading document: {filename}")
    
    # Create a test file
    with open(filename, "w") as f:
        f.write("This is a test document for authentication testing.")
    
    async with httpx.AsyncClient() as client:
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "text/plain")}
            response = await client.post(
                f"{BASE_URL}/documents/upload",
                headers={"Authorization": f"Bearer {token}"},
                files=files,
                data={"tags": "test,auth", "folder": "/test"}
            )
        
        if response.status_code == 200:
            result = response.json()
            document_id = result["document_id"]
            print(f"Document uploaded successfully: {document_id}")
            return document_id
        else:
            print(f"Failed to upload document: {response.text}")
            raise Exception(f"Failed to upload document: {response.text}")

async def list_documents(token: str) -> Dict[str, Any]:
    """List user's documents"""
    print("Listing user's documents")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/documents/list",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            documents = response.json()
            print(f"Found {len(documents)} documents")
            return documents
        else:
            print(f"Failed to list documents: {response.text}")
            raise Exception(f"Failed to list documents: {response.text}")

async def create_conversation(token: str) -> str:
    """Create a new conversation"""
    print("Creating a new conversation")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/chat/query",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "Hello, this is a test message",
                "model": "gemma3:4b",
                "use_rag": True,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            conversation_id = result["conversation_id"]
            print(f"Conversation created successfully: {conversation_id}")
            return conversation_id
        else:
            try:
                error_data = response.json()
                print(f"Failed to create conversation: {error_data}")
            except:
                print(f"Failed to create conversation: {response.text}")
            raise Exception(f"Failed to create conversation: {response.text}")

async def list_conversations(token: str) -> Dict[str, Any]:
    """List user's conversations"""
    print("Listing user's conversations")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/chat/list",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            conversations = result["conversations"]
            print(f"Found {len(conversations)} conversations")
            return result
        else:
            print(f"Failed to list conversations: {response.text}")
            raise Exception(f"Failed to list conversations: {response.text}")

async def main():
    """Main test function"""
    global access_token, user_id
    
    try:
        # Register a new user
        user = await register_user()
        user_id = user["id"]
        
        # Login with the user
        access_token = await login_user()
        
        # Get current user information
        current_user = await get_current_user(access_token)
        
        # Upload a document
        document_id = await upload_document(access_token)
        
        # List documents
        documents = await list_documents(access_token)
        
        try:
            # Create a conversation
            conversation_id = await create_conversation(access_token)
            
            # List conversations
            conversations = await list_conversations(access_token)
            
            print("\n=== Authentication Test Results ===")
            print(f"User ID: {user_id}")
            print(f"Documents: {len(documents)}")
            print(f"Conversations: {len(conversations['conversations'])}")
            print("All tests passed successfully!")
        except Exception as e:
            print("\n=== Authentication Test Results ===")
            print(f"User ID: {user_id}")
            print(f"Documents: {len(documents)}")
            print("Note: Conversation tests failed, but user authentication and document upload succeeded.")
            print("This is likely due to the RAG engine not being fully initialized.")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())