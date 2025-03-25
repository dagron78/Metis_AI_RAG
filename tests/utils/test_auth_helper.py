#!/usr/bin/env python3
"""
Authentication helper for Metis RAG end-to-end tests.
This module provides functions to authenticate with the Metis RAG API
and maintain session state between requests.

NOTE: This approach may encounter issues with event loops and async code.
For a more reliable approach, see scripts/test_api_directly.py and
tests/authentication_setup_guide.md.
"""

import os
import json
import logging
import requests
from typing import Dict, Optional, Tuple
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_auth_helper")

def authenticate_with_session(base_url: str, username: str, password: str) -> Tuple[requests.Session, Optional[str]]:
    """
    Authenticate with the API using a requests.Session to maintain cookies and state.
    
    Args:
        base_url: Base URL of the API (e.g., http://localhost:8000)
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        Tuple of (session, token) where session is a requests.Session object and token is the access token
    """
    session = requests.Session()
    
    # Try to authenticate
    try:
        logger.info(f"Authenticating with username: {username}")
        
        # Use form data for token endpoint
        login_response = session.post(
            f"{base_url}/api/auth/token",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            }
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                logger.info("Authentication successful")
                
                # Set the token in the session headers for subsequent requests
                session.headers.update({"Authorization": f"Bearer {access_token}"})
                
                # Also set the token in a cookie
                session.cookies.set("auth_token", access_token)
                
                return session, access_token
            else:
                logger.error("No access token in response")
        else:
            logger.error(f"Authentication failed: {login_response.status_code} - {login_response.text}")
            
            # Try to register a new test user if login fails
            register_response = session.post(
                f"{base_url}/api/auth/register",
                json={
                    "username": f"{username}_new",
                    "email": f"{username}_new@example.com",
                    "password": password,
                    "full_name": "Test User",
                    "is_active": True,
                    "is_admin": False
                }
            )
            
            if register_response.status_code == 200:
                logger.info(f"Registered new test user: {username}_new")
                
                # Try to login with the new user
                login_response = session.post(
                    f"{base_url}/api/auth/token",
                    data={
                        "username": f"{username}_new",
                        "password": password,
                        "grant_type": "password"
                    }
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    access_token = token_data.get("access_token")
                    
                    if access_token:
                        logger.info("Authentication successful with new user")
                        
                        # Set the token in the session headers for subsequent requests
                        session.headers.update({"Authorization": f"Bearer {access_token}"})
                        
                        # Also set the token in a cookie
                        session.cookies.set("auth_token", access_token)
                        
                        return session, access_token
                    else:
                        logger.error("No access token in response for new user")
                else:
                    logger.error(f"Login with new user failed: {login_response.status_code} - {login_response.text}")
            else:
                logger.error(f"Registration failed: {register_response.status_code} - {register_response.text}")
    
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
    
    return session, None

def configure_test_client(app, username: str = "testuser", password: str = "testpassword") -> TestClient:
    """
    Configure a FastAPI TestClient with authentication.
    
    Args:
        app: FastAPI application
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        Configured TestClient
    """
    # Create a TestClient that will maintain cookies between requests
    client = TestClient(app)
    
    # Try to authenticate
    try:
        logger.info(f"Authenticating TestClient with username: {username}")
        
        # Use form data for token endpoint
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            }
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                logger.info("TestClient authentication successful")
                
                # Set the token in the client's headers for subsequent requests
                client.headers["Authorization"] = f"Bearer {access_token}"
                
                # Save cookies to a file for debugging
                with open("cookies.txt", "w") as f:
                    f.write(str(client.cookies))
                
                return client
            else:
                logger.error("No access token in TestClient response")
        else:
            logger.error(f"TestClient authentication failed: {login_response.status_code} - {login_response.text}")
            
            # Try to register a new test user if login fails
            register_response = client.post(
                "/api/auth/register",
                json={
                    "username": f"{username}_new",
                    "email": f"{username}_new@example.com",
                    "password": password,
                    "full_name": "Test User",
                    "is_active": True,
                    "is_admin": False
                }
            )
            
            if register_response.status_code == 200:
                logger.info(f"Registered new test user: {username}_new")
                
                # Try to login with the new user
                login_response = client.post(
                    "/api/auth/token",
                    data={
                        "username": f"{username}_new",
                        "password": password,
                        "grant_type": "password"
                    }
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    access_token = token_data.get("access_token")
                    
                    if access_token:
                        logger.info("TestClient authentication successful with new user")
                        
                        # Set the token in the client's headers for subsequent requests
                        client.headers["Authorization"] = f"Bearer {access_token}"
                        
                        return client
                    else:
                        logger.error("No access token in TestClient response for new user")
                else:
                    logger.error(f"TestClient login with new user failed: {login_response.status_code} - {login_response.text}")
            else:
                logger.error(f"TestClient registration failed: {register_response.status_code} - {register_response.text}")
    
    except Exception as e:
        logger.error(f"TestClient authentication error: {str(e)}")
    
    return client

def verify_authentication(client: TestClient) -> bool:
    """
    Verify that the client is authenticated by making a request to a protected endpoint.
    
    Args:
        client: TestClient to verify
        
    Returns:
        True if authenticated, False otherwise
    """
    try:
        # Try to access a protected endpoint
        response = client.get("/api/auth/me")
        
        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"Authenticated as user: {user_data.get('username')}")
            return True
        else:
            logger.error(f"Authentication verification failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Authentication verification error: {str(e)}")
        return False

if __name__ == "__main__":
    # Example usage
    from app.main import app
    
    # Configure the test client
    client = configure_test_client(app)
    
    # Verify authentication
    is_authenticated = verify_authentication(client)
    print(f"Is authenticated: {is_authenticated}")