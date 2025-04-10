# Metis RAG File Structure Reorganization Proposal

## Current Issues

The root directory of the Metis RAG project contains numerous files of different types and purposes, making it difficult to navigate and understand the project structure. This proposal aims to reorganize these files into a more logical and maintainable structure.

## Proposed Directory Structure

```
metis_rag/
├── app/                      # Main application code (existing structure)
├── config/                   # Configuration files
│   ├── .env.example
│   ├── docker-compose.yml
│   └── requirements.txt
├── docs/                     # Documentation
│   ├── implementation/       # Implementation plans and technical details
│   │   ├── llm_enhanced_rag_implementation_plan.md
│   │   ├── mem0_integration_plan.md
│   │   └── langgraph_integration.md
│   ├── setup/                # Setup and improvement plans
│   │   ├── Metis_RAG_Setup_Plan.md
│   │   └── Metis_RAG_Improvement_Plan.md
│   ├── technical/            # Technical documentation
│   │   ├── technical_documentation.md
│   │   └── TESTING.md
│   └── demos/                # Demo documentation
│       ├── Metis_RAG_Technical_Demo.md
│       └── Metis_RAG_Technical_Demo.html
├── scripts/                  # Utility scripts
│   ├── maintenance/          # Maintenance scripts
│   │   ├── clear_cache.py
│   │   ├── clear_database.py
│   │   └── reprocess_documents.py
│   ├── generation/           # Data generation scripts
│   │   ├── generate_pdf.py
│   │   └── generate_test_data.py
│   └── demo/                 # Demo scripts
│       ├── demo_presentation.py
│       └── demo_tests.py
├── tests/                    # Test code and data
│   ├── integration/          # Integration tests (existing)
│   ├── unit/                 # Unit tests (existing)
│   ├── retrieval_judge/      # Retrieval judge tests (existing)
│   ├── data/                 # Test data files
│   │   ├── test_data.csv
│   │   ├── test_document.txt
│   │   └── sample_report.pdf
│   └── results/              # Test results
│       ├── chunking_judge_results/
│       │   ├── chunking_judge_real_results.json
│       │   └── chunking_judge_test_results.json
│       ├── retrieval_results/
│       │   ├── test_citation_results.json
│       │   ├── test_multi_doc_results.json
│       │   └── test_response_time_results.json
│       └── quality_results/
│           ├── test_quality_results.json
│           └── metis_rag_test_report.json
├── data/                     # Application data
│   ├── chroma_db/            # Vector database
│   ├── uploads/              # User uploads
│   ├── test_docs/            # Test documents
│   ├── test_perf_chroma/     # Performance test database
│   └── test_quality_chroma/  # Quality test database
├── .env                      # Environment variables (not in version control)
├── .gitignore                # Git ignore file
├── Dockerfile                # Docker configuration
├── pyproject.toml            # Python project configuration
├── README.md                 # Project README
└── run_tests.py              # Main test runner script
```

## Migration Plan

1. **Create the new directory structure**:
   ```bash
   mkdir -p config docs/{implementation,setup,technical,demos} scripts/{maintenance,generation,demo} tests/{data,results/{chunking_judge_results,retrieval_results,quality_results}} data
   ```

2. **Move configuration files**:
   ```bash
   mv .env.example docker-compose.yml requirements.txt config/
   ```

3. **Move documentation files**:
   ```bash
   mv llm_enhanced_rag_implementation_plan*.md mem0_integration_plan.md docs/implementation/
   mv Metis_RAG_*Plan.md docs/setup/
   mv technical_documentation.md TESTING.md docs/technical/
   mv Metis_RAG_Technical_Demo.* docs/demos/
   ```

4. **Move utility scripts**:
   ```bash
   mv clear_*.py reprocess_documents.py scripts/maintenance/
   mv generate_*.py scripts/generation/
   mv demo_*.py scripts/demo/
   ```

5. **Move test data and results**:
   ```bash
   mv test_data.csv test_document.txt sample_report.pdf tests/data/
   mv chunking_judge*results.json tests/results/chunking_judge_results/
   mv test_citation_results.json test_multi_doc_results.json test_response_time_results.json tests/results/retrieval_results/
   mv test_quality_results.json metis_rag_test_report.json tests/results/quality_results/
   mv metis_rag_test_report.html tests/results/
   ```

6. **Move data directories**:
   ```bash
   mv chroma_db/ uploads/ test_docs/ test_perf_chroma/ test_quality_chroma/ data/
   ```

7. **Update import paths and file references** in Python code to reflect the new structure.

8. **Update documentation** to reference the new file locations.

## Benefits of the New Structure

1. **Improved Navigation**: Files are organized by purpose, making it easier to find what you're looking for.

2. **Better Maintainability**: Related files are grouped together, making maintenance and updates more straightforward.

3. **Cleaner Root Directory**: The root directory contains only the most essential files, reducing clutter.

4. **Logical Grouping**: Files are grouped by their function and relationship to each other.

5. **Scalability**: The structure can easily accommodate new files and components as the project grows.

6. **Better Onboarding**: New developers can more quickly understand the project structure and find relevant files.

## Implementation Considerations

1. **Path Updates**: Scripts and code that reference files by path will need to be updated to reflect the new structure.

2. **Documentation Updates**: Documentation should be updated to reference the new file locations.

3. **Gradual Migration**: The migration can be done gradually, starting with the most disorganized areas.

4. **Version Control**: The reorganization should be done in a separate branch and thoroughly tested before merging.

5. **Docker Configuration**: If using Docker, the Dockerfile and docker-compose.yml may need updates to reflect the new paths.

## Next Steps

1. Review this proposal and make any necessary adjustments.
2. Create a new git branch for the reorganization.
3. Implement the directory structure changes.
4. Update file paths in code and documentation.
5. Test the application to ensure everything works correctly.
6. Merge the changes into the main branch.