# Metis RAG Test Files Inventory

This document provides a comprehensive inventory of all test files in the Metis RAG project, categorized by component type and test type, with an assessment of the required actions for each file.

## Action Categories

- **Update Imports**: The file needs to have its import statements updated to match the new structure
- **Move to Legacy**: The file should be moved to the appropriate legacy directory
- **Rewrite**: The file needs to be rewritten to work with the new architecture
- **No Changes**: The file is already using the new import structure
- **Completed**: The file has been updated and moved to the new location

## Unit Tests

| File | Component Type | Current Import Pattern | Required Action | Status |
|------|---------------|------------------------|----------------|--------|
| tests/unit/test_rag_engine.py | RAG Engine | `from app.rag.engine.rag_engine import RAGEngine` | Completed | Moved to tests/unit/rag/engine/test_rag_engine.py |
| tests/unit/test_text_formatting.py | Text Formatting | `from app.utils.text_formatting.formatters.code_formatter import CodeFormatter` | No Changes | Not Started |
| tests/unit/test_query_analyzer.py | Query Analysis | `from app.rag.query_analyzer import QueryAnalyzer` | Completed | Moved to tests/unit/rag/test_query_analyzer.py |
| tests/unit/test_process_logger.py | Process Logger | `from app.rag.process_logger import ProcessLogger` | Completed | Moved to tests/unit/rag/test_process_logger.py |
| tests/unit/test_plan_executor.py | Plan Executor | `from app.rag.plan_executor import PlanExecutor` | Completed | Moved to tests/unit/rag/test_plan_executor.py |
| tests/unit/test_tools.py | Tools | `from app.rag.tools import Tool, ToolRegistry, RAGTool, CalculatorTool, DatabaseTool` | Completed | Split into multiple files in tests/unit/rag/tools/ |
| tests/unit/test_cache.py | Cache | Unknown | Needs Review | Not Started |
| tests/unit/test_chunking_judge.py | Chunking | Unknown | Needs Review | Not Started |
| tests/unit/test_connection_manager.py | Database | Unknown | Needs Review | Not Started |
| tests/unit/test_csv_json_handler.py | Utils | Unknown | Needs Review | Not Started |
| tests/unit/test_database_tool_async_concurrent.py | Database | Unknown | Needs Review | Not Started |
| tests/unit/test_database_tool_async.py | Database | Unknown | Needs Review | Not Started |
| tests/unit/test_database_tool_simple.py | Database | Unknown | Needs Review | Not Started |
| tests/unit/test_document_analysis_service.py | Document Analysis | Unknown | Needs Review | Not Started |
| tests/unit/test_mem0_client.py | LLM | Unknown | Needs Review | Not Started |
| tests/unit/test_memory_buffer.py | Memory | Unknown | Needs Review | Not Started |
| tests/unit/test_processing_job.py | Document Processing | Unknown | Needs Review | Not Started |
| tests/unit/test_prompt_manager.py | LLM | Unknown | Needs Review | Not Started |
| tests/unit/test_query_planner.py | Query Planning | Unknown | Needs Review | Not Started |
| tests/unit/test_response_quality.py | Quality | Unknown | Needs Review | Not Started |
| tests/unit/test_retrieval_judge.py | Retrieval | Unknown | Needs Review | Not Started |
| tests/unit/test_schema_inspector.py | Database | Unknown | Needs Review | Not Started |
| tests/unit/test_security_utils.py | Security | Unknown | Needs Review | Not Started |
| tests/unit/test_semantic_chunker.py | Chunking | Unknown | Needs Review | Not Started |
| tests/unit/test_text_processor.py | Text Processing | Unknown | Needs Review | Not Started |

## New Unit Tests

| File | Component Type | Import Pattern | Status |
|------|---------------|----------------|--------|
| tests/unit/rag/engine/test_rag_engine.py | RAG Engine | `from app.rag.engine.rag_engine import RAGEngine` | Completed |
| tests/unit/rag/test_query_analyzer.py | Query Analysis | `from app.rag.query_analyzer import QueryAnalyzer` | Completed |
| tests/unit/rag/test_process_logger.py | Process Logger | `from app.rag.process_logger import ProcessLogger` | Completed |
| tests/unit/rag/test_plan_executor.py | Plan Executor | `from app.rag.plan_executor import PlanExecutor` | Completed |
| tests/unit/rag/tools/test_registry.py | Tool Registry | `from app.rag.tools import ToolRegistry` | Completed |
| tests/unit/rag/tools/test_rag_tool.py | RAG Tool | `from app.rag.tools import RAGTool` | Completed |
| tests/unit/rag/tools/test_calculator_tool.py | Calculator Tool | `from app.rag.tools import CalculatorTool` | Completed |
| tests/unit/rag/tools/test_database_tool.py | Database Tool | `from app.rag.tools import DatabaseTool` | Completed |

## Integration Tests

| File | Component Type | Current Import Pattern | Required Action | Status |
|------|---------------|------------------------|----------------|--------|
| tests/integration/test_langgraph_rag_integration.py | RAG Engine | `from app.rag.agents.langgraph_rag_agent import LangGraphRAGAgent` <br> `from app.rag.vector_store import VectorStore` <br> `from app.rag.ollama_client import OllamaClient` | Completed | Moved to tests/integration/rag_api/test_langgraph_rag_agent.py |
| tests/integration/test_api.py | API | Unknown | Needs Review | Not Started |
| tests/integration/test_auth_endpoints.py | Auth | Unknown | Needs Review | Not Started |
| tests/integration/test_chunking_judge_integration.py | Chunking | Unknown | Needs Review | Not Started |
| tests/integration/test_enhanced_langgraph_rag_integration.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/integration/test_permissions_db.py | Permissions | Unknown | Needs Review | Not Started |
| tests/integration/test_permissions_vector.py | Permissions | Unknown | Needs Review | Not Started |
| tests/integration/test_semantic_chunker_integration.py | Chunking | Unknown | Needs Review | Not Started |

## New Integration Tests

| File | Component Type | Import Pattern | Status |
|------|---------------|----------------|--------|
| tests/integration/rag_api/test_langgraph_rag_agent.py | RAG Engine | `from app.rag.agents.langgraph_rag_agent import LangGraphRAGAgent` | Completed |

## E2E Tests

| File | Component Type | Current Import Pattern | Required Action | Status |
|------|---------------|------------------------|----------------|--------|
| tests/e2e/test_auth_flows.py | Auth | Unknown | Needs Review | Not Started |
| tests/e2e/test_permission_scenarios.py | Permissions | Unknown | Needs Review | Not Started |

## Legacy Tests

| File | Component Type | Current Import Pattern | Required Action | Status |
|------|---------------|------------------------|----------------|--------|
| tests/legacy/test_text_formatting.py | Text Formatting | `from app.utils.text_processor import normalize_text, format_code_blocks` <br> `from app.rag.rag_generation import GenerationMixin` | Update Imports | Not Started |
| tests/legacy/test_edge_cases.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/legacy/test_fixes.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/legacy/test_performance.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/legacy/test_query_performance.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/legacy/test_query_refinement_fix.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/legacy/test_rag_entity_preservation.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/legacy/test_rag_quality.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/legacy/test_rag_retrieval.py | RAG Engine | Unknown | Needs Review | Not Started |
| tests/legacy/test_structured_output_monitoring.py | Text Formatting | Unknown | Needs Review | Not Started |
| tests/legacy/test_text_formatting_structured_output.py | Text Formatting | Unknown | Needs Review | Not Started |
| tests/legacy/try_rag_query.py | RAG Engine | Unknown | Needs Review | Not Started |

## Legacy Unit Tests

| File | Component Type | Current Import Pattern | Required Action | Status |
|------|---------------|------------------------|----------------|--------|
| tests/legacy_unit/test_rag_engine.py | RAG Engine | `from app.rag.engine.rag_engine import RAGEngine` | No Changes | Not Started |
| tests/legacy_unit/test_text_formatting.py | Text Formatting | `from app.utils.text_formatting.formatters.code_formatter import CodeFormatter` | No Changes | Not Started |

## Legacy Integration Tests

| File | Component Type | Current Import Pattern | Required Action | Status |
|------|---------------|------------------------|----------------|--------|
| tests/legacy/integration/test_response_quality_integration.py | Quality | Unknown | Needs Review | Not Started |
| tests/legacy/integration/test_retrieval_judge_integration.py | Retrieval | Unknown | Needs Review | Not Started |

## Legacy Retrieval Judge Tests

| File | Component Type | Current Import Pattern | Required Action | Status |
|------|---------------|------------------------|----------------|--------|
| tests/legacy/retrieval_judge/test_performance_analysis.py | Retrieval | Unknown | Needs Review | Not Started |
| tests/legacy/retrieval_judge/test_retrieval_judge_comparison.py | Retrieval | Unknown | Needs Review | Not Started |
| tests/legacy/retrieval_judge/test_single_query.py | Retrieval | Unknown | Needs Review | Not Started |
| tests/legacy/retrieval_judge/test_timing_analysis.py | Retrieval | Unknown | Needs Review | Not Started |

## Retrieval Judge Tests

| File | Component Type | Current Import Pattern | Required Action | Status |
|------|---------------|------------------------|----------------|--------|
| tests/retrieval_judge/test_judge_edge_cases.py | Retrieval | Unknown | Needs Review | Not Started |

## Summary

| Category | Total Files | No Changes | Update Imports | Needs Review | Completed | Remaining |
|----------|------------|------------|---------------|-------------|-----------|-----------|
| Unit Tests | 25 | 1 | 0 | 18 | 6 | 19 |
| New Unit Tests | 8 | 0 | 0 | 0 | 8 | 0 |
| Integration Tests | 8 | 0 | 0 | 7 | 1 | 7 |
| New Integration Tests | 1 | 0 | 0 | 0 | 1 | 0 |
| E2E Tests | 2 | 0 | 0 | 2 | 0 | 2 |
| Legacy Tests | 12 | 0 | 1 | 11 | 0 | 12 |
| Legacy Unit Tests | 2 | 2 | 0 | 0 | 0 | 0 |
| Legacy Integration Tests | 2 | 0 | 0 | 2 | 0 | 2 |
| Legacy Retrieval Judge Tests | 4 | 0 | 0 | 4 | 0 | 4 |
| Retrieval Judge Tests | 1 | 0 | 0 | 1 | 0 | 1 |
| **Total** | **65** | **3** | **1** | **45** | **16** | **47** |

## Next Steps

1. Continue reviewing and updating the remaining test files
2. Focus on the unit tests first, then integration tests
3. Run tests to verify the changes
4. Update the status of each file as we progress