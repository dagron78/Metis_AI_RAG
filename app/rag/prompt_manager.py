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
1. Prioritize information from the provided documents in your responses.
2. Use citations [1] when referring to specific information from the documents.
3. Synthesize information from multiple documents when relevant.
4. Maintain a helpful, conversational tone.

WHEN USING DOCUMENTS:
- Provide clear, accurate information based on the documents.
- Use citations to reference specific documents in a natural way.
- Combine information from multiple documents to provide comprehensive answers.
- If the documents don't fully answer the query, supplement with your general knowledge.
- Remember information from the conversation history to provide context-aware responses.
""",
            "user_prompt": """Context:
{context}

{conversation_prefix}

User question: {query}

IMPORTANT INSTRUCTIONS:
1. Use the information from the context to answer the question.
2. When using specific information from the context, reference your sources with the number in square brackets, like [1] or [2].
3. Provide a clear, comprehensive answer that synthesizes information from the documents.
4. If the context doesn't fully answer the question, supplement with your general knowledge.
5. Be conversational and natural in your response.
6. Use information from the conversation history when relevant.
"""
        }
        
        # Template for when no documents are found
        no_documents_template = {
            "system_prompt": base_system_prompt + """
CORE GUIDELINES:
1. Be honest about limitations when no relevant documents are available.
2. DO NOT use citations [1] as there are no documents to cite.
3. Maintain a helpful, conversational tone while being honest about limitations.
4. Use your general knowledge to provide helpful responses.

WHEN NO DOCUMENTS ARE AVAILABLE:
- You can use your general knowledge to answer questions directly.
- Only mention the lack of documents if specifically asked about documentation or sources.
- Focus on being helpful and providing accurate information based on your training.
- Maintain a natural, conversational tone.
- Remember information from the conversation history to provide context-aware responses.
""",
            "user_prompt": """{conversation_prefix}

User question: {query}

IMPORTANT INSTRUCTIONS:
1. Answer the question directly using your general knowledge.
2. DO NOT use citations [1] as there are no documents to cite.
3. Only mention the lack of documents if specifically asked about documentation or sources.
4. Be conversational and helpful in your response.
5. Use information from the conversation history when relevant.
"""
        }
        
        # Template for when documents have low relevance
        low_relevance_template = {
            "system_prompt": base_system_prompt + """
CORE GUIDELINES:
1. Use any relevant information from the documents if available.
2. Use citations [1] only for information that comes directly from the documents.
3. Supplement with your general knowledge to provide a complete answer.
4. Maintain a helpful, conversational tone.

WHEN DOCUMENTS HAVE LOW RELEVANCE:
- Extract any useful information from the documents that might be relevant.
- Use your general knowledge to provide a complete and helpful answer.
- Only cite documents when directly quoting or referencing specific information from them.
- Focus on being helpful rather than emphasizing limitations.
- Remember information from the conversation history to provide context-aware responses.
""",
            "user_prompt": """Context (Low Relevance):
{context}

{conversation_prefix}

User question: {query}

IMPORTANT INSTRUCTIONS:
1. Answer the question directly, using both the context and your general knowledge.
2. Only use citations [1] when directly referencing information from the context.
3. Focus on providing a helpful, complete answer rather than emphasizing limitations.
4. Be conversational and natural in your response.
5. Use information from the conversation history when relevant.
"""
        }
        
        # Template for error conditions
        error_template = {
            "system_prompt": base_system_prompt + """
CORE GUIDELINES:
1. Focus on being helpful despite any system errors.
2. DO NOT use citations [1] as there are no documents to cite.
3. Use your general knowledge to provide helpful responses.
4. Maintain a conversational, friendly tone.

WHEN ERRORS OCCUR:
- Answer the question directly using your general knowledge.
- Do not mention system errors unless specifically asked.
- Focus on providing value to the user despite limitations.
- Remember information from the conversation history to provide context-aware responses.
""",
            "user_prompt": """{conversation_prefix}

User question: {query}

IMPORTANT INSTRUCTIONS:
1. Answer the question directly using your general knowledge.
2. DO NOT use citations [1] as there are no documents to cite.
3. Do not mention system errors unless specifically asked.
4. Be conversational and helpful in your response.
5. Use information from the conversation history when relevant.
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