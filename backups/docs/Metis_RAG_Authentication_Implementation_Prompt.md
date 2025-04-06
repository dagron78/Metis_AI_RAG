# Metis RAG Authentication Implementation Prompt

## Task Overview

Implement the JWT authentication system for the Metis RAG application based on the detailed plan in `docs/Metis_RAG_Authentication_Implementation_Detailed_Plan.md`. This implementation will focus on Phase 1 of the plan, which establishes the core JWT authentication infrastructure.

## Background

The Metis RAG application requires a secure authentication system that not only verifies user identities but also maintains persistent relationships between users and their documents. The authentication system should be designed to ensure that user access to their data remains consistent regardless of credential changes, password resets, or periods of inactivity.

## Current State

- The application has a database schema with a `users` table including essential fields (id, username, email, password_hash, etc.)
- There's a basic `AuthMiddleware` class in `app/middleware/auth.py` that handles authorization headers
- Protected routes are defined for both web UI and API endpoints
- No proper JWT authentication is implemented yet

## Implementation Requirements

Please implement Phase 1 of the authentication system as outlined in the detailed plan:

1. **JWT Authentication Core**
   - Create JWT configuration settings in `app/core/config.py`
   - Implement JWT token handling in `app/core/security.py`
   - Create JWT bearer class in `app/middleware/jwt_bearer.py`

2. **User Authentication Endpoints**
   - Implement login endpoint in `app/api/endpoints/auth.py`
   - Implement token refresh endpoint
   - Create user registration endpoint

3. **Authentication Middleware Integration**
   - Update `app/middleware/auth.py` to use JWT validation
   - Apply authentication middleware to FastAPI app

## Key Considerations

- The implementation should maintain persistent user-document relationships
- JWT tokens should be temporary but user identity should be preserved across authentication events
- The system should clearly separate authentication (identity verification) from authorization (access control)
- Password reset functionality should preserve the same user identity
- The implementation should follow security best practices for JWT tokens

## Specific Files to Modify/Create

1. `app/core/config.py` - Add JWT configuration settings
2. `app/core/security.py` - Implement JWT token handling functions
3. `app/middleware/jwt_bearer.py` - Create JWT bearer class
4. `app/api/endpoints/auth.py` - Implement authentication endpoints
5. `app/middleware/auth.py` - Update to use JWT validation
6. `app/main.py` - Apply authentication middleware

## Testing Requirements

After implementation, the following should be testable:
- User registration with proper password hashing
- User login with JWT token generation
- Token refresh functionality
- Protected route access with valid JWT tokens
- Rejection of invalid or expired tokens

## Resources

- The existing user model is defined in `app/models/user.py`
- The current authentication middleware is in `app/middleware/auth.py`
- Detailed implementation plan: `docs/Metis_RAG_Authentication_Implementation_Detailed_Plan.md`

## Deliverables

1. Implemented JWT authentication system
2. Brief documentation of any design decisions or deviations from the plan
3. Example of how to test the authentication system