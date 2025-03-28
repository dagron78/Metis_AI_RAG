#!/usr/bin/env python3
"""
Simple authentication test for Metis RAG.
This script tests authentication using direct API calls without TestClient.
"""

import os
import sys
import logging
import requests
import json
from typing import Dict, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("simple_auth_test")

def authenticate_with_api(base_url: str, username: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Authenticate with the API using direct requests.
    
    Args:
        base_url: Base URL of the API (e.g., http://localhost:8000)
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        Tuple of (success, token) where success is a boolean and token is the access token if successful
    """
    try:
        logger.info(f"Authenticating with username: {username}")
        
        # Use form data for token endpoint
        login_response = requests.post(
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
                logger.info("✓ Authentication successful")
                return True, access_token
            else:
                logger.error("✗ No access token in response")
                return False, None
        else:
            logger.error(f"✗ Authentication failed: {login_response.status_code} - {login_response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"✗ Authentication error: {str(e)}")
        return False, None

def register_test_user(base_url: str, username: str, password: str) -> bool:
    """
    Register a new test user.
    
    Args:
        base_url: Base URL of the API
        username: Username for the new user
        password: Password for the new user
        
    Returns:
        True if registration was successful, False otherwise
    """
    try:
        logger.info(f"Registering new test user: {username}")
        
        register_response = requests.post(
            f"{base_url}/api/auth/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": password,
                "full_name": "Test User",
                "is_active": True,
                "is_admin": False
            }
        )
        
        if register_response.status_code == 200:
            logger.info(f"✓ User {username} registered successfully")
            return True
        else:
            logger.error(f"✗ Registration failed: {register_response.status_code} - {register_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Registration error: {str(e)}")
        return False

def test_protected_endpoint(base_url: str, token: str) -> bool:
    """
    Test accessing a protected endpoint.
    
    Args:
        base_url: Base URL of the API
        token: Access token
        
    Returns:
        True if access was successful, False otherwise
    """
    try:
        logger.info("Testing access to protected endpoint")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try different protected endpoints
        endpoints = [
            "/api/documents",
            "/api/auth/me",
            "/api/system/status"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✓ Successfully accessed {endpoint}")
                return True
            else:
                logger.warning(f"✗ Failed to access {endpoint}: {response.status_code} - {response.text}")
        
        logger.error("✗ Could not access any protected endpoint")
        return False
            
    except Exception as e:
        logger.error(f"✗ Error accessing protected endpoint: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Starting simple authentication test...")
    
    base_url = "http://localhost:8000"
    
    # Test with existing user
    success, token = authenticate_with_api(base_url, "testuser", "testpassword")
    
    if not success:
        logger.warning("Authentication with existing user failed, trying with a new user")
        
        # Try with a unique username
        import uuid
        test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        test_password = "testpassword"
        
        # Register new user
        if register_test_user(base_url, test_username, test_password):
            # Try to authenticate with the new user
            success, token = authenticate_with_api(base_url, test_username, test_password)
    
    if success and token:
        # Test accessing a protected endpoint
        if test_protected_endpoint(base_url, token):
            logger.info("✓ Authentication test passed successfully!")
            return 0
        else:
            logger.error("✗ Could not access protected endpoints")
            return 1
    else:
        logger.error("✗ Authentication test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())