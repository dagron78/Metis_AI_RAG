"""
Relevance Utility for RAG Engine

This module provides utilities for calculating and evaluating relevance
scores in the RAG Engine.
"""
import logging
import math
from typing import Dict, Any, Optional, List, Tuple, Union
import re

logger = logging.getLogger("app.rag.engine.utils.relevance")

def calculate_relevance_score(query: str, 
                             document: str, 
                             distance: Optional[float] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> float:
    """
    Calculate a relevance score between a query and a document
    
    Args:
        query: The user query
        document: The document text
        distance: Optional vector distance (if available)
        metadata: Optional document metadata
        
    Returns:
        Relevance score between 0 and 1
    """
    # If distance is provided, convert it to a relevance score
    # (lower distance = higher relevance)
    if distance is not None:
        # Ensure distance is between 0 and 1
        if distance < 0:
            distance = 0
        elif distance > 1:
            distance = 1
        
        # Convert distance to relevance score
        vector_score = 1.0 - distance
    else:
        # Default vector score if distance not provided
        vector_score = 0.5
    
    # Calculate text-based relevance using TF-IDF approach
    text_score = _calculate_text_relevance(query, document)
    
    # Calculate metadata relevance if metadata is provided
    metadata_score = _calculate_metadata_relevance(query, metadata) if metadata else 0.5
    
    # Combine scores with weights
    # Vector score is most important, followed by text score, then metadata
    combined_score = (vector_score * 0.6) + (text_score * 0.3) + (metadata_score * 0.1)
    
    # Ensure score is between 0 and 1
    combined_score = max(0.0, min(1.0, combined_score))
    
    logger.debug(f"Relevance scores - Vector: {vector_score:.4f}, Text: {text_score:.4f}, Metadata: {metadata_score:.4f}, Combined: {combined_score:.4f}")
    
    return combined_score

def _calculate_text_relevance(query: str, document: str) -> float:
    """
    Calculate text-based relevance using TF-IDF approach
    
    Args:
        query: The user query
        document: The document text
        
    Returns:
        Relevance score between 0 and 1
    """
    # Normalize text
    query = query.lower()
    document = document.lower()
    
    # Tokenize
    query_tokens = _tokenize(query)
    document_tokens = _tokenize(document)
    
    if not query_tokens or not document_tokens:
        return 0.0
    
    # Calculate term frequencies
    query_tf = _calculate_term_frequency(query_tokens)
    document_tf = _calculate_term_frequency(document_tokens)
    
    # Calculate cosine similarity
    similarity = _calculate_cosine_similarity(query_tf, document_tf)
    
    # Check for exact phrase matches (boost score for exact matches)
    exact_match_boost = _calculate_exact_match_boost(query, document)
    
    # Combine similarity with exact match boost
    score = similarity + exact_match_boost
    
    # Ensure score is between 0 and 1
    score = max(0.0, min(1.0, score))
    
    return score

def _tokenize(text: str) -> List[str]:
    """
    Tokenize text into words
    
    Args:
        text: Text to tokenize
        
    Returns:
        List of tokens
    """
    # Remove punctuation and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Remove stopwords
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than', 'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during', 'to'}
    tokens = [word for word in words if word not in stopwords and len(word) > 1]
    
    return tokens

def _calculate_term_frequency(tokens: List[str]) -> Dict[str, float]:
    """
    Calculate term frequency
    
    Args:
        tokens: List of tokens
        
    Returns:
        Dictionary of term frequencies
    """
    # Count occurrences of each token
    token_counts = {}
    for token in tokens:
        token_counts[token] = token_counts.get(token, 0) + 1
    
    # Calculate term frequency
    total_tokens = len(tokens)
    term_frequency = {token: count / total_tokens for token, count in token_counts.items()}
    
    return term_frequency

def _calculate_cosine_similarity(tf1: Dict[str, float], tf2: Dict[str, float]) -> float:
    """
    Calculate cosine similarity between two term frequency dictionaries
    
    Args:
        tf1: First term frequency dictionary
        tf2: Second term frequency dictionary
        
    Returns:
        Cosine similarity between 0 and 1
    """
    # Find common terms
    common_terms = set(tf1.keys()) & set(tf2.keys())
    
    if not common_terms:
        return 0.0
    
    # Calculate dot product
    dot_product = sum(tf1[term] * tf2[term] for term in common_terms)
    
    # Calculate magnitudes
    magnitude1 = math.sqrt(sum(tf**2 for tf in tf1.values()))
    magnitude2 = math.sqrt(sum(tf**2 for tf in tf2.values()))
    
    # Calculate cosine similarity
    if magnitude1 * magnitude2 == 0:
        return 0.0
    
    similarity = dot_product / (magnitude1 * magnitude2)
    
    return similarity

def _calculate_exact_match_boost(query: str, document: str) -> float:
    """
    Calculate boost for exact phrase matches
    
    Args:
        query: The user query
        document: The document text
        
    Returns:
        Boost value between 0 and 0.5
    """
    # Extract phrases from query (2+ words)
    query_phrases = re.findall(r'\b\w+\s+\w+(?:\s+\w+)*\b', query.lower())
    
    if not query_phrases:
        return 0.0
    
    # Check for exact matches
    match_count = 0
    for phrase in query_phrases:
        if phrase in document.lower():
            match_count += 1
    
    # Calculate boost based on proportion of matching phrases
    if match_count == 0:
        return 0.0
    
    boost = (match_count / len(query_phrases)) * 0.5
    
    return boost

def _calculate_metadata_relevance(query: str, metadata: Optional[Dict[str, Any]]) -> float:
    """
    Calculate relevance based on document metadata
    
    Args:
        query: The user query
        metadata: Document metadata
        
    Returns:
        Relevance score between 0 and 1
    """
    if not metadata:
        return 0.5
    
    # Initialize score
    score = 0.5
    
    # Normalize query
    query = query.lower()
    
    # Check filename match
    if 'filename' in metadata:
        filename = str(metadata['filename']).lower()
        if any(term in filename for term in query.split()):
            score += 0.1
    
    # Check title match
    if 'title' in metadata:
        title = str(metadata['title']).lower()
        if any(term in title for term in query.split()):
            score += 0.15
    
    # Check tag match
    if 'tags' in metadata and isinstance(metadata['tags'], list):
        tags = [str(tag).lower() for tag in metadata['tags']]
        if any(term in tag for term in query.split() for tag in tags):
            score += 0.1
    
    # Check author match
    if 'author' in metadata:
        author = str(metadata['author']).lower()
        if any(term in author for term in query.split()):
            score += 0.05
    
    # Check date recency if available
    if 'date' in metadata:
        try:
            # Assuming date is in ISO format
            from datetime import datetime
            doc_date = datetime.fromisoformat(str(metadata['date']).replace('Z', '+00:00'))
            now = datetime.now()
            
            # Calculate days since document was created
            days_old = (now - doc_date).days
            
            # Boost score for recent documents
            if days_old < 30:  # Less than a month old
                score += 0.1
            elif days_old < 90:  # Less than 3 months old
                score += 0.05
        except (ValueError, TypeError):
            # If date parsing fails, ignore
            pass
    
    # Ensure score is between 0 and 1
    score = max(0.0, min(1.0, score))
    
    return score

def rank_documents(query: str, 
                  documents: List[Dict[str, Any]], 
                  min_score: float = 0.4) -> List[Dict[str, Any]]:
    """
    Rank documents by relevance to a query
    
    Args:
        query: The user query
        documents: List of documents with content and metadata
        min_score: Minimum relevance score to include
        
    Returns:
        List of documents sorted by relevance
    """
    # Calculate relevance scores
    scored_documents = []
    
    for doc in documents:
        # Get document content and distance
        content = doc.get('content', '')
        distance = doc.get('distance')
        metadata = doc.get('metadata', {})
        
        # Calculate relevance score
        score = calculate_relevance_score(query, content, distance, metadata)
        
        # Add score to document
        doc_with_score = doc.copy()
        doc_with_score['relevance_score'] = score
        
        # Add to list if score is above threshold
        if score >= min_score:
            scored_documents.append(doc_with_score)
    
    # Sort by relevance score (descending)
    ranked_documents = sorted(scored_documents, key=lambda x: x['relevance_score'], reverse=True)
    
    logger.info(f"Ranked {len(ranked_documents)} documents out of {len(documents)} (min score: {min_score})")
    
    return ranked_documents

def evaluate_retrieval_quality(query: str, 
                              retrieved_documents: List[Dict[str, Any]], 
                              relevant_document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Evaluate the quality of retrieved documents
    
    Args:
        query: The user query
        retrieved_documents: List of retrieved documents
        relevant_document_ids: Optional list of known relevant document IDs
        
    Returns:
        Dictionary with evaluation metrics
    """
    # Initialize metrics
    metrics = {
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0,
        "mean_relevance_score": 0.0,
        "relevant_count": 0,
        "retrieved_count": len(retrieved_documents)
    }
    
    # If no documents retrieved, return zeros
    if not retrieved_documents:
        return metrics
    
    # Calculate mean relevance score
    relevance_scores = [doc.get('relevance_score', 0.0) for doc in retrieved_documents]
    metrics["mean_relevance_score"] = sum(relevance_scores) / len(relevance_scores)
    
    # If we have known relevant document IDs, calculate precision and recall
    if relevant_document_ids:
        # Get IDs of retrieved documents
        retrieved_ids = [doc.get('document_id') for doc in retrieved_documents]
        
        # Count relevant documents that were retrieved
        relevant_retrieved = set(retrieved_ids) & set(relevant_document_ids)
        relevant_count = len(relevant_retrieved)
        
        # Calculate precision and recall
        if retrieved_ids:
            metrics["precision"] = relevant_count / len(retrieved_ids)
        
        if relevant_document_ids:
            metrics["recall"] = relevant_count / len(relevant_document_ids)
        
        # Calculate F1 score
        if metrics["precision"] + metrics["recall"] > 0:
            metrics["f1_score"] = 2 * (metrics["precision"] * metrics["recall"]) / (metrics["precision"] + metrics["recall"])
        
        metrics["relevant_count"] = relevant_count
    
    return metrics