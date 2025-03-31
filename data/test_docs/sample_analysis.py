#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sample Python file for testing Metis_RAG document processing capabilities.
This file demonstrates various Python constructs and NLP-related functions
that might be relevant to a RAG system.
"""

import os
import sys
import json
import re
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime, timedelta
from collections import Counter, defaultdict

class DocumentProcessor:
    """A sample document processor class for RAG systems."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """Initialize the document processor with chunking parameters.
        
        Args:
            chunk_size: The size of each text chunk in characters
            overlap: The overlap between consecutive chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.processed_docs = 0
        self.total_chunks = 0
        self.processing_stats = {
            "start_time": None,
            "end_time": None,
            "total_docs": 0,
            "total_chunks": 0,
            "avg_chunks_per_doc": 0,
            "processing_errors": 0
        }
    
    def process_document(self, document_text: str, metadata: Dict = None) -> List[Dict]:
        """Process a document by chunking it and preparing for embedding.
        
        Args:
            document_text: The text content of the document
            metadata: Optional metadata about the document
            
        Returns:
            A list of chunks with their metadata
        """
        if not document_text:
            raise ValueError("Document text cannot be empty")
            
        if not self.processing_stats["start_time"]:
            self.processing_stats["start_time"] = datetime.now()
            
        chunks = self._chunk_text(document_text)
        result = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_id": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "processing_timestamp": datetime.now().isoformat()
            })
            
            result.append({
                "text": chunk,
                "metadata": chunk_metadata
            })
            
        self.processed_docs += 1
        self.total_chunks += len(chunks)
        self.processing_stats["total_docs"] = self.processed_docs
        self.processing_stats["total_chunks"] = self.total_chunks
        self.processing_stats["avg_chunks_per_doc"] = self.total_chunks / self.processed_docs
        
        return result
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with specified overlap.
        
        Args:
            text: The text to chunk
            
        Returns:
            A list of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
            
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to find a good breaking point (newline or period)
            if end < len(text):
                # Look for newline
                newline_pos = text.rfind('\n', start, end)
                period_pos = text.rfind('. ', start, end)
                
                if newline_pos > start + self.chunk_size // 2:
                    end = newline_pos + 1
                elif period_pos > start + self.chunk_size // 2:
                    end = period_pos + 2
            
            chunks.append(text[start:end])
            start = end - self.overlap
            
        return chunks
    
    def get_processing_stats(self) -> Dict:
        """Get statistics about document processing.
        
        Returns:
            A dictionary with processing statistics
        """
        stats = self.processing_stats.copy()
        stats["end_time"] = datetime.now()
        
        if stats["start_time"]:
            duration = stats["end_time"] - stats["start_time"]
            stats["processing_duration_seconds"] = duration.total_seconds()
            
            if stats["total_docs"] > 0:
                stats["seconds_per_document"] = duration.total_seconds() / stats["total_docs"]
                
        return stats


def calculate_embedding_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score
    """
    # Convert to numpy arrays
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Calculate cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    return dot_product / (norm1 * norm2)


if __name__ == "__main__":
    # Sample usage
    processor = DocumentProcessor(chunk_size=500, overlap=100)
    
    sample_text = """
    Retrieval-Augmented Generation (RAG) is a technique that enhances large language models
    by incorporating external knowledge retrieval. This approach allows models to access and
    utilize information beyond their training data, improving factuality and reducing hallucinations.
    
    The RAG architecture typically consists of two main components:
    1. A retrieval system that identifies relevant documents or passages from a knowledge base
    2. A generation system that produces responses based on both the query and the retrieved information
    
    Benefits of RAG include:
    - Improved accuracy and factuality
    - Reduced hallucinations
    - Ability to access up-to-date information
    - Enhanced domain-specific knowledge
    - Greater transparency and explainability
    
    Common challenges in implementing RAG systems include:
    - Ensuring retrieval quality and relevance
    - Managing computational efficiency
    - Balancing between retrieved information and model knowledge
    - Handling contradictory information
    - Addressing potential biases in the knowledge base
    """
    
    chunks = processor.process_document(sample_text, {"source": "sample_script", "filetype": "python"})
    
    print(f"Generated {len(chunks)} chunks from the sample text")
    print(f"Processing stats: {processor.get_processing_stats()}")