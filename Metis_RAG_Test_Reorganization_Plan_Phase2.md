# Metis RAG Test Reorganization Plan - Phase 2

This document outlines the next phase of reorganizing and updating the test files in the Metis RAG project to align with the restructured architecture.

## Current Status

We've made good progress with the initial reorganization:
- Created the basic directory structure for tests
- Moved and updated core RAG component tests
- Verified that all moved tests are passing
- Updated documentation to reflect changes

However, there are still several areas that need to be addressed:

1. **Incomplete Directory Structure**:
   - Several app components don't yet have corresponding test directories
   - Missing directories for middleware, models, tasks, utils, etc.

2. **Tests Still at Root Level**:
   - Many test files (20+) still reside at the root `/tests` directory
   - These need to be categorized and moved to appropriate directories

3. **Inconsistent Integration Test Organization**:
   - Some integration tests are still at the root of `/tests/integration`
   - Need to organize based on component interactions

4. **E2E Test Organization**:
   - E2E tests have been partially organized, but still have many files at root level

## Phase 2 Implementation Plan

### Step 1: Complete Unit Test Directory Structure

Create remaining directories for all app components:

```bash
mkdir -p /Users/charleshoward/Metis_RAG/tests/unit/api
mkdir -p /Users/charleshoward/Metis_RAG/tests/unit/cache
mkdir -p /Users/charleshoward/Metis_RAG/tests/unit/core
mkdir -p /Users/charleshoward/Metis_RAG/tests/unit/db/repositories
mkdir -p /Users/charleshoward/Metis_RAG/tests/unit/middleware
mkdir -p /Users/charleshoward/Metis_RAG/tests/unit/models
mkdir -p /Users/charleshoward/Metis_RAG/tests/unit/tasks
mkdir -p /Users/charleshoward/Metis_RAG/tests/unit/utils
```

Create appropriate `conftest.py` files for each directory with relevant fixtures.

### Step 2: Categorize and Move Root Tests

Analyze and categorize each test file at the root level, then move to the appropriate directory:

| File | Component Type | Target Directory |
|------|---------------|-----------------|
| test_chat_api.py | API | tests/unit/api/ |
| test_document_repository.py | Database | tests/unit/db/repositories/ |
| test_background_tasks.py | Tasks | tests/unit/tasks/ |
| test_authentication.py | Auth | tests/unit/middleware/ |
| test_cache.py | Cache | tests/unit/cache/ |
| test_chunking_judge.py | RAG | tests/unit/rag/ |
| test_connection_manager.py | Database | tests/unit/db/ |
| test_csv_json_handler.py | Utils | tests/unit/utils/ |
| test_database_tool_async_concurrent.py | Database | tests/unit/db/ |
| test_database_tool_async.py | Database | tests/unit/db/ |
| test_database_tool_simple.py | Database | tests/unit/db/ |
| test_document_analysis_service.py | Document Analysis | tests/unit/models/ |
| test_mem0_client.py | LLM | tests/unit/rag/ |
| test_memory_buffer.py | Memory | tests/unit/rag/ |
| test_processing_job.py | Document Processing | tests/unit/tasks/ |
| test_prompt_manager.py | LLM | tests/unit/rag/ |
| test_query_planner.py | Query Planning | tests/unit/rag/ |
| test_response_quality.py | Quality | tests/unit/rag/ |
| test_retrieval_judge.py | Retrieval | tests/unit/rag/ |
| test_schema_inspector.py | Database | tests/unit/db/ |
| test_security_utils.py | Security | tests/unit/utils/ |
| test_semantic_chunker.py | Chunking | tests/unit/rag/ |
| test_text_processor.py | Text Processing | tests/unit/utils/ |

### Step 3: Complete Integration Test Structure

Organize integration tests based on component interactions:

```bash
mkdir -p /Users/charleshoward/Metis_RAG/tests/integration/api_db
mkdir -p /Users/charleshoward/Metis_RAG/tests/integration/rag_db
mkdir -p /Users/charleshoward/Metis_RAG/tests/integration/middleware_api
mkdir -p /Users/charleshoward/Metis_RAG/tests/integration/tasks_db
```

Move integration tests to appropriate directories:

| File | Component Interaction | Target Directory |
|------|----------------------|-----------------|
| test_api.py | API | tests/integration/api_db/ |
| test_auth_endpoints.py | Auth | tests/integration/middleware_api/ |
| test_chunking_judge_integration.py | Chunking | tests/integration/rag_api/ |
| test_enhanced_langgraph_rag_integration.py | RAG Engine | tests/integration/rag_api/ |
| test_permissions_db.py | Permissions | tests/integration/api_db/ |
| test_permissions_vector.py | Permissions | tests/integration/rag_db/ |
| test_semantic_chunker_integration.py | Chunking | tests/integration/rag_api/ |

### Step 4: Refactor E2E Tests

Organize E2E tests by user flow or feature:

```bash
mkdir -p /Users/charleshoward/Metis_RAG/tests/e2e/auth
mkdir -p /Users/charleshoward/Metis_RAG/tests/e2e/chat
mkdir -p /Users/charleshoward/Metis_RAG/tests/e2e/document_processing
mkdir -p /Users/charleshoward/Metis_RAG/tests/e2e/permissions
```

Move E2E tests to appropriate directories:

| File | Feature | Target Directory |
|------|---------|-----------------|
| test_auth_flows.py | Auth | tests/e2e/auth/ |
| test_permission_scenarios.py | Permissions | tests/e2e/permissions/ |
| test_metis_rag_e2e.py | RAG | tests/e2e/chat/ |
| test_document_processing_performance.py | Document Processing | tests/e2e/document_processing/ |

### Step 5: Update Test References

1. Ensure imports and pytest discovery still work after moving files
2. Update any CI/CD configuration if needed
3. Run tests to verify everything still works

### Step 6: Update Documentation

1. Update `Metis_RAG_Test_Files_Inventory.md` with new file locations
2. Update `Metis_RAG_Test_Reorganization_Plan.md` with completed tasks
3. Update `Metis_RAG_Restructuring_Checklist.md` to reflect progress

## Implementation Approach

We'll implement this plan in stages:

1. First, create all the necessary directories
2. Move files one category at a time, starting with unit tests
3. Run tests after each category is moved to ensure they still pass
4. Update imports and references as needed
5. Document progress as we go

## Success Criteria

The reorganization will be considered successful when:

1. All test files are in the appropriate directories
2. The directory structure mirrors the application structure
3. All tests pass after reorganization
4. Documentation is updated to reflect the new structure
5. The project follows a consistent testing approach

## Timeline

This phase of the reorganization is expected to take 1-2 weeks, depending on the complexity of the tests and any issues that arise during the process.