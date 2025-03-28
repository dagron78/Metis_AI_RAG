#!/usr/bin/env python3
"""
Test script to verify authentication with the Metis RAG API.
This script tests both direct API calls and the TestClient approach.
"""

import os
import sys
import logging
import requests
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_authentication")

# Import app and authentication helper
sys.path.append(".")  # Add current directory to path
from app.main import app
from tests.utils.test_auth_helper import (
    configure_test_client,
    verify_authentication,
    authenticate_with_session
)

def test_direct_api_authentication():
    """Test authentication using direct API calls with requests"""
    logger.info("Testing direct API authentication...")
    
    base_url = "http://localhost:8000"
    
    # Test with valid credentials
    session, token = authenticate_with_session(base_url, "testuser", "testpassword")
    
    if token:
        logger.info("✓ Authentication successful with valid credentials")
        
        # Test accessing a protected endpoint
        response = session.get(f"{base_url}/api/documents")
        
        if response.status_code == 200:
            logger.info("✓ Successfully accessed protected endpoint")
            return True
        else:
            logger.error(f"✗ Failed to access protected endpoint: {response.status_code} - {response.text}")
    else:
        logger.error("✗ Authentication failed with valid credentials")
    
    # Test with invalid credentials
    session, token = authenticate_with_session(base_url, "testuser", "wrongpassword")
    
    if token:
        logger.error("✗ Authentication succeeded with invalid credentials (unexpected)")
    else:
        logger.info("✓ Authentication correctly failed with invalid credentials")
    
    return False

def test_testclient_authentication():
    """Test authentication using TestClient"""
    logger.info("Testing TestClient authentication...")
    
    # Configure TestClient with valid credentials
    client = configure_test_client(app, "testuser", "testpassword")
    
    # Verify authentication
    if verify_authentication(client):
        logger.info("✓ TestClient authentication successful with valid credentials")
        
        # Test accessing a protected endpoint
        response = client.get("/api/documents")
        
        if response.status_code == 200:
            logger.info("✓ TestClient successfully accessed protected endpoint")
            return True
        else:
            logger.error(f"✗ TestClient failed to access protected endpoint: {response.status_code} - {response.text}")
    else:
        logger.error("✗ TestClient authentication failed with valid credentials")
    
    # Configure TestClient with invalid credentials
    client = configure_test_client(app, "testuser", "wrongpassword")
    
    # Verify authentication (should fail)
    if verify_authentication(client):
        logger.error("✗ TestClient authentication succeeded with invalid credentials (unexpected)")
    else:
        logger.info("✓ TestClient authentication correctly failed with invalid credentials")
    
    return False

def main():
    """Main function"""
    logger.info("Starting authentication tests...")
    
    # Test direct API authentication
    direct_api_success = test_direct_api_authentication()
    
    # Test TestClient authentication
    testclient_success = test_testclient_authentication()
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("Authentication Test Summary")
    logger.info("="*80)
    logger.info(f"Direct API Authentication: {'✓ Success' if direct_api_success else '✗ Failed'}")
    logger.info(f"TestClient Authentication: {'✓ Success' if testclient_success else '✗ Failed'}")
    logger.info("="*80)
    
    # Return success if either test passed
    return 0 if (direct_api_success or testclient_success) else 1

if __name__ == "__main__":
    sys.exit(main())