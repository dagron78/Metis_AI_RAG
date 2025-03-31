#!/usr/bin/env python3
"""
End-to-end tests for authentication flows in Metis RAG
"""

import pytest
import uuid
import requests
import json
import time
from typing import Dict, Tuple, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_auth_flows")


class TestAuthFlows:
    """End-to-end tests for authentication flows"""
    
    # Base URL for API
    base_url = "http://localhost:8000"
    
    def setup_method(self):
        """Setup method for each test"""
        # Create unique test users for each test
        self.test_users = []
    
    def teardown_method(self):
        """Teardown method for each test"""
        # Clean up test users
        for user in self.test_users:
            if "token" in user:
                try:
                    # Delete user if possible
                    headers = {"Authorization": f"Bearer {user['token']}"}
                    requests.delete(f"{self.base_url}/api/auth/users/{user['id']}", headers=headers)
                except Exception as e:
                    logger.warning(f"Failed to delete test user: {e}")
    
    def create_test_user(self) -> Dict:
        """Create a test user"""
        unique_id = uuid.uuid4().hex[:8]
        user_data = {
            "username": f"testuser_{unique_id}",
            "email": f"testuser_{unique_id}@example.com",
            "password": "testpassword123",
            "full_name": f"Test User {unique_id}",
            "is_active": True,
            "is_admin": False
        }
        
        # Register user
        response = requests.post(
            f"{self.base_url}/api/auth/register",
            json=user_data
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create test user: {response.text}")
            raise Exception(f"Failed to create test user: {response.text}")
        
        # Add user to list for cleanup
        user_info = response.json()
        user_info["password"] = user_data["password"]
        self.test_users.append(user_info)
        
        return user_info
    
    def login_user(self, username: str, password: str) -> Tuple[Dict, requests.Session]:
        """Login a user and return token data and session"""
        session = requests.Session()
        
        # Login
        response = session.post(
            f"{self.base_url}/api/auth/token",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to login user: {response.text}")
            raise Exception(f"Failed to login user: {response.text}")
        
        token_data = response.json()
        
        # Set token in session headers
        session.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
        
        # Update user info with token
        for user in self.test_users:
            if user["username"] == username:
                user["token"] = token_data["access_token"]
                user["refresh_token"] = token_data["refresh_token"]
                break
        
        return token_data, session
    
    def refresh_token(self, refresh_token: str, session: Optional[requests.Session] = None) -> Dict:
        """Refresh an access token"""
        if session is None:
            session = requests.Session()
        
        # Refresh token
        response = session.post(
            f"{self.base_url}/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to refresh token: {response.text}")
            raise Exception(f"Failed to refresh token: {response.text}")
        
        token_data = response.json()
        
        # Update session headers with new token
        session.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
        
        return token_data
    
    def create_document(self, session: requests.Session, title: str, content: str, is_public: bool = False) -> Dict:
        """Create a document"""
        doc_data = {
            "title": title,
            "content": content,
            "is_public": is_public
        }
        
        response = session.post(
            f"{self.base_url}/api/documents",
            json=doc_data
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create document: {response.text}")
            raise Exception(f"Failed to create document: {response.text}")
        
        return response.json()
    
    def share_document(self, session: requests.Session, document_id: str, user_id: str, permission_level: str) -> Dict:
        """Share a document with another user"""
        share_data = {
            "document_id": document_id,
            "user_id": user_id,
            "permission_level": permission_level
        }
        
        response = session.post(
            f"{self.base_url}/api/documents/{document_id}/share",
            json=share_data
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to share document: {response.text}")
            raise Exception(f"Failed to share document: {response.text}")
        
        return response.json()
    
    def test_complete_user_journey(self):
        """Test a complete user journey: Register -> Login -> Access Protected Resource -> Refresh Token -> Access Again -> Logout"""
        logger.info("Starting complete user journey test")
        
        # Step 1: Register a new user
        logger.info("Step 1: Registering a new user")
        user_info = self.create_test_user()
        assert "id" in user_info
        assert "username" in user_info
        logger.info(f"✓ User registered: {user_info['username']}")
        
        # Step 2: Login with the new user
        logger.info("Step 2: Logging in with the new user")
        token_data, session = self.login_user(user_info["username"], user_info["password"])
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        logger.info("✓ Login successful")
        
        # Step 3: Access a protected resource (get user profile)
        logger.info("Step 3: Accessing a protected resource")
        profile_response = session.get(f"{self.base_url}/api/auth/me")
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["username"] == user_info["username"]
        logger.info("✓ Protected resource accessed successfully")
        
        # Step 4: Create a document (another protected resource)
        logger.info("Step 4: Creating a document")
        doc_title = f"Test Document {uuid.uuid4().hex[:8]}"
        doc_content = "This is a test document created during the authentication flow test."
        doc_data = self.create_document(session, doc_title, doc_content)
        assert "id" in doc_data
        assert doc_data["title"] == doc_title
        logger.info(f"✓ Document created: {doc_data['title']}")
        
        # Step 5: Wait for token to be closer to expiry (in a real test, we might use a shorter expiry time)
        logger.info("Step 5: Waiting briefly before refreshing token")
        time.sleep(2)  # Just a short wait for demonstration
        
        # Step 6: Refresh the token
        logger.info("Step 6: Refreshing the token")
        new_token_data = self.refresh_token(token_data["refresh_token"], session)
        assert "access_token" in new_token_data
        assert new_token_data["access_token"] != token_data["access_token"]
        logger.info("✓ Token refreshed successfully")
        
        # Step 7: Access a protected resource with the new token
        logger.info("Step 7: Accessing a protected resource with the new token")
        docs_response = session.get(f"{self.base_url}/api/documents")
        assert docs_response.status_code == 200
        docs_data = docs_response.json()
        assert isinstance(docs_data, list)
        assert any(doc["id"] == doc_data["id"] for doc in docs_data)
        logger.info("✓ Protected resource accessed with refreshed token")
        
        # Step 8: Simulate logout (just clear the session)
        logger.info("Step 8: Logging out")
        session.headers.pop("Authorization", None)
        
        # Step 9: Verify that protected resources are no longer accessible
        logger.info("Step 9: Verifying protected resources are no longer accessible")
        unauth_response = session.get(f"{self.base_url}/api/auth/me")
        assert unauth_response.status_code == 401
        logger.info("✓ Protected resource correctly denied after logout")
        
        logger.info("Complete user journey test passed successfully")
    
    def test_permission_scenario(self):
        """Test a complex permission scenario with multiple users"""
        logger.info("Starting permission scenario test")
        
        # Step 1: Create two users (owner and collaborator)
        logger.info("Step 1: Creating two test users")
        owner_info = self.create_test_user()
        collaborator_info = self.create_test_user()
        logger.info(f"✓ Created owner user: {owner_info['username']}")
        logger.info(f"✓ Created collaborator user: {collaborator_info['username']}")
        
        # Step 2: Login as owner
        logger.info("Step 2: Logging in as owner")
        owner_token_data, owner_session = self.login_user(owner_info["username"], owner_info["password"])
        logger.info("✓ Owner login successful")
        
        # Step 3: Login as collaborator
        logger.info("Step 3: Logging in as collaborator")
        collaborator_token_data, collaborator_session = self.login_user(collaborator_info["username"], collaborator_info["password"])
        logger.info("✓ Collaborator login successful")
        
        # Step 4: Owner creates a private document
        logger.info("Step 4: Owner creates a private document")
        private_doc_title = f"Private Document {uuid.uuid4().hex[:8]}"
        private_doc_content = "This is a private document that will be shared with the collaborator."
        private_doc = self.create_document(owner_session, private_doc_title, private_doc_content, is_public=False)
        logger.info(f"✓ Owner created private document: {private_doc['title']}")
        
        # Step 5: Owner creates a public document
        logger.info("Step 5: Owner creates a public document")
        public_doc_title = f"Public Document {uuid.uuid4().hex[:8]}"
        public_doc_content = "This is a public document that anyone can see."
        public_doc = self.create_document(owner_session, public_doc_title, public_doc_content, is_public=True)
        logger.info(f"✓ Owner created public document: {public_doc['title']}")
        
        # Step 6: Collaborator tries to access owner's private document (should fail)
        logger.info("Step 6: Collaborator tries to access owner's private document")
        private_doc_response = collaborator_session.get(f"{self.base_url}/api/documents/{private_doc['id']}")
        assert private_doc_response.status_code == 404
        logger.info("✓ Collaborator correctly denied access to private document")
        
        # Step 7: Collaborator accesses owner's public document (should succeed)
        logger.info("Step 7: Collaborator accesses owner's public document")
        public_doc_response = collaborator_session.get(f"{self.base_url}/api/documents/{public_doc['id']}")
        assert public_doc_response.status_code == 200
        public_doc_data = public_doc_response.json()
        assert public_doc_data["id"] == public_doc["id"]
        logger.info("✓ Collaborator successfully accessed public document")
        
        # Step 8: Owner shares private document with collaborator (read permission)
        logger.info("Step 8: Owner shares private document with collaborator (read permission)")
        share_result = self.share_document(owner_session, private_doc["id"], collaborator_info["id"], "read")
        logger.info("✓ Owner shared private document with collaborator")
        
        # Step 9: Collaborator accesses the now-shared private document (should succeed)
        logger.info("Step 9: Collaborator accesses the now-shared private document")
        shared_doc_response = collaborator_session.get(f"{self.base_url}/api/documents/{private_doc['id']}")
        assert shared_doc_response.status_code == 200
        shared_doc_data = shared_doc_response.json()
        assert shared_doc_data["id"] == private_doc["id"]
        logger.info("✓ Collaborator successfully accessed shared document")
        
        # Step 10: Collaborator tries to update the shared document (should fail with read permission)
        logger.info("Step 10: Collaborator tries to update the shared document")
        update_data = {"title": f"Updated {private_doc_title}"}
        update_response = collaborator_session.put(f"{self.base_url}/api/documents/{private_doc['id']}", json=update_data)
        assert update_response.status_code in [403, 404]  # Either forbidden or not found
        logger.info("✓ Collaborator correctly denied update permission")
        
        # Step 11: Owner upgrades collaborator's permission to write
        logger.info("Step 11: Owner upgrades collaborator's permission to write")
        upgrade_result = self.share_document(owner_session, private_doc["id"], collaborator_info["id"], "write")
        logger.info("✓ Owner upgraded collaborator's permission to write")
        
        # Step 12: Collaborator updates the shared document (should succeed now)
        logger.info("Step 12: Collaborator updates the shared document")
        update_data = {"title": f"Updated {private_doc_title}"}
        update_response = collaborator_session.put(f"{self.base_url}/api/documents/{private_doc['id']}", json=update_data)
        assert update_response.status_code == 200
        updated_doc = update_response.json()
        assert updated_doc["title"] == update_data["title"]
        logger.info("✓ Collaborator successfully updated shared document")
        
        # Step 13: Owner revokes collaborator's access
        logger.info("Step 13: Owner revokes collaborator's access")
        revoke_response = owner_session.delete(f"{self.base_url}/api/documents/{private_doc['id']}/share/{collaborator_info['id']}")
        assert revoke_response.status_code == 200
        logger.info("✓ Owner revoked collaborator's access")
        
        # Step 14: Collaborator tries to access the document again (should fail)
        logger.info("Step 14: Collaborator tries to access the document again")
        final_response = collaborator_session.get(f"{self.base_url}/api/documents/{private_doc['id']}")
        assert final_response.status_code == 404
        logger.info("✓ Collaborator correctly denied access after revocation")
        
        logger.info("Permission scenario test passed successfully")


if __name__ == "__main__":
    # Run the tests
    test = TestAuthFlows()
    try:
        test.test_complete_user_journey()
        test.test_permission_scenario()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        test.teardown_method()