#!/usr/bin/env python3
"""
Integration tests for authentication endpoints in app/api/auth.py
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from datetime import datetime, timedelta

from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.db.dependencies import get_db
from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserUpdate


@pytest.fixture
def client():
    """Create a TestClient instance for each test"""
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """Create unique test user data for each test"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "is_active": True,
        "is_admin": False
    }


@pytest.fixture
async def test_user(test_user_data):
    """Create a test user in the database"""
    # Get database session
    db = await anext(get_db())
    
    try:
        # Create user repository
        user_repository = UserRepository(db)
        
        # Create user
        user_create = UserCreate(**test_user_data)
        user = await user_repository.create_user(user_create)
        
        # Return user and credentials
        yield user, test_user_data
        
        # Clean up - delete user
        await user_repository.delete_user(user.id)
    finally:
        await db.close()


@pytest.fixture
def event_loop():
    """Create an event loop for each test"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class TestAuthEndpoints:
    """Tests for authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Test successful login"""
        user, user_data = await test_user
        
        # Login with valid credentials
        response = client.post(
            "/api/auth/token",
            data={
                "username": user_data["username"],
                "password": user_data["password"],
                "grant_type": "password"
            }
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check token data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        user, user_data = await test_user
        
        # Login with invalid password
        response = client.post(
            "/api/auth/token",
            data={
                "username": user_data["username"],
                "password": "wrongpassword",
                "grant_type": "password"
            }
        )
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
        
        # Login with non-existent user
        response = client.post(
            "/api/auth/token",
            data={
                "username": "nonexistentuser",
                "password": user_data["password"],
                "grant_type": "password"
            }
        )
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Test successful user registration"""
        # Create unique user data
        unique_id = uuid.uuid4().hex[:8]
        user_data = {
            "username": f"newuser_{unique_id}",
            "email": f"newuser_{unique_id}@example.com",
            "password": "testpassword123",
            "full_name": "New Test User",
            "is_active": True,
            "is_admin": False
        }
        
        # Register new user
        response = client.post(
            "/api/auth/register",
            json=user_data
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check user data
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] == user_data["is_active"]
        assert data["is_admin"] == user_data["is_admin"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
        
        # Clean up - delete user
        db = await anext(get_db())
        try:
            user_repository = UserRepository(db)
            await user_repository.delete_user(data["id"])
        finally:
            await db.close()
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        user, user_data = await test_user
        
        # Try to register with existing username
        duplicate_data = user_data.copy()
        duplicate_data["email"] = f"different_{uuid.uuid4().hex[:8]}@example.com"  # Different email
        
        response = client.post(
            "/api/auth/register",
            json=duplicate_data
        )
        
        # Check response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "username already exists" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        user, user_data = await test_user
        
        # Try to register with existing email
        duplicate_data = user_data.copy()
        duplicate_data["username"] = f"different_{uuid.uuid4().hex[:8]}"  # Different username
        
        response = client.post(
            "/api/auth/register",
            json=duplicate_data
        )
        
        # Check response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "email already exists" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client, test_user):
        """Test refreshing an access token"""
        user, user_data = await test_user
        
        # Login to get tokens
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": user_data["username"],
                "password": user_data["password"],
                "grant_type": "password"
            }
        )
        
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Refresh token
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # Check response
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        # Check new token data
        assert "access_token" in refresh_data
        assert refresh_data["access_token"] != login_data["access_token"]  # New token should be different
        assert refresh_data["token_type"] == "bearer"
        assert refresh_data["expires_in"] > 0
        assert refresh_data["refresh_token"] == refresh_token  # Same refresh token returned
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client):
        """Test refreshing with an invalid token"""
        # Try to refresh with invalid token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid refresh token" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client, test_user):
        """Test getting the current user"""
        user, user_data = await test_user
        
        # Login to get token
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": user_data["username"],
                "password": user_data["password"],
                "grant_type": "password"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check user data
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client):
        """Test getting the current user without a token"""
        # Try to get current user without token
        response = client.get("/api/auth/me")
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_update_current_user(self, client, test_user):
        """Test updating the current user"""
        user, user_data = await test_user
        
        # Login to get token
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": user_data["username"],
                "password": user_data["password"],
                "grant_type": "password"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Update user data
        update_data = {
            "full_name": "Updated Test User",
            "email": f"updated_{uuid.uuid4().hex[:8]}@example.com"
        }
        
        response = client.put(
            "/api/auth/me",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check updated user data
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]
        assert data["username"] == user_data["username"]  # Username should not change
    
    @pytest.mark.asyncio
    async def test_account_deactivation_reactivation(self, client, test_user):
        """Test account deactivation and reactivation (persistence test)"""
        user, user_data = await test_user
        
        # Login to get token
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": user_data["username"],
                "password": user_data["password"],
                "grant_type": "password"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Deactivate account (requires admin access, so we'll do it directly in the DB)
        db = await anext(get_db())
        try:
            user_repository = UserRepository(db)
            await user_repository.update_user(user.id, {"is_active": False})
            
            # Try to access protected endpoint
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should fail with 403 Forbidden
            assert response.status_code == 403
            data = response.json()
            assert "detail" in data
            assert "Inactive user" in data["detail"]
            
            # Try to login
            login_response = client.post(
                "/api/auth/token",
                data={
                    "username": user_data["username"],
                    "password": user_data["password"],
                    "grant_type": "password"
                }
            )
            
            # Should fail with 401 Unauthorized
            assert login_response.status_code == 401
            
            # Reactivate account
            await user_repository.update_user(user.id, {"is_active": True})
            
            # Try to login again
            login_response = client.post(
                "/api/auth/token",
                data={
                    "username": user_data["username"],
                    "password": user_data["password"],
                    "grant_type": "password"
                }
            )
            
            # Should succeed
            assert login_response.status_code == 200
            new_token = login_response.json()["access_token"]
            
            # Access protected endpoint with new token
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {new_token}"}
            )
            
            # Should succeed
            assert response.status_code == 200
            
        finally:
            await db.close()
    
    @pytest.mark.asyncio
    async def test_password_reset_persistence(self, client, test_user):
        """Test password reset with persistence of user-document relationships"""
        user, user_data = await test_user
        
        # Login to get token
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": user_data["username"],
                "password": user_data["password"],
                "grant_type": "password"
            }
        )
        
        original_token = login_response.json()["access_token"]
        
        # Change password directly in the DB (simulating password reset)
        new_password = "newpassword456"
        db = await anext(get_db())
        try:
            user_repository = UserRepository(db)
            new_password_hash = get_password_hash(new_password)
            await user_repository.update_user(user.id, {"password_hash": new_password_hash})
            
            # Try to login with old password
            login_response = client.post(
                "/api/auth/token",
                data={
                    "username": user_data["username"],
                    "password": user_data["password"],
                    "grant_type": "password"
                }
            )
            
            # Should fail
            assert login_response.status_code == 401
            
            # Login with new password
            login_response = client.post(
                "/api/auth/token",
                data={
                    "username": user_data["username"],
                    "password": new_password,
                    "grant_type": "password"
                }
            )
            
            # Should succeed
            assert login_response.status_code == 200
            new_token = login_response.json()["access_token"]
            
            # Access protected endpoint with new token
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {new_token}"}
            )
            
            # Should succeed
            assert response.status_code == 200
            user_data = response.json()
            
            # User ID should be the same (persistence)
            assert user_data["id"] == user.id
            
        finally:
            await db.close()
    
    @pytest.mark.asyncio
    async def test_token_expiry_refresh(self, client, test_user):
        """Test token expiry and refresh (persistence test)"""
        user, user_data = await test_user
        
        # Create a short-lived token (expires in 2 seconds)
        db = await anext(get_db())
        try:
            user_repository = UserRepository(db)
            user_db = await user_repository.get_by_username(user_data["username"])
            
            token_data = {
                "sub": user_db.username,
                "user_id": user_db.id,
                "aud": "metis-rag",
                "iss": "metis-rag-auth",
                "jti": str(uuid.uuid4())
            }
            
            # Create short-lived token
            short_lived_token = create_access_token(
                data=token_data,
                expires_delta=timedelta(seconds=2)
            )
            
            # Access protected endpoint with token
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {short_lived_token}"}
            )
            
            # Should succeed
            assert response.status_code == 200
            
            # Wait for token to expire
            await asyncio.sleep(3)
            
            # Try to access protected endpoint with expired token
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {short_lived_token}"}
            )
            
            # Should fail with 401 Unauthorized
            assert response.status_code == 401
            
            # Login to get new tokens
            login_response = client.post(
                "/api/auth/token",
                data={
                    "username": user_data["username"],
                    "password": user_data["password"],
                    "grant_type": "password"
                }
            )
            
            # Should succeed
            assert login_response.status_code == 200
            new_token = login_response.json()["access_token"]
            
            # Access protected endpoint with new token
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {new_token}"}
            )
            
            # Should succeed
            assert response.status_code == 200
            user_data_response = response.json()
            
            # User ID should be the same (persistence)
            assert user_data_response["id"] == user_db.id
            
        finally:
            await db.close()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])