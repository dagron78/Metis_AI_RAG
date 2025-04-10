# Metis RAG JWT Authentication System

This document provides an overview of the JWT authentication system implemented for the Metis RAG application, including how to test it and integrate it with client applications.

## Overview

The Metis RAG authentication system uses JSON Web Tokens (JWT) to secure API endpoints and maintain user sessions. The system includes:

1. **Access Tokens**: Short-lived tokens used for API requests
2. **Refresh Tokens**: Longer-lived tokens used to obtain new access tokens
3. **Persistent User Identity**: User identity is preserved across authentication events

## Authentication Flow

The authentication flow works as follows:

1. User registers or logs in with credentials
2. Server validates credentials and issues access and refresh tokens
3. Client includes access token in API requests
4. When access token expires, client uses refresh token to get a new access token
5. User identity remains consistent regardless of token refreshes or password changes

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Database
    
    Client->>Server: Register/Login with credentials
    Server->>Database: Validate credentials
    Database-->>Server: User information
    Server->>Server: Generate JWT tokens
    Server-->>Client: Return access & refresh tokens
    
    Note over Client,Server: Using Access Token
    
    Client->>Server: API request with access token
    Server->>Server: Validate token
    Server-->>Client: Protected resource
    
    Note over Client,Server: Token Refresh
    
    Client->>Server: Request with expired token
    Server-->>Client: 401 Unauthorized
    Client->>Server: Refresh token request
    Server->>Server: Validate refresh token
    Server-->>Client: New access token
```

## Token Structure

### Access Token

Access tokens contain the following claims:

- `sub`: Username (subject)
- `user_id`: User's unique identifier
- `exp`: Expiration time
- `iat`: Issued at time
- `token_type`: "access"
- `aud`: Audience (API identifier)
- `iss`: Issuer (Metis RAG)
- `jti`: Unique token identifier

### Refresh Token

Refresh tokens contain similar claims but with a longer expiration time and a different token type:

- `token_type`: "refresh"

## Testing the Authentication System

The repository includes a test script (`run_authentication_test.py`) that demonstrates the complete authentication flow:

1. User registration
2. Login to obtain tokens
3. Accessing protected endpoints
4. Token refresh
5. Using the new access token

### Running the Test

To test the authentication system:

1. Start the Metis RAG application:
   ```bash
   python -m scripts.run_app
   ```

2. In a separate terminal, run the authentication test script:
   ```bash
   python run_authentication_test.py
   ```

The test script will:
- Register a test user (if not already registered)
- Log in to get access and refresh tokens
- Access a protected endpoint
- Refresh the access token
- Access the protected endpoint with the new token

## API Endpoints

### Registration

```
POST /api/auth/register
```

Request body:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepassword",
  "full_name": "Test User"
}
```

Response:
```json
{
  "id": "user-uuid",
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-03-25T12:00:00",
  "last_login": null,
  "metadata": {}
}
```

### Login

```
POST /api/auth/token
```

Form data:
```
username=testuser&password=securepassword
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Token Refresh

```
POST /api/auth/refresh
```

Request body:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Get Current User

```
GET /api/auth/me
```

Headers:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:
```json
{
  "id": "user-uuid",
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-03-25T12:00:00",
  "last_login": "2025-03-25T12:30:00",
  "metadata": {}
}
```

## Client Integration

### JavaScript Example

```javascript
// Login and get tokens
async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch('http://localhost:8000/api/auth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData
  });
  
  if (!response.ok) {
    throw new Error('Login failed');
  }
  
  const tokenData = await response.json();
  
  // Store tokens securely
  localStorage.setItem('access_token', tokenData.access_token);
  localStorage.setItem('refresh_token', tokenData.refresh_token);
  localStorage.setItem('token_expiry', Date.now() + (tokenData.expires_in * 1000));
  
  return tokenData;
}

// Access protected endpoint
async function fetchProtectedResource(url) {
  // Check if token needs refresh
  const tokenExpiry = localStorage.getItem('token_expiry');
  if (tokenExpiry && Date.now() > tokenExpiry) {
    await refreshToken();
  }
  
  const accessToken = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  if (response.status === 401) {
    // Token might be invalid, try refreshing
    await refreshToken();
    // Retry with new token
    return fetchProtectedResource(url);
  }
  
  return response.json();
}

// Refresh token
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:8000/api/auth/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  if (!response.ok) {
    // Refresh failed, redirect to login
    window.location.href = '/login';
    throw new Error('Token refresh failed');
  }
  
  const tokenData = await response.json();
  
  // Update stored tokens
  localStorage.setItem('access_token', tokenData.access_token);
  localStorage.setItem('token_expiry', Date.now() + (tokenData.expires_in * 1000));
  
  return tokenData;
}
```

### Python Example

```python
import requests
import time

class MetisRAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = 0
    
    def login(self, username, password):
        """Login and get tokens"""
        login_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(
            f"{self.base_url}/api/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.token_expiry = time.time() + token_data["expires_in"]
        
        return token_data
    
    def refresh_token(self):
        """Refresh the access token"""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        refresh_data = {
            "refresh_token": self.refresh_token
        }
        
        response = requests.post(
            f"{self.base_url}/api/auth/refresh",
            json=refresh_data
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        self.access_token = token_data["access_token"]
        self.token_expiry = time.time() + token_data["expires_in"]
        
        return token_data
    
    def get_resource(self, endpoint):
        """Get a protected resource"""
        # Check if token needs refresh
        if time.time() > self.token_expiry:
            self.refresh_token()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
        
        # If unauthorized, try refreshing token
        if response.status_code == 401:
            self.refresh_token()
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
        
        response.raise_for_status()
        return response.json()
```

## Security Considerations

1. **Token Storage**: 
   - Store tokens securely
   - For web applications, use HttpOnly cookies for access tokens
   - For mobile applications, use secure storage mechanisms

2. **Token Expiration**:
   - Access tokens have a short lifetime (default: 30 minutes)
   - Refresh tokens have a longer lifetime (default: 7 days)

3. **HTTPS**:
   - Always use HTTPS in production to protect tokens in transit

4. **Token Validation**:
   - All tokens are validated for:
     - Signature
     - Expiration time
     - Required claims
     - Token type

## Persistent User-Document Relationships

The authentication system maintains persistent relationships between users and their documents:

1. User identity (user_id) is preserved across all authentication events
2. Document ownership is tied to user_id, not to authentication tokens
3. Password resets and token refreshes do not affect document access rights
4. Account deactivation temporarily prevents login but maintains document relationships

This ensures that users always have access to their documents, regardless of authentication status or history.

## Customization

The authentication system can be customized through environment variables:

- `SECRET_KEY`: JWT signing key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token lifetime in minutes (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token lifetime in days (default: 7)
- `JWT_AUDIENCE`: Token audience claim (default: metis-rag-api)
- `JWT_ISSUER`: Token issuer claim (default: metis-rag)

## Troubleshooting

### Invalid Token

If you receive a 401 Unauthorized error with "Invalid token or token expired":

1. Check that the token is correctly included in the Authorization header
2. Verify that the token has not expired
3. Try refreshing the token

### Refresh Token Failed

If token refresh fails:

1. The refresh token may have expired
2. The refresh token may be invalid
3. The user account may have been deactivated

In these cases, the user needs to log in again with their credentials.