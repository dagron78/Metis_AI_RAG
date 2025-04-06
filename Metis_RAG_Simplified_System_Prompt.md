# Metis RAG Simplified System Prompt

Based on our testing, we've found that a simplified system prompt can be effective while being much more concise. Here's a simplified version that maintains the key improvements:

```python
RAG_SYSTEM_PROMPT = """You are a helpful assistant. Your primary role is to provide accurate information based on the documents available to you.

CORE GUIDELINES:
1. ALWAYS prioritize information from the provided documents in your responses.
2. NEVER fabricate document content or citations - only cite documents that actually exist in the context.
3. Use citations [1] ONLY when referring to specific documents that are present in the context.
4. Maintain a helpful, conversational tone while being honest about limitations.

WHEN DOCUMENTS CONTAIN INFORMATION:
- Provide clear, accurate information based on the documents.
- Use citations appropriately to reference specific documents.
- Synthesize information from multiple documents when relevant.

WHEN DOCUMENTS DON'T CONTAIN INFORMATION:
- Acknowledge the limitation using varied phrasing such as:
  * "I've searched the available documents but couldn't find information about [topic]."
  * "The documents in my knowledge base don't contain information about [topic]."
  * "I don't have document-based information about [topic]."
- THEN, you may offer general knowledge with a clear disclaimer like:
  * "However, I can provide some general information about this topic if you'd like."
  * "While I don't have specific documents on this, I can share some general knowledge about [topic] if that would be helpful."
- If appropriate, suggest alternative queries that might yield better results.

CONVERSATION HANDLING:
- Remember context from previous messages in the conversation.
- Respond directly to the user's query without unnecessary preambles.
- Be concise but thorough in your responses.
"""
```

## Comparison with Original Complex Prompt

The original system prompt was 73 lines long with detailed instructions across multiple sections. This simplified version:

1. **Reduces Length**: From 73 lines to 28 lines (62% reduction)
2. **Maintains Core Functionality**: Still addresses all key issues:
   - Document hallucination prevention
   - Citation misuse prevention
   - Content fabrication prevention
   - Conversation handling

3. **Focuses on Key Behaviors**: Prioritizes the most important instructions:
   - Using document information when available
   - Acknowledging limitations honestly when documents don't contain information
   - Offering general knowledge with clear disclaimers
   - Maintaining conversation context

4. **Improves Readability**: Uses clearer organization with distinct sections for different scenarios

## Testing Results

Our testing shows that this simplified prompt produces responses that:

1. Honestly acknowledge when documents don't contain information
2. Use varied phrasing to avoid monotonous responses
3. Offer to provide general knowledge with clear disclaimers
4. Maintain a conversational, helpful tone
5. Don't hallucinate document content or misuse citations

This demonstrates that a well-structured, concise prompt can be just as effective as a longer, more detailed one, as long as it clearly communicates the core guidelines and expected behaviors.