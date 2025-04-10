# Metis RAG Important Tests

This document outlines the most important tests for the Metis RAG system, organized in a logical execution order that builds from core components to complete system testing.

## Test Execution Order

The tests are organized into five categories, with each category building on the previous one:

1. **Core Component Unit Tests** - Test individual components in isolation
2. **Component Integration Tests** - Verify that components work correctly together
3. **Feature-Level Tests** - Test complete features that users interact with
4. **End-to-End Tests** - Test full flows that simulate real user scenarios
5. **Performance and Edge Case Tests** - Test performance and special cases

This approach helps identify issues at the lowest level possible, making debugging easier. If a basic component test fails, there's no need to run the higher-level tests that depend on it until that issue is fixed.

## Running the Tests

### Using the Shell Script

The easiest way to run the tests is using the provided shell script:

```bash
# Run all tests in order
./scripts/run_important_tests.sh

# Run only a specific section (1-5)
./scripts/run_important_tests.sh -s 1

# Show more detailed output
./scripts/run_important_tests.sh -v

# Show help
./scripts/run_important_tests.sh --help
```

### Using the Python Script Directly

You can also run the Python script directly:

```bash
# Activate the virtual environment
source venv_py310/bin/activate

# Run the script
python scripts/run_important_tests.py
```

## Test Log

The test execution creates a log file `test_execution_log.txt` in the current directory, which contains detailed information about each test run, including:

- Start and end times
- Test results (pass/fail)
- Standard output and error messages
- Summary of failed tests

## Test Categories and Files

### 1. Core Component Unit Tests

```
/tests/unit/rag/engine/test_rag_engine.py                # Core RAG engine
/tests/unit/test_security_utils.py                       # Security fundamentals
/tests/unit/test_text_formatting.py                      # Text formatting components
/tests/unit/db/test_db_connection.py                     # Database connection
/tests/unit/db/repositories/test_document_repository.py  # Document repository
/tests/unit/rag/test_query_analyzer.py                   # Query analysis
/tests/unit/rag/tools/test_rag_tool.py                   # RAG tools
/tests/unit/middleware/test_authentication.py            # Authentication middleware
```

### 2. Component Integration Tests

```
/tests/integration/test_chunking_judge_integration.py    # Document chunking integration
/tests/integration/rag_api/test_langgraph_rag_agent.py   # LangGraph RAG agent
/tests/integration/test_permissions_db.py                # Database permissions
/tests/integration/test_auth_endpoints.py                # Authentication endpoints
/tests/integration/tasks_db/test_simplified_document_processing_with_db.py  # Document processing with DB
```

### 3. Feature-Level Tests

```
/tests/unit/utils/test_code_formatting.py                # Code formatting features
/tests/unit/api/test_chat_api.py                         # Chat API functionality
/tests/unit/api/test_document_upload.py                  # Document upload features
/tests/integration/test_permissions_vector.py            # Vector store permissions
```

### 4. End-to-End Tests

```
/tests/e2e/document_processing/test_document_processing_performance.py  # Document processing E2E
/tests/e2e/auth/test_auth_flows.py                       # Authentication flows E2E
/tests/e2e/chat/test_metis_rag_e2e.py                    # Complete RAG system E2E
```

### 5. Performance and Edge Case Tests

```
/tests/unit/test_memory_buffer.py                        # Memory management
/tests/e2e/chat/test_metis_rag_e2e_demo.py               # Demo scenario testing
```

## Troubleshooting

If tests are failing, check the following:

1. Make sure all dependencies are installed
2. Verify that the database is properly set up
3. Check that any required environment variables are set
4. Look at the detailed log file for specific error messages

For persistent issues, consider running individual tests with increased verbosity:

```bash
python -m pytest tests/unit/test_security_utils.py -v