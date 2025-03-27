#!/usr/bin/env python3
"""
Test script for JWT authentication in Metis RAG

This script tests the JWT authentication system by:
1. Registering a new user (if needed)
2. Logging in to get access and refresh tokens
3. Using the access token to access a protected endpoint
4. Refreshing the access token using the refresh token
5. Using the new access token to access a protected endpoint

Usage:
    python run_authentication_test.py
"""

import requests
import json
import time
import sys
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"
USERNAME = "testuser"
PASSWORD = "Test@password123"
EMAIL = "testuser@example.com"

# API endpoints
AUTH_REGISTER_URL = urljoin(BASE_URL, f"{API_PREFIX}/auth/register")
AUTH_TOKEN_URL = urljoin(BASE_URL, f"{API_PREFIX}/auth/token")
AUTH_REFRESH_URL = urljoin(BASE_URL, f"{API_PREFIX}/auth/refresh")
ME_URL = urljoin(BASE_URL, f"{API_PREFIX}/auth/me")

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_json(data):
    """Print JSON data in a formatted way"""
    print(json.dumps(data, indent=4))

def register_user():
    """Register a new user"""
    print_header("REGISTERING NEW USER")
    
    user_data = {
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": "Test User"
    }
    
    print(f"Registering user: {USERNAME}")
    try:
        response = requests.post(AUTH_REGISTER_URL, json=user_data)
        
        if response.status_code == 200:
            print("User registered successfully!")
            print_json(response.json())
            return True
        else:
            print(f"Registration failed with status code: {response.status_code}")
            print_json(response.json())
            
            # If user already exists, that's fine
            if response.status_code == 400 and "already exists" in response.text:
                print("User already exists, continuing with login test.")
                return True
            
            return False
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        return False

def login_user():
    """Login and get access token"""
    print_header("LOGGING IN")
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    print(f"Logging in as: {USERNAME}")
    try:
        response = requests.post(
            AUTH_TOKEN_URL, 
            data=login_data,  # Note: using form data, not JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("Login successful!")
            print("Token data:")
            print_json(token_data)
            return token_data
        else:
            print(f"Login failed with status code: {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return None

def get_user_profile(access_token):
    """Get user profile using access token"""
    print_header("ACCESSING PROTECTED ENDPOINT")
    
    print("Getting user profile with access token")
    try:
        response = requests.get(
            ME_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print("User profile retrieved successfully!")
            print_json(user_data)
            return True
        else:
            print(f"Profile retrieval failed with status code: {response.status_code}")
            print_json(response.json())
            return False
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return False

def refresh_token(refresh_token):
    """Refresh access token using refresh token"""
    print_header("REFRESHING ACCESS TOKEN")
    
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    print("Refreshing access token")
    try:
        response = requests.post(
            AUTH_REFRESH_URL,
            json=refresh_data
        )
        
        if response.status_code == 200:
            new_token_data = response.json()
            print("Token refreshed successfully!")
            print("New token data:")
            print_json(new_token_data)
            return new_token_data
        else:
            print(f"Token refresh failed with status code: {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print(f"Error refreshing token: {str(e)}")
        return None

def main():
    """Main function to run the authentication test"""
    print_header("JWT AUTHENTICATION TEST")
    
    # Step 1: Register a new user (if needed)
    if not register_user():
        print("Registration failed, exiting.")
        sys.exit(1)
    
    # Step 2: Login to get tokens
    token_data = login_user()
    if not token_data:
        print("Login failed, exiting.")
        sys.exit(1)
    
    access_token = token_data["access_token"]
    refresh_token_str = token_data["refresh_token"]
    
    # Step 3: Access protected endpoint with access token
    if not get_user_profile(access_token):
        print("Failed to access protected endpoint, exiting.")
        sys.exit(1)
    
    # Optional: Wait a moment to simulate time passing
    print("\nWaiting for 2 seconds...\n")
    time.sleep(2)
    
    # Step 4: Refresh the token
    new_token_data = refresh_token(refresh_token_str)
    if not new_token_data:
        print("Token refresh failed, exiting.")
        sys.exit(1)
    
    new_access_token = new_token_data["access_token"]
    
    # Step 5: Access protected endpoint with new access token
    print_header("ACCESSING PROTECTED ENDPOINT WITH NEW TOKEN")
    if not get_user_profile(new_access_token):
        print("Failed to access protected endpoint with new token, exiting.")
        sys.exit(1)
    
    print_header("TEST COMPLETED SUCCESSFULLY")
    print("The JWT authentication system is working correctly!")

if __name__ == "__main__":
    main()