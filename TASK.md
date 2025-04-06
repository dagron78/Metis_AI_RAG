# Metis RAG Project Tasks

This document outlines the current tasks, priorities, and TODOs for the Metis RAG project. It serves as a working document to track progress and guide development efforts.

## Current Priorities

1. ✅ **Fix Memory Functionality Issues**
2. ✅ **Fix Performance and Authentication Issues**
3. **Improve RAG Response Accuracy**
4. **Enhance System Prompts**
5. **Optimize Document Processing**

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

## Documentation Updates

- [ ] **Update API Documentation**
  - [ ] Document memory-related endpoints
  - [ ] Update authentication endpoints documentation
  - [ ] Document new system configuration options

- [ ] **Update User Guide**
  - [ ] Add memory command usage instructions
  - [ ] Update document upload guidelines
  - [ ] Add troubleshooting section for common issues

- [ ] **Update Developer Documentation**
  - [ ] Document memory buffer implementation
  - [ ] Update system prompt configuration guide
  - [ ] Add testing guidelines for new features
  - [ ] Document ID lifecycle and persistence throughout the system
  - [ ] Add session management best practices

## Next Steps

1. ✅ Implement the memory functionality fixes to address the most critical issues
2. ✅ Test the memory functionality to ensure it works correctly
3. ✅ Fix the remaining issues identified in log analysis (query classification, analytics auth, memory management, user ID edge cases, performance)
4. Proceed with RAG response accuracy improvements
5. Implement and test the remaining enhancements
6. Update documentation to reflect the changes
7. Create comprehensive unit tests for all fixed components

## Completion Criteria

- ✅ All memory functionality issues are resolved
- ✅ Performance and authentication issues are fixed
- RAG responses accurately reflect available documents
- System prompts effectively guide the LLM behavior
- Document processing is optimized for performance
- Comprehensive tests verify all functionality
- Documentation is updated to reflect all changes

## Metis RAG System Fixes - Implementation Plan

### 1. Root Cause Analysis

#### Issue 1: Conversation ID Persistence Timing
- The API creates a conversation in the database and passes its ID to the RAG engine
- The RAG engine ignores this ID and generates a new one that isn't persisted in the database
- When memory_buffer.py tries to use this new ID, it fails to find the conversation in the database

#### Issue 2: User ID Format Inconsistency
- The system expects UUIDs for user_id in the database
- The RAG engine generates string-based session IDs (e.g., "session_bb90aa96") when no authenticated user is present
- These string IDs are incompatible with database columns expecting UUIDs

#### Issue 3: Session Management
- SQLAlchemy async sessions are not being properly managed
- Sessions are being closed while operations are still in progress

### 2. Implementation Details

#### Fix 1: Conversation ID Consistency
- Replace the conversation_id generation logic in rag_engine.py
- Always use the provided conversation_id
- Log warnings when no conversation_id is provided

#### Fix 2: User ID Handling
- Replace the user_id generation logic in rag_engine.py
- Generate proper UUIDs for anonymous users
- Ensure user_id is a valid UUID
- Generate deterministic UUIDs for invalid user_id formats

#### Fix 3: Session Management
- Improve get_session function in session.py
- Implement proper session cleanup
- Add error handling for session operations

#### Fix 4: Memory Optimization
- Implement memory cleanup in rag_engine.py
- Force garbage collection after query processing
- Clear cached data and large temporary variables

### 3. Testing Plan

1. **Unit Tests**:
   - Test session management with concurrent operations
   - Test UUID conversion and validation
   - Test conversation ID handling

2. **Integration Tests**:
   - Test the full flow from API to RAG engine to memory buffer
   - Verify conversation IDs are consistent throughout the system
   - Verify memory operations work correctly

3. **Load Tests**:
   - Test memory usage under load
   - Verify the system can handle multiple concurrent requests

## Completed Implementation Tasks

- [x] **Fixed session.py to properly manage async sessions** (April 6, 2025)
   - [x] Improved session tracking with session_yielded flag
   - [x] Added proper rollback handling before closing sessions
   - [x] Added garbage collection to clean up lingering references
   - [x] Improved error handling for session closing

- [x] **Fixed memory_buffer.py to properly handle sessions** (April 6, 2025)
   - [x] Properly tracked session generators to ensure they can be closed
   - [x] Added proper finally blocks to ensure sessions are closed
   - [x] Used aclose() on the session generator to trigger cleanup
   - [x] Separated session creation and management logic

- [x] **Fixed user ID format inconsistency in the RAG engine** (April 6, 2025)
   - [x] Added more robust type checking for user IDs
   - [x] Used deterministic UUID generation for consistent mapping
   - [x] Updated the user_id variable after conversion for consistency
   - [x] Improved error handling for invalid user ID formats

- [x] **Fixed conversation ID persistence in the RAG engine** (April 6, 2025)
   - [x] Ensured the RAG engine respects the conversation ID passed from the API
   - [x] Only extracted conversation_id from conversation_history if not already provided
   - [x] Properly passed the conversation_id to the memory buffer

- [x] **Fixed test_fixes.py to properly manage sessions** (April 6, 2025)
   - [x] Used session generators correctly with proper cleanup
   - [x] Properly checked session state after closing
   - [x] Used async context managers for session management
   - [x] Fixed the test assertions to be more reliable

- [x] **Run the test_fixes.py script to verify the fixes** (April 6, 2025)
   - [x] Execute the test script to verify session management
   - [x] Verify conversation ID handling
   - [x] Verify memory operations with valid conversation IDs

- [x] **Address any remaining issues found during testing** (April 6, 2025)
   - [x] Fix any issues discovered during testing
   - [x] Update documentation to reflect the changes

## Completed Implementation Tasks (April 6, 2025)

- [x] **Fix Session Management in test_conversation_id_persistence**
   - [x] Modify the test to use separate sessions for RAG engine and database operations
   - [x] Ensure sessions are not closed while they're still being used
   - [x] Add proper error handling for session operations
   - [x] Implement more robust session lifecycle management

- [x] **Fix RAG Engine to Accept a Database Session**
   - [x] Add db parameter to query method
   - [x] Pass the provided session to memory buffer operations
   - [x] Ensure the session is not closed prematurely
   - [x] Add proper error handling for session operations

- [x] **Fix User ID Format Inconsistency**
   - [x] Ensure valid UUIDs are passed to the RAG engine
   - [x] Fix the root cause of passing invalid string IDs
   - [x] Update tests to use valid UUID strings
   - [x] Add validation for user IDs at the API level

- [x] **Improve Session Management in memory_buffer.py**
   - [x] Enhance process_query function to be more robust
   - [x] Add better logging for session operations
   - [x] Ensure sessions are properly tracked and closed
   - [x] Add proper error handling for concurrent operations

- [x] **Improve Session Management in session.py**
   - [x] Enhance get_session function to handle concurrent operations better
   - [x] Add more robust error handling for session operations
   - [x] Implement better connection pool management
   - [x] Add more detailed logging for session lifecycle events

## Completed Implementation Tasks (April 6, 2025 - Part 2)

- [x] **Fix Incorrect Query Type Detection**
   - [x] Refine code keywords list in `_is_code_related_query` method to avoid false positives
   - [x] Add negative patterns (terms that indicate it's NOT a code query)
   - [x] Implement word boundary checks to prevent partial matches
   - [x] Add more detailed logging of matched keywords/patterns
   - [x] Fix issue with "RAG summary" query being incorrectly classified as code-related

- [x] **Fix Analytics Endpoint Authentication**
   - [x] Modify `_record_analytics` method to include authentication headers
   - [x] Implement a method to get a system JWT token for internal API calls
   - [x] Use environment variables for API endpoint configuration
   - [x] Add retry logic for failed analytics requests
   - [x] Ensure analytics failures don't impact the main application flow

- [x] **Improve Memory Management**
   - [x] Enhance the `_cleanup_memory` method to be more aggressive
   - [x] Implement more detailed memory usage logging
   - [x] Add adaptive behavior based on system load
   - [x] Clear additional caches and temporary variables
   - [x] Add emergency cleanup for critical memory situations

- [x] **Fix User ID Edge Cases**
   - [x] Ensure all user ID generation paths create valid UUIDs
   - [x] Replace any "system" or session-based IDs with proper UUIDs
   - [x] Add validation for user IDs before database operations
   - [x] Log warnings for invalid user IDs
   - [x] Convert invalid IDs to valid UUIDs when necessary

- [x] **Optimize Performance**
   - [x] Add detailed timing logs for each step of response generation
   - [x] Identify bottlenecks in the process
   - [x] Streamline the prompt creation process
   - [x] Add timing summaries for performance analysis
   - [x] Enhance the caching strategy for frequently used prompts

## Next Implementation Tasks (April 7, 2025)

- [ ] **Create Unit Tests for Query Classification**
   - [ ] Create test cases for code-related queries
   - [ ] Create test cases for non-code queries
   - [ ] Create test cases for edge cases
   - [ ] Verify classification accuracy
   - [ ] Add regression tests for fixed issues

- [ ] **Implement Memory Usage Monitoring**
   - [ ] Create a memory usage dashboard
   - [ ] Set up alerts for high memory usage
   - [ ] Implement automatic scaling based on memory usage
   - [ ] Add memory usage metrics to analytics
   - [ ] Create a memory usage report generator

- [ ] **Optimize Caching Strategy**
   - [ ] Analyze cache hit/miss rates
   - [ ] Implement more efficient cache key generation
   - [ ] Add cache warming for frequently used prompts
   - [ ] Implement cache eviction policies
   - [ ] Add cache statistics to analytics

- [ ] **Enhance Analytics System**
   - [ ] Create a comprehensive analytics dashboard
   - [ ] Add more detailed query performance metrics
   - [ ] Implement user behavior analytics
   - [ ] Add document usage analytics
   - [ ] Create periodic analytics reports

- [ ] **Improve Error Handling and Logging**
   - [ ] Implement centralized error handling
   - [ ] Add structured logging for all components
   - [ ] Create error reporting dashboard
   - [ ] Implement automatic error notification
   - [ ] Add error trend analysis
   - [ ] Identify bottlenecks in the process
   - [ ] Streamline the prompt creation process
   - [ ] Reduce unnecessary string operations
   - [ ] Enhance the caching strategy for frequently used prompts