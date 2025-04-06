# Metis RAG System Fix Plan

## Identified Issues

After analyzing the code and logs, I've identified several critical issues with the Metis RAG system:

### 1. Document Hallucination
- The system claims to have access to a document "Introduction to China's Provinces" when it doesn't exist
- When no documents are found, the system doesn't clearly communicate this to the user

### 2. Memory Loss
- The system forgets the user's name (Charles) despite being told earlier in the conversation
- Conversation history is not being effectively utilized

### 3. Content Fabrication
- When asked for content from a non-existent document, it generates text instead of admitting it doesn't have it
- The system is not properly handling "no documents found" scenarios

### 4. Citation Misuse
- The system uses citation markers [1] that don't correspond to actual documents
- Citations are included even when no actual documents are retrieved

### 5. Vector Store Query Issues
- The handling of empty search results in the vector store could be improved
- The "no documents found" message from the vector store isn't being prominently included in the context
- Permission filtering might be causing documents to be filtered out without clear communication to the user

## Fix Plan

### 1. Improve System Prompts

The current system prompts have good instructions, but they need to be strengthened:

```python
# Modified RAG_SYSTEM_PROMPT
RAG_SYSTEM_PROMPT = """You are a helpful assistant that provides accurate, factual responses based on the Metis RAG system.

ROLE AND CAPABILITIES:
- You have access to a Retrieval-Augmented Generation (RAG) system that can retrieve relevant documents to answer questions.
- Your primary function is to use the retrieved context to provide accurate, well-informed answers.
- You can cite sources using the numbers in square brackets like [1] or [2] ONLY when they are provided in the context.

STRICT GUIDELINES FOR USING CONTEXT:
- ONLY use information that is explicitly stated in the provided context.
- NEVER make up or hallucinate information that is not in the context.
- If the context doesn't contain the answer, explicitly state: "Based on the provided documents, I don't have information about [topic]."
- NEVER pretend to have documents or information that isn't in the context.
- If the context indicates no documents were found, clearly state this and DO NOT fabricate document information.
- DO NOT create fake document IDs, titles, or content.
- If asked about a specific document that isn't in the context, clearly state you don't have access to that document.
- NEVER use citation markers [1] unless actual documents are referenced in the context.

CONVERSATION HANDLING:
- IMPORTANT: Remember key user information (like names) from previous exchanges.
- When a user introduces themselves, store and use their name in future responses.
- Only refer to previous conversations if they are explicitly provided in the conversation history.
- NEVER fabricate or hallucinate previous exchanges that weren't actually provided.

WHEN CONTEXT IS INSUFFICIENT:
- Clearly state: "Based on the provided documents, I don't have information about [topic]."
- Be specific about what information is missing.
- Only then provide a general response based on your knowledge, and clearly state: "However, generally speaking..." to distinguish this from information in the context.
- Never pretend to have information that isn't in the context.

RESPONSE STYLE:
- Be clear, direct, and helpful.
- Structure your responses logically.
- Use appropriate formatting to enhance readability.
- Maintain a consistent, professional tone throughout the conversation.
- For new conversations with no history, start fresh without referring to non-existent previous exchanges.
- DO NOT start your responses with phrases like "I've retrieved relevant context" or similar preambles.
- Answer questions directly without mentioning the retrieval process.
- Only use citation markers [1] when actual documents are referenced in the context.
"""
```

### 2. Enhance "No Documents Found" Handling

Modify how the system handles cases where no documents are found to make it more explicit:

```python
# In rag_engine.py, modify the context formatting for empty results
if len(relevant_results) == 0:
    logger.warning("No sufficiently relevant documents found for the query")
    context = "IMPORTANT: NO DOCUMENTS FOUND. No sufficiently relevant documents found in the knowledge base for your query. The system cannot provide a specific answer based on the available documents."
elif len(context.strip()) < 50:  # Very short context might not be useful
    logger.warning("Context is too short to be useful")
    context = "IMPORTANT: INSUFFICIENT CONTEXT. The retrieved context is too limited to provide a comprehensive answer to your query. The system cannot provide a specific answer based on the available documents."
```

### 3. Improve Vector Store Empty Results Handling

Enhance how the vector store communicates when no results are found:

```python
# In vector_store.py, modify the search method to provide clearer empty results
if results["ids"] and len(results["ids"][0]) > 0:
    logger.info(f"Raw search results: {len(results['ids'][0])} chunks found")
    
    # ... existing code for processing results ...
    
else:
    logger.warning(f"No results found for query: {query[:50]}...")
    # Return a special result that clearly indicates no documents were found
    formatted_results = [{
        "chunk_id": "no_results",
        "content": "IMPORTANT: NO DOCUMENTS FOUND. The system searched for relevant documents but found none that match your query.",
        "metadata": {"document_id": "no_results", "filename": "No Results", "tags": [], "folder": "/"},
        "distance": 1.0  # Maximum distance (least relevant)
    }]
```

### 4. Add User Information Extraction

Implement a mechanism to extract and track important user information from the conversation:

```python
# In rag_engine.py, add user information extraction
def _extract_user_info(self, conversation_history):
    """Extract important user information from conversation history"""
    user_info = {}
    
    # Extract user name
    name_patterns = [
        r"my name is (\w+)",
        r"I am (\w+)",
        r"I'm (\w+)",
        r"call me (\w+)"
    ]
    
    for message in conversation_history:
        if message.role == "user":
            for pattern in name_patterns:
                match = re.search(pattern, message.content, re.IGNORECASE)
                if match:
                    user_info["name"] = match.group(1)
    
    return user_info

# Then in the query method, add this to the context
user_info = self._extract_user_info(conversation_history) if conversation_history else {}
if user_info:
    user_context = f"USER INFORMATION: "
    if "name" in user_info:
        user_context += f"The user's name is {user_info['name']}. "
    
    # Add user context to the beginning of the full prompt
    full_prompt = user_context + "\n\n" + full_prompt
```

### 5. Fix Citation Handling

Modify how citations are included in responses to ensure they only appear when actual documents are referenced:

```python
# In rag_engine.py, modify the context formatting to only include citations when documents exist
if search_results and len(relevant_results) > 0:
    # Process search results and format context with citations
    context_pieces = []
    
    for i, result in enumerate(relevant_results):
        # ... existing code for formatting context pieces ...
        
        # Format the context piece with metadata and citation marker
        context_piece = f"[{i+1}] Source: {filename}, Tags: {tags}, Folder: {folder}\n\n{result['content']}"
        context_pieces.append(context_piece)
        
        # ... existing code for tracking sources ...
    
    # Join all context pieces
    context = "\n\n".join(context_pieces)
else:
    # No results or no relevant results
    context = "IMPORTANT: NO RELEVANT DOCUMENTS FOUND. The system searched for relevant documents but found none that match your query."
    # Empty the sources list to ensure no citations are included
    sources = []
```

### 6. Add Verification Step Before Response Generation

Add a verification step that checks if any documents were actually retrieved before generating a response:

```python
# In rag_engine.py, add a verification step before generating a response
# After retrieving context but before generating a response
if not sources:
    logger.warning("No sources found for query, adding explicit instruction to not use citations")
    # Add an explicit instruction to not use citations when no sources are found
    full_prompt += "\n\nIMPORTANT: No documents were found for this query. DO NOT use citation markers [1] in your response and clearly state that no relevant documents were found."
```

### 7. Improve Vector Store Stats Checking

Enhance how the system checks if there are any documents in the vector store:

```python
# In rag_engine.py, improve the check for documents in the vector store
# Check if there are any documents in the vector store
stats = self.vector_store.get_stats()
if stats["count"] == 0:
    logger.warning("RAG is enabled but no documents are available in the vector store")
    # Add a prominent note to the context that no documents are available
    context = "IMPORTANT: NO DOCUMENTS AVAILABLE. The knowledge base is empty. Please upload documents to use RAG effectively."
    # Empty the sources list to ensure no citations are included
    sources = []
    # Skip the retrieval process entirely
    return context, sources, []
```

### 8. Enhance Error Handling

Improve error handling to ensure errors are properly communicated to the user:

```python
# In rag_engine.py, enhance error handling in the query method
try:
    # ... existing code ...
except Exception as e:
    logger.error(f"Error in RAG retrieval: {str(e)}")
    # Provide a clear error message in the context
    context = f"IMPORTANT: RETRIEVAL ERROR. An error occurred during document retrieval: {str(e)}. The system cannot provide a specific answer based on the available documents."
    # Empty the sources list to ensure no citations are included
    sources = []
    # Continue with response generation using the error context
```

## Testing Plan

1. **Empty Vector Store Test**
   - Clear the vector store
   - Submit a query
   - Verify the system clearly states no documents are available

2. **No Relevant Documents Test**
   - Add documents to the vector store that are unrelated to the query
   - Submit a query
   - Verify the system clearly states no relevant documents were found

3. **User Information Test**
   - Start a conversation with "My name is [Name]"
   - Ask a follow-up question
   - Verify the system remembers and uses the name

4. **Document Request Test**
   - Ask about a specific document that doesn't exist
   - Verify the system clearly states it doesn't have that document

5. **Citation Test**
   - Add relevant documents to the vector store
   - Submit a query
   - Verify citations are only included when actual documents are referenced

## Implementation Strategy

1. Implement the system prompt changes first, as this is the simplest change with potentially significant impact
2. Add the user information extraction functionality
3. Enhance the "no documents found" handling in both the vector store and RAG engine
4. Implement the citation handling improvements
5. Add the verification step before response generation
6. Enhance error handling
7. Test each change incrementally to ensure it resolves the specific issue it targets

## Conclusion

The issues in the Metis RAG system stem from a combination of factors:
1. The LLM not strictly following the system prompt instructions
2. Insufficient handling of "no documents found" scenarios
3. Lack of user information tracking in conversation history
4. Improper citation handling

By implementing the changes outlined in this plan, we can significantly improve the system's accuracy, honesty, and user experience. The key is to make the instructions more explicit, improve how empty results are handled, and ensure the system only includes citations when actual documents are referenced.