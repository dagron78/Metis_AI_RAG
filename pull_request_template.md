# Implement PromptManager for Single Source of Truth in Prompt Architecture

## Problem

The current prompt architecture has several issues:
- Fragmented prompt architecture with multiple separate prompts
- Direct message injection into the context
- Inconsistent error handling
- Redundant instructions
- Poor responses when no documents are found

## Solution

This PR implements a PromptManager class that serves as a single source of truth for all prompt-related operations:

1. **PromptManager Class**: A new class that manages templates and creates appropriate prompts based on the current state
2. **State-Based Prompt Selection**: Uses explicit state to select the appropriate prompt instead of injecting messages
3. **Clear Separation of Data and Instructions**: Keeps retrieved documents as pure data without injected messages
4. **Improved Templates**: Updated templates to be more helpful and natural, especially when no documents are found

## Changes

- Added `PromptManager` class in `app/rag/prompt_manager.py`
- Added proper initialization in `RAGEngine` class
- Updated prompt templates to be more helpful and natural
- Removed explicit mentions of missing documents unless specifically asked
- Moved unused prompt templates to the `unused_code` directory

## Testing

The changes have been successfully tested with various queries:

- **General Knowledge**: Correctly answered "There are three 'r's in the word strawberry"
- **Code Generation**: Successfully generated SVG code for a butterfly
- **Memory**: Remembered that the user asked about "strawberry" earlier
- **Conversation Context**: Remembered the user's name (Charles) after being told
- **Natural Responses**: No longer mentions "I don't have document-based information" for every response

## Next Steps After Merging

1. Monitor the system for any regressions
2. Consider adding more templates for different scenarios
3. Consider externalizing templates for easier editing