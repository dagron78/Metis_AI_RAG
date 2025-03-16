"""
Chunking Judge - LLM-based agent that analyzes documents and recommends optimal chunking strategies
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional

from app.models.document import Document
from app.rag.ollama_client import OllamaClient
from app.core.config import CHUNKING_JUDGE_MODEL

logger = logging.getLogger("app.rag.agents.chunking_judge")

class ChunkingJudge:
    """
    LLM-based agent that analyzes documents and recommends optimal chunking strategies
    """
    def __init__(self, ollama_client: Optional[OllamaClient] = None, model: str = CHUNKING_JUDGE_MODEL):
        self.ollama_client = ollama_client or OllamaClient()
        self.model = model
    
    async def analyze_document(self, document: Document) -> Dict[str, Any]:
        """
        Analyze a document and recommend the best chunking strategy and parameters
        
        Returns:
            Dict with keys:
            - strategy: The recommended chunking strategy
            - parameters: Dict of parameters for the chosen strategy
            - justification: Explanation of the recommendation
        """
        # Extract a sample of the document content (to avoid exceeding context window)
        content_sample = self._extract_representative_sample(document.content, document.filename)
        
        # Create prompt for the LLM
        prompt = self._create_analysis_prompt(document.filename, content_sample)
        
        # Get recommendation from LLM
        response = await self.ollama_client.generate(
            prompt=prompt,
            model=self.model,
            stream=False
        )
        
        # Parse the response
        recommendation = self._parse_recommendation(response.get("response", ""))
        
        logger.info(f"Chunking Judge recommended strategy '{recommendation['strategy']}' for document {document.filename}")
        
        return recommendation
    
    def _extract_representative_sample(self, content: str, filename: str, max_length: int = 5000) -> str:
        """
        Extract a representative sample of the document content
        
        This function prioritizes:
        1. Headers (especially for markdown files)
        2. Introduction and conclusion sections
        3. A mix of content from throughout the document
        """
        if len(content) <= max_length:
            return content
        
        # Check if it's a markdown file
        is_markdown = filename.lower().endswith(('.md', '.markdown'))
        
        # For markdown files, prioritize headers
        if is_markdown:
            # Extract headers
            header_pattern = r'^(#{1,6}\s+.+)$'
            headers = re.findall(header_pattern, content, re.MULTILINE)
            
            # If we have headers, include them in the sample
            if headers:
                # Take all headers (they're usually short)
                headers_text = "\n".join(headers)
                
                # Calculate remaining space
                remaining_space = max_length - len(headers_text) - 100  # 100 chars buffer
                
                # Divide remaining space between intro, middle, and conclusion
                section_size = remaining_space // 3
                
                # Get intro, middle, and conclusion
                intro = content[:section_size]
                middle_start = (len(content) - section_size) // 2
                middle = content[middle_start:middle_start + section_size]
                conclusion = content[-section_size:]
                
                return f"{headers_text}\n\n--- DOCUMENT SAMPLE ---\n\nINTRO:\n{intro}\n\n[...]\n\nMIDDLE SECTION:\n{middle}\n\n[...]\n\nCONCLUSION:\n{conclusion}"
        
        # For non-markdown files or markdown files without headers
        # Take larger portions from the beginning and end (intro/conclusion)
        intro_size = max_length * 2 // 5  # 40% for intro
        conclusion_size = max_length * 2 // 5  # 40% for conclusion
        middle_size = max_length - intro_size - conclusion_size  # 20% for middle
        
        intro = content[:intro_size]
        middle_start = (len(content) - middle_size) // 2
        middle = content[middle_start:middle_start + middle_size]
        conclusion = content[-conclusion_size:]
        
        return f"INTRO:\n{intro}\n\n[...]\n\nMIDDLE SECTION:\n{middle}\n\n[...]\n\nCONCLUSION:\n{conclusion}"
    
    def _create_analysis_prompt(self, filename: str, content_sample: str) -> str:
        """Create a prompt for the LLM to analyze the document"""
        return f"""You are a document analysis expert. Your task is to analyze the following document and recommend the best chunking strategy for a RAG (Retrieval Augmented Generation) system.

Available Strategies:
- recursive: Splits text recursively by characters. Good for general text with natural separators.
- token: Splits text by tokens. Good for preserving semantic units in technical content.
- markdown: Splits markdown documents by headers. Good for structured documents with clear sections.

Document Filename: {filename}

Document Sample:
{content_sample}

Analyze the document structure, content type, and formatting. Consider:
1. Is this a structured document with clear sections or headers?
2. Does it contain code, tables, or other special formatting?
3. What's the typical paragraph and sentence length?
4. Are there natural breaks in the content?
5. Would semantic chunking be more appropriate than fixed-size chunking?

Here are some examples of good chunking strategy recommendations:

Example 1:
Document: technical_documentation.md
Recommendation: 
{{
    "strategy": "markdown",
    "parameters": {{
        "chunk_size": 1000,
        "chunk_overlap": 100
    }},
    "justification": "This is a markdown document with clear header structure. Using markdown chunking will preserve the semantic structure of the document and ensure that related content stays together."
}}

Example 2:
Document: research_paper.txt
Recommendation:
{{
    "strategy": "recursive",
    "parameters": {{
        "chunk_size": 1500,
        "chunk_overlap": 200
    }},
    "justification": "This document has long paragraphs with complex sentences. A larger chunk size with significant overlap will help preserve context and ensure that related concepts aren't split across chunks."
}}

Example 3:
Document: code_examples.py
Recommendation:
{{
    "strategy": "token",
    "parameters": {{
        "chunk_size": 500,
        "chunk_overlap": 50
    }},
    "justification": "This document contains code snippets where preserving token-level semantics is important. Token-based chunking will ensure that code blocks remain coherent."
}}

Output your recommendation in JSON format:
{{
    "strategy": "...",  // One of: recursive, token, markdown
    "parameters": {{
        "chunk_size": ...,  // Recommended chunk size (characters or tokens)
        "chunk_overlap": ...  // Recommended overlap size
    }},
    "justification": "..." // Explanation of your reasoning
}}
"""
    
    def _parse_recommendation(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response to extract the recommendation"""
        try:
            # Extract JSON from the response
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                json_str = json_match.group(1)
                recommendation = json.loads(json_str)
                
                # Validate the recommendation
                if "strategy" not in recommendation:
                    raise ValueError("Missing 'strategy' in recommendation")
                
                # Validate strategy is one of the allowed values
                allowed_strategies = ["recursive", "token", "markdown"]
                if recommendation["strategy"] not in allowed_strategies:
                    logger.warning(f"Invalid strategy '{recommendation['strategy']}', falling back to recursive")
                    recommendation["strategy"] = "recursive"
                
                # Set defaults if missing
                if "parameters" not in recommendation:
                    recommendation["parameters"] = {}
                if "chunk_size" not in recommendation["parameters"]:
                    recommendation["parameters"]["chunk_size"] = 500
                if "chunk_overlap" not in recommendation["parameters"]:
                    recommendation["parameters"]["chunk_overlap"] = 50
                
                return recommendation
            else:
                raise ValueError("Could not find JSON in response")
        except Exception as e:
            logger.error(f"Error parsing chunking recommendation: {str(e)}")
            # Return default recommendation
            return {
                "strategy": "recursive",
                "parameters": {
                    "chunk_size": 500,
                    "chunk_overlap": 50
                },
                "justification": "Failed to parse LLM recommendation, using default strategy."
            }