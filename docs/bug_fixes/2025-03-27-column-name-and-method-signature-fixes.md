# Bug Fixes: Column Name and Method Signature Issues (2025-03-27)

## Issues Fixed

### 1. Column Name Issue in Document Listing API Endpoint

**Problem:**
The document listing API endpoint was failing with a `UndefinedColumnError: column "metadata" does not exist` error. This was due to a previous database schema change where the column was renamed from `metadata` to `doc_metadata` to avoid conflicts with SQLAlchemy's reserved `metadata` attribute, but the SQL queries in the API endpoints were not updated to reflect this change.

**Files Modified:**
- `app/api/documents.py`

**Changes Made:**
- Updated SQL queries in `list_documents` function to use `doc_metadata` instead of `metadata AS doc_metadata`
- Updated SQL queries in `filter_documents` function to use `doc_metadata` instead of `metadata AS doc_metadata`
- Fixed the SQL query in `process_document_background` function to use `doc_metadata` instead of `metadata`
- Updated the Document creation in `process_document_background` to use `doc_row.doc_metadata` instead of `doc_row.metadata`

### 2. Conversation Repository Method Signature Issue

**Problem:**
The chat functionality was failing with a `ConversationRepository.create_conversation() got an unexpected keyword argument 'user_id'` error. This was because the `create_conversation` method in the `ConversationRepository` class was updated to use `self.user_id` from the constructor instead of accepting it as a parameter, but the calls to this method in the chat API endpoints were still passing the `user_id` parameter.

**Files Modified:**
- `app/api/chat.py`

**Changes Made:**
- Removed the `user_id` parameter from all calls to `conversation_repository.create_conversation()` in the chat API endpoints
- This includes calls in the `query_chat`, `langgraph_query_chat`, and `enhanced_langgraph_query_chat` functions

## Impact

These fixes resolve the errors that were preventing the document listing and chat functionality from working properly:
- The document listing endpoint can now correctly query the database using the renamed column
- The chat functionality can now create conversations without passing the user_id parameter

## Testing

After applying these fixes, the following functionality should be tested:
1. Document listing and filtering
2. Chat functionality with different models
3. RAG-enabled chat queries
4. LangGraph RAG Agent queries (if enabled)
5. Enhanced LangGraph RAG Agent queries (if enabled)