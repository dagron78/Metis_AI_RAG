# Retrieval Judge Testing

This directory contains tests and analysis tools for evaluating the effectiveness of the Retrieval Judge component in the Metis RAG system.

## Overview

The Retrieval Judge is an LLM-based agent that enhances the RAG retrieval process by:

1. Analyzing queries to determine optimal retrieval parameters
2. Evaluating retrieved chunks for relevance
3. Refining queries when needed to improve retrieval precision
4. Optimizing context assembly for better response generation

These tests compare standard retrieval against retrieval with the judge enabled to measure the impact and effectiveness of the judge.

## Test Files

- `test_retrieval_judge_comparison.py`: Main test script that compares standard retrieval vs. retrieval with the judge enabled
- `analyze_retrieval_judge_results.py`: Analysis script that processes test results and generates visualizations and recommendations
- `run_tests.sh`: Shell script to run both the comparison test and analysis in sequence
- `run_tests.py`: Python script to run both the comparison test and analysis in sequence
- `IMPLEMENTATION_NOTES.md`: Technical details about the implementation and testing framework

## Directory Structure

- `data/`: Test documents used for retrieval testing
- `results/`: JSON output files from test runs
- `visualizations/`: Generated charts and graphs showing test results

## Running the Tests

### Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install matplotlib numpy
```

### Option 1: Run the Complete Test Suite

The easiest way to run all tests is to use one of the provided runner scripts:

#### Using the Shell Script:

```bash
cd /path/to/Metis_RAG
./tests/retrieval_judge/run_tests.sh
```

#### Using the Python Script:

```bash
cd /path/to/Metis_RAG
python -m tests.retrieval_judge.run_tests
```

Both scripts will run the comparison tests and the analysis in sequence.

### Option 2: Run Tests Individually

#### Step 1: Run the Comparison Test

```bash
cd /path/to/Metis_RAG
python -m tests.retrieval_judge.test_retrieval_judge_comparison
```

This will:
- Create test documents in the `tests/retrieval_judge/data/` directory
- Process these documents and add them to a test vector store
- Run test queries with both standard retrieval and judge-enhanced retrieval
- Save the results to `tests/retrieval_judge/results/retrieval_judge_comparison_results.json`
- Save metrics to `tests/retrieval_judge/results/retrieval_judge_metrics.json`

#### Step 2: Analyze the Results

```bash
cd /path/to/Metis_RAG
python -m tests.retrieval_judge.analyze_retrieval_judge_results
```

This will:
- Load the test results and metrics
- Perform detailed analysis on the effectiveness of the Retrieval Judge
- Generate visualizations in the `tests/retrieval_judge/visualizations/` directory
- Generate recommendations for improving the Retrieval Judge
- Save the analysis report to `tests/retrieval_judge/results/retrieval_judge_analysis_report.json`

## Test Queries

The test includes queries of varying complexity:

1. **Simple factual queries**: Direct questions with clear answers in the documents
2. **Moderate complexity queries**: Questions requiring synthesis of information
3. **Complex analytical queries**: Questions requiring deeper understanding and inference
4. **Ambiguous queries**: Questions with unclear intent or multiple interpretations
5. **Multi-part queries**: Questions that combine multiple distinct information needs

## Analysis Metrics

The analysis evaluates the Retrieval Judge on several dimensions:

1. **Source relevance**: How relevant are the retrieved chunks to the query?
2. **Query refinement effectiveness**: How well does the judge improve ambiguous or complex queries?
3. **Context optimization**: How effectively does the judge select and order chunks?
4. **Performance impact**: What is the processing time overhead of using the judge?

## Customizing Tests

You can modify the test queries or add new ones by editing the `TEST_QUERIES` list in `test_retrieval_judge_comparison.py`.

To test with different documents, you can modify the document content variables (`MARKDOWN_CONTENT`, `PDF_CONTENT`, `TECHNICAL_SPECS_CONTENT`) or add new test documents.

## Interpreting Results

The analysis generates several visualizations to help interpret the results:

1. **Relevance by complexity**: Shows how the judge improves relevance across query types
2. **Source count comparison**: Compares the number of sources retrieved by each method
3. **Processing time comparison**: Shows the performance impact of using the judge
4. **Query refinement effectiveness**: Shows how well the judge handles ambiguous queries

The analysis also generates specific recommendations for improving the Retrieval Judge based on the test results.

## Implementation Details

For more information about the implementation and testing methodology, see the `IMPLEMENTATION_NOTES.md` file in this directory.