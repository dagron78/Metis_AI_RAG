#!/usr/bin/env python3
"""
Authentication System Test Script

This script tests the various authentication endpoints of the Metis RAG application.
It covers user registration, login, password reset, and admin functionality.
"""

import argparse
import json
import sys
import time
import uuid
from typing import Dict, Tuple, Optional, List, Any

import requests

# Default settings
DEFAULT_BASE_URL = "http://localhost:8000/api"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_TEST_USERNAME = f"testuser_{uuid.uuid4().hex[:8]}"
DEFAULT_TEST_EMAIL = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
DEFAULT_TEST_PASSWORD = "password123"


class AuthTester:
    """Test the authentication system of Metis RAG"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.test_user_id = None
        self.reset_token = None

    def register_user(self, username: str, email: str, password: str, full_name: Optional[str] = None) -> Tuple[Dict, int]:
        """Register a new user"""
        print(f"\n[*] Registering user: {username}")
        
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        
        if full_name:
            data["full_name"] = full_name
            
        response = requests.post(
            f"{self.base_url}/auth/register",
            json=data
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"User created: {result.get('username')} (ID: {result.get('id')})")
            self.test_user_id = result.get('id')
        else:
            print(f"Error: {result}")
            
        return result, response.status_code

    def login(self, username: str, password: str) -> Tuple[Dict, int]:
        """Login and get access token"""
        print(f"\n[*] Logging in as: {username}")
        
        response = requests.post(
            f"{self.base_url}/auth/token",
            data={
                "username": username,
                "password": password
            }
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200 and "access_token" in result:
            print(f"Login successful. Token received.")
            if username == DEFAULT_ADMIN_USERNAME:
                self.admin_token = result["access_token"]
            else:
                self.user_token = result["access_token"]
        else:
            print(f"Login failed: {result}")
            
        return result, response.status_code

    def get_current_user(self, token: str) -> Tuple[Dict, int]:
        """Get current user information"""
        print("\n[*] Getting current user info")
        
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"User: {result.get('username')} (ID: {result.get('id')})")
        else:
            print(f"Error: {result}")
            
        return result, response.status_code

    def request_password_reset(self, email: str) -> Tuple[Dict, int]:
        """Request a password reset"""
        print(f"\n[*] Requesting password reset for: {email}")
        
        response = requests.post(
            f"{self.base_url}/password-reset/request-reset",
            json={"email": email}
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        print(f"Response: {result}")
        print("Note: Check server logs for the reset token")
            
        return result, response.status_code

    def reset_password(self, token: str, new_password: str) -> Tuple[Dict, int]:
        """Reset password using token"""
        print(f"\n[*] Resetting password with token")
        
        response = requests.post(
            f"{self.base_url}/password-reset/reset-password",
            json={
                "token": token,
                "password": new_password,
                "confirm_password": new_password
            }
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        print(f"Response: {result}")
            
        return result, response.status_code

    def list_users(self, admin_token: str, search: Optional[str] = None) -> Tuple[List[Dict], int]:
        """List all users (admin only)"""
        print("\n[*] Listing all users")
        
        url = f"{self.base_url}/admin/users"
        if search:
            url += f"?search={search}"
            
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Found {len(result)} users")
            for user in result:
                print(f"  - {user.get('username')} ({user.get('email')})")
        else:
            print(f"Error: {result}")
            
        return result, response.status_code

    def get_user(self, admin_token: str, user_id: str) -> Tuple[Dict, int]:
        """Get a specific user (admin only)"""
        print(f"\n[*] Getting user with ID: {user_id}")
        
        response = requests.get(
            f"{self.base_url}/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"User: {result.get('username')} (Email: {result.get('email')})")
        else:
            print(f"Error: {result}")
            
        return result, response.status_code

    def create_user(self, admin_token: str, user_data: Dict[str, Any]) -> Tuple[Dict, int]:
        """Create a new user (admin only)"""
        print(f"\n[*] Creating new user: {user_data.get('username')}")
        
        response = requests.post(
            f"{self.base_url}/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=user_data
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"User created: {result.get('username')} (ID: {result.get('id')})")
        else:
            print(f"Error: {result}")
            
        return result, response.status_code

    def update_user(self, admin_token: str, user_id: str, user_data: Dict[str, Any]) -> Tuple[Dict, int]:
        """Update a user (admin only)"""
        print(f"\n[*] Updating user with ID: {user_id}")
        
        response = requests.put(
            f"{self.base_url}/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=user_data
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"User updated: {result.get('username')} (Email: {result.get('email')})")
        else:
            print(f"Error: {result}")
            
        return result, response.status_code

    def delete_user(self, admin_token: str, user_id: str) -> Tuple[Dict, int]:
        """Delete a user (admin only)"""
        print(f"\n[*] Deleting user with ID: {user_id}")
        
        response = requests.delete(
            f"{self.base_url}/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON response", "text": response.text}
            
        print(f"Status: {response.status_code}")
        print(f"Response: {result}")
            
        return result, response.status_code

    def run_basic_tests(self):
        """Run basic authentication tests"""
        print("\n=== Running Basic Authentication Tests ===\n")
        
        # 1. Register a test user
        self.register_user(
            DEFAULT_TEST_USERNAME, 
            DEFAULT_TEST_EMAIL, 
            DEFAULT_TEST_PASSWORD, 
            "Test User"
        )
        
        # 2. Login as the test user
        self.login(DEFAULT_TEST_USERNAME, DEFAULT_TEST_PASSWORD)
        
        # 3. Get current user info
        if self.user_token:
            self.get_current_user(self.user_token)
        
        # 4. Request password reset
        self.request_password_reset(DEFAULT_TEST_EMAIL)
        
        print("\n=== Basic Authentication Tests Completed ===")

    def run_admin_tests(self):
        """Run admin functionality tests"""
        print("\n=== Running Admin Functionality Tests ===\n")
        
        # 1. Login as admin
        self.login(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
        
        if not self.admin_token:
            print("Admin login failed. Skipping admin tests.")
            return
        
        # 2. List all users
        self.list_users(self.admin_token)
        
        # 3. Get specific user
        if self.test_user_id:
            self.get_user(self.admin_token, self.test_user_id)
        
        # 4. Create a new user
        new_user_data = {
            "username": f"adminuser_{uuid.uuid4().hex[:8]}",
            "email": f"adminuser_{uuid.uuid4().hex[:8]}@example.com",
            "password": "adminpass123",
            "full_name": "Admin Created User",
            "is_active": True,
            "is_admin": False
        }
        
        user_result, _ = self.create_user(self.admin_token, new_user_data)
        created_user_id = user_result.get('id')
        
        # 5. Update the user
        if created_user_id:
            update_data = {
                "full_name": "Updated User Name",
                "is_admin": True
            }
            self.update_user(self.admin_token, created_user_id, update_data)
        
        # 6. Delete the user
        if created_user_id:
            self.delete_user(self.admin_token, created_user_id)
        
        print("\n=== Admin Functionality Tests Completed ===")

    def run_all_tests(self):
        """Run all authentication tests"""
        self.run_basic_tests()
        self.run_admin_tests()
        
        print("\n=== All Authentication Tests Completed ===")


def main():
    """Main function"""
    # Declare globals at the beginning of the function
    global DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
    global DEFAULT_TEST_USERNAME, DEFAULT_TEST_EMAIL, DEFAULT_TEST_PASSWORD
    
    parser = argparse.ArgumentParser(description='Test Metis RAG Authentication System')
    parser.add_argument('--url', default=DEFAULT_BASE_URL, help='Base API URL')
    parser.add_argument('--admin-user', default=DEFAULT_ADMIN_USERNAME, help='Admin username')
    parser.add_argument('--admin-pass', default=DEFAULT_ADMIN_PASSWORD, help='Admin password')
    parser.add_argument('--test-user', default=DEFAULT_TEST_USERNAME, help='Test username')
    parser.add_argument('--test-email', default=DEFAULT_TEST_EMAIL, help='Test email')
    parser.add_argument('--test-pass', default=DEFAULT_TEST_PASSWORD, help='Test password')
    parser.add_argument('--basic-only', action='store_true', help='Run only basic tests')
    parser.add_argument('--admin-only', action='store_true', help='Run only admin tests')
    
    args = parser.parse_args()
    
    tester = AuthTester(args.url)
    
    # Override defaults if provided
    
    DEFAULT_ADMIN_USERNAME = args.admin_user
    DEFAULT_ADMIN_PASSWORD = args.admin_pass
    DEFAULT_TEST_USERNAME = args.test_user
    DEFAULT_TEST_EMAIL = args.test_email
    DEFAULT_TEST_PASSWORD = args.test_pass
    
    try:
        if args.basic_only:
            tester.run_basic_tests()
        elif args.admin_only:
            tester.run_admin_tests()
        else:
            tester.run_all_tests()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()