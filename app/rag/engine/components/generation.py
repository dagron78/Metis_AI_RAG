"""
Generation Component for RAG Engine

This module provides the GenerationComponent class for handling
response generation in the RAG Engine.
"""
import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple, Union, AsyncGenerator
import asyncio

from app.core.config import DEFAULT_MODEL
from app.rag.engine.utils.error_handler import GenerationError, safe_execute_async
from app.rag.engine.utils.timing import async_timing_context, TimingStats
from app.rag.prompt_manager import PromptManager
from app.rag.system_prompts import (
    CODE_GENERATION_SYSTEM_PROMPT,
    PYTHON_CODE_GENERATION_PROMPT,
    JAVASCRIPT_CODE_GENERATION_PROMPT,
    STRUCTURED_CODE_OUTPUT_PROMPT
)

logger = logging.getLogger("app.rag.engine.components.generation")

class GenerationComponent:
    """
    Component for handling response generation in the RAG Engine
    
    This component is responsible for generating responses using the LLM,
    including streaming responses, handling system prompts, and processing
    structured outputs.
    """
    
    def __init__(self, ollama_client=None, cache_manager=None):
        """
        Initialize the generation component
        
        Args:
            ollama_client: Ollama client instance
            cache_manager: Cache manager instance
        """
        self.ollama_client = ollama_client
        self.cache_manager = cache_manager
        self.prompt_manager = PromptManager()
        self.timing_stats = TimingStats()
    
    async def generate(self,
                      query: str,
                      context: str = "",
                      conversation_context: str = "",
                      model: str = DEFAULT_MODEL,
                      system_prompt: Optional[str] = None,
                      model_parameters: Optional[Dict[str, Any]] = None,
                      retrieval_state: str = "success",
                      stream: bool = False) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Generate a response
        
        Args:
            query: User query
            context: Retrieved context
            conversation_context: Conversation history
            model: Model to use
            system_prompt: System prompt
            model_parameters: Model parameters
            retrieval_state: State of retrieval (success, no_documents, low_relevance)
            stream: Whether to stream the response
            
        Returns:
            Response dictionary or async generator of response chunks
        """
        self.timing_stats.start("total")
        
        try:
            # Create system prompt and user prompt
            async with async_timing_context("create_prompts", self.timing_stats):
                system_prompt, user_prompt = await self._create_prompts(
                    query=query,
                    context=context,
                    conversation_context=conversation_context,
                    system_prompt=system_prompt,
                    retrieval_state=retrieval_state
                )
            
            # Log the prompts
            logger.debug(f"System prompt: {system_prompt[:200]}...")
            logger.debug(f"User prompt: {user_prompt[:200]}...")
            
            # Generate response
            if stream:
                # For streaming, return the generator
                return self._generate_streaming(
                    prompt=user_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    model_parameters=model_parameters or {}
                )
            else:
                # For non-streaming, generate the complete response
                async with async_timing_context("generate_complete", self.timing_stats):
                    response = await self._generate_complete(
                        prompt=user_prompt,
                        model=model,
                        system_prompt=system_prompt,
                        model_parameters=model_parameters or {}
                    )
                
                # Process the response
                async with async_timing_context("process_response", self.timing_stats):
                    processed_response = await self._process_response(response)
                
                # Log generation stats
                self.timing_stats.stop("total")
                logger.info(f"Generated response in {self.timing_stats.get_timing('total'):.2f}s")
                self.timing_stats.log_summary()
                
                return processed_response
        
        except Exception as e:
            self.timing_stats.stop("total")
            logger.error(f"Error generating response: {str(e)}")
            raise GenerationError(f"Error generating response: {str(e)}")
    
    async def _create_prompts(self,
                             query: str,
                             context: str = "",
                             conversation_context: str = "",
                             system_prompt: Optional[str] = None,
                             retrieval_state: str = "success") -> Tuple[str, str]:
        """
        Create system prompt and user prompt
        
        Args:
            query: User query
            context: Retrieved context
            conversation_context: Conversation history
            system_prompt: System prompt
            retrieval_state: State of retrieval
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Check if this is a code-related query
        is_code_query = self._is_code_related_query(query)
        
        # If system prompt is not provided, create one
        if not system_prompt:
            if is_code_query:
                # Use the structured code output prompt for code-related queries
                system_prompt = STRUCTURED_CODE_OUTPUT_PROMPT
                
                # Add language-specific guidelines if detected
                if "python" in query.lower():
                    system_prompt += "\n\n" + PYTHON_CODE_GENERATION_PROMPT
                elif "javascript" in query.lower() or "js" in query.lower():
                    system_prompt += "\n\n" + JAVASCRIPT_CODE_GENERATION_PROMPT
                
                # Create a simple user prompt for code queries
                user_prompt = f"User Question: {query}"
                
                # For code queries, we'll use a simpler approach without structured output
                # to avoid 400 Bad Request errors with Ollama
                
                # Set temperature to 0.2 for more deterministic but still creative output
                if not model_parameters:
                    model_parameters = {}
                
                model_parameters["temperature"] = 0.2
                
                logger.info("Using structured output format for code-related query")
                
                return system_prompt, user_prompt
            else:
                # For non-code queries, use the PromptManager
                system_prompt, user_prompt = self.prompt_manager.create_prompt(
                    query=query,
                    retrieval_state=retrieval_state,
                    context=context,
                    conversation_history=self._parse_conversation_context(conversation_context)
                )
                
                return system_prompt, user_prompt
        else:
            # If system prompt is provided, still use PromptManager for user prompt
            _, user_prompt = self.prompt_manager.create_prompt(
                query=query,
                retrieval_state=retrieval_state,
                context=context,
                conversation_history=self._parse_conversation_context(conversation_context)
            )
            
            return system_prompt, user_prompt
    
    def _parse_conversation_context(self, conversation_context: str) -> Optional[List[Dict[str, str]]]:
        """
        Parse conversation context string into a list of messages
        
        Args:
            conversation_context: Conversation context string
            
        Returns:
            List of message dictionaries or None
        """
        if not conversation_context:
            return None
        
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
        
        return conversation_history if conversation_history else None
    
    def _is_code_related_query(self, query: str) -> bool:
        """
        Determine if a query is related to code or programming
        
        Args:
            query: The user query
            
        Returns:
            True if the query is code-related, False otherwise
        """
        # Import the base engine's implementation
        from app.rag.engine.base.base_engine import BaseEngine
        
        # Create a temporary instance to use the method
        base_engine = BaseEngine()
        
        return base_engine._is_code_related_query(query)
    
    async def _generate_streaming(self,
                                 prompt: str,
                                 model: str,
                                 system_prompt: str,
                                 model_parameters: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        # Ensure we're using the correct model for generation
        from app.core.config import DEFAULT_MODEL
        if model == "nomic-embed-text:latest":
            logger.warning(f"Attempted to use embedding model for generation. Switching to {DEFAULT_MODEL}")
            model = DEFAULT_MODEL
        """
        Generate a streaming response
        
        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: System prompt
            model_parameters: Model parameters
            
        Yields:
            Response chunks
        """
        # We're no longer using structured output format for code queries
        # but keeping this code for future reference if needed
        is_structured_output = False
        
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
                parameters=model_parameters
            )
            
            # Process the structured response
            processed_text = self._process_response_text(response)
            
            # Yield the processed text as a single chunk
            yield {"content": processed_text}
            return
        
        # For non-structured outputs, use the normal streaming approach
        # Get the raw stream from the LLM
        stream = await self.ollama_client.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            stream=True,
            parameters=model_parameters
        )
        
        # Stream tokens directly with minimal processing
        async for chunk in stream:
            # Handle string chunks
            if isinstance(chunk, str):
                yield {"content": chunk}
            # Handle dictionary chunks (for backward compatibility)
            elif isinstance(chunk, dict) and "response" in chunk:
                yield {"content": chunk["response"]}
            else:
                yield {"content": str(chunk)}
    
    async def _generate_complete(self,
                                prompt: str,
                                model: str,
                                system_prompt: str,
                                model_parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure we're using the correct model for generation
        from app.core.config import DEFAULT_MODEL
        if model == "nomic-embed-text:latest":
            logger.warning(f"Attempted to use embedding model for generation. Switching to {DEFAULT_MODEL}")
            model = DEFAULT_MODEL
        """
        Generate a complete response
        
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
                                              system_prompt: str,
                                              model_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a cached response or generate a new one
        
        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: System prompt
            model_parameters: Model parameters
            
        Returns:
            Response dictionary
        """
        # Check if cache manager is available
        if not self.cache_manager:
            # Generate new response without caching
            return await self.ollama_client.generate(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                stream=False,
                parameters=model_parameters
            )
        
        # Create cache parameters
        temperature = model_parameters.get("temperature", 0.0)
        max_tokens = model_parameters.get("max_tokens")
        
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
                parameters=model_parameters
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
        Process response text
        
        Args:
            response: Response dictionary
            
        Returns:
            Processed response text
        """
        # Check if there was an error in the response
        if "error" in response:
            error_message = response.get("error", "Unknown error")
            logger.warning(f"Model returned an error: {error_message}")
            return f"Error: {error_message}"
        
        # Get response text
        response_text = response.get("response", "")
        
        # Check if the response is structured JSON with code blocks
        try:
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
                return main_text
        except (json.JSONDecodeError, AttributeError, TypeError):
            # Continue with normal processing for non-JSON responses
            pass
        
        return response_text
    
    async def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the complete response
        
        Args:
            response: Response dictionary
            
        Returns:
            Processed response dictionary
        """
        # Process response text
        response_text = self._process_response_text(response)
        
        # Create processed response
        processed_response = {
            "content": response_text,
            "model": response.get("model", ""),
            "created_at": response.get("created_at", time.time()),
            "raw_response": response
        }
        
        # Add usage information if available
        if "prompt_eval_count" in response and "eval_count" in response:
            processed_response["usage"] = {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
            }
        
        return processed_response
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List available models
        
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