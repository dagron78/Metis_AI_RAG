# Prompt Manager Refactor

## Overview

This document describes the refactoring of the prompt architecture in Metis RAG to address issues with hallucination, citation misuse, and inconsistent handling of missing information.

## Problem Statement

The original prompt architecture had several issues:

1. **Fragmented Prompt Architecture**: The system used multiple separate prompts (system prompt, conversation templates) with overlapping and sometimes contradictory instructions.

2. **Direct Message Injection**: When no documents were found, the system injected "Note: No documents..." messages directly into the context, which could be confused with actual document content.

3. **Inconsistent Error Handling**: Different error conditions resulted in different messages being injected into the context.

4. **Redundant Instructions**: The same instructions for handling missing information appeared in multiple places.

## Solution: Single Source of Truth

The refactoring introduces a `PromptManager` class that serves as a single source of truth for all prompt-related operations. Key components:

1. **PromptManager**: A new class responsible for all prompt-related operations
   - Maintains templates and instructions
   - Creates appropriate prompts based on the current state
   - Handles all scenarios (with/without documents, with/without conversation history)

2. **State-Based Prompt Selection**: Instead of injecting messages into the context, we use explicit state to select the appropriate prompt
   - Track whether documents were found
   - Track whether documents met relevance thresholds
   - Select the appropriate template based on this state

3. **Clear Separation of Data and Instructions**:
   - Keep retrieved documents as pure data without injected messages
   - Keep conversation history as pure data
   - Apply instructions through templates, not by modifying the data

## Implementation Details

### 1. PromptManager Class

The `PromptManager` class in `app/rag/prompt_manager.py` provides:

- Template loading and management
- State-based prompt selection
- Consistent instructions across different scenarios

### 2. Modified RAG Engine

The RAG Engine has been updated to:

- Use the `PromptManager` for prompt creation
- Track retrieval state explicitly instead of injecting messages
- Pass the retrieval state to the prompt creation functions

### 3. Modified Retrieval Process

The retrieval process has been updated to:

- Return empty context instead of injecting messages
- Let the `PromptManager` handle the appropriate response based on retrieval state

## Benefits

1. **Consistency**: All instructions come from a single source of truth
2. **Maintainability**: Changes to prompting logic only need to be made in one place
3. **Clarity**: Clear separation between data and instructions
4. **Flexibility**: Easy to add new scenarios or modify existing ones
5. **Reliability**: Reduced chance of hallucination and citation misuse

## Testing

Unit tests have been added in `tests/unit/test_prompt_manager.py` to verify the functionality of the `PromptManager` class.

## Future Improvements

1. **Template Externalization**: Move templates to external files for easier editing
2. **Dynamic Template Loading**: Support loading templates at runtime
3. **A/B Testing**: Add support for testing different prompt variations