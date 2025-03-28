# Metis RAG Testing Framework

This directory contains test scripts for verifying the functionality and quality of the Metis RAG (Retrieval Augmented Generation) system.

## Test Scripts

### Entity Preservation Test (`test_rag_entity_preservation.py`)

This script tests the Metis RAG system's ability to preserve named entities during query refinement, ensure minimum context requirements are met, and handle citations properly.

#### Features

- Creates a test environment with synthetic documents about fictional entities
- Executes a series of increasingly complex queries against the RAG system
- Analyzes the results to verify entity preservation, context selection, and citation handling
- Generates detailed reports for each query and a summary report

#### Usage

```bash
python tests/test_rag_entity_preservation.py
```

#### Test Queries

The test includes five queries of increasing complexity:

1. **Basic Entity Query**: "Tell me about Stabilium and its applications in quantum computing."
2. **Multi-Entity Query**: "Compare the properties of Stabilium and Quantum Resonance Modulation in cold fusion experiments."
3. **Query with Potential Ambiguity**: "What are the differences between Stabilium QRM-12X and earlier versions?"
4. **Query Requiring Context Synthesis**: "How does Stabilium interact with Heisenberg's Uncertainty Principle when used in quantum entanglement experiments?"
5. **Query with Specialized Terminology**: "Explain the role of Stabilium in facilitating quantum tunneling through non-Euclidean space-time manifolds."

#### Results

The test generates the following outputs:

- Individual query reports in `tests/results/query_<query_id>/report.md`
- A summary report in `tests/results/summary_report.md`
- Detailed logs in `tests/results/entity_preservation_test_results.log`

## Lessons Learned

During the development and testing of the Metis RAG system, we encountered several important insights:

1. **Log-Based Metrics Extraction**: The RAG engine doesn't directly expose metrics like chunks retrieved and used in its response. We had to implement a custom log handler to capture and extract this information from log messages. This approach is more robust than trying to modify the core RAG engine to expose these metrics directly.

2. **Entity Preservation Importance**: Our tests confirmed that preserving named entities during query refinement is critical for maintaining the user's intent. The system successfully identified and preserved entities like "Stabilium", "Heisenberg's Uncertainty Principle", and "QRM-12X" even when refining queries.

3. **Context Selection Trade-offs**: The tests revealed that the system retrieves many chunks (15) but uses only a subset (3-6) in the final context. This selective approach balances comprehensive information retrieval with focused, relevant responses.

4. **Retrieval Judge Effectiveness**: The Retrieval Judge component successfully refined queries and optimized context assembly, demonstrating its value in improving RAG quality. For example, it refined the basic query to focus on specific applications of Stabilium in quantum computing.

5. **Testing with Fictional Entities**: Using fictional entities (like Stabilium) for testing proved effective as it allowed us to create controlled test cases without relying on external knowledge. This approach ensures tests are reproducible and focused on system behavior rather than factual accuracy.

6. **Importance of Detailed Logging**: Comprehensive logging was essential for debugging and understanding the system's behavior. The logs provided insights into query refinement, chunk selection, and context optimization that weren't visible in the final response.

These lessons have informed our approach to RAG system development and testing, leading to more robust and effective implementations.