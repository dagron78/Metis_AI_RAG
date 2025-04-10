# Metis RAG Authentication Testing Guide

This guide provides instructions for running the authentication and authorization tests for the Metis RAG application. These tests verify the security features implemented according to the [Authentication Implementation Plan](../docs/Metis_RAG_Authentication_Implementation_Detailed_Plan.md).

## Test Structure

The authentication tests are organized into three levels:

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test complete user flows and scenarios

### Unit Tests

Located in `tests/unit/`:

- `test_security_utils.py`: Tests for JWT token functions and password hashing utilities

### Integration Tests

Located in `tests/integration/`:

- `test_auth_endpoints.py`: Tests for authentication API endpoints (login, register, refresh, etc.)
- `test_permissions_db.py`: Tests for database-level permissions (Row Level Security)
- `test_permissions_vector.py`: Tests for vector database security (metadata filtering)

### End-to-End Tests

Located in `tests/e2e/`:

- `test_auth_flows.py`: Tests for complete authentication flows (register, login, access, refresh, logout)
- `test_permission_scenarios.py`: Tests for complex permission scenarios with multiple users, roles, and organizations

## Prerequisites

Before running the tests, ensure you have:

1. Set up the Metis RAG application according to the setup instructions
2. Created a test database (separate from your production database)
3. Installed the required testing dependencies:
   ```
   pip install pytest pytest-asyncio httpx
   ```

## Running the Tests

### Running All Tests

To run all authentication tests:

```bash
pytest tests/unit/test_security_utils.py tests/integration/test_auth_endpoints.py tests/integration/test_permissions_db.py tests/integration/test_permissions_vector.py tests/e2e/test_auth_flows.py tests/e2e/test_permission_scenarios.py -v
```

### Running Unit Tests Only

```bash
pytest tests/unit/test_security_utils.py -v
```

### Running Integration Tests Only

```bash
pytest tests/integration/test_auth_endpoints.py tests/integration/test_permissions_db.py tests/integration/test_permissions_vector.py -v
```

### Running End-to-End Tests Only

```bash
pytest tests/e2e/test_auth_flows.py tests/e2e/test_permission_scenarios.py -v
```

### Running Individual Test Files

```bash
# Example: Run only the security utils tests
pytest tests/unit/test_security_utils.py -v

# Example: Run only the auth endpoints tests
pytest tests/integration/test_auth_endpoints.py -v
```

### Running Specific Test Functions

```bash
# Example: Run only the password hash test
pytest tests/unit/test_security_utils.py::TestPasswordUtils::test_password_hash_and_verify -v

# Example: Run only the login test
pytest tests/integration/test_auth_endpoints.py::TestAuthEndpoints::test_login_success -v
```

## Test Environment Setup

The tests require a running instance of the Metis RAG application. You can set up a test environment using:

```bash
# Set environment variables for testing
export METIS_RAG_ENV=test
export METIS_RAG_DB_URL=sqlite:///test.db

# Run the application in test mode
python scripts/run_app.py
```

In a separate terminal, run the tests:

```bash
pytest tests/unit/test_security_utils.py -v
```

## Test Data

The tests create temporary test users, documents, and other data as needed. This data is cleaned up after each test to avoid polluting the test database.

For end-to-end tests, the application should be running with a clean database to ensure consistent results.

## Troubleshooting

### Common Issues

1. **Database connection errors**: Ensure the test database exists and is accessible
2. **Permission errors**: Ensure the application is running with the correct permissions
3. **Token validation errors**: Check that the JWT secret key is correctly set in the test environment

### Debugging Tests

To enable more verbose output:

```bash
pytest tests/unit/test_security_utils.py -vv
```

To enable debug logging:

```bash
pytest tests/unit/test_security_utils.py -v --log-cli-level=DEBUG
```

## Security Considerations

These tests verify the security features of the Metis RAG application, including:

1. **Authentication**: User identity verification with JWT tokens
2. **Authorization**: Access control for documents and conversations
3. **Row Level Security**: Database-level access control
4. **Vector Database Security**: Metadata filtering for vector searches
5. **Persistent User-Document Relationships**: Maintaining relationships across authentication events

The tests are designed to ensure that these security features work correctly and that unauthorized access is properly prevented.

## Additional Resources

- [Authentication Implementation Plan](../docs/Metis_RAG_Authentication_Implementation_Detailed_Plan.md)
- [Authentication Testing Plan](../docs/Metis_RAG_Authentication_Testing_Plan.md)