# Metis RAG Project Tasks

This document outlines the current tasks, priorities, and TODOs for the Metis RAG project. It serves as a working document to track progress and guide development efforts.

## Current Priorities

1. **Fix Memory Functionality Issues**
2. **Improve RAG Response Accuracy**
3. **Enhance System Prompts**
4. **Optimize Document Processing**

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

1. Implement the memory functionality fixes to address the most critical issues
2. Test the memory functionality to ensure it works correctly
3. Proceed with RAG response accuracy improvements
4. Implement and test the remaining enhancements
5. Update documentation to reflect the changes

## Completion Criteria

- All memory functionality issues are resolved
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
```python
# In rag_engine.py
# Replace the conversation_id generation logic with:
if conversation_id:
    # Always use the provided conversation_id
    logger.info(f"Using provided conversation_id: {conversation_id}")
    self.conversation_id = conversation_id
else:
    # This should rarely happen since the API always creates a conversation
    logger.warning("No conversation_id provided, this may cause issues with memory operations")
```

#### Fix 2: User ID Handling
```python
# In rag_engine.py
# Replace the user_id generation logic with:
if not user_id:
    # Generate a proper UUID for anonymous users
    user_id = str(uuid.uuid4())
    logger.info(f"Generated UUID for anonymous user: {user_id}")
else:
    logger.info(f"Using provided user_id: {user_id}")

# Ensure user_id is a valid UUID
try:
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
except ValueError:
    # If conversion fails, generate a deterministic UUID based on the string
    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{user_id}")
    logger.warning(f"Converted invalid user_id format to UUID: {user_uuid}")
```

#### Fix 3: Session Management
```python
# In session.py
async def get_session():
    """
    Get a database session.
    
    This is an async generator that yields a session and handles proper cleanup.
    The session is automatically closed when the generator is closed.
    
    Yields:
        AsyncSession: Database session
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {str(e)}")
```

#### Fix 4: Memory Optimization
```python
# In rag_engine.py
async def _cleanup_memory(self) -> None:
    """
    Perform memory cleanup to reduce memory usage
    """
    try:
        # Import gc module for garbage collection
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Clear any cached data
        if hasattr(self, '_context_cache'):
            self._context_cache = {}
        
        # Clear any large temporary variables
        context = None
        sources = None
        
        logger.info("Memory cleanup performed after query processing")
    except Exception as e:
        logger.warning(f"Error during memory cleanup: {str(e)}")
```

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

1. **Fixed session.py to properly manage async sessions**
   - [x] Removed the second yield statement in the get_session function
   - [x] Created test for session management with concurrent operations

2. **Modified the RAG engine to respect the conversation_id passed from the API**
   - [x] Updated the conversation ID handling logic to never generate a new ID if one is provided
   - [x] Removed the code that generates a new conversation ID in the RAG engine
   - [x] Created test for conversation ID handling to ensure it's consistent throughout the system

## Next Implementation Tasks

1. **Run the test_fixes.py script to verify the fixes**
   - [x] Execute the test script to verify session management
   - [x] Verify conversation ID handling
   - [x] Verify memory operations with valid conversation IDs

2. **Address any remaining issues found during testing**
   - [x] Fix any issues discovered during testing
   - [x] Update documentation to reflect the changes

## Completed Implementation Tasks (April 6, 2025)

1. **Fixed session.py to properly manage async sessions**
   - [x] Improved session tracking with session_yielded flag
   - [x] Added proper rollback handling before closing sessions
   - [x] Added garbage collection to clean up lingering references
   - [x] Improved error handling for session closing

2. **Fixed memory_buffer.py to properly handle sessions**
   - [x] Properly tracked session generators to ensure they can be closed
   - [x] Added proper finally blocks to ensure sessions are closed
   - [x] Used aclose() on the session generator to trigger cleanup
   - [x] Separated session creation and management logic

3. **Fixed user ID format inconsistency in the RAG engine**
   - [x] Added more robust type checking for user IDs
   - [x] Used deterministic UUID generation for consistent mapping
   - [x] Updated the user_id variable after conversion for consistency
   - [x] Improved error handling for invalid user ID formats

4. **Fixed conversation ID persistence in the RAG engine**
   - [x] Ensured the RAG engine respects the conversation ID passed from the API
   - [x] Only extracted conversation_id from conversation_history if not already provided
   - [x] Properly passed the conversation_id to the memory buffer

5. **Fixed test_fixes.py to properly manage sessions**
   - [x] Used session generators correctly with proper cleanup
   - [x] Properly checked session state after closing
   - [x] Used async context managers for session management
   - [x] Fixed the test assertions to be more reliable