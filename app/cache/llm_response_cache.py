"""
LLM response cache implementation for Metis_RAG.
"""

import hashlib
import json
from typing import Dict, Any, Optional, List, Tuple

from app.cache.base import Cache

class LLMResponseCache(Cache[Dict[str, Any]]):
    """
    Cache implementation for LLM responses.
    
    This cache stores responses from language models to avoid redundant API calls,
    reducing latency and costs.
    
    Attributes:
        Inherits all attributes from the base Cache class
    """
    
    def __init__(
        self,
        ttl: int = 86400,  # 24 hours default TTL for LLM responses
        max_size: int = 2000,  # Higher default max size for LLM responses
        persist: bool = True,
        persist_dir: str = "data/cache"
    ):
        """
        Initialize a new LLM response cache.
        
        Args:
            ttl: Time-to-live in seconds for cache entries (default: 86400)
            max_size: Maximum number of entries in the cache (default: 2000)
            persist: Whether to persist the cache to disk (default: True)
            persist_dir: Directory for cache persistence (default: "data/cache")
        """
        super().__init__(
            name="llm_response",
            ttl=ttl,
            max_size=max_size,
            persist=persist,
            persist_dir=persist_dir
        )
    
    def get_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a cached LLM response.
        
        Args:
            prompt: The prompt sent to the LLM
            model: The model identifier
            temperature: The temperature parameter (default: 0.0)
            max_tokens: The maximum tokens parameter (default: None)
            additional_params: Additional parameters sent to the LLM (default: None)
            
        Returns:
            Cached LLM response if found, None otherwise
        """
        cache_key = self._create_response_key(prompt, model, temperature, max_tokens, additional_params)
        return self.get(cache_key)
    
    def set_response(
        self,
        prompt: str,
        model: str,
        response: Dict[str, Any],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache an LLM response.
        
        Args:
            prompt: The prompt sent to the LLM
            model: The model identifier
            response: The LLM response to cache
            temperature: The temperature parameter (default: 0.0)
            max_tokens: The maximum tokens parameter (default: None)
            additional_params: Additional parameters sent to the LLM (default: None)
        """
        cache_key = self._create_response_key(prompt, model, temperature, max_tokens, additional_params)
        self.set(cache_key, response)
    
    def _create_response_key(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a cache key for an LLM response.
        
        Args:
            prompt: The prompt sent to the LLM
            model: The model identifier
            temperature: The temperature parameter
            max_tokens: The maximum tokens parameter
            additional_params: Additional parameters sent to the LLM
            
        Returns:
            Cache key string
        """
        # Normalize the prompt by removing extra whitespace
        normalized_prompt = " ".join(prompt.split())
        
        # Create a dictionary of all parameters
        params = {
            "model": model,
            "temperature": temperature
        }
        
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
            
        if additional_params:
            params.update(additional_params)
        
        # Convert parameters to a stable string representation
        params_str = json.dumps(params, sort_keys=True)
        
        # Create a hash of the combined parameters for a shorter key
        key_data = f"{normalized_prompt}:{params_str}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"llm:{key_hash}"
    
    def invalidate_by_model(self, model: str) -> int:
        """
        Invalidate all cache entries for a specific model.
        
        Args:
            model: Model identifier to invalidate
            
        Returns:
            Number of cache entries invalidated
        """
        invalidated_count = 0
        keys_to_delete = []
        
        # Find all cache entries for the specified model
        for key, entry in list(self.cache.items()):
            response = entry["value"]
            if response.get("model") == model:
                keys_to_delete.append(key)
                invalidated_count += 1
        
        # Delete the identified entries
        for key in keys_to_delete:
            self.delete(key)
        
        self.logger.info(f"Invalidated {invalidated_count} cache entries for model {model}")
        return invalidated_count
    
    def get_response_by_prompt_prefix(self, prefix: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get cached responses for prompts starting with a specific prefix.
        
        Args:
            prefix: Prompt prefix to filter by
            limit: Maximum number of responses to return (default: 10)
            
        Returns:
            List of cached responses for prompts with the specified prefix
        """
        responses = []
        count = 0
        
        for key, entry in list(self.cache.items()):
            if count >= limit:
                break
                
            response = entry["value"]
            if "prompt" in response and response["prompt"].startswith(prefix):
                responses.append(response)
                count += 1
        
        return responses
    
    def get_cache_stats_by_model(self) -> Dict[str, Tuple[int, int]]:
        """
        Get hit/miss statistics by model.
        
        Returns:
            Dictionary mapping model identifiers to (hits, misses) tuples
        """
        # This is a simplified implementation that would need to be enhanced
        # with actual tracking of per-model statistics in a real system
        return {}
    
    def should_cache_response(
        self,
        prompt: str,
        model: str,
        temperature: float,
        response: Dict[str, Any]
    ) -> bool:
        """
        Determine whether a response should be cached based on various factors.
        
        Args:
            prompt: The prompt sent to the LLM
            model: The model identifier
            temperature: The temperature parameter
            response: The LLM response
            
        Returns:
            True if the response should be cached, False otherwise
        """
        # Don't cache responses from high-temperature requests (more random)
        if temperature > 0.5:
            return False
            
        # Don't cache very short responses
        if len(response.get("response", "")) < 10:
            return False
            
        # Don't cache error responses
        if response.get("error"):
            return False
            
        return True