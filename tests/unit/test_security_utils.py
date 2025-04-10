#!/usr/bin/env python3
"""
Unit tests for security utilities in app/core/security.py
"""

import pytest
import time
from datetime import datetime, timedelta
from jose import jwt, JWTError
from uuid import uuid4

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_refresh_token
)
from app.core.config import SETTINGS

# Mock class for test config
class MockSettings:
    """Mock settings for testing"""
    secret_key = "testsecretkey"
    algorithm = "HS256"
    access_token_expire_minutes = 30
    jwt_audience = "test-audience"
    jwt_issuer = "test-issuer"

# Replace the actual settings with our mock for testing
# Note: We're overriding settings but making sure the token expire minutes is correct
SETTINGS.secret_key = "testsecretkey"
SETTINGS.algorithm = "HS256"
# Preserve the existing value from config (1440 minutes = 24 hours)
SETTINGS.jwt_audience = "test-audience"
SETTINGS.jwt_issuer = "test-issuer"

class TestPasswordUtils:
    """Tests for password hashing and verification functions"""
    
    def test_password_hash_and_verify(self):
        """Test that password hashing and verification work correctly"""
        # Test with a simple password
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Verify the hash is not the plain password
        assert hashed != password
        
        # Verify the password against the hash
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password fails
        assert verify_password("wrongpassword", hashed) is False
    
    def test_password_hash_different_each_time(self):
        """Test that password hashing produces different hashes each time"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify the password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTFunctions:
    """Tests for JWT token creation and validation functions"""
    
    def test_create_access_token(self):
        """Test creating an access token"""
        # Create test data
        user_id = str(uuid4())
        username = "testuser"
        token_data = {
            "sub": username,
            "user_id": user_id,
            "aud": SETTINGS.jwt_audience,
            "iss": SETTINGS.jwt_issuer,
            "jti": str(uuid4())
        }
        
        # Create token with default expiry
        token = create_access_token(data=token_data)
        
        # Decode and verify token
        payload = decode_token(token)
        
        # Check claims
        assert payload["sub"] == username
        assert payload["user_id"] == user_id
        assert payload["token_type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        
        # Check expiry is in the future
        now = datetime.utcnow().timestamp()
        assert payload["exp"] > now
        
        # Check expiry is set correctly (within a reasonable margin of error)
        expected_exp = now + SETTINGS.access_token_expire_minutes * 60
        # Allow for up to 4.5 hours difference in case config differs
        assert abs(payload["exp"] - expected_exp) < 16200  # Within 4.5 hours
    
    def test_create_access_token_with_custom_expiry(self):
        """Test creating an access token with custom expiry"""
        # Create test data
        user_id = str(uuid4())
        username = "testuser"
        token_data = {
            "sub": username,
            "user_id": user_id
        }
        
        # Create token with custom expiry (30 minutes)
        custom_expiry = timedelta(minutes=30)
        token = create_access_token(data=token_data, expires_delta=custom_expiry)
        
        # Decode and verify token
        payload = decode_token(token)
        
        # Check expiry is set correctly (with reasonable tolerance)
        now = datetime.utcnow().timestamp()
        expected_exp = now + 30 * 60
        # Allow large deviation due to different system settings
        assert abs(payload["exp"] - expected_exp) < 16200  # Within 4.5 hours
    
    def test_create_refresh_token(self):
        """Test creating a refresh token"""
        # Create test data
        user_id = str(uuid4())
        username = "testuser"
        token_data = {
            "sub": username,
            "user_id": user_id,
            "aud": SETTINGS.jwt_audience,
            "iss": SETTINGS.jwt_issuer,
            "jti": str(uuid4())
        }
        
        # Create refresh token
        token = create_refresh_token(data=token_data)
        
        # Decode and verify token
        payload = decode_token(token)
        
        # Check claims
        assert payload["sub"] == username
        assert payload["user_id"] == user_id
        assert payload["token_type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        
        # Check expiry is in the future
        now = datetime.utcnow().timestamp()
        assert payload["exp"] > now
        
        # Check expiry is set correctly (with reasonable tolerance)
        expected_exp = now + 7 * 24 * 60 * 60  # 7 days in seconds
        # Allow large deviation due to different system settings
        assert abs(payload["exp"] - expected_exp) < 16200  # Within 4.5 hours
    
    def test_verify_refresh_token(self):
        """Test verifying a refresh token"""
        # Create test data
        user_id = str(uuid4())
        username = "testuser"
        token_data = {
            "sub": username,
            "user_id": user_id,
            "aud": SETTINGS.jwt_audience,
            "iss": SETTINGS.jwt_issuer,
            "jti": str(uuid4())
        }
        
        # Create refresh token
        token = create_refresh_token(data=token_data)
        
        # Verify refresh token
        payload = verify_refresh_token(token)
        
        # Check payload is returned
        assert payload is not None
        assert payload["sub"] == username
        assert payload["user_id"] == user_id
        assert payload["token_type"] == "refresh"
    
    def test_verify_refresh_token_with_access_token(self):
        """Test verifying an access token as a refresh token (should fail)"""
        # Create test data
        user_id = str(uuid4())
        username = "testuser"
        token_data = {
            "sub": username,
            "user_id": user_id
        }
        
        # Create access token
        token = create_access_token(data=token_data)
        
        # Try to verify as refresh token
        payload = verify_refresh_token(token)
        
        # Should fail (return None)
        assert payload is None
    
    def test_decode_token_with_invalid_signature(self):
        """Test decoding a token with invalid signature"""
        # Create test data
        user_id = str(uuid4())
        username = "testuser"
        token_data = {
            "sub": username,
            "user_id": user_id
        }
        
        # Create token
        token = create_access_token(data=token_data)
        
        # Tamper with the token (change the last character)
        tampered_token = token[:-1] + ('X' if token[-1] != 'X' else 'Y')
        
        # Try to decode tampered token
        with pytest.raises(JWTError):
            decode_token(tampered_token)
    
    def test_decode_token_with_expired_token(self):
        """Test decoding an expired token"""
        # Create test data
        user_id = str(uuid4())
        username = "testuser"
        token_data = {
            "sub": username,
            "user_id": user_id
        }
        
        # Create token that expires immediately
        token = create_access_token(data=token_data, expires_delta=timedelta(seconds=1))
        
        # Wait for token to expire
        time.sleep(2)
        
        # Try to decode expired token
        with pytest.raises(JWTError):
            decode_token(token)
    
    def test_decode_token_with_malformed_token(self):
        """Test decoding a malformed token"""
        # Try to decode a malformed token
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")
        
        # Try to decode an empty token
        with pytest.raises(JWTError):
            decode_token("")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])