"""
Retrieval Component for RAG Engine

This module provides the RetrievalComponent class for handling
document retrieval in the RAG Engine.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from uuid import UUID

from app.rag.engine.utils.relevance import rank_documents, calculate_relevance_score
from app.rag.engine.utils.error_handler import RetrievalError, safe_execute_async
from app.rag.engine.utils.timing import async_timing_context, TimingStats

logger = logging.getLogger("app.rag.engine.components.retrieval")

class RetrievalComponent:
    """
    Component for handling document retrieval in the RAG Engine
    
    This component is responsible for retrieving relevant documents from
    the vector store based on a query, with optional filtering and
    permission checking.
    """
    
    def __init__(self, vector_store=None, retrieval_judge=None):
        """
        Initialize the retrieval component
        
        Args:
            vector_store: Vector store instance
            retrieval_judge: Retrieval judge instance for enhanced retrieval
        """
        self.vector_store = vector_store
        self.retrieval_judge = retrieval_judge
        self.timing_stats = TimingStats()
    
    async def retrieve(self,
                      query: str,
                      top_k: int = 5,
                      metadata_filters: Optional[Dict[str, Any]] = None,
                      user_id: Optional[UUID] = None,
                      min_relevance_score: float = 0.4) -> Tuple[List[Dict[str, Any]], str]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Query string
            top_k: Number of results to return
            metadata_filters: Metadata filters to apply
            user_id: User ID for permission filtering
            min_relevance_score: Minimum relevance score for documents
            
        Returns:
            Tuple of (documents, retrieval_state)
        """
        self.timing_stats.start("total")
        
        try:
            # Check if vector store is available
            if not self.vector_store:
                logger.error("Vector store not available")
                return [], "no_documents"
            
            # Check if there are any documents in the vector store
            async with async_timing_context("get_stats", self.timing_stats):
                stats = self.vector_store.get_stats()
            
            if stats["count"] == 0:
                logger.warning("No documents available in the vector store")
                return [], "no_documents"
            
            # Retrieve documents
            documents = []
            retrieval_state = "success"
            
            # Use enhanced retrieval if retrieval judge is available
            if self.retrieval_judge:
                documents, retrieval_state = await self._enhanced_retrieval(
                    query=query,
                    top_k=top_k,
                    metadata_filters=metadata_filters,
                    user_id=user_id,
                    min_relevance_score=min_relevance_score
                )
            else:
                documents, retrieval_state = await self._standard_retrieval(
                    query=query,
                    top_k=top_k,
                    metadata_filters=metadata_filters,
                    user_id=user_id,
                    min_relevance_score=min_relevance_score
                )
            
            # Log retrieval stats
            self.timing_stats.stop("total")
            logger.info(f"Retrieved {len(documents)} documents in {self.timing_stats.get_timing('total'):.2f}s")
            self.timing_stats.log_summary()
            
            return documents, retrieval_state
        
        except Exception as e:
            self.timing_stats.stop("total")
            logger.error(f"Error retrieving documents: {str(e)}")
            raise RetrievalError(f"Error retrieving documents: {str(e)}")
    
    async def _standard_retrieval(self,
                                 query: str,
                                 top_k: int = 5,
                                 metadata_filters: Optional[Dict[str, Any]] = None,
                                 user_id: Optional[UUID] = None,
                                 min_relevance_score: float = 0.4) -> Tuple[List[Dict[str, Any]], str]:
        """
        Perform standard retrieval without the retrieval judge
        
        Args:
            query: Query string
            top_k: Number of results to return
            metadata_filters: Metadata filters to apply
            user_id: User ID for permission filtering
            min_relevance_score: Minimum relevance score for documents
            
        Returns:
            Tuple of (documents, retrieval_state)
        """
        # Search for documents
        async with async_timing_context("vector_search", self.timing_stats):
            search_results = await self.vector_store.search(
                query=query,
                top_k=top_k + 5,  # Get a few extra for filtering
                filter_criteria=metadata_filters,
                user_id=user_id
            )
        
        if not search_results:
            logger.warning("No documents found for query")
            return [], "no_documents"
        
        # Rank documents by relevance
        async with async_timing_context("rank_documents", self.timing_stats):
            ranked_documents = rank_documents(
                query=query,
                documents=search_results,
                min_score=min_relevance_score
            )
        
        # Determine retrieval state
        retrieval_state = "success"
        if not ranked_documents:
            retrieval_state = "no_documents"
        elif len(ranked_documents) < min(3, top_k // 2):
            retrieval_state = "low_relevance"
        
        # Limit to top_k
        documents = ranked_documents[:top_k]
        
        # Format documents for return
        formatted_documents = []
        for doc in documents:
            formatted_doc = self._format_document(doc)
            formatted_documents.append(formatted_doc)
        
        return formatted_documents, retrieval_state
    
    async def _enhanced_retrieval(self,
                                 query: str,
                                 top_k: int = 5,
                                 metadata_filters: Optional[Dict[str, Any]] = None,
                                 user_id: Optional[UUID] = None,
                                 min_relevance_score: float = 0.4) -> Tuple[List[Dict[str, Any]], str]:
        """
        Perform enhanced retrieval using the retrieval judge
        
        Args:
            query: Query string
            top_k: Number of results to return
            metadata_filters: Metadata filters to apply
            user_id: User ID for permission filtering
            min_relevance_score: Minimum relevance score for documents
            
        Returns:
            Tuple of (documents, retrieval_state)
        """
        # Analyze query with retrieval judge
        async with async_timing_context("analyze_query", self.timing_stats):
            query_analysis = await self.retrieval_judge.analyze_query(query)
        
        # Extract recommended parameters
        recommended_k = query_analysis.get("parameters", {}).get("k", top_k)
        relevance_threshold = query_analysis.get("parameters", {}).get("threshold", min_relevance_score)
        apply_reranking = query_analysis.get("parameters", {}).get("reranking", True)
        
        logger.info(f"Query complexity: {query_analysis.get('complexity', 'unknown')}")
        logger.info(f"Recommended parameters: k={recommended_k}, threshold={relevance_threshold}, reranking={apply_reranking}")
        
        # Search for documents
        async with async_timing_context("vector_search", self.timing_stats):
            search_results = await self.vector_store.search(
                query=query,
                top_k=max(15, recommended_k + 5),  # Get a few extra for filtering
                filter_criteria=metadata_filters,
                user_id=user_id
            )
        
        if not search_results:
            logger.warning("No documents found for query")
            return [], "no_documents"
        
        # Evaluate chunks with retrieval judge
        async with async_timing_context("evaluate_chunks", self.timing_stats):
            evaluation = await self.retrieval_judge.evaluate_chunks(query, search_results)
        
        # Extract relevance scores and refinement decision
        relevance_scores = evaluation.get("relevance_scores", {})
        needs_refinement = evaluation.get("needs_refinement", False)
        
        # Refine query if needed
        if needs_refinement:
            logger.info("Refining query based on initial retrieval")
            
            async with async_timing_context("refine_query", self.timing_stats):
                refined_query = await self.retrieval_judge.refine_query(query, search_results)
            
            logger.info(f"Refined query: {refined_query}")
            
            # Perform additional retrieval with refined query
            async with async_timing_context("refined_search", self.timing_stats):
                additional_results = await self.vector_store.search(
                    query=refined_query,
                    top_k=recommended_k,
                    filter_criteria=metadata_filters,
                    user_id=user_id
                )
            
            if additional_results:
                logger.info(f"Retrieved {len(additional_results)} additional chunks with refined query")
                
                # Combine results, avoiding duplicates
                existing_chunk_ids = {result["chunk_id"] for result in search_results}
                for result in additional_results:
                    if result["chunk_id"] not in existing_chunk_ids:
                        search_results.append(result)
                
                # Re-evaluate all chunks
                logger.info("Re-evaluating all chunks after query refinement")
                async with async_timing_context("reevaluate_chunks", self.timing_stats):
                    evaluation = await self.retrieval_judge.evaluate_chunks(refined_query, search_results)
                
                relevance_scores = evaluation.get("relevance_scores", {})
        
        # Filter and re-rank chunks based on relevance scores
        async with async_timing_context("filter_and_rank", self.timing_stats):
            relevant_results = []
            
            for result in search_results:
                # Skip results with None content
                if "content" not in result or result["content"] is None:
                    continue
                
                chunk_id = result["chunk_id"]
                
                # Get relevance score from evaluation or calculate from distance
                if chunk_id in relevance_scores:
                    relevance_score = relevance_scores[chunk_id]
                else:
                    # Calculate relevance score (lower distance = higher relevance)
                    relevance_score = 1.0 - (result["distance"] if result["distance"] is not None else 0)
                
                # Only include chunks that are sufficiently relevant
                if relevance_score >= relevance_threshold:
                    # Add relevance score to result for sorting
                    result["relevance_score"] = relevance_score
                    relevant_results.append(result)
            
            # Sort by relevance score if reranking is enabled
            if apply_reranking:
                relevant_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Determine retrieval state
        retrieval_state = "success"
        if not relevant_results:
            retrieval_state = "no_documents"
        elif len(relevant_results) < min(3, top_k // 2):
            retrieval_state = "low_relevance"
        
        # Limit to top_k
        documents = relevant_results[:top_k]
        
        # Format documents for return
        formatted_documents = []
        for doc in documents:
            formatted_doc = self._format_document(doc)
            formatted_documents.append(formatted_doc)
        
        return formatted_documents, retrieval_state
    
    def _format_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a document for return
        
        Args:
            document: Document to format
            
        Returns:
            Formatted document
        """
        # Extract metadata
        metadata = document.get("metadata", {})
        
        # Create formatted document
        formatted_doc = {
            "document_id": metadata.get("document_id", ""),
            "chunk_id": document.get("chunk_id", ""),
            "content": document.get("content", ""),
            "relevance_score": document.get("relevance_score", 0.0),
            "metadata": {
                "filename": metadata.get("filename", "Unknown"),
                "title": metadata.get("title", metadata.get("filename", "Unknown")),
                "source": metadata.get("source", ""),
                "author": metadata.get("author", ""),
                "date": metadata.get("date", ""),
                "page": metadata.get("page", ""),
                "tags": metadata.get("tags", []),
                "folder": metadata.get("folder", "/")
            }
        }
        
        # Create excerpt
        content = document.get("content", "")
        excerpt = content[:200] + "..." if len(content) > 200 else content
        formatted_doc["excerpt"] = excerpt
        
        return formatted_doc
    
    async def get_document_by_id(self, 
                                document_id: str, 
                                user_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID
        
        Args:
            document_id: Document ID
            user_id: User ID for permission checking
            
        Returns:
            Document or None if not found
        """
        try:
            # Get document from vector store
            document = await safe_execute_async(
                self.vector_store.get_document,
                document_id=document_id,
                user_id=user_id
            )
            
            if not document:
                logger.warning(f"Document not found: {document_id}")
                return None
            
            # Format document
            formatted_doc = self._format_document(document)
            
            return formatted_doc
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None