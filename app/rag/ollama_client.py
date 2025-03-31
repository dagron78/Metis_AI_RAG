import httpx
import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Generator, Tuple, Union
from sse_starlette.sse import EventSourceResponse

from app.core.config import OLLAMA_BASE_URL, DEFAULT_MODEL

logger = logging.getLogger("app.rag.ollama_client")

class OllamaClient:
    """
    Client for interacting with Ollama API
    """
    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = await self.client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return response.json().get("models", [])
            except Exception as e:
                logger.error(f"Error listing models (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
    
    async def generate(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        system_prompt: Optional[str] = None,
        stream: bool = True,
        parameters: Dict[str, Any] = None
    ) -> Union[Dict[str, Any], Generator[str, None, None]]:
        """
        Generate a response from the model
        """
        if parameters is None:
            parameters = {}
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **parameters
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if stream:
                    return await self._stream_response(payload)
                else:
                    response = await self.client.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    
                    # Check if the response contains an error message from the model
                    if 'error' in response_data:
                        logger.warning(f"Model returned an error: {response_data['error']}")
                        # Return the error message instead of raising an exception
                        return {
                            "response": f"I'm unable to answer that question. {response_data['error']}",
                            "error": response_data['error']
                        }
                    
                    return response_data
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error generating response (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    # Return a user-friendly error message
                    return {
                        "response": "I'm unable to answer that question right now. There was an issue connecting to the language model.",
                        "error": str(e)
                    }
            except Exception as e:
                logger.error(f"Error generating response (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    # Return a user-friendly error message instead of raising
                    return {
                        "response": "I'm unable to process your request right now. There might be an issue with the language model or your question.",
                        "error": str(e)
                    }
    
    async def _stream_response(self, payload: Dict[str, Any]):
        """
        Stream response from the model with improved error handling and longer timeouts
        """
        # Increase timeout for streaming responses
        STREAM_TIMEOUT = 300  # 5 minutes
        
        async def event_generator():
            try:
                # Use a longer timeout for streaming responses
                async with httpx.AsyncClient(timeout=STREAM_TIMEOUT) as client:
                    try:
                        # Set longer read timeout and connection timeout
                        async with client.stream(
                            "POST",
                            f"{self.base_url}/api/generate",
                            json=payload,
                            timeout=httpx.Timeout(connect=30, read=STREAM_TIMEOUT, write=30, pool=30)
                        ) as response:
                            response.raise_for_status()
                            
                            # Process the stream with better error handling
                            async for line in response.aiter_lines():
                                if line:
                                    try:
                                        data = json.loads(line)
                                        
                                        # Check if the response contains an error message
                                        if 'error' in data:
                                            error_msg = data['error']
                                            logger.warning(f"Model returned an error in stream: {error_msg}")
                                            yield f"I'm unable to answer that question. {error_msg}"
                                            break
                                        
                                        # Extract and yield the response token directly
                                        token = data.get("response", "")
                                        if token:
                                            yield token
                                            
                                        # Check if we're done
                                        if data.get("done", False):
                                            logger.info("Stream completed successfully")
                                            break
                                    except json.JSONDecodeError:
                                        logger.error(f"Error decoding JSON: {line}")
                    except httpx.ReadTimeout:
                        logger.error("Read timeout while streaming response")
                        yield "\n\nThe response was taking too long to generate. Please try again with a simpler query or disable streaming."
                    except httpx.ConnectTimeout:
                        logger.error("Connection timeout while streaming response")
                        yield "\n\nCouldn't connect to the language model server. Please check if Ollama is running."
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error in streaming response: {str(e)}")
                yield "\n\nI'm unable to answer that question right now. There was an issue connecting to the language model."
            except Exception as e:
                logger.error(f"Error in streaming response: {str(e)}", exc_info=True)
                yield "\n\nI'm unable to process your request right now. There might be an issue with the language model or your question."
        
        return event_generator()  # Return the generator directly
    
    async def create_embedding(
        self, 
        text: str, 
        model: str = DEFAULT_MODEL
    ) -> List[float]:
        """
        Create an embedding for the given text
        """
        payload = {
            "model": model,
            "prompt": text
        }
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload
                )
                response.raise_for_status()
                return response.json().get("embedding", [])
            except Exception as e:
                logger.error(f"Error creating embedding (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise