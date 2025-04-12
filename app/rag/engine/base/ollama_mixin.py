"""
Ollama Mixin for RAG Engine

This module provides the OllamaMixin class that adds Ollama LLM
functionality to the RAG Engine.
"""
import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
import uuid

from app.core.config import DEFAULT_MODEL
from app.models.chat import Message

logger = logging.getLogger("app.rag.engine.base.ollama_mixin")

class OllamaMixin:
    """
    Mixin class that adds Ollama LLM functionality to the RAG Engine
    
    This mixin provides methods for interacting with the Ollama LLM service,
    including generating responses, streaming responses, and managing system prompts.
    """
    
    async def _get_system_token(self) -> str:
        """
        Create a system token for internal API calls
        
        Returns:
            JWT token for system authentication
        """
        from app.core.security import create_access_token
        
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
                               document_id_list: List[str],
                               token_count: int) -> None:
        """
        Record query analytics asynchronously
        
        Args:
            query: Query string
            model: Model used
            use_rag: Whether RAG was used
            response_time_ms: Response time in milliseconds
            document_id_list: List of document IDs used
            token_count: Approximate token count
        """
        try:
            # Prepare analytics data
            analytics_data = {
                "query": query,
                "model": model,
                "use_rag": use_rag,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "response_time_ms": response_time_ms,
                "document_id_list": document_id_list,
                "token_count": token_count
            }
            
            # Get system token for authentication
            token = await self._get_system_token()
            
            # Get API endpoint from environment or config
            from app.core.config import SETTINGS
            api_base_url = getattr(SETTINGS, 'base_url', "http://localhost:8000")
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
                        elif response.status_code == 404:
                            # Analytics endpoint not found, log at debug level and stop retrying
                            logger.debug(f"Analytics API endpoint not found (404). This is normal if analytics is not configured.")
                            # No need to retry for 404 errors
                            break
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
    
    async def generate_streaming_response(self,
                                         prompt: str,
                                         model: str = DEFAULT_MODEL,
                                         system_prompt: Optional[str] = None,
                                         model_parameters: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the LLM
        
        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: System prompt
            model_parameters: Model parameters
            
        Returns:
            Async generator of response tokens
        """
        # Check if this is a structured output request
        is_structured_output = model_parameters is not None and "format" in model_parameters
        
        # For structured outputs, we can't stream the response directly
        # because we need to process the complete JSON
        if is_structured_output:
            logger.info("Using non-streaming approach for structured output")
            
            # Generate the complete response
            response = await self.ollama_client.generate(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                stream=False,
                parameters=model_parameters or {}
            )
            
            # Process the structured response
            processed_text = self._process_response_text(response)
            
            # Yield the processed text as a single chunk
            yield processed_text
            return
        
        # For non-structured outputs, use the normal streaming approach
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
    
    async def generate_complete_response(self,
                                        prompt: str,
                                        model: str = DEFAULT_MODEL,
                                        system_prompt: Optional[str] = None,
                                        model_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a complete response from the LLM
        
        Args:
            prompt: User prompt
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
                                              system_prompt: Optional[str],
                                              model_parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
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
            
            # Log the response type and structure to understand when JSON is returned
            if isinstance(response, dict):
                logger.debug(f"Ollama response type: dict with keys: {list(response.keys())}")
                if "response" in response:
                    response_content = response["response"]
                    try:
                        # Check if the response is JSON
                        import json
                        json_data = json.loads(response_content) if isinstance(response_content, str) else None
                        if json_data and isinstance(json_data, dict):
                            logger.debug(f"Response content appears to be JSON with keys: {list(json_data.keys())}")
                            if "text" in json_data and "code_blocks" in json_data:
                                logger.debug("Response contains structured code format with 'text' and 'code_blocks'")
                    except json.JSONDecodeError:
                        logger.debug("Response content is not JSON")
            else:
                logger.debug(f"Ollama response type: {type(response)}")
            
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
        # Get the raw response text for logging
        raw_response_text = response.get("response", "")
        query_id = getattr(self, 'conversation_id', str(uuid.uuid4()))
        logger.debug(f"RAW OLLAMA OUTPUT (Query ID: {query_id}):\n```\n{raw_response_text}\n```")
        
        # Check if there was an error in the response
        if "error" in response:
            error_message = response.get("error", "Unknown error")
            logger.warning(f"Model returned an error: {error_message}")
            return response.get("response", f"Error: {error_message}")
        
        # Get response text
        response_text = response.get("response", "")
        
        # Check if the response is structured JSON with code blocks
        try:
            import json
            json_data = json.loads(response_text) if isinstance(response_text, str) else None
            
            if json_data and isinstance(json_data, dict) and "text" in json_data and "code_blocks" in json_data:
                logger.info("Detected structured JSON response with code blocks")
                
                # Extract the main text and code blocks
                main_text = json_data.get("text", "")
                code_blocks = json_data.get("code_blocks", [])
                
                # Process each code block and replace placeholders
                for i, code_block in enumerate(code_blocks):
                    language = code_block.get("language", "")
                    code = code_block.get("code", "")
                    
                    # Ensure code has proper newlines
                    if code and not code.startswith('\n'):
                        code = '\n' + code
                    if code and not code.endswith('\n'):
                        code = code + '\n'
                    
                    # Create properly formatted markdown code block
                    formatted_block = f"```{language}\n{code}\n```"
                    
                    # Replace placeholder in main text
                    placeholder = f"{{CODE_BLOCK_{i}}}"
                    main_text = main_text.replace(placeholder, formatted_block)
                
                # Use the processed text instead of the raw JSON
                response_text = main_text
                
                # Log that we're using the structured format
                logger.info("Using structured JSON format for code blocks")
                
                # Return the processed text
                return response_text
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.debug(f"Response is not structured JSON: {str(e)}")
            # Continue with normal processing for non-JSON responses
        
        # For normal responses, just return the text
        return response_text
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List available models from Ollama
        
        Returns:
            List of available models
        """
        try:
            models = await self.ollama_client.list_models()
            logger.info(f"Found {len(models)} available models")
            return models
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []