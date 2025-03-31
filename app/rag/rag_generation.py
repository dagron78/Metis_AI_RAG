"""
RAG generation functionality
"""
import logging
import time
import re
from typing import Dict, Any, Optional, List, AsyncGenerator
from uuid import UUID

from app.core.config import DEFAULT_MODEL
from app.models.chat import Citation, Message
from app.rag.mem0_client import store_message
from app.utils.text_processor import normalize_text, format_code_blocks
from app.rag.prompt_manager import PromptManager
from app.rag.system_prompts import (
    CODE_GENERATION_SYSTEM_PROMPT,
    PYTHON_CODE_GENERATION_PROMPT,
    JAVASCRIPT_CODE_GENERATION_PROMPT
)

logger = logging.getLogger("app.rag.rag_generation")

class GenerationMixin:
    """
    Mixin class for RAG generation functionality
    """
    
    def __init__(self):
        """Initialize the GenerationMixin."""
        super().__init__()
        self.prompt_manager = PromptManager()
        logger.info("GenerationMixin initialized with PromptManager")
    
    async def _record_analytics(self,
                               query: str,
                               model: str,
                               use_rag: bool,
                               response_time_ms: float,
                               document_ids: List[str],
                               token_count: int) -> None:
        """
        Record query analytics asynchronously
        """
        try:
            # Prepare analytics data
            analytics_data = {
                "query": query,
                "model": model,
                "use_rag": use_rag,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "response_time_ms": response_time_ms,
                "document_ids": document_ids,
                "token_count": token_count
            }
            
            # Send analytics data to the API
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8000/api/analytics/record_query",
                    json=analytics_data,
                    timeout=5.0
                )
            
            logger.debug(f"Recorded analytics for query: {query[:30]}...")
        except Exception as e:
            # Don't let analytics errors affect the main functionality
            logger.error(f"Error recording analytics: {str(e)}")
    
    async def _generate_streaming_response(self,
                                          prompt: str,
                                          model: str,
                                          system_prompt: str,
                                          model_parameters: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response
        
        Args:
            prompt: Full prompt
            model: Model to use
            system_prompt: System prompt
            model_parameters: Model parameters
            
        Returns:
            Async generator of response chunks
        """
        # Create a wrapper for the stream that applies text normalization
        original_stream = await self.ollama_client.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            stream=True,
            parameters=model_parameters or {}
        )
        
        # Create a normalized stream wrapper
        buffer = ""
        async for chunk in original_stream:
            # Handle string chunks (from OllamaClient)
            if isinstance(chunk, str):
                buffer += chunk
                # Apply normalization to the buffer periodically
                # Only normalize when we have complete sentences or paragraphs
                if any(buffer.endswith(c) for c in ['.', '!', '?', '\n']):
                    normalized_chunk = normalize_text(buffer)
                    buffer = ""
                    yield normalized_chunk
                else:
                    yield chunk
            # Handle dictionary chunks (for backward compatibility)
            elif isinstance(chunk, dict) and "response" in chunk:
                buffer += chunk["response"]
                # Apply normalization to the buffer periodically
                # Only normalize when we have complete sentences or paragraphs
                if any(buffer.endswith(c) for c in ['.', '!', '?', '\n']):
                    normalized_chunk = normalize_text(buffer)
                    buffer = ""
                    yield normalized_chunk
                else:
                    yield chunk["response"]
            else:
                yield chunk
        
        # Process any remaining text in the buffer
        if buffer:
            normalized_chunk = normalize_text(buffer)
            yield normalized_chunk
    
    def _create_system_prompt(self, query: str) -> str:
        """
        Create a system prompt based on the query
        
        Args:
            query: User query
            
        Returns:
            System prompt
        """
        # Check if this is a code-related query
        is_code_query = self._is_code_related_query(query)
        
        if is_code_query:
            logger.info("Detected code-related query, using code generation system prompt")
            system_prompt = CODE_GENERATION_SYSTEM_PROMPT
            
            # Add language-specific guidelines if detected
            if re.search(r'\bpython\b', query.lower()):
                system_prompt += "\n\n" + PYTHON_CODE_GENERATION_PROMPT
            elif re.search(r'\bjavascript\b|\bjs\b', query.lower()):
                system_prompt += "\n\n" + JAVASCRIPT_CODE_GENERATION_PROMPT
            
            return system_prompt
        
        # For non-code queries, we'll use the PromptManager later
        # This is just a placeholder that will be replaced
        return "PLACEHOLDER_SYSTEM_PROMPT"
    
    def _create_full_prompt(self,
                           query: str,
                           context: str = "",
                           conversation_context: str = "",
                           retrieval_state: str = "success") -> tuple[str, str]:
        """
        Create a full prompt with context and conversation history using the PromptManager
        
        Args:
            query: User query
            context: Retrieved context
            conversation_context: Conversation history
            retrieval_state: State of the retrieval process
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Convert conversation_context string to list of dicts if provided
        conversation_history = None
        if conversation_context:
            # Parse the conversation context string into a list of messages
            conversation_history = []
            lines = conversation_context.strip().split('\n')
            for line in lines:
                if line.startswith("User: "):
                    conversation_history.append({
                        "role": "user",
                        "content": line[6:]  # Remove "User: " prefix
                    })
                elif line.startswith("Assistant: "):
                    conversation_history.append({
                        "role": "assistant",
                        "content": line[11:]  # Remove "Assistant: " prefix
                    })
        
        # Use the PromptManager to create the prompt
        system_prompt, user_prompt = self.prompt_manager.create_prompt(
            query=query,
            retrieval_state=retrieval_state,
            context=context,
            conversation_history=conversation_history
        )
        
        logger.info(f"Created prompt with retrieval_state: {retrieval_state}")
        
        return system_prompt, user_prompt
    
    async def _get_cached_or_generate_response(self,
                                              prompt: str,
                                              model: str,
                                              system_prompt: str,
                                              model_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a cached response or generate a new one
        
        Args:
            prompt: Full prompt
            model: Model to use
            system_prompt: System prompt
            model_parameters: Model parameters
            
        Returns:
            Response dictionary
        """
        # Create cache parameters
        temperature = model_parameters.get("temperature", 0.0) if model_parameters else 0.0
        max_tokens = model_parameters.get("max_tokens") if model_parameters else None
        
        # Check if response is in cache
        cached_response = self.cache_manager.llm_response_cache.get_response(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            additional_params={"system_prompt": system_prompt} if system_prompt else None
        )
        
        if cached_response:
            logger.info("Using cached response")
            response = cached_response
        else:
            # Generate new response
            logger.info("Cache miss, generating new response")
            response = await self.ollama_client.generate(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                stream=False,
                parameters=model_parameters or {}
            )
            
            # Cache the response if appropriate
            if "error" not in response and self.cache_manager.llm_response_cache.should_cache_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                response=response
            ):
                self.cache_manager.llm_response_cache.set_response(
                    prompt=prompt,
                    model=model,
                    response=response,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    additional_params={"system_prompt": system_prompt} if system_prompt else None
                )
                logger.info("Response cached for future use")
        
        return response
    
    def _process_response_text(self, response: Dict[str, Any]) -> str:
        """
        Process response text with normalization and formatting
        
        Args:
            response: Response dictionary
            
        Returns:
            Processed response text
        """
        # Check if there was an error in the response
        if "error" in response:
            error_message = response.get("error", "Unknown error")
            logger.warning(f"Model returned an error: {error_message}")
            return response.get("response", f"Error: {error_message}")
        
        # Get response text
        response_text = response.get("response", "")
        
        # Apply text normalization to improve formatting
        response_text = normalize_text(response_text)
        response_text = format_code_blocks(response_text)
        
        return response_text