"""
RAG retrieval functionality
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from app.rag.rag_engine_base import BaseRAGEngine
from app.rag.mem0_client import store_document_interaction

logger = logging.getLogger("app.rag.rag_retrieval")

class RetrievalMixin:
    """
    Mixin class for RAG retrieval functionality
    """
    
    async def retrieve(self, 
                      query: str,
                      top_k: int = 5,
                      filters: Optional[Dict[str, Any]] = None,
                      user_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query with permission filtering
        
        Args:
            query: Query string
            top_k: Number of results to return
            filters: Additional filters to apply
            user_id: User ID for permission filtering (overrides the instance's user_id)
            
        Returns:
            List of relevant documents
        """
        try:
            # Use provided user_id or fall back to the instance's user_id
            effective_user_id = user_id or self.user_id
            
            # Log the retrieval request
            logger.info(f"Retrieving documents for query: {query[:50]}...")
            
            # Search for relevant documents with permission filtering
            search_results = await self.vector_store.search(
                query=query,
                top_k=top_k,
                filter_criteria=filters,
                user_id=effective_user_id
            )
            
            # Log the number of results
            logger.info(f"Retrieved {len(search_results)} documents")
            
            return search_results
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    async def _enhanced_retrieval(self,
                                 query: str,
                                 conversation_context: str = "",
                                 top_k: int = 10,
                                 metadata_filters: Optional[Dict[str, Any]] = None,
                                 user_id: Optional[UUID] = None) -> Tuple[str, List[Dict[str, Any]], List[str]]:
        """
        Enhanced retrieval using the Retrieval Judge with permission filtering
        
        Args:
            query: The user query
            conversation_context: Optional conversation history context
            top_k: Number of chunks to retrieve
            metadata_filters: Optional filters for retrieval
            user_id: User ID for permission filtering
            
        Returns:
            Tuple of (context, sources, document_ids)
        """
        document_ids = []
        sources = []
        context = ""
        
        try:
            # Check if there are any documents in the vector store
            stats = self.vector_store.get_stats()
            if stats["count"] == 0:
                logger.warning("RAG is enabled but no documents are available in the vector store")
                return "", [], []
            
            # Step 1: Analyze the query using the Retrieval Judge
            logger.info("Analyzing query with Retrieval Judge")
            query_analysis = await self.retrieval_judge.analyze_query(query)
            
            # Extract recommended parameters
            recommended_k = query_analysis.get("parameters", {}).get("k", top_k)
            relevance_threshold = query_analysis.get("parameters", {}).get("threshold", 0.4)
            apply_reranking = query_analysis.get("parameters", {}).get("reranking", True)
            
            logger.info(f"Query complexity: {query_analysis.get('complexity', 'unknown')}")
            logger.info(f"Recommended parameters: k={recommended_k}, threshold={relevance_threshold}, reranking={apply_reranking}")
            
            # Combine the current query with conversation context for better retrieval
            search_query = query
            if conversation_context:
                # For retrieval, we focus more on the current query but include
                # some context from the conversation to improve relevance
                search_query = f"{query} {conversation_context[-200:]}"
            
            # Log the search query
            logger.info(f"Searching with query: {search_query[:100]}...")
            
            # Step 2: Initial retrieval with recommended parameters
            search_results = await self.vector_store.search(
                query=search_query,
                top_k=max(15, recommended_k + 5),  # Get a few extra for filtering
                filter_criteria=metadata_filters,
                user_id=user_id  # Pass user_id for permission filtering
            )
            
            if not search_results:
                logger.warning("No relevant documents found for the query")
                return "", [], []
            
            # Log the number of results
            logger.info(f"Retrieved {len(search_results)} chunks from vector store")
            
            # Step 3: Evaluate chunks with the Retrieval Judge
            logger.info("Evaluating chunks with Retrieval Judge")
            evaluation = await self.retrieval_judge.evaluate_chunks(query, search_results)
            
            # Extract relevance scores and refinement decision
            relevance_scores = evaluation.get("relevance_scores", {})
            needs_refinement = evaluation.get("needs_refinement", False)
            
            logger.info(f"Chunk evaluation complete, needs_refinement={needs_refinement}")
            
            # Step 4: Refine query if needed and perform additional retrieval
            if needs_refinement:
                logger.info("Refining query based on initial retrieval")
                refined_query = await self.retrieval_judge.refine_query(query, search_results)
                
                logger.info(f"Refined query: {refined_query}")
                
                # Perform additional retrieval with refined query
                additional_results = await self.vector_store.search(
                    query=refined_query,
                    top_k=recommended_k,
                    filter_criteria=metadata_filters,
                    user_id=user_id  # Pass user_id for permission filtering
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
                    evaluation = await self.retrieval_judge.evaluate_chunks(refined_query, search_results)
                    relevance_scores = evaluation.get("relevance_scores", {})
            
            # Step 5: Filter and re-rank chunks based on relevance scores
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
            
            # Step 6: Format context with source information
            context_pieces = []
            
            for i, result in enumerate(relevant_results):
                # Extract metadata for better context
                metadata = result["metadata"]
                filename = metadata.get("filename", "Unknown")
                tags = metadata.get("tags", [])
                folder = metadata.get("folder", "/")
                
                # Format the context piece with metadata
                context_piece = f"[{i+1}] Source: {filename}, Tags: {tags}, Folder: {folder}\n\n{result['content']}"
                context_pieces.append(context_piece)
                
                # Track the source for citation
                doc_id = metadata["document_id"]
                document_ids.append(doc_id)
                
                # Get relevance score (either from judge or distance)
                relevance_score = result.get("relevance_score", 1.0 - (result["distance"] if result["distance"] is not None else 0))
                
                source_info = {
                    "document_id": doc_id,
                    "chunk_id": result["chunk_id"],
                    "relevance_score": relevance_score,
                    "excerpt": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                    "filename": filename,
                    "tags": tags,
                    "folder": folder
                }
                
                sources.append(source_info)
                
                # Store document interaction in Mem0 if available
                if self.mem0_client and user_id:
                    await store_document_interaction(
                        human_id=str(user_id),
                        document_id=doc_id,
                        interaction_type="retrieval",
                        data={
                            "query": query,
                            "chunk_id": result["chunk_id"],
                            "relevance_score": relevance_score,
                            "filename": filename
                        }
                    )
            
            # Join all context pieces
            context = "\n\n".join(context_pieces)
            
            # Log how many chunks were used
            logger.info(f"Using {len(relevant_results)} chunks after Retrieval Judge optimization")
            
            # Log the total context length
            logger.info(f"Total context length: {len(context)} characters")
            
            # Check if we have enough relevant context
            if len(relevant_results) == 0:
                logger.warning("No sufficiently relevant documents found for the query")
                context = ""
            elif len(context.strip()) < 50:  # Very short context might not be useful
                logger.warning("Context is too short to be useful")
                context = ""
            
            return context, sources, document_ids
            
        except Exception as e:
            logger.error(f"Error in enhanced retrieval: {str(e)}")
            # Return empty context in case of error
            return "", [], []