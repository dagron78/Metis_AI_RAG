# Metis RAG Authentication System

This document provides an overview of the authentication system implemented in the Metis RAG application.

## Overview

The authentication system provides user management and access control for the Metis RAG application. It ensures that users can only access their own documents and conversations, and that sensitive operations are protected.

## Features

- User registration and login
- JWT-based authentication
- Role-based access control (user/admin)
- Resource ownership validation
- Protected API endpoints
- Middleware for route protection

## Components

### Models

- `User` model in `app/models/user.py`
- Database model in `app/db/models.py`

### Repositories

- `UserRepository` in `app/db/repositories/user_repository.py`

### API Endpoints

- `/api/auth/register` - Register a new user
- `/api/auth/token` - Login and get access token
- `/api/auth/me` - Get current user information
- `/api/auth/users` - List all users (admin only)
- `/api/auth/users/{user_id}` - Get user by ID (admin or self)

### Security

- Password hashing with bcrypt
- JWT token generation and validation
- Token expiration and refresh

### Middleware

- `AuthMiddleware` in `app/middleware/auth.py` - Protects routes and API endpoints

### Frontend

- Login and registration pages
- Authentication UI elements in the base template
- JavaScript for token management and authentication

## Database Schema

The authentication system adds the following to the database schema:

- `users` table with fields:
  - `id` (UUID, primary key)
  - `username` (string, unique)
  - `email` (string, unique)
  - `password_hash` (string)
  - `full_name` (string, optional)
  - `is_active` (boolean)
  - `is_admin` (boolean)
  - `created_at` (timestamp)
  - `last_login` (timestamp)
  - `metadata` (JSONB)

- Foreign key relationships:
  - `documents.user_id` references `users.id`
  - `conversations.user_id` references `users.id`

## Usage

### Registration

```python
# Register a new user
response = requests.post(
    "http://localhost:8000/api/auth/register",
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword",
        "full_name": "Test User"
    }
)
```

### Login

```python
# Login and get access token
response = requests.post(
    "http://localhost:8000/api/auth/token",
    data={
        "username": "testuser",
        "password": "securepassword"
    }
)
token = response.json()["access_token"]
```

### Authenticated Requests

```python
# Make authenticated request
response = requests.get(
    "http://localhost:8000/api/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)
```

## Testing

A test script is provided in `scripts/test_authentication.py` that demonstrates the authentication flow:

1. Register a new user
2. Login with user credentials
3. Get current user information
4. Upload a document
5. List user's documents
6. Create a conversation
7. List conversations

Run the test script with:

```bash
python scripts/test_authentication.py
```

## Implementation Details

### Password Hashing

Passwords are hashed using bcrypt with automatic salt generation. The hashing is handled by the `passlib` library.

### Token Generation

JWT tokens are generated using the `python-jose` library with the HS256 algorithm. Tokens include:
- Subject (`sub`): Username
- User ID (`user_id`): UUID of the user
- Expiration (`exp`): Token expiration timestamp

### Middleware Protection

The `AuthMiddleware` protects routes based on configuration:
- Protected routes: Redirects to login if not authenticated
- API routes: Returns 401 Unauthorized if not authenticated
- Excluded routes: Allows access without authentication

## Configuration

Authentication settings are configured in `app/core/config.py`:

- `SECRET_KEY`: Secret key for JWT token generation
- `ALGORITHM`: Algorithm for JWT token generation (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes

## Security Considerations

- HTTPS should be used in production to protect tokens in transit
- Passwords are never stored in plain text
- Tokens have a limited lifetime
- Resource ownership is validated for all operations
- CORS is configured to restrict cross-origin requests