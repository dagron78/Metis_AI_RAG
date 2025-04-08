"""
RAG generation functionality
"""
import logging
import time
import re
import asyncio
import sys
from typing import Dict, Any, Optional, List, AsyncGenerator
from app.rag.text_formatting_monitor import get_monitor, FormattingApproach, FormattingEvent
from uuid import UUID, uuid4
import uuid

from app.core.config import DEFAULT_MODEL
from app.models.chat import Citation, Message
from app.rag.mem0_client import store_message
from app.utils.text_processor import normalize_text, format_code_blocks
from app.rag.prompt_manager import PromptManager
from app.rag.system_prompts import (
    CODE_GENERATION_SYSTEM_PROMPT,
    PYTHON_CODE_GENERATION_PROMPT,
    JAVASCRIPT_CODE_GENERATION_PROMPT,
    STRUCTURED_CODE_OUTPUT_PROMPT
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
                               document_id_list: List[str],  # Changed from document_ids to document_id_list
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
                "document_id_list": document_id_list,  # Changed from document_ids to document_id_list
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
        # Check if this is a structured output request
        is_structured_output = "format" in model_parameters
        
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
            logger.info("Detected code-related query, using structured code output prompt")
            # Use the structured code output prompt for code-related queries
            system_prompt = STRUCTURED_CODE_OUTPUT_PROMPT
            
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
        # Get the monitor
        monitor = get_monitor()
        
        # Get the raw response text for logging
        raw_response_text = response.get("response", "")
        query_id = getattr(self, 'conversation_id', str(uuid.uuid4()))
        logger.debug(f"RAW OLLAMA OUTPUT (Query ID: {query_id}):\n```\n{raw_response_text}\n```")
        
        # Check if there was an error in the response
        if "error" in response:
            error_message = response.get("error", "Unknown error")
            logger.warning(f"Model returned an error: {error_message}")
            
            # Record the error
            monitor.record_event(
                approach=FormattingApproach.STRUCTURED_OUTPUT,
                event=FormattingEvent.ERROR,
                error_message=error_message
            )
            
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
                
                # Record the event
                monitor.record_event(
                    approach=FormattingApproach.STRUCTURED_OUTPUT,
                    event=FormattingEvent.SUCCESS,
                    details={"code_blocks": len(code_blocks)}
                )
                
                # Return the processed text, marking it as already processed from structured JSON
                # so it won't go through additional formatting in process_complete_response
                return self.process_complete_response(response_text, apply_normalization=False, is_structured_json=True)
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.debug(f"Response is not structured JSON: {str(e)}")
            # Continue with normal processing for non-JSON responses
        
        # Check if this is a structured output response (JSON)
        try:
            # Try to parse as JSON
            from app.models.structured_output import FormattedResponse, TextBlock
            import json
            import traceback
            
            # Check if the response looks like JSON
            if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                # Track the stage of processing for better error reporting
                processing_stage = "initial"
                try:
                    # Parse the JSON response
                    processing_stage = "json_parsing"
                    try:
                        structured_data = json.loads(response_text)
                    except json.JSONDecodeError as json_err:
                        # Attempt to fix common JSON formatting issues
                        logger.warning(f"JSON parsing error: {str(json_err)}. Attempting to fix...")
                        fixed_json = self._attempt_json_repair(response_text)
                        if fixed_json:
                            structured_data = json.loads(fixed_json)
                            logger.info("Successfully repaired malformed JSON")
                        else:
                            raise json_err
                    
                    # Validate against our schema
                    processing_stage = "schema_validation"
                    try:
                        formatted_response = FormattedResponse.model_validate(structured_data)
                    except Exception as validation_err:
                        # Try partial validation if full validation fails
                        logger.warning(f"Schema validation error: {str(validation_err)}. Attempting partial validation...")
                        formatted_response = self._attempt_partial_validation(structured_data)
                        if not formatted_response:
                            raise validation_err
                    
                    # Process the structured response
                    processing_stage = "text_block_processing"
                    if formatted_response.text_blocks:
                        # Use the structured text blocks if provided
                        logger.info(f"Processing structured response with {len(formatted_response.text_blocks)} text blocks")
                        
                        # Combine text blocks into a single text with proper paragraph structure
                        text_parts = []
                        for block in formatted_response.text_blocks:
                            if block.format_type == "paragraph":
                                text_parts.append(block.content)
                            elif block.format_type == "heading":
                                text_parts.append(f"## {block.content}")
                            elif block.format_type == "list_item":
                                text_parts.append(f"- {block.content}")
                            elif block.format_type == "quote":
                                text_parts.append(f"> {block.content}")
                            else:
                                text_parts.append(block.content)
                        
                        # Join with double newlines to preserve paragraph structure
                        main_text = "\n\n".join(text_parts)
                    else:
                        # Use the main text field
                        main_text = formatted_response.text
                    
                    # Replace code block placeholders with properly formatted code blocks
                    processing_stage = "code_block_processing"
                    for i, code_block in enumerate(formatted_response.code_blocks):
                        placeholder = f"{{CODE_BLOCK_{i}}}"
                        # Ensure code has proper newlines
                        code = code_block.code
                        if code and not code.startswith('\n'):
                            code = '\n' + code
                        if code and not code.endswith('\n'):
                            code = code + '\n'
                        
                        formatted_block = f"```{code_block.language}\n{code}\n```"
                        main_text = main_text.replace(placeholder, formatted_block)
                    
                    # Process table placeholders
                    processing_stage = "table_processing"
                    if hasattr(formatted_response, 'tables') and formatted_response.tables:
                        logger.info(f"Processing {len(formatted_response.tables)} tables")
                        for i, table in enumerate(formatted_response.tables):
                            placeholder = f"{{TABLE_{i}}}"
                            formatted_table = self._format_table(table)
                            main_text = main_text.replace(placeholder, formatted_table)
                    
                    # Process image placeholders
                    processing_stage = "image_processing"
                    if hasattr(formatted_response, 'images') and formatted_response.images:
                        logger.info(f"Processing {len(formatted_response.images)} images")
                        for i, image in enumerate(formatted_response.images):
                            placeholder = f"{{IMAGE_{i}}}"
                            formatted_image = self._format_image(image)
                            main_text = main_text.replace(placeholder, formatted_image)
                    
                    # Process math block placeholders
                    processing_stage = "math_processing"
                    if hasattr(formatted_response, 'math_blocks') and formatted_response.math_blocks:
                        logger.info(f"Processing {len(formatted_response.math_blocks)} math blocks")
                        for i, math_block in enumerate(formatted_response.math_blocks):
                            placeholder = f"{{MATH_{i}}}"
                            formatted_math = self._format_math(math_block)
                            main_text = main_text.replace(placeholder, formatted_math)
                    
                    # Check for unreplaced placeholders
                    placeholder_pattern = r'\{CODE_BLOCK_\d+\}'
                    import re
                    if re.search(placeholder_pattern, main_text):
                        logger.warning("Found unreplaced code block placeholders. Attempting to fix...")
                        main_text = self._fix_unreplaced_placeholders(main_text, formatted_response.code_blocks)
                    # Collect content types for monitoring
                    content_types = ["text"]
                    if formatted_response.code_blocks:
                        content_types.append("code")
                    if hasattr(formatted_response, 'tables') and formatted_response.tables:
                        content_types.append("table")
                    if hasattr(formatted_response, 'images') and formatted_response.images:
                        content_types.append("image")
                    if hasattr(formatted_response, 'math_blocks') and formatted_response.math_blocks:
                        content_types.append("math")
                    
                    # Record successful structured output processing
                    monitor = get_monitor()
                    monitor.record_structured_output_success(
                        response_size=len(main_text),
                        content_types=content_types
                    )
                    
                    logger.info(f"Successfully processed structured output response with {len(formatted_response.code_blocks)} code blocks")
                    
                    # Apply text normalization to the processed text if preserve_paragraphs is True
                    if formatted_response.preserve_paragraphs:
                        return self.process_complete_response(main_text)
                    else:
                        # Skip normalization to preserve the exact structure
                        return main_text
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse structured output at stage '{processing_stage}': {str(e)}")
                    logger.debug(f"Error details: {traceback.format_exc()}")
                    # Log the problematic JSON for debugging
                    if processing_stage == "json_parsing":
                        logger.debug(f"Problematic JSON: {response_text[:500]}...")
                    
                    # Record structured output error
                    monitor = get_monitor()
                    monitor.record_structured_output_error(
                        error_message=str(e),
                        processing_stage=processing_stage
                    )
                    
                    # Record fallback to backend processing
                    monitor.record_fallback(
                        from_approach=FormattingApproach.STRUCTURED_OUTPUT,
                        to_approach=FormattingApproach.BACKEND_PROCESSING,
                        reason=f"Error in {processing_stage}: {str(e)}"
                    )
                    
                    # Fall back to normal processing
            
        except Exception as e:
            logger.warning(f"Error processing structured output: {str(e)}")
            logger.debug(f"Error details: {traceback.format_exc()}")
            
            # Record structured output error
            monitor = get_monitor()
            monitor.record_structured_output_error(
                error_message=str(e),
                processing_stage="unknown"
            )
            
            # Record fallback to backend processing
            monitor.record_fallback(
                from_approach=FormattingApproach.STRUCTURED_OUTPUT,
                to_approach=FormattingApproach.BACKEND_PROCESSING,
                reason=f"Unexpected error: {str(e)}"
            )
            
            # Fall back to normal processing
        
        # Apply text normalization to improve formatting
        logger.info("Falling back to backend text processing")
        
        # Record backend processing event
        monitor = get_monitor()
        monitor.record_event(
            approach=FormattingApproach.BACKEND_PROCESSING,
            event=FormattingEvent.SUCCESS,
            details={
                "response_size": len(response_text),
                "content_types": ["text"]
            }
        )
        
        # Process the response text with the standard pipeline
        response_text = self.process_complete_response(response_text, apply_normalization=True, is_structured_json=False)
        
        return response_text
    def process_complete_response(self, response_text: str, apply_normalization: bool = True, is_structured_json: bool = False) -> str:
        """
        Process a complete response with optional normalization
        
        Args:
            response_text: The complete response text
            apply_normalization: Whether to apply text normalization
            is_structured_json: Whether the response is already processed from structured JSON
            
        Returns:
            Processed response text
        """
        # Log the raw response text from Ollama
        logger.debug(f"Raw response from Ollama (length: {len(response_text)})")
        logger.debug(f"Raw response preview: {response_text[:200]}...")
        
        # If this is already processed from structured JSON, skip additional processing
        if is_structured_json:
            logger.info("Response was already processed from structured JSON, skipping additional formatting")
            
            # Log the final processed output for comparison with raw output
            query_id = getattr(self, 'conversation_id', str(uuid.uuid4()))
            logger.debug(f"PROCESSED BACKEND OUTPUT (Query ID: {query_id}):\n```\n{response_text}\n```")
            
            return response_text
        
        # Log paragraph structure in raw response
        paragraphs = response_text.count('\n\n') + 1
        newlines = response_text.count('\n')
        double_newlines = response_text.count('\n\n')
        logger.debug(f"Raw response paragraph structure: paragraphs={paragraphs}, single newlines={newlines}, double newlines={double_newlines}")
        
        # Check for code blocks in raw response
        code_block_pattern = r'```([\w\-+#]*)\s*(.*?)```'
        code_blocks = len(re.findall(code_block_pattern, response_text, re.DOTALL))
        logger.debug(f"Raw response code blocks: {code_blocks}")
        
        if not apply_normalization:
            logger.debug("Skipping normalization as requested")
            return response_text
        
        # Apply text normalization
        logger.debug("Applying text normalization...")
        normalized_text = normalize_text(response_text)
        
        # Log changes after normalization
        if normalized_text != response_text:
            logger.debug("Text was modified during normalization")
            length_diff = len(normalized_text) - len(response_text)
            logger.debug(f"Length change after normalization: {length_diff} characters")
        else:
            logger.debug("No changes made during normalization")
        
        # Format code blocks
        logger.debug("Formatting code blocks...")
        formatted_text = format_code_blocks(normalized_text)
        
        # Log changes after code block formatting
        if formatted_text != normalized_text:
            logger.debug("Text was modified during code block formatting")
            length_diff = len(formatted_text) - len(normalized_text)
            logger.debug(f"Length change after code block formatting: {length_diff} characters")
        else:
            logger.debug("No changes made during code block formatting")
        
        # Log final paragraph structure
        final_paragraphs = formatted_text.count('\n\n') + 1
        final_newlines = formatted_text.count('\n')
        final_double_newlines = formatted_text.count('\n\n')
        logger.debug(f"Final response paragraph structure: paragraphs={final_paragraphs}, single newlines={final_newlines}, double newlines={final_double_newlines}")
        
        # Check if paragraphs were lost during processing
        if paragraphs > final_paragraphs:
            logger.warning(f"Paragraph count decreased during processing: {paragraphs} -> {final_paragraphs}")
            
        # Log the final processed output for comparison with raw output
        query_id = getattr(self, 'conversation_id', str(uuid.uuid4()))
        logger.debug(f"PROCESSED BACKEND OUTPUT (Query ID: {query_id}):\n```\n{formatted_text}\n```")
        
        return formatted_text
        
    def _format_table(self, table) -> str:
        """
        Format a table into markdown format
        
        Args:
            table: The Table object to format
            
        Returns:
            Markdown representation of the table
        """
        logger = logging.getLogger("app.rag.rag_generation")
        logger.debug(f"Formatting table with {len(table.rows)} rows")
        
        # Start with the caption if available
        markdown_lines = []
        if table.caption:
            markdown_lines.append(f"**{table.caption}**\n")
        
        # Process the rows
        for i, row in enumerate(table.rows):
            # Create the row content
            row_cells = []
            for cell in row.cells:
                # Apply alignment if specified
                content = cell.content.strip()
                if cell.align == "center":
                    content = f" {content} "
                elif cell.align == "right":
                    content = f" {content}"
                else:  # left alignment (default)
                    content = f"{content} "
                
                row_cells.append(content)
            
            # Add the row to the markdown
            markdown_lines.append(f"| {' | '.join(row_cells)} |")
            
            # Add the header separator after the first row if it's a header row
            if i == 0 and (row.is_header_row or any(cell.is_header for cell in row.cells)):
                separators = []
                for cell in row.cells:
                    if cell.align == "center":
                        separators.append(":---:")
                    elif cell.align == "right":
                        separators.append("---:")
                    else:  # left alignment (default)
                        separators.append("---")
                
                markdown_lines.append(f"| {' | '.join(separators)} |")
        
        # Join the lines with newlines
        return "\n".join(markdown_lines)
    
    def _format_image(self, image) -> str:
        """
        Format an image into markdown format
        
        Args:
            image: The Image object to format
            
        Returns:
            Markdown representation of the image
        """
        logger = logging.getLogger("app.rag.rag_generation")
        logger.debug(f"Formatting image with URL: {image.url}")
        
        # Create the basic image markdown
        markdown = f"![{image.alt_text}]({image.url})"
        
        # Add the caption if available
        if image.caption:
            markdown += f"\n*{image.caption}*"
        
        return markdown
    
    def _format_math(self, math_block) -> str:
        """
        Format a math block into markdown format
        
        Args:
            math_block: The MathBlock object to format
            
        Returns:
            Markdown representation of the math block
        """
        logger = logging.getLogger("app.rag.rag_generation")
        logger.debug("Formatting math block")
        
        # Format based on display mode
        if math_block.display_mode:
            # Display mode (block)
            return f"$$\n{math_block.latex}\n$$"
        else:
            # Inline mode
            return f"${math_block.latex}$"
        
    def _attempt_json_repair(self, json_text: str) -> str:
        """
        Attempt to repair malformed JSON
        
        Args:
            json_text: The malformed JSON text
            
        Returns:
            Repaired JSON text or empty string if repair failed
        """
        import re
        import json
        
        logger = logging.getLogger("app.rag.rag_generation")
        logger.debug("Attempting to repair malformed JSON")
        
        try:
            # Common JSON formatting issues and their fixes
            
            # 1. Fix unescaped quotes in strings
            # Look for patterns like: "key": "value with "quotes" inside"
            fixed_text = re.sub(r'(?<=[:\s]\s*"[^"]*)"(?=[^"]*"(?:\s*[,}]))', r'\"', json_text)
            
            # 2. Fix missing quotes around keys
            # Look for patterns like: {key: "value"} instead of {"key": "value"}
            fixed_text = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', fixed_text)
            
            # 3. Fix trailing commas in objects and arrays
            # Look for patterns like: {"key": "value",} or [1, 2, 3,]
            fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
            
            # 4. Fix missing commas between elements
            # Look for patterns like: {"key1": "value1" "key2": "value2"}
            fixed_text = re.sub(r'(["\d])\s*"', r'\1, "', fixed_text)
            
            # 5. Fix single quotes used instead of double quotes
            # First, escape any existing double quotes
            fixed_text = fixed_text.replace('"', '\\"')
            # Then replace all single quotes with double quotes
            fixed_text = fixed_text.replace("'", '"')
            # Finally, fix the double-escaped quotes
            fixed_text = fixed_text.replace('\\"', '"')
            
            # Validate the fixed JSON
            json.loads(fixed_text)
            logger.info("JSON repair successful")
            return fixed_text
        except Exception as e:
            logger.warning(f"JSON repair failed: {str(e)}")
            return ""
    
    def _attempt_partial_validation(self, data: dict) -> Optional['FormattedResponse']:
        """
        Attempt partial validation of structured output data
        
        Args:
            data: The structured output data
            
        Returns:
            FormattedResponse object or None if validation failed
        """
        from app.models.structured_output import FormattedResponse, CodeBlock, TextBlock
        from typing import Optional
        
        logger = logging.getLogger("app.rag.rag_generation")
        logger.debug("Attempting partial validation of structured output data")
        
        try:
            # Create a minimal valid response
            minimal_response = {
                "text": "",
                "code_blocks": [],
                "preserve_paragraphs": True
            }
            
            # Copy valid fields from the original data
            if "text" in data and isinstance(data["text"], str):
                minimal_response["text"] = data["text"]
            
            # Process code blocks if available
            if "code_blocks" in data and isinstance(data["code_blocks"], list):
                code_blocks = []
                for block in data["code_blocks"]:
                    if isinstance(block, dict):
                        # Ensure required fields are present
                        if "language" in block and "code" in block:
                            code_blocks.append({
                                "language": block["language"],
                                "code": block["code"],
                                "metadata": block.get("metadata")
                            })
                minimal_response["code_blocks"] = code_blocks
            
            # Process text blocks if available
            if "text_blocks" in data and isinstance(data["text_blocks"], list):
                text_blocks = []
                for block in data["text_blocks"]:
                    if isinstance(block, dict):
                        # Ensure required fields are present
                        if "content" in block:
                            text_blocks.append({
                                "content": block["content"],
                                "format_type": block.get("format_type", "paragraph"),
                                "metadata": block.get("metadata")
                            })
                if text_blocks:
                    minimal_response["text_blocks"] = text_blocks
            
            # Set preserve_paragraphs if available
            if "preserve_paragraphs" in data and isinstance(data["preserve_paragraphs"], bool):
                minimal_response["preserve_paragraphs"] = data["preserve_paragraphs"]
            
            # Validate the minimal response
            formatted_response = FormattedResponse.model_validate(minimal_response)
            logger.info("Partial validation successful")
            return formatted_response
        except Exception as e:
            logger.warning(f"Partial validation failed: {str(e)}")
            return None
    
    def _fix_unreplaced_placeholders(self, text: str, code_blocks: list) -> str:
        """
        Fix unreplaced code block placeholders
        
        Args:
            text: The text with unreplaced placeholders
            code_blocks: The list of code blocks
            
        Returns:
            Text with placeholders replaced or removed
        """
        import re
        
        logger = logging.getLogger("app.rag.rag_generation")
        logger.debug("Fixing unreplaced code block placeholders")
        
        # Find all unreplaced placeholders
        placeholder_pattern = r'\{CODE_BLOCK_(\d+)\}'
        placeholders = re.findall(placeholder_pattern, text)
        
        # Replace or remove each placeholder
        for placeholder_index in placeholders:
            try:
                index = int(placeholder_index)
                placeholder = f"{{CODE_BLOCK_{index}}}"
                
                # If we have a code block for this index, replace it
                if index < len(code_blocks):
                    code_block = code_blocks[index]
                    formatted_block = f"```{code_block.language}\n{code_block.code}\n```"
                    text = text.replace(placeholder, formatted_block)
                    logger.debug(f"Replaced placeholder {placeholder} with code block")
                else:
                    # Otherwise, remove the placeholder
                    text = text.replace(placeholder, "")
                    logger.warning(f"Removed placeholder {placeholder} with no corresponding code block")
            except ValueError:
                # If the index is not a valid integer, just remove the placeholder
                logger.warning(f"Found invalid placeholder index: {placeholder_index}")
                placeholder = f"{{CODE_BLOCK_{placeholder_index}}}"
                text = text.replace(placeholder, "")
        
        return text
        return formatted_text