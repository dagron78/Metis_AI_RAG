# Metis RAG End-to-End Test

This directory contains an end-to-end test for the Metis RAG system. The test evaluates the complete pipeline from document upload and processing to query response generation and evaluation.

## Test Components

The end-to-end test consists of the following components:

1. **Test Documents**: Sample documents in all supported formats (PDF, TXT, CSV, MD) containing complementary information about a fictional "SmartHome" system.
   - `smart_home_technical_specs.txt`/`.pdf` - Technical specifications (PDF generated from TXT)
   - `smart_home_user_guide.txt` - User guide and troubleshooting
   - `smart_home_device_comparison.csv` - Structured device data
   - `smart_home_developer_reference.md` - API documentation

2. **PDF Generation Utility**: A script to convert the technical specifications from text to PDF.
   - `tests/utils/create_test_pdf.py`

3. **End-to-End Test Script**: The main test script that runs all test cases.
   - `tests/test_metis_rag_e2e.py`

4. **Test Runner**: A runner script that sets up the environment and executes the test.
   - `run_metis_rag_e2e_test.py`

## Test Coverage

The end-to-end test evaluates:

- Document upload and processing for all supported file formats
- Chunking and embedding functionality
- Single-document query processing
- Multi-document (cross-document) retrieval
- Complex queries requiring synthesis
- Response quality and factual accuracy
- Citation quality
- System performance

## Prerequisites

- Python 3.8+
- ReportLab library (for PDF generation)
- Access to an instance of the Metis RAG system

## Running the Test

### Option 1: Using the Test Runner

The simplest way to run the test is to use the provided runner script:

```bash
python run_metis_rag_e2e_test.py
```

This script will:
1. Check and install required dependencies
2. Create necessary directories
3. Generate the PDF file from the text file
4. Run the end-to-end test
5. Collect and organize the test results

### Option 2: Running Individual Components

If you prefer to run the components individually:

1. Generate the PDF:
```bash
python tests/utils/create_test_pdf.py
```

2. Run the test:
```bash
pytest -xvs tests/test_metis_rag_e2e.py
```

## Test Results

The test generates several JSON result files with detailed information about each aspect of the testing:

- `test_e2e_upload_results.json` - Document upload and processing results
- `test_e2e_single_doc_results.json` - Single-document query results
- `test_e2e_multi_doc_results.json` - Multi-document query results
- `test_e2e_complex_results.json` - Complex query results
- `test_e2e_citation_results.json` - Citation quality results
- `test_e2e_performance_results.json` - Performance metrics
- `test_e2e_comprehensive_report.json` - Comprehensive report combining all results

All result files are moved to the `test_results` directory after test execution.

## Test Structure

The test follows this structure:

1. **Setup**: Create test directories and files
2. **Document Upload**: Upload all test documents to the system
3. **Document Processing**: Process the uploaded documents for RAG
4. **Query Testing**:
   - Test single-document queries
   - Test multi-document queries
   - Test complex queries
5. **Quality Assessment**:
   - Evaluate factual accuracy
   - Evaluate citation quality
6. **Performance Testing**: Measure system performance
7. **Cleanup**: Remove test documents and generate final report

## Modifying the Test

To modify the test for specific needs:

- Add or modify test documents in the `data/test_docs` directory
- Update the `TEST_DOCUMENTS` dictionary in `test_metis_rag_e2e.py`
- Add or modify test queries in the query test cases
- Adjust the expected facts for the queries

## Troubleshooting

### Common Issues

1. **PDF Generation Fails**:
   - Ensure ReportLab is installed: `pip install reportlab`
   - Check if the text file exists at the expected location

2. **Document Upload Fails**:
   - Verify the Metis RAG system is running
   - Check API endpoints are accessible
   - Ensure all test files exist in the correct locations

3. **Tests Fail with Low Factual Accuracy**:
   - Check that the documents contain the expected information
   - Verify the expected facts in the test cases match the document content
   - Check that the RAG system is properly configured for retrieval

4. **Authentication Issues**:
   - See the detailed troubleshooting guide in `authentication_setup_guide.md`
   - Try using the direct API testing approach described below

## Alternative Testing Approach: Direct API Testing

If you encounter authentication issues with the TestClient approach, we provide an alternative testing method that uses direct API calls:

### Option 3: Using the Direct API Test

```bash
python run_api_test.py
```

This approach:
- Requires the Metis RAG API to be running (`python -m uvicorn app.main:app --reload`)
- Uses the requests library instead of TestClient
- Properly handles authentication
- Avoids event loop conflicts

### Direct API Test Components

1. **API Test Script**: Tests the API directly using HTTP requests.
   - `scripts/test_api_directly.py`

2. **API Test Runner**: A runner script that checks if the API is running and executes the test.
   - `run_api_test.py`

### Direct API Test Results

The direct API test generates these result files:
- `api_test_upload_results.json` - Document upload and processing results
- `api_test_query_results.json` - Query results

All result files are saved to the `test_results` directory.

For detailed information about authentication issues and solutions, please refer to `tests/authentication_setup_guide.md`.