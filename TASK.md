# Metis RAG Project Tasks

This document outlines the current tasks, priorities, and TODOs for the Metis RAG project. It serves as a working document to track progress and guide development efforts.

## Current Priorities

1. ✅ **Fix Memory Functionality Issues**
2. ✅ **Fix Performance and Authentication Issues**
3. **Improve RAG Response Accuracy**
4. **Enhance System Prompts**
5. **Optimize Document Processing**
6. **Improve Code Formatting in Responses**

## Task Breakdown

### Memory Functionality Fixes

- [ ] **Fix Frontend Session Management**
  - [ ] Add localStorage persistence for conversation IDs
  - [ ] Create updateConversationId() function
  - [ ] Modify page load event to retrieve stored conversation IDs
  - [ ] Fix conversation ID handling in streaming responses

- [ ] **Address Authentication Issues**
  - [ ] Increase JWT token expiration time
  - [ ] Implement token refresh functionality
  - [ ] Add frontend token management
  - [ ] Update authenticatedFetch to handle token refresh

- [x] **Ensure Conversation Continuity**
  - [x] Modify RAG engine to maintain consistent user IDs
  - [x] Fix conversation history handling
  - [x] Update conversation repository
  - [x] Fix memory buffer integration

- [x] **Fix Foreign Key Violation in Memory Storage**
  - [x] Modify `process_query` in `memory_buffer.py` to convert string conversation_ids to UUID objects
  - [x] Add conversation existence verification in `add_to_memory_buffer`
  - [x] Add proper error handling and logging for memory operations
  - [x] Update type hints to make the expected types clearer
  - [x] Add unit tests to verify the fixes

- [x] **Fix Session Management and ID Lifecycle Issues**
  - [x] Remove manual session closing in `memory_buffer.py` that causes `IllegalStateChangeError`
  - [x] Implement proper error handling for session operations with try/except/finally blocks
  - [x] Ensure sessions are automatically closed when the generator is closed
  - [x] Fix double yield issue in `app/db/session.py` get_session function

- [x] **Fix Conversation ID Persistence Timing**
  - [x] Add validation to ensure the conversation ID is properly handled throughout the system
  - [x] Ensure memory operations use the same conversation ID that exists in the database
  - [x] Modify the RAG engine to always respect the conversation ID passed from the API
  - [x] Remove code that generates a new conversation ID in the RAG engine

- [x] **Fix User ID Format Inconsistency**
  - [x] Ensure all user IDs are valid UUIDs throughout the system
  - [x] Generate proper UUIDs for anonymous users instead of string-based session IDs
  - [x] Add proper validation and conversion of user IDs to ensure database compatibility
  - [x] Implement deterministic UUID generation for cases where conversion fails

- [x] **Implement Memory Usage Optimization**
  - [x] Add memory cleanup after query processing to reduce memory usage
  - [x] Implement garbage collection to free up memory
  - [x] Clear cached data and large temporary variables
  - [x] Prevent high memory usage (99.5%) that causes task throttling

- [ ] **Add Diagnostics and Testing**
  - [ ] Implement memory diagnostics endpoint
  - [ ] Add detailed logging for memory operations
  - [ ] Create comprehensive memory testing script

### RAG Response Accuracy Improvements

- [ ] **Enhance "No Documents Found" Handling**
  - [ ] Modify context formatting for empty results
  - [ ] Add prominent notice when no documents are found
  - [ ] Improve messaging for insufficient context

- [ ] **Improve Vector Store Empty Results Handling**
  - [ ] Enhance search method to provide clearer empty results
  - [ ] Add special result that clearly indicates no documents were found
  - [ ] Improve logging for empty search results

- [ ] **Fix Citation Handling**
  - [ ] Modify context formatting to only include citations when documents exist
  - [ ] Ensure empty results clear the sources list
  - [ ] Improve citation formatting in responses

- [ ] **Add Verification Step Before Response Generation**
  - [ ] Add check for sources before generating response
  - [ ] Add explicit instruction to not use citations when no sources are found
  - [ ] Improve logging for verification step

### System Prompt Enhancements

- [x] **Improve RAG System Prompt**
  - [x] Add stronger instructions for document hallucination prevention
  - [x] Enhance memory retention instructions
  - [x] Add content fabrication prevention guidelines
  - [x] Implement citation misuse prevention

- [ ] **Implement User Information Extraction**
  - [ ] Add mechanism to extract user information from conversation
  - [ ] Create patterns to identify user names
  - [ ] Include user information in context for response generation

### Document Processing Optimization

- [ ] **Enhance Chunking Strategy**
  - [ ] Refine dynamic chunking parameter selection
  - [ ] Improve entity preservation in chunks
  - [ ] Optimize chunk size and overlap parameters

- [ ] **Improve Vector Embedding Performance**
  - [ ] Implement batch processing for embeddings
  - [ ] Add caching for frequently accessed embeddings
  - [ ] Optimize vector database queries

### Improve Code Formatting in Responses

- [x] **Add Syntax Highlighting Libraries** (April 7, 2025)
  - [x] Add highlight.js to the project
  - [x] Add a lightweight markdown parser (marked.js)
  - [x] Update Content Security Policy in base.html to allow these libraries
  - [x] Add integrity attributes for enhanced security

- [x] **Create Markdown Parser Function** (April 7, 2025)
  - [x] Configure marked.js to use highlight.js for code block formatting
  - [x] Add special handling for code blocks with language tags
  - [x] Implement proper HTML sanitization to prevent XSS attacks
  - [x] Add support for common programming languages (Python, JavaScript, SQL, HTML/CSS)

- [x] **Update Response Rendering Logic** (April 7, 2025)
  - [x] Modify chat.js to use marked.js for parsing markdown in responses
  - [x] Replace contentDiv.textContent with sanitized innerHTML
  - [x] Add code to detect and highlight code blocks
  - [x] Ensure backward compatibility with existing responses

- [x] **Add CSS Styles for Code Blocks** (April 7, 2025)
  - [x] Create styles for code blocks in styles.css
  - [x] Add syntax highlighting theme styles (atom-one-dark)
  - [x] Ensure proper display of code blocks in the chat interface
  - [x] Add responsive styles for mobile devices

- [x] **Implement Security Measures** (April 7, 2025)
  - [x] Add proper HTML sanitization to prevent XSS attacks
  - [x] Validate and sanitize all user-generated content
  - [x] Update Content Security Policy to allow necessary resources
  - [x] Add integrity attributes for external libraries

- [x] **Testing and Validation** (April 7, 2025)
  - [x] Create test page to verify implementation
  - [x] Test with various code examples in different languages
  - [x] Test copy button functionality
  - [x] Verify proper rendering in browser

- [x] **Fix Streaming Code Formatting Issues** (April 7, 2025)
  - [x] Fix issue with parsing incomplete markdown during streaming
  - [x] Use textContent during streaming and only process markdown once at the end
  - [x] Implement improved chat.js with better code organization and error handling
  - [x] Create test files to demonstrate and verify the fix

## Testing Plan

- [ ] **Memory Functionality Tests**
  - [ ] Test conversation persistence across page refreshes
  - [ ] Verify memory storage and retrieval
  - [ ] Test memory operations in multi-turn conversations

- [ ] **RAG Accuracy Tests**
  - [ ] Test empty vector store scenarios
  - [ ] Test no relevant documents scenarios
  - [ ] Test user information retention
  - [ ] Test citation handling

- [ ] **Performance Tests**
  - [ ] Measure document processing times
  - [ ] Evaluate response generation latency
  - [ ] Test system under various load conditions
- [x] **Code Formatting Tests** (April 7, 2025)
  - [x] Test code block rendering with various languages
  - [x] Test syntax highlighting accuracy
  - [x] Test security of HTML rendering
  - [x] Test copy button functionality
  - [x] Test performance impact of markdown parsing

## Bug Fixes

- [ ] **Fix Document Hallucination Issues**
  - [ ] Address system claiming to have non-existent documents
  - [ ] Fix improper handling of empty search results

- [x] **Fix Memory Loss Issues**
  - [x] Address system forgetting user information
  - [x] Fix conversation history not being effectively utilized
  - [x] Fix foreign key violation when storing implicit memories
  - [x] Fix session management issues causing IllegalStateChangeError
  - [x] Fix conversation ID persistence timing issues
  - [x] Fix user ID format inconsistency problems

- [x] **Fix Performance and Authentication Issues**
  - [x] Fix incorrect query type detection causing wrong system prompt usage
  - [x] Fix analytics endpoint authentication failures
  - [x] Improve memory management to reduce high memory usage
  - [x] Fix user ID edge cases with "system" and session-based IDs
  - [x] Add performance monitoring to identify bottlenecks

- [ ] **Fix Content Fabrication Issues**
  - [ ] Prevent generation of text for non-existent documents
  - [ ] Improve handling of "no documents found" scenarios

- [ ] **Fix Citation Misuse**
  - [ ] Prevent use of citation markers when no documents are referenced
  - [ ] Ensure citations correspond to actual documents

- [x] **Fix Code Formatting Issues** (April 7, 2025)
  - [x] Fix improper rendering of code blocks in responses
  - [x] Implement syntax highlighting for different languages
  - [x] Add proper HTML sanitization to prevent XSS attacks
  - [x] Add copy button for easy code reuse
  - [x] Fix streaming code formatting issues by using textContent during streaming
  - [x] Implement improved chat.js with better code organization and error handling
  - [x] Create test files to demonstrate and verify the fix

## Documentation Updates

- [ ] **Update API Documentation**
  - [ ] Document memory-related endpoints
  - [ ] Update authentication endpoints documentation
  - [ ] Document new system configuration options

- [ ] **Update User Guide**
  - [ ] Add memory command usage instructions
  - [ ] Update document upload guidelines
  - [ ] Add troubleshooting section for common issues
  - [x] Add documentation on code formatting features (April 7, 2025)

- [ ] **Update Developer Documentation**
  - [ ] Document memory buffer implementation
  - [ ] Update system prompt configuration guide
  - [ ] Add testing guidelines for new features
  - [ ] Document ID lifecycle and persistence throughout the system
  - [ ] Add session management best practices
  - [x] Document code formatting implementation (April 7, 2025)

## Next Steps

1. ✅ Implement the memory functionality fixes to address the most critical issues
2. ✅ Test the memory functionality to ensure it works correctly
3. ✅ Fix the remaining issues identified in log analysis (query classification, analytics auth, memory management, user ID edge cases, performance)
4. [x] Complete code formatting improvements for better readability of responses (April 7, 2025)
   - [x] Fix remaining issues with code formatting in actual application responses
   - [x] Enhance backend processing to handle edge cases in LLM output
   - [x] Implement comprehensive testing for code formatting
5. Proceed with RAG response accuracy improvements
6. Implement and test the remaining enhancements
7. Update documentation to reflect the changes
8. Create comprehensive unit tests for all fixed components

## Completion Criteria

- ✅ All memory functionality issues are resolved
- ✅ Performance and authentication issues are fixed
- RAG responses accurately reflect available documents
- System prompts effectively guide the LLM behavior
- Document processing is optimized for performance
- ✅ Code blocks in responses are properly formatted and syntax highlighted
- Comprehensive tests verify all functionality
- Documentation is updated to reflect all changes

## Code Formatting Implementation Progress (April 7, 2025)

#### What Has Been Done
1. **Fixed text_processor.py**:
   - Updated the format_code_blocks function to properly handle different language tags (Python, HTML, CSS, JavaScript)
   - Fixed the regex pattern to correctly identify code blocks with any language tag
   - Ensured language tags are preserved in the formatted code blocks
   - Added proper spacing and line breaks for better readability
   - Fixed function and variable names with spaces

2. **Added Unit Tests**:
   - Created comprehensive unit tests for the format_code_blocks function
   - Tested with various language tags (Python, HTML, CSS, JavaScript)
   - Verified that spaces in function names and method calls are fixed
   - All unit tests pass successfully

3. **Updated Frontend**:
   - Added highlight.js and marked.js libraries for syntax highlighting and markdown parsing
   - Updated chat.js to use marked.js for parsing markdown in responses
   - Added CSS styles for code blocks with proper syntax highlighting
   - Implemented security measures (HTML sanitization, CSP updates)

#### Root Cause Analysis (April 7, 2025)
After examining raw LLM output, we've identified that the primary issue is with the LLM's output itself:

1. **Missing Language Tags**: The LLM often uses triple backticks (```) without specifying a language tag.
2. **No Newline After Backticks**: There's frequently no newline after the opening backticks.
3. **Inconsistent Formatting**: Spaces in function names, method calls, and abbreviations.

Despite the LLM claiming it formats code properly when directly asked, actual outputs show inconsistent adherence to markdown best practices.

#### Current Issues
1. **LLM Output Formatting**:
   - The LLM (Ollama with llama3 model) is not properly formatting code blocks with language tags and newlines
   - The language tags in code blocks are sometimes incorrect (e.g., "pythonhtml", "pythoncss", "pythonjavascript")
   - There are still spaces in function names and method calls in the responses

2. **Backend Processing**:
   - The format_code_blocks function needs enhancement to handle missing language tags and infer the language based on content
   - There's a bug in rag_generation.py with an unreachable return statement

3. **Frontend Rendering**:
   - The frontend has redundant logic for language inference and tag fixing that should be removed
   - The markdown-parser.js file needs to be simplified to focus solely on rendering and highlighting

#### Next Steps (Two-Pronged Approach)
1. **System Prompt Enhancement (Primary Solution)**:
   - Update CODE_GENERATION_SYSTEM_PROMPT in system_prompts.py with explicit instructions for code block formatting
   - Add examples of correctly formatted code blocks
   - Add specific instructions about newlines after language tags and before closing backticks
   - Add instructions about not using spaces in abbreviations

2. **Robust Backend Processing (Fallback Solution)**:
   - Fix the bug in process_complete_response method in rag_generation.py
   - Enhance format_code_blocks in text_processor.py to handle missing language tags
   - Add language inference based on code content
   - Improve handling of spaces in method calls and abbreviations

3. **Simplified Frontend Rendering**:
   - Update markdown-parser.js to focus solely on rendering and highlighting
   - Remove redundant language inference and tag fixing logic from the frontend
   - Ensure consistent use of MetisMarkdown.processResponse in chat.js

4. **Testing**:
   - Test system prompts directly with the LLM
   - Test backend processing with various edge cases
   - Test the full flow from user query to rendered response
   - Test streaming responses to ensure proper formatting
   - Test with various code examples in different languages

- [x] **Implement Structured Output Approach for Text Formatting** (April 7, 2025)
   - [x] Create Pydantic models for structured output (FormattedResponse, CodeBlock, TextBlock)
   - [x] Update system prompts to instruct the LLM to use the structured output format
   - [x] Enhance RAG generation module to process structured output
   - [x] Implement multi-layered fallback strategy for robustness
   - [x] Add monitoring and analytics for text formatting performance
   - [x] Create a dashboard to visualize performance metrics
   - [x] Add support for tables, images, and math expressions
   - [x] Implement theme support for styling and visual customization
   - [x] Create comprehensive documentation in docs/implementation/Structured_Output_Implementation_Summary.md