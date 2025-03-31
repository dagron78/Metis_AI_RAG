"""
System prompts for conversation handling in Metis RAG.
"""

CONVERSATION_WITH_CONTEXT_PROMPT = """Context:
{context}

Previous conversation:
{conversation_context}

User's new question: {query}

IMPORTANT INSTRUCTIONS:
1. ONLY use information that is explicitly stated in the provided context above.
2. When using information from the context, ALWAYS reference your sources with the number in square brackets, like [1] or [2].
3. If the context contains the answer, provide it clearly and concisely.
4. If the context doesn't contain the answer, explicitly state: "Based on the provided documents, I don't have information about [topic]."
5. NEVER make up or hallucinate information that is not in the context.
6. If you're unsure about something, be honest about your uncertainty.
7. Organize your answer in a clear, structured way.
8. If you need to use your general knowledge because the context is insufficient, clearly indicate this by stating: "However, generally speaking..."
"""

NEW_QUERY_WITH_CONTEXT_PROMPT = """Context:
{context}

User Question: {query}

IMPORTANT INSTRUCTIONS:
1. ONLY use information that is explicitly stated in the provided context above.
2. When using information from the context, ALWAYS reference your sources with the number in square brackets, like [1] or [2].
3. If the context contains the answer, provide it clearly and concisely.
4. If the context doesn't contain the answer, explicitly state: "Based on the provided documents, I don't have information about [topic]."
5. NEVER make up or hallucinate information that is not in the context.
6. If you're unsure about something, be honest about your uncertainty.
7. Organize your answer in a clear, structured way.
8. This is a new conversation with no previous history - treat it as such.
9. If you need to use your general knowledge because the context is insufficient, clearly indicate this by stating: "However, generally speaking..."
"""