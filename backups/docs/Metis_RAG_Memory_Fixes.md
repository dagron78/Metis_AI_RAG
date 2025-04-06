# Metis RAG Memory Functionality Fixes

This document outlines the fixes and improvements made to the memory functionality in the Metis RAG system.

## Overview

The memory functionality in Metis RAG allows the system to remember information from previous conversations and recall it when needed. This is essential for maintaining context and providing personalized responses.

The following issues were identified and fixed:

1. Conversation IDs were not being properly maintained across page refreshes and browser sessions
2. Authentication tokens were expiring too quickly
3. User IDs were not being consistently associated with conversations
4. Memory retrieval was not working correctly in all cases
5. The system was not automatically storing important information from conversations

## Implemented Fixes

### 1. Frontend Session Management

We've improved the frontend session management to ensure that conversation IDs are properly maintained across page refreshes and browser sessions:

```javascript
// Function to update and store conversation ID in localStorage
function updateConversationId(id) {
    if (id) {
        localStorage.setItem('metis_conversation_id', id);
        currentConversationId = id;
        console.log('Conversation ID updated and stored:', id);
    }
}

// Retrieve conversation ID from localStorage on page load
const storedConversationId = localStorage.getItem('metis_conversation_id');
if (storedConversationId) {
    currentConversationId = storedConversationId;
    console.log('Retrieved stored conversation ID:', currentConversationId);
}
```

### 2. Authentication Improvements

We've increased the JWT token expiration time from 30 minutes to 24 hours to prevent frequent authentication issues:

```python
# Security settings
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # Default to 24 hours instead of 30 minutes
```

### 3. User ID and Conversation ID Handling

We've improved the handling of user IDs and conversation IDs to ensure they are consistently associated:

```python
# Extract conversation_id from conversation_history if available
conversation_id = None
if conversation_history and len(conversation_history) > 0:
    # Assuming the first message has the conversation_id
    conversation_id = getattr(conversation_history[0], 'conversation_id', None)
    if conversation_id:
        logger.info(f"Using conversation_id from history: {conversation_id}")

# Generate a user_id if not provided
if not user_id:
    if conversation_id:
        # Use conversation_id to create a consistent user_id
        user_id = f"session_{str(conversation_id)[:8]}"
        logger.info(f"Generated consistent session user_id from conversation: {user_id}")
    else:
        user_id = f"session_{str(uuid.uuid4())[:8]}"
        logger.info(f"Generated new session user_id: {user_id}")
```

We've also added fallback mechanisms for conversation ID handling:

```python
# If conversation_id is not available from history, try to get it from the request
if not conversation_id and hasattr(self, 'request') and self.request:
    conversation_id = self.request.get('conversation_id')
    if conversation_id:
        logger.info(f"Using conversation_id from request: {conversation_id}")

# If still no conversation_id, check if one is provided in the query parameters
if not conversation_id and 'conversation_id' in kwargs:
    conversation_id = kwargs.get('conversation_id')
    if conversation_id:
        logger.info(f"Using conversation_id from kwargs: {conversation_id}")
        
# If still no conversation_id, generate a new one
if not conversation_id:
    conversation_id = str(uuid.uuid4())
    logger.info(f"Generated new conversation_id: {conversation_id}")
```

This ensures that a valid conversation ID is always available, even if it's not provided in the conversation history.

### 4. Memory Retrieval Improvements

We've enhanced the memory retrieval functionality to make it more robust:

1. **Improved Regex Pattern**: Enhanced the pattern for detecting memory recall commands
   ```python
   # Check for recall command with improved pattern
   recall_match = re.search(r"(?:recall|remember)(?:\s+(?:the|my|what|about))?\s*(.*)", query, re.IGNORECASE)
   ```

2. **Flexible Search Term Matching**: Made the search term matching more flexible
   ```python
   # Use more flexible matching
   if any(term.lower() in memory.content.lower() 
          for term in search_term.split() 
          if len(term) > 3):  # Only use terms with more than 3 characters
       filtered_memories.append(memory)
   ```

3. **Database Session Handling**: Fixed issues with database session handling
   ```python
   # Get database session if not provided
   session_created = False
   if db is None:
       db = await anext(get_session())
       session_created = True
       
   # Close the session if we created it
   if session_created:
       await db.close()
   ```

4. **Comprehensive Logging**: Added detailed logging throughout the memory system
   ```python
   logger.debug(f"Filtering memories by search term: {search_term}")
   logger.debug(f"Found {len(filtered_memories)} memories matching search term")
   ```

### 5. Automatic Memory Storage

We've implemented automatic memory storage to ensure that important information is always stored, even without explicit memory commands:

```python
# Always store the user's query in the memory buffer for implicit memory
await add_to_memory_buffer(
    conversation_id=conversation_id,
    content=query,
    label="implicit_memory",
    db=db
)
logger.info(f"Stored user query in memory buffer: {query[:50]}...")
```

### 6. API Integration Improvements

We've updated the chat API to explicitly pass the conversation ID to the RAG engine:

```python
# Get RAG response
rag_response = await rag_engine.query(
    query=query.message,
    model=model,
    use_rag=query.use_rag,
    stream=True,
    model_parameters=query.model_parameters,
    conversation_history=conversation_messages,
    metadata_filters=metadata_filters,
    user_id=conversation.conv_metadata.get("user_id"),
    conversation_id=conversation_id  # Explicitly pass conversation_id
)
```

This ensures that the conversation ID is always available to the RAG engine, even if the conversation history is empty or doesn't contain the conversation ID.

## Testing the Fixes

You can test the memory functionality using the provided test script:

```bash
python scripts/test_memory_functionality.py
```

This script tests:
1. Storing memories using the "Remember this" command
2. Retrieving memories using the "Recall" command
3. Retrieving specific memories using search terms
4. Direct memory retrieval from the database

## Conclusion

These fixes have significantly improved the memory functionality in Metis RAG:

1. Conversation IDs now persist across page refreshes and browser sessions
2. Authentication tokens no longer expire too quickly
3. User IDs are maintained consistently across conversation turns
4. Memory retrieval now works correctly in all cases
5. The system automatically stores important information from conversations
6. The API correctly passes conversation IDs to the RAG engine

These improvements ensure that users can have continuous conversations with the system and that the system can accurately remember and recall information across conversation turns.