"""
RAG generation functionality
"""
import logging
import time
import re
import asyncio
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
    async def _get_system_token(self) -> str:
        """
        Create a system token for internal API calls
        
        Returns:
            JWT token for system authentication
        """
        from app.core.security import create_access_token
        import uuid
        
        # Create token data for system user
        token_data = {
            "sub": "system",
            "user_id": str(uuid.uuid4()),  # Generate a unique ID for this request
            "aud": "metis-rag-internal",
            "iss": "metis-rag-system",
            "jti": str(uuid.uuid4())
        }
        
        # Create access token with longer expiration (30 minutes)
        from datetime import timedelta
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=30)
        )
        
        return access_token
    
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
            
            # Get system token for authentication
            token = await self._get_system_token()
            
            # Get API endpoint from environment or config
            from app.core.config import SETTINGS
            api_base_url = SETTINGS.api_base_url or "http://localhost:8000"
            api_endpoint = f"{api_base_url}/api/analytics/record_query"
            
            # Send analytics data to the API with authentication
            import httpx
            async with httpx.AsyncClient() as client:
                # Add retry logic for robustness
                max_retries = 3
                retry_delay = 1.0  # seconds
                
                for attempt in range(max_retries):
                    try:
                        response = await client.post(
                            api_endpoint,
                            json=analytics_data,
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=5.0
                        )
                        
                        if response.status_code == 200 or response.status_code == 201:
                            logger.debug(f"Recorded analytics for query: {query[:30]}...")
                            break
                        elif response.status_code == 401:
                            # Authentication failed, try with a new token
                            logger.warning("Authentication failed for analytics, retrying with new token")
                            token = await self._get_system_token()
                            if attempt == max_retries - 1:
                                logger.error(f"Failed to authenticate for analytics after {max_retries} attempts")
                        else:
                            logger.warning(f"Analytics API returned status code {response.status_code}")
                            if attempt == max_retries - 1:
                                logger.error(f"Failed to record analytics after {max_retries} attempts")
                        
                        # Wait before retrying (except on last attempt)
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                    
                    except httpx.TimeoutException:
                        logger.warning(f"Timeout while recording analytics (attempt {attempt+1}/{max_retries})")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                    
                    except Exception as e:
                        logger.error(f"Error during analytics request (attempt {attempt+1}/{max_retries}): {str(e)}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
            
        except Exception as e:
            # Don't let analytics errors affect the main functionality
            logger.error(f"Error recording analytics: {str(e)}")
    
    
    async def _generate_streaming_response(self,
                                          prompt: str,
                                          model: str,
                                          system_prompt: str,
                                          model_parameters: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response with minimal processing
        
        Args:
            prompt: Full prompt
            model: Model to use
            system_prompt: System prompt
            model_parameters: Model parameters
            
        Returns:
            Async generator of response tokens
        """
        # Get the raw stream from the LLM
        stream = await self.ollama_client.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            stream=True,
            parameters=model_parameters or {}
        )
        
        # Stream tokens directly with minimal processing
        async for chunk in stream:
            # Handle string chunks
            if isinstance(chunk, str):
                yield chunk
            # Handle dictionary chunks (for backward compatibility)
            elif isinstance(chunk, dict) and "response" in chunk:
                yield chunk["response"]
            else:
                yield chunk
    
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
    
    async def generate_complete_response(self,
                                        prompt: str,
                                        model: str,
                                        system_prompt: str,
                                        model_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete response without streaming
        
        Args:
            prompt: Full prompt
            model: Model to use
            system_prompt: System prompt
            model_parameters: Model parameters
            
        Returns:
            Response dictionary
        """
        # Get cached or generate new response
        response = await self._get_cached_or_generate_response(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            model_parameters=model_parameters
        )
        
        return response
    
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
        response_text = self.process_complete_response(response_text)
        
        return response_text
    def process_complete_response(self, response_text: str, apply_normalization: bool = True) -> str:
        """
        Process a complete response with optional normalization
        
        Args:
            response_text: The complete response text
            apply_normalization: Whether to apply text normalization
            
        Returns:
            Processed response text
        """
        if not apply_normalization:
            return response_text
        
        # Apply text normalization
        normalized_text = normalize_text(response_text)
        
        # Format code blocks
        formatted_text = format_code_blocks(normalized_text)
        
        return formatted_text
        return response_text