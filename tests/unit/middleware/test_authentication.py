#!/usr/bin/env python3
"""
Unit tests to verify authentication with the Metis RAG API.
These are simplified tests focused on core authentication functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from jose import jwt
import time
from datetime import datetime, timedelta

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_refresh_token
)
from app.core.config import SETTINGS

class TestAuthenticationCore:
    """Tests for core authentication functionality"""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification"""
        password = "test_password123"
        
        # Hash the password
        hashed = get_password_hash(password)
        
        # Verify it's not the original password
        assert hashed != password
        
        # Verify the password correctly
        assert verify_password(password, hashed) is True
        
        # Verify wrong password fails
        assert verify_password("wrong_password", hashed) is False
    
    def test_access_token_creation(self):
        """Test creating and validating access tokens"""
        # Create token data
        user_data = {
            "sub": "testuser",
            "user_id": "1234567890"
        }
        
        # Create the token
        token = create_access_token(data=user_data)
        
        # Decode and verify
        decoded = decode_token(token)
        
        # Check basic token contents
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == "1234567890"
        assert decoded["token_type"] == "access"
        
        # Verify expiration is in the future
        now = datetime.utcnow().timestamp()
        assert decoded["exp"] > now
    
    def test_refresh_token_creation(self):
        """Test creating and validating refresh tokens"""
        # Create token data
        user_data = {
            "sub": "testuser",
            "user_id": "1234567890"
        }
        
        # Create the token
        token = create_refresh_token(data=user_data)
        
        # Verify the token
        verified = verify_refresh_token(token)
        
        # Check token was verified
        assert verified is not None
        assert verified["sub"] == "testuser"
        assert verified["user_id"] == "1234567890"
        assert verified["token_type"] == "refresh"
    
    def test_token_expiration(self):
        """Test token expiration"""
        # Create token data
        user_data = {
            "sub": "testuser",
            "user_id": "1234567890"
        }
        
        # Create a token that expires in 2 seconds
        token = create_access_token(data=user_data, expires_delta=timedelta(seconds=2))
        
        # Verify it's valid now
        decoded = decode_token(token)
        assert decoded["sub"] == "testuser"
        
        # Wait for expiration
        time.sleep(3)
        
        # Should raise an exception now
        with pytest.raises(jwt.JWTError):
            decode_token(token)
    
    def test_refresh_token_validation(self):
        """Test refresh token validation"""
        # Create token data
        user_data = {
            "sub": "testuser",
            "user_id": "1234567890"
        }
        
        # Create an access token (not a refresh token)
        access_token = create_access_token(data=user_data)
        
        # Verify it fails refresh token validation
        result = verify_refresh_token(access_token)
        assert result is None  # Should fail since it's not a refresh token

class TestMockAuthentication:
    """Mock-based authentication tests"""
    
    @pytest.fixture
    def mock_auth_request(self):
        """Create a mock authentication request"""
        mock_request = MagicMock()
        mock_request.form = {
            "username": "testuser",
            "password": "testpassword"
        }
        return mock_request
    
    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository"""
        mock_repo = MagicMock()
        # Configure mock to return a user with valid password hash
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.id = "1234567890"
        mock_user.password_hash = get_password_hash("testpassword")
        mock_user.is_active = True
        
        mock_repo.get_by_username.return_value = mock_user
        return mock_repo
    
    def test_auth_success_flow(self, mock_auth_request, mock_user_repo):
        """Test successful authentication flow"""
        # Get username and password from request
        username = mock_auth_request.form["username"]
        password = mock_auth_request.form["password"]
        
        # Get user from repo
        user = mock_user_repo.get_by_username(username)
        
        # Verify password
        is_password_valid = verify_password(password, user.password_hash)
        assert is_password_valid is True
        
        # Create tokens
        user_data = {
            "sub": user.username,
            "user_id": user.id
        }
        
        access_token = create_access_token(data=user_data)
        refresh_token = create_refresh_token(data=user_data)
        
        # Verify tokens
        assert access_token is not None
        assert refresh_token is not None
        
        # Decode and check tokens
        access_payload = decode_token(access_token)
        assert access_payload["sub"] == user.username
        assert access_payload["token_type"] == "access"
        
        refresh_payload = decode_token(refresh_token)
        assert refresh_payload["sub"] == user.username
        assert refresh_payload["token_type"] == "refresh"
    
    def test_auth_failure_flow(self, mock_auth_request, mock_user_repo):
        """Test failed authentication flow"""
        # Mock wrong password
        username = mock_auth_request.form["username"]
        wrong_password = "wrong_password"
        
        # Get user from repo
        user = mock_user_repo.get_by_username(username)
        
        # Verify password fails
        is_password_valid = verify_password(wrong_password, user.password_hash)
        assert is_password_valid is False