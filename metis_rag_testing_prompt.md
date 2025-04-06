# Metis RAG Testing Prompt

I need help troubleshooting and testing the Metis RAG system. I've created an end-to-end test suite that includes test documents in all supported formats (PDF, TXT, CSV, MD) and comprehensive test cases for evaluating document processing, query handling, and response quality.

## Authentication Issues

I'm encountering authentication issues when running the full test suite:

1. The test attempts to authenticate using the `/api/auth/token` endpoint with the following credentials:
   - Username: `testuser`
   - Password: `testpassword`

2. The authentication fails with the error: `{"detail":"Incorrect username or password"}`

3. When the test tries to access protected endpoints like `/api/documents/upload`, it receives a 401 Unauthorized response: `{"detail":"Not authenticated"}`

4. I've verified that the user exists in the system by attempting to register the same username, which returns: `{"detail":"Username or email already exists"}`

## Current Status

- The demo test (`run_metis_rag_e2e_demo.py`) runs successfully as it simulates the document processing and query responses without requiring authentication.
- The full test (`run_metis_rag_e2e_test.py`) fails at the authentication step.

## What I Need Help With

1. **Authentication Troubleshooting**: How can I properly authenticate with the Metis RAG system? The current approach using the TestClient in FastAPI doesn't seem to maintain the authentication state.

2. **Test Client Configuration**: Is there a specific way to configure the TestClient to work with the authentication system in Metis RAG?

3. **Alternative Testing Approaches**: Are there alternative approaches to testing the system that might bypass or simplify the authentication requirements?

4. **API Endpoint Verification**: How can I verify the correct authentication endpoints and required parameters?

## System Information

- The Metis RAG system is running locally at `http://localhost:8000`
- The authentication endpoints appear to be:
  - `/api/auth/register` for user registration
  - `/api/auth/token` for obtaining access tokens
- The system uses JWT-based authentication with tokens

## Test Files Created

1. Test documents in various formats:
   - `data/test_docs/smart_home_technical_specs.pdf`
   - `data/test_docs/smart_home_user_guide.txt`
   - `data/test_docs/smart_home_device_comparison.csv`
   - `data/test_docs/smart_home_developer_reference.md`

2. Test scripts:
   - `tests/test_metis_rag_e2e.py`: Main test script
   - `tests/test_metis_rag_e2e_demo.py`: Demo version without authentication
   - `tests/utils/create_test_pdf.py`: PDF generation utility
   - `run_metis_rag_e2e_test.py`: Runner for the full test
   - `run_metis_rag_e2e_demo.py`: Runner for the demo test

Can you help me resolve these authentication issues and successfully run the full end-to-end test against the actual Metis RAG system?