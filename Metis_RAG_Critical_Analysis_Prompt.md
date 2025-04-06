# Prompt for Critical Analysis of Metis RAG System Architecture

```
I'm working on improving a Retrieval-Augmented Generation (RAG) system called Metis RAG. I need your help to critically analyze the system's architecture and prompt design to identify fundamental improvements.

## Current System Overview

Metis RAG is a system that:
1. Retrieves relevant documents from a vector store based on user queries
2. Formats these documents as context for an LLM
3. Generates responses using this context and a system prompt
4. Handles conversation history and user information

## Current Issues

We've identified several problems:
- Document hallucination: The system claims to have documents that don't exist
- Citation misuse: The system uses citation markers [1] even when no documents are retrieved
- Content fabrication: When no documents are found, the system makes up information instead of admitting its limitations
- Monotonous responses: When no information is available, responses are repetitive and unhelpful

## Current Implementation

The system uses multiple prompt templates:
1. A system prompt (RAG_SYSTEM_PROMPT) that provides general instructions
2. Conversation templates that format the context, conversation history, and query
3. These templates are stored in different files, making it hard to maintain consistency

The key issue is that when no documents are found, the system is instructed to say "Based on the provided documents, I don't have information about [topic]" but doesn't offer alternatives or acknowledge limitations in a helpful way.

## Current Fix Approach

Our current fix involves:
1. Updating the system prompt to be more explicit about not fabricating information
2. Modifying conversation templates to use varied phrasing when acknowledging limitations
3. Adding instructions to offer general knowledge with clear disclaimers when documents aren't available
4. Suggesting alternative queries that might yield better results

## What I Need From You

1. **Fundamental Architecture Questions**:
   - Is the multi-prompt approach (system prompt + conversation templates) fundamentally flawed?
   - Should we consolidate all prompting logic into a single source of truth?
   - Is there a better way to structure the system to prevent hallucination and citation misuse?

2. **Prompt Design Analysis**:
   - Analyze our improved system prompt (below) and suggest fundamental improvements
   - Is the approach of "acknowledge limitations, then offer general knowledge" the right one?
   - How can we balance honesty about limitations with helpfulness?

3. **Single Source of Truth**:
   - Propose a design where all prompting logic is in one place
   - How should this be structured and maintained?
   - What are the tradeoffs of this approach?

## Our Improved System Prompt

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

## Technical Implementation Details

Here's how the system currently works:

1. The system has a `rag_engine.py` file that handles the main RAG logic:
   - It retrieves documents from a vector store
   - It formats the context and conversation history
   - It calls the LLM to generate a response

2. The prompting logic is split across multiple files:
   - `app/rag/system_prompts/rag.py` contains the RAG_SYSTEM_PROMPT
   - `app/rag/system_prompts/conversation.py` contains templates for formatting the context and query
   - `app/rag/rag_generation.py` contains the logic for constructing the final prompt

3. When generating a response, the system:
   - Calls `_create_system_prompt(query)` to get the system prompt
   - Calls `_create_full_prompt(query, context, conversation_context)` to format the context and query
   - Passes both to the LLM to generate a response

4. The conversation templates contain explicit instructions like:
   ```
   If the context doesn't contain the answer, explicitly state: "Based on the provided documents, I don't have information about [topic]."
   ```

This fragmented approach means that instructions are duplicated and sometimes contradictory across different files, making it hard to maintain consistency and leading to the issues we're seeing.

Please think deeply about the fundamental architecture of this system and whether our approach makes sense. Don't be afraid to suggest radical changes if they would lead to a better system.