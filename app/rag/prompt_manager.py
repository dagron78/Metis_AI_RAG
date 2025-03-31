"""
Prompt Manager for RAG System

This module provides a centralized manager for all prompt-related operations,
serving as a single source of truth for prompt templates and instructions.
"""
import logging
import os
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("app.rag.prompt_manager")

class PromptManager:
    """
    PromptManager serves as a single source of truth for all prompt-related operations.
    
    It manages templates, handles state-based prompt selection, and ensures
    consistent instructions across different scenarios.
    """
    
    def __init__(self):
        """Initialize the PromptManager with templates."""
        self.templates = self._load_templates()
        logger.info("PromptManager initialized with templates")
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Load all prompt templates.
        
        Returns:
            Dictionary of templates for different scenarios
        """
        # Base system prompt that applies to all scenarios
        base_system_prompt = """You are a helpful assistant. Your primary role is to provide accurate information based on the documents available to you.

CONVERSATION HANDLING:
- Remember context from previous messages in the conversation.
- Respond directly to the user's query without unnecessary preambles.
- Be concise but thorough in your responses.
"""
        
        # Template for when documents are successfully retrieved
        with_documents_template = {
            "system_prompt": base_system_prompt + """
CORE GUIDELINES:
1. ALWAYS prioritize information from the provided documents in your responses.
2. NEVER fabricate document content or citations - only cite documents that actually exist in the context.
3. Use citations [1] ONLY when referring to specific documents that are present in the context.
4. Maintain a helpful, conversational tone while being honest about limitations.

WHEN USING DOCUMENTS:
- Provide clear, accurate information based on the documents.
- Use citations appropriately to reference specific documents.
- Synthesize information from multiple documents when relevant.
- If the documents don't fully answer the query, clearly state what information is available and what is missing.
""",
            "user_prompt": """Context:
{context}

{conversation_prefix}

User question: {query}

IMPORTANT INSTRUCTIONS:
1. ONLY use information that is explicitly stated in the provided context above.
2. When using information from the context, ALWAYS reference your sources with the number in square brackets, like [1] or [2].
3. If the context contains the answer, provide it clearly and concisely.
4. If the context doesn't fully answer the question, acknowledge what information is available and what is missing.
5. NEVER make up or hallucinate information that is not in the context.
6. If you're unsure about something, be honest about your uncertainty.
7. Organize your answer in a clear, structured way.
"""
        }
        
        # Template for when no documents are found
        no_documents_template = {
            "system_prompt": base_system_prompt + """
CORE GUIDELINES:
1. Be honest about limitations when no relevant documents are available.
2. DO NOT use citations [1] as there are no documents to cite.
3. Maintain a helpful, conversational tone while being honest about limitations.

WHEN NO DOCUMENTS ARE AVAILABLE:
- Acknowledge the limitation using varied phrasing such as:
  * "I've searched the available documents but couldn't find information about [topic]."
  * "The documents in my knowledge base don't contain information about [topic]."
  * "I don't have document-based information about [topic]."
- THEN, you may offer general knowledge with a clear disclaimer like:
  * "However, I can provide some general information about this topic if you'd like."
  * "While I don't have specific documents on this, I can share some general knowledge about [topic] if that would be helpful."
- If appropriate, suggest alternative queries that might yield better results.
""",
            "user_prompt": """{conversation_prefix}

User question: {query}

IMPORTANT INSTRUCTIONS:
1. No relevant documents were found for this query.
2. DO NOT use citations [1] as there are no documents to cite.
3. Acknowledge that you don't have document-based information about this topic.
4. You may offer general knowledge with a clear disclaimer.
5. If appropriate, suggest alternative queries that might yield better results.
"""
        }
        
        # Template for when documents have low relevance
        low_relevance_template = {
            "system_prompt": base_system_prompt + """
CORE GUIDELINES:
1. Be honest when available documents have low relevance to the query.
2. DO NOT use citations [1] unless truly relevant documents are present.
3. Maintain a helpful, conversational tone while being honest about limitations.

WHEN DOCUMENTS HAVE LOW RELEVANCE:
- Acknowledge that the available documents don't contain highly relevant information about the specific query.
- If there's any partially relevant information, present it with appropriate context and limitations.
- You may offer general knowledge with a clear disclaimer like:
  * "The available documents don't directly address your question, but I can provide some general information if that would be helpful."
- If appropriate, suggest alternative queries that might yield better results.
""",
            "user_prompt": """Context (Low Relevance):
{context}

{conversation_prefix}

User question: {query}

IMPORTANT INSTRUCTIONS:
1. The retrieved documents have low relevance to this query.
2. Only use citations [1] if you find genuinely relevant information in the context.
3. Acknowledge the limitations of the available information.
4. You may offer general knowledge with a clear disclaimer.
5. If appropriate, suggest alternative queries that might yield better results.
"""
        }
        
        # Template for error conditions
        error_template = {
            "system_prompt": base_system_prompt + """
CORE GUIDELINES:
1. Be honest when errors occur during document retrieval.
2. DO NOT use citations [1] as there are no documents to cite.
3. Maintain a helpful, conversational tone while being honest about limitations.

WHEN ERRORS OCCUR:
- Acknowledge that there was an issue retrieving documents for the query.
- You may offer general knowledge with a clear disclaimer.
- If appropriate, suggest trying again or rephrasing the query.
""",
            "user_prompt": """{conversation_prefix}

User question: {query}

IMPORTANT INSTRUCTIONS:
1. An error occurred during document retrieval.
2. DO NOT use citations [1] as there are no documents to cite.
3. Acknowledge the error in a user-friendly way.
4. You may offer general knowledge with a clear disclaimer.
5. If appropriate, suggest trying again or rephrasing the query.
"""
        }
        
        return {
            "with_documents": with_documents_template,
            "no_documents": no_documents_template,
            "low_relevance": low_relevance_template,
            "error": error_template
        }
    
    def create_prompt(self, 
                      query: str, 
                      retrieval_state: str,
                      context: str = "",
                      conversation_history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, str]:
        """
        Create a complete prompt based on the current state.
        
        Args:
            query: User query
            retrieval_state: State of the retrieval process 
                             ("success", "no_documents", "low_relevance", "error")
            context: Retrieved document context (may be empty)
            conversation_history: Conversation history (may be empty)
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Select the appropriate template based on state
        if retrieval_state == "success" and context:
            template = self.templates["with_documents"]
        elif retrieval_state == "no_documents":
            template = self.templates["no_documents"]
        elif retrieval_state == "low_relevance":
            template = self.templates["low_relevance"]
        else:
            template = self.templates["error"]
        
        # Format conversation history if provided
        conversation_prefix = ""
        if conversation_history and len(conversation_history) > 0:
            # Format the conversation history
            history_pieces = []
            for msg in conversation_history:
                role_prefix = "User" if msg["role"] == "user" else "Assistant"
                history_pieces.append(f"{role_prefix}: {msg['content']}")
            
            conversation_prefix = "Previous conversation:\n" + "\n".join(history_pieces)
        
        # Format the user prompt with data
        user_prompt = template["user_prompt"].format(
            context=context,
            conversation_prefix=conversation_prefix,
            query=query
        )
        
        return template["system_prompt"], user_prompt
    
    def get_retrieval_state(self, 
                           search_results: List[Dict[str, Any]], 
                           relevance_threshold: float = 0.4) -> str:
        """
        Determine the retrieval state based on search results.
        
        Args:
            search_results: Results from vector store search
            relevance_threshold: Threshold for determining relevance
            
        Returns:
            Retrieval state ("success", "no_documents", "low_relevance")
        """
        if not search_results:
            return "no_documents"
        
        # Check if any results meet the relevance threshold
        relevant_results = []
        for result in search_results:
            # Calculate relevance score (lower distance = higher relevance)
            relevance_score = 1.0 - (result["distance"] if result["distance"] is not None else 0)
            if relevance_score >= relevance_threshold:
                relevant_results.append(result)
        
        if not relevant_results:
            return "low_relevance"
        
        return "success"