"""
Semantic Chunker - LLM-based chunker that splits text based on semantic boundaries
"""
import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple

from langchain.schema import Document as LangchainDocument
from langchain.text_splitter import TextSplitter

from app.rag.ollama_client import OllamaClient
from app.core.config import CHUNKING_JUDGE_MODEL

logger = logging.getLogger("app.rag.chunkers.semantic_chunker")

class SemanticChunker(TextSplitter):
    """
    LLM-based chunker that splits text based on semantic boundaries rather than
    just character or token counts.
    
    This chunker uses an LLM to identify natural semantic boundaries in text,
    ensuring that chunks maintain coherent meaning and context.
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        model: str = CHUNKING_JUDGE_MODEL,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
        max_llm_context_length: int = 8000,
        cache_enabled: bool = True
    ):
        """
        Initialize the SemanticChunker.
        
        Args:
            ollama_client: Optional OllamaClient instance
            model: LLM model to use for semantic analysis
            chunk_size: Target size for chunks (in characters)
            chunk_overlap: Target overlap between chunks (in characters)
            max_llm_context_length: Maximum context length for LLM input
            cache_enabled: Whether to cache chunking results
        """
        # Initialize with default separator to satisfy TextSplitter requirements
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        self.ollama_client = ollama_client or OllamaClient()
        self.model = model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_llm_context_length = max_llm_context_length
        self.cache_enabled = cache_enabled
        self.cache = {}  # Simple in-memory cache
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text based on semantic boundaries.
        
        This method overrides the TextSplitter.split_text method to use
        LLM-based semantic chunking instead of simple character-based splitting.
        
        Args:
            text: The text to split
            
        Returns:
            List of text chunks split at semantic boundaries
        """
        # Check cache first if enabled
        if self.cache_enabled and text in self.cache:
            logger.info("Using cached semantic chunks")
            return self.cache[text]
        
        # If text is short enough, return it as a single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        # For longer texts, use semantic chunking
        chunks = self._semantic_chunking(text)
        
        # Cache the result if enabled
        if self.cache_enabled:
            self.cache[text] = chunks
        
        return chunks
    
    async def split_text_async(self, text: str) -> List[str]:
        """
        Asynchronous version of split_text.
        
        Args:
            text: The text to split
            
        Returns:
            List of text chunks split at semantic boundaries
        """
        # Check cache first if enabled
        if self.cache_enabled and text in self.cache:
            logger.info("Using cached semantic chunks")
            return self.cache[text]
        
        # If text is short enough, return it as a single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        # For longer texts, use semantic chunking
        chunks = await self._semantic_chunking_async(text)
        
        # Cache the result if enabled
        if self.cache_enabled:
            self.cache[text] = chunks
        
        return chunks
    
    def _semantic_chunking(self, text: str) -> List[str]:
        """
        Synchronous wrapper for _semantic_chunking_async.
        
        This is needed because TextSplitter.split_text is synchronous.
        In practice, this will be less efficient than the async version
        because it blocks on the LLM call.
        
        Args:
            text: The text to split
            
        Returns:
            List of text chunks split at semantic boundaries
        """
        import asyncio
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, create a new one in a thread
                logger.warning("Running async semantic chunking in a new event loop")
                return asyncio.run(self._semantic_chunking_async(text))
            else:
                # If no event loop is running, use the current one
                return loop.run_until_complete(self._semantic_chunking_async(text))
        except RuntimeError:
            # If no event loop is available, create a new one
            logger.warning("No event loop available, creating a new one")
            return asyncio.run(self._semantic_chunking_async(text))
    
    async def _semantic_chunking_async(self, text: str) -> List[str]:
        """
        Split text based on semantic boundaries using LLM.
        
        For long texts, this method:
        1. Divides the text into sections that fit within the LLM context window
        2. Processes each section to identify semantic boundaries
        3. Combines the results, ensuring proper handling of section boundaries
        
        Args:
            text: The text to split
            
        Returns:
            List of text chunks split at semantic boundaries
        """
        # If text is too long for a single LLM call, process it in sections
        if len(text) > self.max_llm_context_length:
            return await self._process_long_text(text)
        
        # For text that fits in a single LLM call, process directly
        return await self._identify_semantic_boundaries(text)
    
    async def _process_long_text(self, text: str) -> List[str]:
        """
        Process a long text by dividing it into sections and processing each section.
        
        Args:
            text: The long text to process
            
        Returns:
            List of semantically chunked text
        """
        # Calculate section size, leaving room for prompt and instructions
        section_size = self.max_llm_context_length - 2000
        
        # Divide text into overlapping sections
        sections = []
        for i in range(0, len(text), section_size - self.chunk_overlap):
            section_start = max(0, i)
            section_end = min(len(text), i + section_size)
            sections.append(text[section_start:section_end])
        
        logger.info(f"Processing long text in {len(sections)} sections")
        
        # Process each section
        all_chunks = []
        for i, section in enumerate(sections):
            logger.info(f"Processing section {i+1}/{len(sections)}")
            section_chunks = await self._identify_semantic_boundaries(section)
            
            # For all but the first section, check if the first chunk should be merged
            # with the last chunk of the previous section
            if i > 0 and all_chunks and section_chunks:
                # If the first chunk of this section is small, it might be a continuation
                if len(section_chunks[0]) < self.chunk_size / 2:
                    # Merge with the last chunk of the previous section
                    merged_chunk = all_chunks[-1] + section_chunks[0]
                    # If the merged chunk is still reasonable in size, use it
                    if len(merged_chunk) <= self.chunk_size * 1.5:
                        all_chunks[-1] = merged_chunk
                        section_chunks = section_chunks[1:]
            
            all_chunks.extend(section_chunks)
        
        return all_chunks
    
    async def _identify_semantic_boundaries(self, text: str) -> List[str]:
        """
        Use LLM to identify semantic boundaries in text and split accordingly.
        
        Args:
            text: The text to analyze and split
            
        Returns:
            List of text chunks split at semantic boundaries
        """
        prompt = self._create_chunking_prompt(text)
        
        try:
            # Get boundaries from LLM
            response = await self.ollama_client.generate(
                prompt=prompt,
                model=self.model,
                stream=False
            )
            
            # Parse the response
            boundaries = self._parse_boundaries(response.get("response", ""), text)
            
            # If parsing fails or no boundaries are found, fall back to simple chunking
            if not boundaries:
                logger.warning("Failed to identify semantic boundaries, falling back to simple chunking")
                return self._fallback_chunking(text)
            
            # Create chunks based on identified boundaries
            chunks = self._create_chunks_from_boundaries(text, boundaries)
            
            logger.info(f"Created {len(chunks)} semantic chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error in semantic chunking: {str(e)}")
            # Fall back to simple chunking on error
            return self._fallback_chunking(text)
    
    def _create_chunking_prompt(self, text: str) -> str:
        """
        Create a prompt for the LLM to identify semantic boundaries.
        
        Args:
            text: The text to analyze
            
        Returns:
            Prompt for the LLM
        """
        return f"""You are an expert in natural language understanding and text analysis. Your task is to identify natural semantic boundaries in the following text. These boundaries should:

1. Respect the semantic structure of the content
2. Create coherent, self-contained chunks that maintain context
3. Occur at natural transitions between topics, ideas, or sections
4. Result in chunks that are approximately {self.chunk_size} characters in length (but prioritize semantic coherence over exact size)

Text to analyze:
```
{text}
```

Analyze the text and identify the character positions where natural semantic boundaries occur. Consider:
- Paragraph breaks that signal topic transitions
- Section boundaries
- Shifts in subject matter or perspective
- Transitions between different types of content (e.g., explanation to example)
- Natural pauses in the flow of information

Output ONLY a JSON array of character positions where chunks should be split, like this:
[500, 1050, 1600, 2200]

These positions should indicate the character index where each new chunk should begin (except the first chunk, which starts at position 0).

Important: Focus on semantic coherence rather than exact chunk size. It's better to have slightly uneven chunks that maintain semantic integrity than equal-sized chunks that break mid-thought.
"""
    
    def _parse_boundaries(self, response_text: str, original_text: str) -> List[int]:
        """
        Parse the LLM response to extract boundary positions.
        
        Args:
            response_text: The LLM response text
            original_text: The original text being chunked
            
        Returns:
            List of character positions for chunk boundaries
        """
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[[\d\s,]+\]', response_text)
            if not json_match:
                logger.warning("Could not find boundary array in LLM response")
                return []
            
            boundaries = json.loads(json_match.group(0))
            
            # Validate boundaries
            if not isinstance(boundaries, list):
                logger.warning(f"Invalid boundary format: {boundaries}")
                return []
            
            # Filter out invalid boundaries
            valid_boundaries = [b for b in boundaries if isinstance(b, (int, float)) and 0 < b < len(original_text)]
            valid_boundaries = sorted(valid_boundaries)
            
            # Add the start position (0) if not present
            if valid_boundaries and valid_boundaries[0] > 0:
                valid_boundaries = [0] + valid_boundaries
            
            logger.info(f"Identified {len(valid_boundaries)} semantic boundaries")
            return valid_boundaries
            
        except Exception as e:
            logger.error(f"Error parsing semantic boundaries: {str(e)}")
            return []
    
    def _create_chunks_from_boundaries(self, text: str, boundaries: List[int]) -> List[str]:
        """
        Create text chunks based on identified boundaries.
        
        Args:
            text: The original text
            boundaries: List of character positions for chunk boundaries
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        # Ensure the text starts at the first boundary
        if not boundaries or boundaries[0] != 0:
            boundaries = [0] + boundaries
        
        # Add the end of the text as the final boundary
        boundaries.append(len(text))
        
        # Create chunks based on boundaries
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            
            # Skip empty chunks
            if start == end:
                continue
                
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
        
        # Apply overlap if specified
        if self.chunk_overlap > 0:
            chunks = self._apply_overlap(chunks)
        
        return chunks
    
    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """
        Apply overlap between chunks to maintain context.
        
        Args:
            chunks: List of text chunks without overlap
            
        Returns:
            List of text chunks with overlap applied
        """
        if not chunks or len(chunks) < 2:
            return chunks
            
        result = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Calculate overlap size (in characters)
            overlap_size = min(self.chunk_overlap, len(prev_chunk) // 2)
            
            # If previous chunk is too small, don't apply overlap
            if len(prev_chunk) <= overlap_size * 2:
                result.append(current_chunk)
                continue
                
            # Get the overlap text from the end of the previous chunk
            overlap_text = prev_chunk[-overlap_size:]
            
            # Add the overlap to the beginning of the current chunk
            result.append(overlap_text + current_chunk)
            
        return result
    
    def _fallback_chunking(self, text: str) -> List[str]:
        """
        Fallback method for chunking when LLM-based chunking fails.
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        logger.info("Using fallback chunking method")
        
        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the chunk size,
            # save the current chunk and start a new one
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                # Otherwise, add the paragraph to the current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Apply overlap if specified
        if self.chunk_overlap > 0:
            chunks = self._apply_overlap(chunks)
        
        return chunks