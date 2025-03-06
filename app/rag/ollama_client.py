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
    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout: int = 60):
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
                    return response.json()
            except Exception as e:
                logger.error(f"Error generating response (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
    
    async def _stream_response(self, payload: Dict[str, Any]):
        """
        Stream response from the model
        """
        async def event_generator():
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                yield data.get("response", "")
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                logger.error(f"Error decoding JSON: {line}")
        
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