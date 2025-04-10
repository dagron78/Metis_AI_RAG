# Metis RAG Codebase Restructuring Checklist

This checklist provides a detailed, step-by-step guide for restructuring the large files in the Metis RAG codebase. Follow these steps in order to ensure a smooth transition with minimal disruption.

## Phase 0: Git Strategy and Backup

### 0.1 Set Up Git Strategy
- [x] Create a new branch for the restructuring work:
  ```bash
  git checkout -b restructure/large-files
  ```
- [ ] Create feature branches for each major component:
  - [ ] `git checkout -b restructure/chat-api`
  - [ ] `git checkout -b restructure/frontend-js`
  - [ ] `git checkout -b restructure/rag-engine`
  - [ ] `git checkout -b restructure/text-formatting`

### 0.2 Create Backup Points
- [ ] Create a tag for the current state before any changes:
  ```bash
  git tag -a pre-restructure-v1.0 -m "Pre-restructuring state"
  ```
- [ ] Push the tag to remote:
  ```bash
  git push origin pre-restructure-v1.0
  ```
- [ ] Create a backup branch:
  ```bash
  git checkout -b backup/pre-restructure
  git push origin backup/pre-restructure
  ```

### 0.3 Set Up Commit Strategy
- [x] Commit after each logical step (not just each file)
- [x] Use consistent commit message format:
  ```
  restructure(component): specific change
  
  - Detailed explanation
  - Reason for change
  ```
- [x] Create commits that can be easily reverted if needed

## Phase 1: Preparation

### 1.1 Set Up Directory Structure
- [x] Create new directory structures for each component:
  - [x] `app/api/chat/`
  - [x] `app/api/chat/handlers/`
  - [x] `app/api/chat/utils/`
  - [x] `app/static/js/chat/`
  - [x] `app/static/js/chat/api/`
  - [x] `app/static/js/chat/components/`
  - [x] `app/static/js/chat/utils/`
  - [x] `app/static/js/chat/state/`
  - [x] `app/rag/engine/`
  - [x] `app/rag/engine/components/`
  - [x] `app/rag/engine/utils/`
  - [x] `app/rag/engine/base/`
  - [x] `app/utils/text_formatting/`
  - [x] `app/utils/text_formatting/formatters/`
  - [x] `app/utils/text_formatting/rules/`

### 1.2 Create Empty Files with Proper Imports
- [x] Create `__init__.py` files in each directory (for chat API and RAG engine)
- [x] Set up empty module files with proper imports (for chat API and RAG engine)
- [x] Add placeholder docstrings explaining the purpose of each file (for chat API and RAG engine)

### 1.3 Set Up Testing Infrastructure
- [x] Create or update unit tests for existing functionality (for chat API)
- [ ] Set up test fixtures for each component
- [ ] Create integration tests to ensure end-to-end functionality

### 1.4 Create Git Checkpoint
- [x] Commit directory structure changes:
  ```bash
  git add .
  git commit -m "restructure(all): create directory structure for refactoring
  
  - Set up empty directories and files
  - Add placeholder docstrings
  - Prepare for component extraction"
  ```
- [x] Push to remote:
  ```bash
  git push origin restructure/large-files
  ```

## Phase 2: Extract Shared Utilities

### 2.1 Extract Chat API Utilities
- [x] Create `app/api/chat/utils/streaming.py`:
  - [x] Extract streaming event generator functions
  - [x] Create reusable streaming response function
- [x] Create `app/api/chat/utils/error_handling.py`:
  - [x] Extract error handling logic
  - [x] Create standardized error response function
- [x] Create `app/api/chat/utils/conversation_helpers.py`:
  - [x] Extract conversation creation/retrieval logic
  - [x] Create helper functions for message handling

### 2.2 Extract Frontend Utilities
- [x] Create `app/static/js/chat/utils/stream-handler.js`:
  - [x] Extract SSE stream handling logic
- [x] Create `app/static/js/chat/utils/markdown-renderer.js`:
  - [x] Extract markdown rendering logic
- [x] Create `app/static/js/chat/utils/error-handler.js`:
  - [x] Extract error handling logic

### 2.3 Extract RAG Engine Utilities
- [x] Create `app/rag/engine/base/base_engine.py`:
  - [x] Extract base engine functionality
- [x] Create `app/rag/engine/base/vector_store_mixin.py`:
  - [x] Extract vector store functionality
- [x] Create `app/rag/engine/base/ollama_mixin.py`:
  - [x] Extract Ollama LLM functionality
- [x] Create `app/rag/engine/base/cache_mixin.py`:
  - [x] Extract caching functionality
- [x] Create `app/rag/engine/base/security_mixin.py`:
  - [x] Extract security functionality
- [x] Create `app/rag/engine/utils/query_processor.py`:
  - [x] Extract query processing logic
- [x] Create `app/rag/engine/utils/timing.py`:
  - [x] Extract performance timing logic
- [x] Create `app/rag/engine/utils/relevance.py`:
  - [x] Extract relevance scoring logic
- [x] Create `app/rag/engine/utils/error_handler.py`:
  - [x] Extract error handling logic

### 2.4 Extract Text Formatting Utilities
- [x] Create `app/utils/text_formatting/rules/code_rules.py`:
  - [x] Extract code formatting rules
- [x] Create `app/utils/text_formatting/rules/list_rules.py`:
  - [x] Extract list formatting rules
- [x] Create `app/utils/text_formatting/rules/table_rules.py`:
  - [x] Extract table formatting rules
- [x] Create `app/utils/text_formatting/rules/markdown_rules.py`:
  - [x] Extract markdown formatting rules

### 2.5 Test Utilities
- [x] Run unit tests for each utility (for chat API)
- [x] Fix any issues that arise (for chat API)
- [x] Document each utility function (for chat API)

### 2.6 Create Git Checkpoint
- [x] Commit utility extraction changes:
  ```bash
  git add .
  git commit -m "restructure(utils): extract shared utilities
  
  - Extract streaming, error handling, and conversation helpers
  - Extract frontend utilities
  - Extract RAG engine utilities
  - Extract text formatting rules
  - Add tests for all utilities"
  ```
- [x] Create a tag for the utilities milestone:
  ```bash
  git tag -a restructure-utils-v1.0 -m "Utilities extraction complete"
  ```
- [x] Push to remote:
  ```bash
  git push origin restructure/large-files
  git push origin restructure-utils-v1.0
  ```

## Phase 3: Component Extraction

### 3.1 Extract Chat API Components
- [x] Create `app/api/chat/handlers/standard.py`:
  - [x] Extract `query_chat` endpoint
  - [x] Update to use utility functions
- [x] Create `app/api/chat/handlers/langgraph.py`:
  - [x] Extract `langgraph_query_chat` endpoint
  - [x] Update to use utility functions
- [x] Create `app/api/chat/handlers/enhanced_langgraph.py`:
  - [x] Extract `enhanced_langgraph_query_chat` endpoint
  - [x] Update to use utility functions
- [x] Create `app/api/chat/handlers/conversation.py`:
  - [x] Extract `get_history` endpoint
  - [x] Extract `save_conversation` endpoint
  - [x] Extract `clear_conversation` endpoint
  - [x] Extract `list_conversations` endpoint
  - [x] Update to use utility functions
- [x] Create `app/api/chat/handlers/memory.py`:
  - [x] Extract `memory_diagnostics` endpoint
  - [x] Update to use utility functions

### 3.2 Extract Frontend Components
- [x] Create `app/static/js/chat/api/chat-service.js`:
  - [x] Extract API calls for chat functionality
- [x] Create `app/static/js/chat/api/conversation-service.js`:
  - [x] Extract API calls for conversation management
- [x] Create `app/static/js/chat/components/chat-interface.js`:
  - [x] Extract chat UI components
- [x] Create `app/static/js/chat/components/message-list.js`:
  - [x] Extract message rendering logic
- [x] Create `app/static/js/chat/components/input-area.js`:
  - [x] Extract user input handling logic
- [x] Create `app/static/js/chat/components/citations.js`:
  - [x] Extract citation display and handling logic
- [x] Create `app/static/js/chat/state/chat-state.js`:
  - [x] Extract chat state management logic
- [x] Create `app/static/js/chat/state/settings-state.js`:
  - [x] Extract user settings state management logic

### 3.3 Extract RAG Engine Components
- [x] Create `app/rag/engine/components/retrieval.py`:
  - [x] Extract retrieval functionality
  - [x] Create `RetrievalComponent` class
- [x] Create `app/rag/engine/components/generation.py`:
  - [x] Extract generation functionality
  - [x] Create `GenerationComponent` class
- [x] Create `app/rag/engine/components/memory.py`:
  - [x] Extract memory operations
  - [x] Create `MemoryComponent` class
- [x] Create `app/rag/engine/components/context_builder.py`:
  - [x] Extract context assembly logic
  - [x] Create `ContextBuilder` class

### 3.4 Extract RAG Engine Base Components
- [x] Create `app/rag/engine/base/base_engine.py`:
  - [x] Extract core base engine functionality
- [x] Create `app/rag/engine/base/vector_store_mixin.py`:
  - [x] Extract vector store integration
- [x] Create `app/rag/engine/base/ollama_mixin.py`:
  - [x] Extract Ollama client integration
- [x] Create `app/rag/engine/base/cache_mixin.py`:
  - [x] Extract cache management
- [x] Create `app/rag/engine/base/security_mixin.py`:
  - [x] Extract security features

### 3.5 Extract Text Formatting Components
- [x] Create `app/utils/text_formatting/monitor.py`:
  - [x] Extract main monitoring functionality
- [x] Create `app/utils/text_formatting/formatters/code_formatter.py`:
  - [x] Extract code block formatting
- [x] Create `app/utils/text_formatting/formatters/list_formatter.py`:
  - [x] Extract list formatting
- [x] Create `app/utils/text_formatting/formatters/table_formatter.py`:
  - [x] Extract table formatting
- [x] Create `app/utils/text_formatting/formatters/markdown_formatter.py`:
  - [x] Extract general markdown formatting

### 3.6 Test Components
- [x] Run unit tests for each component (for chat API)
- [x] Run integration tests (for chat API)
- [x] Fix any issues that arise (for chat API)
- [x] Document each component (for chat API)

### 3.7 Create Git Checkpoints
- [x] Commit chat API component extraction:
  ```bash
  git add app/api/chat/
  git commit -m "restructure(chat-api): extract chat API components
  
  - Extract standard, langgraph, and enhanced langgraph handlers
  - Extract conversation and memory handlers
  - Update to use utility functions
  - Add tests for all components"
  ```
- [x] Commit frontend component extraction:
  ```bash
  git add app/static/js/chat/
  git commit -m "restructure(frontend): extract frontend components
  
  - Extract API services
  - Extract UI components
  - Extract state management
  - Update to use utility functions"
  ```
- [x] Commit RAG engine component extraction:
  ```bash
  git add app/rag/engine/
  git commit -m "restructure(rag-engine): extract RAG engine components
  
  - Extract retrieval, generation, memory, and context builder components
  - Extract base engine components
  - Update to use utility functions
  - Add tests for all components"
  ```
- [x] Commit text formatting component extraction:
  ```bash
  git add app/utils/text_formatting/
  git commit -m "restructure(text-formatting): extract text formatting components
  
  - Extract monitor and formatter components
  - Update to use utility functions
  - Add tests for all components"
  ```
- [x] Create a tag for the components milestone:
  ```bash
  git tag -a restructure-components-v1.0 -m "Component extraction complete"
  ```
- [x] Push to remote:
  ```bash
  git push origin restructure/large-files
  git push origin restructure-components-v1.0
  ```

## Phase 4: Refactor Original Files

### 4.1 Refactor Chat API
- [x] Create `app/api/chat/router.py`:
  - [x] Set up router with all endpoints
  - [x] Import handlers from new modules
- [x] Update `app/api/chat/__init__.py`:
  - [x] Export router
- [x] Refactor `app/api/chat.py`:
  - [x] Convert to thin wrapper that imports from new modules
  - [x] Add deprecation warning

### 4.2 Refactor Frontend
- [x] Create `app/static/js/chat/index.js`:
  - [x] Import and initialize all components
- [x] Refactor `app/static/js/chat.js`:
  - [x] Convert to thin wrapper that imports from new modules
  - [x] Add deprecation warning

### 4.3 Refactor RAG Engine
- [x] Create `app/rag/engine/rag_engine.py`:
  - [x] Create new RAGEngine class that uses components
- [x] Update `app/rag/engine/__init__.py`:
  - [x] Export RAGEngine
- [x] Refactor `app/rag/rag_engine.py`:
  - [x] Convert to thin wrapper that imports from new modules
  - [x] Add deprecation warning

### 4.4 Refactor RAG Engine Base
- [x] Update `app/rag/engine/base/__init__.py`:
  - [x] Export base components
- [x] Refactor `app/rag/rag_engine_base.py`:
  - [x] Convert to thin wrapper that imports from new modules
  - [x] Add deprecation warning

### 4.5 Refactor Text Formatting Monitor
- [x] Update `app/utils/text_formatting/__init__.py`:
  - [x] Export formatting components
- [x] Refactor `app/utils/text_formatting_monitor.py`:
  - [x] Convert to thin wrapper that imports from new modules
  - [x] Add deprecation warning

### 4.6 Test Refactored Files
- [x] Run unit tests (for chat API)
- [x] Run integration tests (for chat API)
- [x] Fix any issues that arise (for chat API)
- [x] Document changes (for chat API)

### 4.7 Create Git Checkpoint
- [x] Commit refactoring changes:
  ```bash
  git add .
  git commit -m "restructure(all): refactor original files to use new components
  
  - Refactor chat API to use new handlers
  - Refactor frontend to use new components
  - Refactor RAG engine to use new components
  - Refactor text formatting to use new components
  - Add deprecation warnings
  - Update tests"
  ```
- [x] Create a tag for the refactoring milestone:
  ```bash
  git tag -a restructure-refactor-v1.0 -m "Original file refactoring complete"
  ```
- [x] Push to remote:
  ```bash
  git push origin restructure/large-files
  git push origin restructure-refactor-v1.0
  ```

## Phase 5: Update Imports

### 5.1 Identify Import Dependencies
- [x] Use a tool like `grep` to find all imports of the original files:
  ```bash
  grep -r "from app.api.chat import" --include="*.py" .
  grep -r "from app.rag.rag_engine import" --include="*.py" .
  grep -r "from app.rag.rag_engine_base import" --include="*.py" .
  grep -r "from app.utils.text_formatting_monitor import" --include="*.py" .
  ```
- [x] Create a list of files that need to be updated

### 5.2 Update Import Statements
- [x] Update imports in other files to use the new structure
- [x] Test each file after updating imports

### 5.3 Test Updated Imports
- [x] Run unit tests
- [x] Run integration tests
- [x] Fix any issues that arise
- [x] Reorganize test files to match new architecture
  - [x] Move RAG Engine tests to tests/unit/rag/engine/
  - [x] Move Query Analyzer tests to tests/unit/rag/
  - [x] Move Process Logger tests to tests/unit/rag/
  - [x] Move Plan Executor tests to tests/unit/rag/
  - [x] Split Tool tests into multiple files in tests/unit/rag/tools/
  - [x] Move LangGraph RAG Agent tests to tests/integration/rag_api/

### 5.4 Create Git Checkpoint
- [x] Commit import updates:
  ```bash
  git add .
  git commit -m "restructure(imports): update import statements across codebase
  
  - Update imports to use new module structure
  - Fix any issues with circular imports
  - Update tests"
  ```
- [x] Create a tag for the imports milestone:
  ```bash
  git tag -a restructure-imports-v1.0 -m "Import updates complete"
  ```
- [x] Push to remote:
  ```bash
  git push origin restructure/large-files
  git push origin restructure-imports-v1.0
  ```

## Phase 6: Documentation and Cleanup

### 6.1 Update Documentation
- [x] Update API documentation
- [x] Update code comments
- [x] Create architecture diagrams
- [x] Update README files

### 6.2 Add Deprecation Warnings
- [x] Add deprecation warnings to original files (for chat API)
- [x] Create migration guide

### 6.3 Final Testing
- [x] Run all tests
- [x] Perform manual testing
- [x] Fix any remaining issues
- [x] Create new tests for restructured components
- [x] Move old tests to legacy directory for reference

### 6.4 Code Review
- [x] Conduct code review
- [x] Address feedback
- [x] Finalize changes

## Phase 7: Deployment

### 7.1 Prepare Deployment
- [ ] Create deployment plan
- [ ] Back up production data
- [ ] Create a release branch:
  ```bash
  git checkout -b release/restructure-v1.0 restructure/large-files
  ```

### 7.2 Deploy Changes
- [ ] Deploy to staging environment
- [ ] Test in staging
- [ ] Create a release tag:
  ```bash
  git tag -a release-restructure-v1.0 -m "Restructuring release v1.0"
  ```
- [ ] Merge to main branch:
  ```bash
  git checkout main
  git merge --no-ff release/restructure-v1.0
  git push origin main
  git push origin release-restructure-v1.0
  ```
- [ ] Deploy to production

### 7.3 Monitor Deployment
- [ ] Monitor for errors
- [ ] Address any issues
- [ ] Collect feedback

### 7.4 Create Git Checkpoint
- [ ] Commit any hotfixes:
  ```bash
  git add .
  git commit -m "fix(hotfix): address issues found in production
  
  - Fix issue 1
  - Fix issue 2"
  ```
- [ ] Push to remote:
  ```bash
  git push origin main
  ```

## Phase 8: Future Improvements

### 8.1 Identify Further Refactoring Opportunities
- [ ] Analyze code metrics
- [ ] Identify additional refactoring opportunities

### 8.2 Plan Next Steps
- [ ] Create plan for future improvements
- [ ] Prioritize improvements
- [ ] Schedule implementation
- [ ] Create new feature branches for each improvement:
  ```bash
  git checkout -b improvement/feature-name
  ```

## Appendix: Code Structure Overview

### A. Chat API Structure
```
app/api/chat/
├── __init__.py                  # Exports router
├── router.py                    # Main router with all endpoints
├── handlers/
│   ├── __init__.py              # Exports all handlers
│   ├── standard.py              # Standard chat endpoint
│   ├── langgraph.py             # LangGraph chat endpoint
│   ├── enhanced_langgraph.py    # Enhanced LangGraph chat endpoint
│   ├── conversation.py          # Conversation management endpoints
│   └── memory.py                # Memory diagnostics endpoint
└── utils/
    ├── __init__.py              # Exports all utilities
    ├── streaming.py             # Streaming response utilities
    ├── error_handling.py        # Error handling utilities
    └── conversation_helpers.py  # Conversation management utilities
```

### B. Frontend Structure
```
app/static/js/chat/
├── index.js                     # Main entry point
├── api/
│   ├── chat-service.js          # Chat API calls
│   └── conversation-service.js  # Conversation API calls
├── components/
│   ├── chat-interface.js        # Main chat UI component
│   ├── message-list.js          # Message rendering component
│   ├── input-area.js            # User input component
│   └── citations.js             # Citation display component
├── state/
│   ├── chat-state.js            # Chat state management
│   └── settings-state.js        # User settings state management
└── utils/
    ├── stream-handler.js        # SSE stream handling
    ├── markdown-renderer.js     # Markdown rendering
    └── error-handler.js         # Error handling
```

### C. RAG Engine Structure
```
app/rag/engine/
├── __init__.py                  # Exports RAGEngine
├── rag_engine.py                # Main RAGEngine class
├── components/
│   ├── __init__.py              # Exports all components
│   ├── retrieval.py             # Retrieval component
│   ├── generation.py            # Generation component
│   ├── memory.py                # Memory component
│   └── context_builder.py       # Context builder component
├── base/
│   ├── __init__.py              # Exports base components
│   ├── base_engine.py           # Base engine class
│   ├── vector_store_mixin.py    # Vector store mixin
│   ├── ollama_mixin.py          # Ollama LLM mixin
│   ├── cache_mixin.py           # Cache mixin
│   └── security_mixin.py        # Security mixin
└── utils/
    ├── __init__.py              # Exports all utilities
    ├── query_processor.py       # Query processing utilities
    ├── timing.py                # Performance timing utilities
    ├── relevance.py             # Relevance scoring utilities
    └── error_handler.py         # Error handling utilities
```

### D. Text Formatting Structure
```
app/utils/text_formatting/
├── __init__.py                  # Exports all components
├── monitor.py                   # Main monitoring functionality
├── formatters/
│   ├── __init__.py              # Exports all formatters
│   ├── code_formatter.py        # Code block formatting
│   ├── list_formatter.py        # List formatting
│   ├── table_formatter.py       # Table formatting
│   └── markdown_formatter.py    # General markdown formatting
└── rules/
    ├── __init__.py              # Exports all rules
    ├── code_rules.py            # Code formatting rules
    ├── list_rules.py            # List formatting rules
    ├── table_rules.py           # Table formatting rules
    └── markdown_rules.py        # Markdown formatting rules