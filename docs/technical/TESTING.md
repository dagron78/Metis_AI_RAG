# Metis RAG Testing Strategy

This document outlines the comprehensive testing strategy for the Metis RAG application, covering automated unit tests, integration tests, performance benchmarks, UI testing, and more.

## Table of Contents

1. [Testing Objectives](#testing-objectives)
2. [Testing Levels](#testing-levels)
3. [Test Implementation](#test-implementation)
4. [Running Tests](#running-tests)
5. [Test Reports](#test-reports)
6. [CI/CD Integration](#cicd-integration)

## Testing Objectives

The primary objectives of this testing strategy are to:

1. Ensure the factual accuracy and quality of RAG responses
2. Verify proper handling of various file types and multiple file uploads
3. Test core RAG components (retrieval, augmentation, generation)
4. Validate end-to-end functionality across system boundaries
5. Measure and optimize performance
6. Identify and address edge cases and potential failure points
7. Establish regression testing to prevent feature regressions
8. Generate detailed test reports for demonstration purposes

## Testing Levels

### Unit Testing

Unit tests focus on testing individual components in isolation:

- **RAG Engine Testing**: Tests query function, context retrieval, response generation, conversation history handling, and citation generation.
- **Vector Store Testing**: Tests document addition and retrieval, embedding creation and storage, search functionality, metadata filtering, and caching mechanisms.
- **Document Processor Testing**: Tests different chunking strategies, handling of various file types, metadata extraction, and error handling.
- **Ollama Client Testing**: Tests model generation, embedding creation, streaming vs. non-streaming responses, and error handling.

### Integration Testing

Integration tests focus on testing component interactions and API endpoints:

- **API Endpoint Testing**: Tests all API endpoints for correct responses, error handling, request validation, and authentication.
- **Component Interaction Testing**: Tests RAG Engine with Vector Store, Document Processor with Vector Store, RAG Engine with Ollama Client, and end-to-end document processing and retrieval flow.

### System Testing

System tests focus on testing end-to-end workflows and performance:

- **End-to-End Workflow Testing**: Tests complete document upload, processing, and retrieval workflow, chat conversation with context from multiple documents, and analytics functionality.
- **Performance Testing**: Measures response time, throughput, and resource utilization under various loads.
- **Stress Testing**: Tests with high concurrency, large document sets, and complex queries.

### Edge Case Testing

Edge case tests focus on testing unusual inputs, error handling, and system resilience:

- **Input Validation**: Tests with malformed queries, invalid documents, and extremely long or short inputs.
- **Error Handling**: Tests network failures, service unavailability, and database connection issues.
- **Resource Constraints**: Tests under memory limitations, limited disk space, and CPU constraints.

## Test Implementation

The test implementation is organized into several test suites:

### RAG Quality Tests (`tests/test_rag_quality.py`)

Tests for factual accuracy, relevance, and citation quality:

- **Factual Accuracy Testing**: Tests if responses contain expected facts from the source documents.
- **Multi-Document Retrieval**: Tests retrieval across multiple documents.
- **Citation Quality**: Tests if responses properly cite sources.
- **API Integration**: Tests the complete flow through the API endpoints.

### File Handling Tests (`tests/test_file_handling.py`)

Tests for different file types, multiple file uploads, and large files:

- **File Type Support**: Tests processing of different file types (PDF, TXT, CSV, MD).
- **Chunking Strategies**: Tests different chunking strategies (recursive, token, markdown).
- **Large File Handling**: Tests processing of very large files.
- **Multiple File Upload**: Tests concurrent processing of multiple documents.

### Performance Tests (`tests/test_performance.py`)

Tests for response time, throughput, and resource utilization:

- **Query Response Time**: Measures response time for different query types.
- **Throughput**: Measures throughput under various concurrency levels.
- **Resource Utilization**: Monitors CPU and memory usage during sustained load.
- **API Performance**: Measures performance of API endpoints.

### Edge Case Tests (`tests/test_edge_cases.py`)

Tests for unusual inputs, error handling, and system resilience:

- **Special Character Queries**: Tests queries with special characters, SQL injection, XSS, etc.
- **Malformed Documents**: Tests handling of malformed or corrupted documents.
- **Network Failures**: Tests handling of network failures when communicating with Ollama.
- **Invalid Model Names**: Tests handling of invalid model names.
- **Concurrent Processing**: Tests handling of concurrent document processing requests.
- **Vector Store Resilience**: Tests vector store resilience to invalid operations.

## Running Tests

### Prerequisites

- Python 3.10 or higher
- All dependencies installed (`pip install -r requirements.txt`)
- Ollama running locally (for tests that interact with the LLM)

### Running All Tests

To run all tests, use the `run_tests.py` script:

```bash
python run_tests.py
```

This will run all test suites and generate a comprehensive report.

### Running Specific Test Suites

To run a specific test suite, use the `--suite` option:

```bash
python run_tests.py --suite rag_quality
python run_tests.py --suite file_handling
python run_tests.py --suite performance
python run_tests.py --suite edge_cases
```

### Additional Options

- `--failfast`: Stop on first failure
- `--open-report`: Open the HTML report in a browser
- `--save-reports`: Save reports to a timestamped directory

### Running Individual Tests

You can also run individual test files directly using pytest:

```bash
pytest -xvs tests/test_rag_quality.py
pytest -xvs tests/test_file_handling.py
pytest -xvs tests/test_performance.py
pytest -xvs tests/test_edge_cases.py
```

## Test Reports

The test runner generates several reports:

- **Master Report**: `metis_rag_test_report.json` and `metis_rag_test_report.html`
- **RAG Quality Reports**: `test_quality_results.json`, `test_multi_doc_results.json`, etc.
- **File Handling Reports**: `test_file_type_results.json`, `test_chunking_strategy_results.json`, etc.
- **Performance Reports**: `performance_benchmark_report.json`, `performance_benchmark_report.html`, etc.
- **Edge Case Reports**: `edge_case_test_report.json`, `edge_case_test_report.html`, etc.

These reports provide detailed information about test results, including:

- Test success/failure status
- Performance metrics
- Factual accuracy metrics
- Edge case handling metrics
- Detailed logs and error messages

## CI/CD Integration

The testing framework is designed to be integrated into a CI/CD pipeline. Here's a recommended approach:

1. **Continuous Integration**: Run unit and integration tests on every commit.
2. **Nightly Builds**: Run performance and edge case tests nightly.
3. **Release Validation**: Run all tests before releasing a new version.

### GitHub Actions Example

```yaml
name: Metis RAG Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python run_tests.py
    - name: Upload test reports
      uses: actions/upload-artifact@v2
      with:
        name: test-reports
        path: |
          metis_rag_test_report.html
          performance_benchmark_report.html
          edge_case_test_report.html
```

## Extending the Test Suite

To add new tests:

1. Create a new test file in the `tests` directory.
2. Add the test file to the appropriate test suite in `run_tests.py`.
3. Implement test functions using the pytest framework.
4. Generate test reports in JSON format for integration with the reporting system.

## Best Practices

- **Isolation**: Ensure tests are isolated and don't depend on each other.
- **Cleanup**: Clean up any resources created during tests.
- **Mocking**: Use mocks for external dependencies when appropriate.
- **Assertions**: Use clear assertions that provide helpful error messages.
- **Documentation**: Document test functions with clear docstrings.
- **Reporting**: Generate detailed reports for analysis and visualization.