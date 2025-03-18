import os
import time
import logging
import random
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.models.document import Document
from app.core.config import UPLOAD_DIR, OLLAMA_BASE_URL, DEFAULT_MODEL

class DocumentAnalysisService:
    """
    Service for analyzing documents and determining optimal processing strategies
    """
    def __init__(self, llm_provider=None, sample_size=3):
        self.llm_provider = llm_provider
        self.sample_size = sample_size
        self.logger = logging.getLogger("app.rag.document_analysis_service")
        
    async def analyze_document(self, document: Document) -> Dict[str, Any]:
        """
        Analyze a document and recommend a processing strategy
        
        Args:
            document: Document to analyze
            
        Returns:
            Dict with processing strategy and parameters
        """
        start_time = time.time()
        self.logger.info(f"Starting analysis of document: {document.filename}")
        
        # Extract sample content from the document
        sample_content = await self._extract_sample_content(document)
        
        # Use LLM to analyze sample and recommend strategy
        strategy = await self._recommend_strategy(document, sample_content)
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Analysis completed in {elapsed_time:.2f}s. Strategy: {strategy['strategy']}")
        
        return strategy
    
    async def analyze_document_batch(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Analyze a batch of documents and recommend a processing strategy
        
        Args:
            documents: List of documents to analyze
            
        Returns:
            Dict with processing strategy and parameters
        """
        start_time = time.time()
        self.logger.info(f"Starting analysis of {len(documents)} documents")
        
        # Sample documents from the batch
        samples = self._sample_documents(documents)
        
        # Extract representative content from samples
        sample_contents = []
        for doc in samples:
            content = await self._extract_sample_content(doc)
            sample_contents.append({
                "filename": doc.filename,
                "content": content,
                "file_type": doc.metadata.get("file_type", "unknown")
            })
        
        # Use LLM to analyze samples and recommend strategy
        strategy = await self._recommend_batch_strategy(sample_contents)
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Batch analysis completed in {elapsed_time:.2f}s. Strategy: {strategy['strategy']}")
        
        return strategy
    
    async def _extract_sample_content(self, document: Document) -> str:
        """
        Extract a representative sample of content from a document
        
        Args:
            document: Document to extract content from
            
        Returns:
            String containing sample content
        """
        try:
            file_path = os.path.join(UPLOAD_DIR, str(document.id), document.filename)
            
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return ""
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # For small files, read the entire content
            if file_size < 10000:  # Less than 10KB
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # For larger files, extract samples from beginning, middle, and end
            samples = []
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Beginning (first 1000 chars)
                f.seek(0)
                samples.append(f.read(1000))
                
                # Middle (1000 chars from the middle)
                f.seek(max(0, file_size // 2 - 500))
                samples.append(f.read(1000))
                
                # End (last 1000 chars)
                f.seek(max(0, file_size - 1000))
                samples.append(f.read(1000))
            
            return "\n...\n".join(samples)
        except Exception as e:
            self.logger.error(f"Error extracting sample content from {document.filename}: {str(e)}")
            return ""
    
    def _sample_documents(self, documents: List[Document]) -> List[Document]:
        """
        Sample a subset of documents from a batch
        
        Args:
            documents: List of documents to sample from
            
        Returns:
            List of sampled documents
        """
        if len(documents) <= self.sample_size:
            return documents
        
        # Ensure we get a diverse sample by file type
        file_types = {}
        for doc in documents:
            file_type = doc.metadata.get("file_type", "unknown")
            if file_type not in file_types:
                file_types[file_type] = []
            file_types[file_type].append(doc)
        
        samples = []
        # Take at least one document of each file type
        for file_type, docs in file_types.items():
            samples.append(random.choice(docs))
        
        # If we need more samples, add random documents
        remaining = self.sample_size - len(samples)
        if remaining > 0:
            remaining_docs = [doc for doc in documents if doc not in samples]
            samples.extend(random.sample(remaining_docs, min(remaining, len(remaining_docs))))
        
        # If we have too many samples, trim to sample_size
        if len(samples) > self.sample_size:
            samples = samples[:self.sample_size]
        
        return samples
    
    async def _recommend_strategy(self, document: Document, sample_content: str) -> Dict[str, Any]:
        """
        Recommend a processing strategy for a document based on its content
        
        Args:
            document: Document to analyze
            sample_content: Sample content from the document
            
        Returns:
            Dict with recommended strategy and parameters
        """
        # Get file type from metadata or filename
        file_type = document.metadata.get("file_type", "")
        if not file_type and document.filename:
            _, ext = os.path.splitext(document.filename.lower())
            file_type = ext[1:] if ext else "unknown"
        
        # If we have an LLM provider, use it to analyze the document
        if self.llm_provider:
            prompt = self._create_analysis_prompt(document.filename, file_type, sample_content)
            response = await self.llm_provider.generate(prompt=prompt)
            try:
                return self._parse_analysis_response(response.get("response", ""))
            except Exception as e:
                self.logger.error(f"Error parsing LLM response: {str(e)}")
                # Fall back to rule-based strategy
        
        # Rule-based strategy if LLM is not available or fails
        return self._rule_based_strategy(document, file_type)
    
    async def _recommend_batch_strategy(self, sample_contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recommend a processing strategy for a batch of documents
        
        Args:
            sample_contents: List of sample contents from documents
            
        Returns:
            Dict with recommended strategy and parameters
        """
        # If we have an LLM provider, use it to analyze the batch
        if self.llm_provider:
            prompt = self._create_batch_analysis_prompt(sample_contents)
            response = await self.llm_provider.generate(prompt=prompt)
            try:
                return self._parse_analysis_response(response.get("response", ""))
            except Exception as e:
                self.logger.error(f"Error parsing LLM response for batch analysis: {str(e)}")
                # Fall back to rule-based strategy
        
        # Rule-based strategy if LLM is not available or fails
        # Default to a general-purpose strategy for mixed document types
        return {
            "strategy": "recursive",
            "parameters": {
                "chunk_size": 1500,
                "chunk_overlap": 150
            },
            "justification": "Default strategy for mixed document types"
        }
    
    def _rule_based_strategy(self, document: Document, file_type: str) -> Dict[str, Any]:
        """
        Determine processing strategy based on file type and simple rules
        
        Args:
            document: Document to analyze
            file_type: File type
            
        Returns:
            Dict with strategy and parameters
        """
        if file_type == "pdf":
            return {
                "strategy": "recursive",
                "parameters": {
                    "chunk_size": 1500,
                    "chunk_overlap": 150
                },
                "justification": "PDF documents benefit from recursive chunking with standard parameters"
            }
        elif file_type == "md":
            return {
                "strategy": "markdown",
                "parameters": {
                    "chunk_size": 1500,
                    "chunk_overlap": 150
                },
                "justification": "Markdown documents benefit from header-based chunking"
            }
        elif file_type == "csv":
            return {
                "strategy": "recursive",
                "parameters": {
                    "chunk_size": 2000,
                    "chunk_overlap": 100
                },
                "justification": "CSV files benefit from larger chunks with less overlap"
            }
        elif file_type == "txt":
            return {
                "strategy": "recursive",
                "parameters": {
                    "chunk_size": 2000,
                    "chunk_overlap": 200
                },
                "justification": "Text files benefit from larger chunks with more overlap"
            }
        else:
            # Default strategy
            return {
                "strategy": "recursive",
                "parameters": {
                    "chunk_size": 1500,
                    "chunk_overlap": 150
                },
                "justification": "Default strategy for unknown file type"
            }
    
    def _create_analysis_prompt(self, filename: str, file_type: str, sample_content: str) -> str:
        """
        Create a prompt for document analysis
        
        Args:
            filename: Document filename
            file_type: Document file type
            sample_content: Sample content from the document
            
        Returns:
            Prompt string
        """
        return f"""
You are an expert document analyst tasked with determining the optimal chunking strategy for a document.

Document Information:
- Filename: {filename}
- File Type: {file_type}

Sample Content:
```
{sample_content[:3000]}  # Limit sample size to avoid token limits
```

Based on the document information and sample content, analyze the document structure and content type, then recommend the best chunking strategy.

Available chunking strategies:
1. recursive - Uses RecursiveCharacterTextSplitter with specified separators
2. token - Uses TokenTextSplitter (better for code or technical content)
3. markdown - Uses MarkdownHeaderTextSplitter (best for markdown with headers)
4. semantic - Uses SemanticChunker (best for complex documents with varying content)

Your analysis should consider:
- Document structure (headers, paragraphs, lists, tables)
- Content type (narrative, technical, code, data)
- Special formatting requirements
- Optimal chunk size and overlap for this document type

Provide your response in the following JSON format:
{{
  "strategy": "strategy_name",
  "parameters": {{
    "chunk_size": size_in_characters,
    "chunk_overlap": overlap_in_characters
  }},
  "justification": "Detailed explanation of your recommendation"
}}
"""
    
    def _create_batch_analysis_prompt(self, sample_contents: List[Dict[str, Any]]) -> str:
        """
        Create a prompt for batch document analysis
        
        Args:
            sample_contents: List of sample contents from documents
            
        Returns:
            Prompt string
        """
        samples_text = ""
        for i, sample in enumerate(sample_contents):
            samples_text += f"\nDocument {i+1}:\n"
            samples_text += f"- Filename: {sample['filename']}\n"
            samples_text += f"- File Type: {sample['file_type']}\n"
            samples_text += f"- Sample Content:\n```\n{sample['content'][:1000]}...\n```\n"
        
        return f"""
You are an expert document analyst tasked with determining the optimal chunking strategy for a batch of documents.

Document Samples:
{samples_text}

Based on these document samples, analyze the document structures and content types, then recommend the best chunking strategy that would work well for the entire batch.

Available chunking strategies:
1. recursive - Uses RecursiveCharacterTextSplitter with specified separators
2. token - Uses TokenTextSplitter (better for code or technical content)
3. markdown - Uses MarkdownHeaderTextSplitter (best for markdown with headers)
4. semantic - Uses SemanticChunker (best for complex documents with varying content)

Your analysis should consider:
- Common document structures across the batch
- Predominant content types
- Special formatting requirements
- Optimal chunk size and overlap that would work for most documents in the batch

Provide your response in the following JSON format:
{{
  "strategy": "strategy_name",
  "parameters": {{
    "chunk_size": size_in_characters,
    "chunk_overlap": overlap_in_characters
  }},
  "justification": "Detailed explanation of your recommendation"
}}
"""
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract the recommended strategy
        
        Args:
            response: LLM response string
            
        Returns:
            Dict with strategy and parameters
        """
        # Simple parsing for JSON response
        # In a real implementation, this would be more robust
        import json
        import re
        
        # Try to extract JSON from the response
        json_match = re.search(r'({[\s\S]*})', response)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                # Validate required fields
                if "strategy" in result and "parameters" in result:
                    return result
            except json.JSONDecodeError:
                pass
        
        # If JSON parsing fails, try to extract key information
        strategy_match = re.search(r'strategy["\']?\s*:\s*["\']?(\w+)["\']?', response)
        chunk_size_match = re.search(r'chunk_size["\']?\s*:\s*(\d+)', response)
        chunk_overlap_match = re.search(r'chunk_overlap["\']?\s*:\s*(\d+)', response)
        
        if strategy_match:
            strategy = strategy_match.group(1)
            chunk_size = int(chunk_size_match.group(1)) if chunk_size_match else 1500
            chunk_overlap = int(chunk_overlap_match.group(1)) if chunk_overlap_match else 150
            
            return {
                "strategy": strategy,
                "parameters": {
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap
                },
                "justification": "Extracted from LLM response"
            }
        
        # If all parsing fails, return default strategy
        return {
            "strategy": "recursive",
            "parameters": {
                "chunk_size": 1500,
                "chunk_overlap": 150
            },
            "justification": "Default strategy due to parsing failure"
        }