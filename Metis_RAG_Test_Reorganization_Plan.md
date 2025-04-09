# Metis RAG Test Reorganization Plan

This document outlines the plan for reorganizing and updating the test files in the Metis RAG project to align with the restructured architecture.

## Current Status

Based on our inventory in `Metis_RAG_Test_Files_Inventory.md`, we have identified:
- 56 test files across various directories
- 3 files already using the new import structure
- 1 file that needs import updates
- 45 files that need further review
- 7 files that have been updated and moved to the new structure

## Reorganization Approach

We are following a test-type-first organization that better mirrors the application structure:

```
/tests
├── conftest.py                  # Global fixtures
├── unit/                        # Unit tests matching app structure
│   ├── api/                     # Tests for app/api modules
│   ├── rag/                     # Tests for app/rag modules
│   │   ├── agents/              # Tests for app/rag/agents
│   │   ├── engine/              # Tests for app/rag/engine
│   │   └── tools/               # Tests for app/rag/tools
│   ├── db/                      # Tests for app/db modules
│   └── utils/                   # Tests for app/utils modules
├── integration/                 # Tests across component boundaries
│   ├── api_db/                  # API and database integration
│   ├── rag_db/                  # RAG and database integration
│   └── rag_api/                 # RAG and API integration
├── e2e/                         # Complete system tests
├── data/                        # Test data shared across tests
└── utils/                       # Test utilities and helpers
```

## Implementation Progress

### Phase 1: Create New Directory Structure ✅

1. Created the new directory structure while maintaining the existing one
2. Set up appropriate `conftest.py` files in each directory

### Phase 2: Update Unit Tests (Completed) ✅

1. RAG Engine tests ✅
   - Moved `tests/unit/test_rag_engine.py` to `tests/unit/rag/engine/test_rag_engine.py`
   - Updated imports to use the new structure

2. Query Analysis tests ✅
   - Moved `tests/unit/test_query_analyzer.py` to `tests/unit/rag/test_query_analyzer.py`
   - Updated imports to use the new structure

3. Process Logger tests ✅
   - Moved `tests/unit/test_process_logger.py` to `tests/unit/rag/test_process_logger.py`
   - Updated imports to use the new structure

4. Plan Executor tests ✅
   - Moved `tests/unit/test_plan_executor.py` to `tests/unit/rag/test_plan_executor.py`
   - Updated imports to use the new structure

5. Tool tests ✅
   - Split `tests/unit/test_tools.py` into multiple files in `tests/unit/rag/tools/`
   - Created separate test files for each tool type:
     - `tests/unit/rag/tools/test_registry.py`
     - `tests/unit/rag/tools/test_rag_tool.py`
     - `tests/unit/rag/tools/test_calculator_tool.py`
     - `tests/unit/rag/tools/test_database_tool.py`
   - Updated imports to use the new structure

6. Text Formatting tests (Deferred)
   - Will be addressed in a separate task

### Phase 3: Update Integration Tests (Completed) ✅

1. LangGraph RAG integration tests ✅
   - Moved `tests/integration/test_langgraph_rag_integration.py` to `tests/integration/rag_api/test_langgraph_rag_agent.py`
   - Updated imports to use the new structure

### Phase 4: Verification (Completed) ✅

1. Ran all tests to ensure they pass ✅
   - All 34 tests are passing
   - Fixed issues with the RAG engine tests
   - Updated mock objects to work with the new architecture
   - Ensured proper async behavior in tests

2. Updated documentation to reflect the new structure ✅
   - Updated `Metis_RAG_Test_Files_Inventory.md`
   - Updated `Metis_RAG_Test_Reorganization_Plan.md`

## Next Steps

1. Continue with the remaining test files in a future task:
   - Remaining unit tests
   - Remaining integration tests
   - E2E tests
   - Legacy tests

2. Focus on the unit tests first, then integration tests

3. Update the test inventory and reorganization plan as we progress

## Tracking Progress

| Phase | Total Files | Completed | In Progress | Not Started |
|-------|------------|-----------|-------------|-------------|
| Create Directory Structure | N/A | 1 | 0 | 0 |
| Unit Tests | 25 | 6 | 0 | 19 |
| Integration Tests | 8 | 1 | 0 | 7 |
| E2E Tests | 2 | 0 | 0 | 2 |
| Legacy Tests | 18 | 0 | 0 | 18 |
| Verification | N/A | 1 | 0 | 0 |
| **Total** | **53** | **9** | **0** | **44** |