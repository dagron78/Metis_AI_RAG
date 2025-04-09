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

## Phase 5: Complete Directory Structure (In Progress)

1. Created remaining unit test directories ✅
   - Created `tests/unit/api/`
   - Created `tests/unit/cache/`
   - Created `tests/unit/core/`
   - Created `tests/unit/db/repositories/`
   - Created `tests/unit/middleware/`
   - Created `tests/unit/models/`
   - Created `tests/unit/tasks/`
   - Created `tests/unit/utils/`

2. Created integration test directories ✅
   - Created `tests/integration/api_db/`
   - Created `tests/integration/rag_db/`
   - Created `tests/integration/middleware_api/`
   - Created `tests/integration/tasks_db/`

3. Created E2E test directories ✅
   - Created `tests/e2e/auth/`
   - Created `tests/e2e/chat/`
   - Created `tests/e2e/document_processing/`
   - Created `tests/e2e/permissions/`

4. Created conftest.py files for each directory ✅
   - Added appropriate fixtures for each test type
   - Ensured proper mocking of dependencies
   - Set up database fixtures for integration and E2E tests

## Next Steps

### Phase 6: Move Remaining Tests (Not Started)

1. Categorize and move remaining unit tests
   - Analyze each test file to determine the appropriate directory
   - Move files to the correct location
   - Update imports as needed
   - Run tests to verify functionality

2. Categorize and move remaining integration tests
   - Analyze each test file to determine the appropriate directory
   - Move files to the correct location
   - Update imports as needed
   - Run tests to verify functionality

3. Categorize and move remaining E2E tests
   - Analyze each test file to determine the appropriate directory
   - Move files to the correct location
   - Update imports as needed
   - Run tests to verify functionality

### Phase 7: Final Verification (Not Started)

1. Run all tests to ensure they pass
2. Update documentation to reflect the final structure
3. Create a migration guide for developers

## Tracking Progress

| Phase | Total Files | Completed | In Progress | Not Started |
|-------|------------|-----------|-------------|-------------|
| Create Directory Structure | N/A | 1 | 0 | 0 |
| Unit Tests | 25 | 6 | 0 | 19 |
| Integration Tests | 8 | 1 | 0 | 7 |
| E2E Tests | 2 | 0 | 0 | 2 |
| Legacy Tests | 18 | 0 | 0 | 18 |
| Complete Directory Structure | 18 | 18 | 0 | 0 |
| Move Remaining Tests | 47 | 0 | 0 | 47 |
| Final Verification | N/A | 0 | 0 | 1 |
| **Total** | **100** | **26** | **0** | **74** |