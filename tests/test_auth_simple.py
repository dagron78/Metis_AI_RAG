#!/usr/bin/env python3
"""
Simple script to test authentication with a known user.
"""

import asyncio
import logging
import sys
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_auth_simple")

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# Test user credentials
TEST_USER = {
    "username": "testuser123",
    "password": "testpassword123"
}

def test_authentication():
    """Test authentication using direct API calls"""
    logger.info(f"Testing authentication with username: {TEST_USER['username']}")
    
    # Try to get a token
    try:
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info("Authentication successful!")
            logger.info(f"Access token: {token_data['access_token'][:20]}...")
            
            # Test accessing a protected endpoint
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Try to get user info
            me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            if me_response.status_code == 200:
                user_data = me_response.json()
                logger.info(f"Successfully accessed protected endpoint: /auth/me")
                logger.info(f"User data: {json.dumps(user_data, indent=2)}")
            else:
                logger.error(f"Failed to access protected endpoint: {me_response.status_code} - {me_response.text}")
            
            # Try to upload a document
            with open("test_document.txt", "w") as f:
                f.write("This is a test document for authentication testing.")
            
            with open("test_document.txt", "rb") as f:
                files = {"file": ("test_document.txt", f, "text/plain")}
                upload_response = requests.post(
                    f"{BASE_URL}/documents/upload",
                    headers=headers,
                    files=files,
                    data={"tags": "test,auth", "folder": "/test"}
                )
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                logger.info(f"Document uploaded successfully: {result['document_id']}")
            else:
                logger.error(f"Failed to upload document: {upload_response.status_code} - {upload_response.text}")
            
            return True
        else:
            logger.error(f"Authentication failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error during authentication test: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Starting authentication test...")
    
    # Test authentication
    success = test_authentication()
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("Authentication Test Summary")
    logger.info("="*80)
    logger.info(f"Authentication: {'✓ Success' if success else '✗ Failed'}")
    logger.info("="*80)
    
    # Return success code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())