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
## Metis RAG System Fixes - Detailed Implementation Plan (April 6, 2025)

### 1. Fix Session Management in test_conversation_id_persistence

```python
@pytest.mark.asyncio
async def test_conversation_id_persistence():
    """
    Test that the RAG engine respects the conversation ID passed from the API
    by creating a conversation in the database first
    """
    logger.info("Testing conversation ID persistence...")
    
    # Create a test conversation ID as a UUID object
    test_conversation_id = uuid.uuid4()
    logger.info(f"Test conversation ID: {test_conversation_id}")
    
    # Create a test user ID as a UUID object
    test_user_id = uuid.uuid4()
    logger.info(f"Test user ID: {test_user_id}")
    
    # Create a session generator
    session_gen = get_session()
    db = None
    
    try:
        # Get the session
        db = await anext(session_gen)
        
        # Create a conversation in the database
        conversation = Conversation(
            id=test_conversation_id,
            user_id=None,  # Set to None to avoid foreign key constraint
            conv_metadata={"title": "Test Conversation"}
        )
        db.add(conversation)
        await db.commit()
        logger.info(f"Created test conversation with ID: {test_conversation_id}")
        
        # Initialize RAG engine
        rag_engine = RAGEngine()
        
        # Create a separate session for the RAG engine to use
        # This prevents session conflicts
        rag_session_gen = get_session()
        rag_db = await anext(rag_session_gen)
        
        try:
            # Test with provided conversation ID
            query_result = await rag_engine.query(
                query="Test query",
                conversation_id=test_conversation_id,
                user_id=str(test_user_id),  # Use a valid UUID string
                use_rag=False,  # Disable RAG to simplify the test
                db=rag_db  # Pass the dedicated session
            )
            
            logger.info(f"Query result: {query_result}")
            
            # Verify that a memory was created for this conversation
            memories = await get_memory_buffer(
                conversation_id=test_conversation_id,
                db=db  # Use the original session
            )
            
            # Verify that at least one memory was created
            assert len(memories) > 0, "At least one memory should have been created"
            logger.info(f"Found {len(memories)} memories for conversation {test_conversation_id}")
            
            # Verify the memory has the correct conversation ID
            assert memories[0].conversation_id == test_conversation_id, \
                f"Memory should have the correct conversation ID: {test_conversation_id}, but got: {memories[0].conversation_id}"
            
            logger.info(f"Memory has the correct conversation ID: {memories[0].conversation_id}")
            
            # Clean up
            await db.execute(text(f"DELETE FROM memories WHERE conversation_id = '{test_conversation_id}'"))
            await db.execute(text(f"DELETE FROM conversations WHERE id = '{test_conversation_id}'"))
            await db.commit()
            
            logger.info("Conversation ID persistence test passed")
        finally:
            # Close the RAG session
            if rag_session_gen:
                await rag_session_gen.aclose()
    finally:
        # Close the main session
        if session_gen:
            await session_gen.aclose()
```

### 2. Fix RAG Engine to Accept a Database Session

```python
async def query(self,
               query: str,
               model: str = DEFAULT_MODEL,
               use_rag: bool = True,
               top_k: int = 10,
               system_prompt: Optional[str] = None,
               stream: bool = False,
               model_parameters: Dict[str, Any] = None,
               conversation_history: Optional[List[Message]] = None,
               metadata_filters: Optional[Dict[str, Any]] = None,
               user_id: Optional[str] = None,
               conversation_id: Optional[str] = None,
               db: AsyncSession = None,  # Add db parameter
               **kwargs) -> Dict[str, Any]:
    """
    Query the RAG engine with optional conversation history and metadata filtering
    
    Args:
        query: Query string
        model: Model to use
        use_rag: Whether to use RAG
        conversation_id: Conversation ID for memory operations
        top_k: Number of results to return
        system_prompt: System prompt
        stream: Whether to stream the response
        model_parameters: Model parameters
        conversation_history: Conversation history
        metadata_filters: Metadata filters
        user_id: User ID for permission filtering
        db: Database session to use for memory operations
        
    Returns:
        Response dictionary
    """
    # ... existing code ...
    
    # Process memory commands if user_id is provided
    processed_query = query
    memory_response = None
    memory_operation = None
    
    if user_id and conversation_id:
        processed_query, memory_response, memory_operation = await process_query(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db  # Pass the provided session
        )
        
        # ... rest of the method ...
```

### 3. Fix User ID Format Inconsistency

```python
# Test with provided conversation ID
query_result = await rag_engine.query(
    query="Test query",
    conversation_id=test_conversation_id,
    user_id=str(uuid.uuid4()),  # Use a valid UUID string
    use_rag=False  # Disable RAG to simplify the test
)
```

### 4. Improve Session Management in memory_buffer.py

```python
async def process_query(
    query: str,
    user_id: str,
    conversation_id: Union[str, UUID],
    db: AsyncSession = None
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Process a query for memory commands before sending to RAG
    
    Args:
        query: User query
        user_id: User ID
        conversation_id: Conversation ID (can be string or UUID)
        db: Database session
        
    Returns:
        Tuple of (processed_query, memory_response, memory_operation)
    """
    # Track if we created a session
    session_created = False
    session_gen = None
    
    try:
        # Get database session if not provided
        if db is None:
            session_gen = get_session()
            db = await anext(session_gen)
            session_created = True
            logger.debug("Created new session for process_query")
        else:
            logger.debug("Using provided session for process_query")
        
        # Convert conversation_id to UUID if it's a string
        if isinstance(conversation_id, str):
            try:
                conversation_id = UUID(conversation_id)
                logger.info(f"Converted string conversation_id to UUID: {conversation_id}")
            except ValueError:
                logger.error(f"Invalid conversation_id format: {conversation_id}")
                # Return original query without memory processing
                return query, None, None
        
        # Convert user_id to UUID if it's a string
        user_uuid = None
        if isinstance(user_id, str):
            try:
                user_uuid = UUID(user_id)
                logger.info(f"Converted string user_id to UUID: {user_uuid}")
            except ValueError:
                # Generate a deterministic UUID based on the string
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{user_id}")
                logger.warning(f"Invalid user_id format: {user_id}, generated deterministic UUID: {user_uuid}")
        elif isinstance(user_id, UUID):
            user_uuid = user_id
        else:
            logger.error(f"Unexpected user_id type: {type(user_id)}")
            # Return original query without memory processing
            return query, None, None
        
        # ... rest of the function ...
    finally:
        # Only close the session if we created it
        if session_created and session_gen:
            try:
                # Close the generator to trigger the finally block in get_session
                await session_gen.aclose()
                logger.debug("Closed session generator in process_query")
            except Exception as e:
                logger.warning(f"Error closing session generator: {str(e)}")
```

### 5. Improve Session Management in session.py

```python
async def get_session():
    """
    Get a database session.
    
    This is an async generator that yields a session and handles proper cleanup.
    The session is automatically closed when the generator is closed.
    
    Yields:
        AsyncSession: Database session
    """
    # Create a new session
    session = AsyncSessionLocal()
    
    # Track if we've yielded the session
    session_yielded = False
    
    try:
        # Yield the session to the caller
        session_yielded = True
        yield session
    except Exception as e:
        # Log the error
        logger.error(f"Session error: {str(e)}")
        
        # Ensure transaction is rolled back on error
        if session_yielded:
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.warning(f"Error rolling back session: {str(rollback_error)}")
        
        # Re-raise the exception
        raise
    finally:
        # Clean up the session
        if session_yielded:
            try:
                # Check if the session is in a transaction
                if session.in_transaction():
                    # Roll back any active transaction
                    await session.rollback()
                
                # Close the session to return connections to the pool
                await session.close()
                
                # Force garbage collection to clean up any lingering references
                import gc
                gc.collect()
            except Exception as e:
                logger.warning(f"Error during session cleanup: {str(e)}")
```
   - [ ] Ensure the session is not closed prematurely
   - [ ] Add proper error handling for session operations

- [ ] **Fix User ID Format Inconsistency**
   - [ ] Ensure valid UUIDs are passed to the RAG engine
   - [ ] Fix the root cause of passing invalid string IDs
   - [ ] Update tests to use valid UUID strings
   - [ ] Add validation for user IDs at the API level

- [ ] **Improve Session Management in memory_buffer.py**
   - [ ] Enhance process_query function to be more robust
   - [ ] Add better logging for session operations
   - [ ] Ensure sessions are properly tracked and closed
   - [ ] Add proper error handling for concurrent operations

- [ ] **Improve Session Management in session.py**
   - [ ] Enhance get_session function to handle concurrent operations better
   - [ ] Add more robust error handling for session operations
   - [ ] Implement better connection pool management
   - [ ] Add more detailed logging for session lifecycle events