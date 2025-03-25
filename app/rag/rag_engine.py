import logging
import time
import asyncio
import httpx
import uuid
import gc
import random
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.core.config import DEFAULT_MODEL, USE_RETRIEVAL_JUDGE
from app.models.chat import Citation, Message
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.rag.agents.retrieval_judge import RetrievalJudge
from app.rag.mem0_client import get_mem0_client, store_message, get_conversation_history, store_document_interaction, get_user_preferences
from app.utils.text_processor import normalize_text, format_code_blocks
from app.cache.cache_manager import CacheManager
from app.rag.system_prompts import (
    CODE_GENERATION_SYSTEM_PROMPT,
    PYTHON_CODE_GENERATION_PROMPT,
    JAVASCRIPT_CODE_GENERATION_PROMPT
)

logger = logging.getLogger("app.rag.rag_engine")

class RAGEngine:
    """
    RAG (Retrieval Augmented Generation) Engine
    """
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        ollama_client: Optional[OllamaClient] = None,
        retrieval_judge: Optional[RetrievalJudge] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        self.vector_store = vector_store or VectorStore()
        self.ollama_client = ollama_client or OllamaClient()
        self.retrieval_judge = retrieval_judge if retrieval_judge is not None else (
            RetrievalJudge(ollama_client=self.ollama_client) if USE_RETRIEVAL_JUDGE else None
        )
        
        # Initialize Mem0 client
        self.mem0_client = get_mem0_client()
        
        # Initialize cache manager
        self.cache_manager = cache_manager or CacheManager()
        
        if self.retrieval_judge:
            logger.info("Retrieval Judge is enabled")
        else:
            logger.info("Retrieval Judge is disabled")
            
        if self.mem0_client:
            logger.info("Mem0 integration is enabled")
        else:
            logger.info("Mem0 integration is disabled")
            
        # Log cache status
        cache_stats = self.cache_manager.get_all_cache_stats()
        if cache_stats.get("caching_enabled", False):
            logger.info("Caching is enabled")
        else:
            logger.info("Caching is disabled")
    
    async def query(
        self,
        query: str,
        model: str = DEFAULT_MODEL,
        use_rag: bool = True,
        top_k: int = 10,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        model_parameters: Dict[str, Any] = None,
        conversation_history: Optional[List[Message]] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG engine with optional conversation history and metadata filtering
        """
        start_time = time.time()
        document_ids = []
        
        try:
            logger.info(f"RAG query: {query[:50]}...")
            
            # Get context from vector store if RAG is enabled
            context = ""
            sources = []
            
            # Generate a user_id if not provided
            if not user_id:
                user_id = f"session_{str(uuid.uuid4())[:8]}"
                logger.info(f"Generated session user_id: {user_id}")
            
            # Integrate with Mem0 if available
            if self.mem0_client and user_id:
                # Store the user query in Mem0
                await store_message(user_id, "user", query)
                
                # Get user preferences if available
                user_prefs = await get_user_preferences(user_id)
                if user_prefs:
                    logger.info(f"Retrieved user preferences: {user_prefs}")
                    # Apply user preferences if available
                    if "preferred_model" in user_prefs and user_prefs["preferred_model"]:
                        model = user_prefs["preferred_model"]
                        logger.info(f"Using preferred model from user preferences: {model}")
            
            # Format conversation history if provided
            conversation_context = ""
            if conversation_history and len(conversation_history) > 1:  # Only include history if there's more than just the current message
                # Get the last few messages (up to 5) to keep context manageable, but exclude the most recent user message
                # which is the current query and shouldn't be treated as history
                recent_history = conversation_history[:-1]
                if len(recent_history) > 5:
                    recent_history = recent_history[-5:]
                
                # Format the conversation history
                history_pieces = []
                for msg in recent_history:
                    role_prefix = "User" if msg.role == "user" else "Assistant"
                    history_pieces.append(f"{role_prefix}: {msg.content}")
                
                conversation_context = "\n".join(history_pieces)
                logger.info(f"Including conversation history with {len(recent_history)} messages")
            elif self.mem0_client and user_id:
                # Try to get conversation history from Mem0 if not provided
                mem0_history = await get_conversation_history(user_id, limit=5)
                if mem0_history:
                    # Format the conversation history from Mem0
                    history_pieces = []
                    for msg in mem0_history:
                        role_prefix = "User" if msg["role"] == "user" else "Assistant"
                        history_pieces.append(f"{role_prefix}: {msg['content']}")
                    
                    conversation_context = "\n".join(history_pieces)
                    logger.info(f"Including conversation history from Mem0 with {len(mem0_history)} messages")
                else:
                    logger.info("No previous conversation history found in Mem0")
            else:
                logger.info("No previous conversation history to include")
            
            if use_rag:
                # Use enhanced retrieval if Retrieval Judge is enabled
                if self.retrieval_judge:
                    logger.info("Using enhanced retrieval with Retrieval Judge")
                    context, sources, document_ids = await self._enhanced_retrieval(
                        query=query,
                        conversation_context=conversation_context,
                        top_k=top_k,
                        metadata_filters=metadata_filters,
                        user_id=user_id
                    )
                else:
                    # Use standard retrieval
                    logger.info("Using standard retrieval (Retrieval Judge disabled)")
                    # Check if there are any documents in the vector store
                    stats = self.vector_store.get_stats()
                    if stats["count"] == 0:
                        logger.warning("RAG is enabled but no documents are available in the vector store")
                        # Add a note to the context that no documents are available
                        context = "Note: No documents are available for retrieval. Please upload documents to use RAG effectively."
                    else:
                        # Combine the current query with conversation context for better retrieval
                        search_query = query
                        if conversation_context:
                            # For retrieval, we focus more on the current query but include
                            # some context from the conversation to improve relevance
                            search_query = f"{query} {conversation_context[-200:]}"
                        
                        # Log the search query
                        logger.info(f"Searching with query: {search_query[:100]}...")
                        
                        # Use a higher fixed value for top_k to get more potential matches, then filter by relevance
                        search_results = await self.vector_store.search(
                            query=search_query,
                            top_k=15,  # Fixed value to retrieve more chunks (document has 24 chunks total)
                            filter_criteria=metadata_filters
                        )
                        
                        if search_results:
                            # Log the number of results
                            logger.info(f"Retrieved {len(search_results)} chunks from vector store")
                            
                            # Format context with source information
                            context_pieces = []
                            relevant_results = []
                            
                            # Set a relevance threshold - only include chunks with relevance score above this
                            relevance_threshold = 0.4  # Lower threshold to ensure we include more relevant chunks
                            
                            for i, result in enumerate(search_results):
                                # Skip results with None content
                                if "content" not in result or result["content"] is None:
                                    logger.warning(f"Skipping result {i+1} due to missing or None content")
                                    continue
                                    
                                # Extract metadata for better context
                                metadata = result["metadata"]
                                filename = metadata.get("filename", "Unknown")
                                tags = metadata.get("tags", [])
                                folder = metadata.get("folder", "/")
                                
                                # Calculate relevance score (lower distance = higher relevance)
                                relevance_score = 1.0 - (result["distance"] if result["distance"] is not None else 0)
                                
                                # Log the relevance score for debugging
                                logger.debug(f"Chunk {i+1} relevance score: {relevance_score:.4f}")
                                
                                # Only include chunks that are sufficiently relevant
                                if relevance_score >= relevance_threshold:
                                    # Format the context piece with metadata
                                    context_piece = f"[{len(relevant_results)+1}] Source: {filename}, Tags: {tags}, Folder: {folder}\n\n{result['content']}"
                                    context_pieces.append(context_piece)
                                    
                                    # Track the source for citation
                                    doc_id = metadata["document_id"]
                                    document_ids.append(doc_id)
                                    
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
                                            human_id=user_id,
                                            document_id=doc_id,
                                            interaction_type="retrieval",
                                            data={
                                                "query": query,
                                                "chunk_id": result["chunk_id"],
                                                "relevance_score": relevance_score,
                                                "filename": filename
                                            }
                                        )
                                    
                                    relevant_results.append(result)
                                else:
                                    logger.info(f"Skipping chunk {i+1} with low relevance score: {relevance_score:.4f}")
                            
                            # Join all context pieces
                            context = "\n\n".join(context_pieces)
                            
                            # Log how many chunks were filtered out due to low relevance
                            logger.info(f"Using {len(relevant_results)} of {len(search_results)} chunks after relevance filtering")
                            
                            # Log the total context length
                            logger.info(f"Total context length: {len(context)} characters")
                            
                            # Check if we have enough relevant context
                            if len(relevant_results) == 0:
                                logger.warning("No sufficiently relevant documents found for the query")
                                context = "Note: No sufficiently relevant documents found in the knowledge base for your query. The system cannot provide a specific answer based on the available documents."
                            elif len(context.strip()) < 50:  # Very short context might not be useful
                                logger.warning("Context is too short to be useful")
                                context = "Note: The retrieved context is too limited to provide a comprehensive answer to your query. The system cannot provide a specific answer based on the available documents."
                        else:
                            logger.warning("No relevant documents found for the query")
                            context = "Note: No relevant documents found in the knowledge base for your query. The system cannot provide a specific answer based on the available documents."
            
            # Create full prompt with context and conversation history
            full_prompt = query
            
            # If we have conversation history, include it
            if conversation_context:
                full_prompt = f"""Previous conversation:
{conversation_context}

User's new question: {query}"""
            else:
                # No conversation history, just use the query directly
                full_prompt = f"""User Question: {query}"""
            
            # If we have context from RAG, include it
            if context:
                # Construct the prompt differently based on whether we have conversation history
                if conversation_context:
                    full_prompt = f"""Context:
{context}

Previous conversation:
{conversation_context}

User's new question: {query}

IMPORTANT INSTRUCTIONS:
1. ONLY use information that is explicitly stated in the provided context above.
2. When using information from the context, ALWAYS reference your sources with the number in square brackets, like [1] or [2].
3. If the context contains the answer, provide it clearly and concisely.
4. If the context doesn't contain the answer, explicitly state: "Based on the provided documents, I don't have information about [topic]."
5. NEVER make up or hallucinate information that is not in the context.
6. If you're unsure about something, be honest about your uncertainty.
7. Organize your answer in a clear, structured way.
8. If you need to use your general knowledge because the context is insufficient, clearly indicate this by stating: "However, generally speaking..."
"""
                else:
                    full_prompt = f"""Context:
{context}

User Question: {query}

IMPORTANT INSTRUCTIONS:
1. ONLY use information that is explicitly stated in the provided context above.
2. When using information from the context, ALWAYS reference your sources with the number in square brackets, like [1] or [2].
3. If the context contains the answer, provide it clearly and concisely.
4. If the context doesn't contain the answer, explicitly state: "Based on the provided documents, I don't have information about [topic]."
5. NEVER make up or hallucinate information that is not in the context.
6. If you're unsure about something, be honest about your uncertainty.
7. Organize your answer in a clear, structured way.
8. This is a new conversation with no previous history - treat it as such.
9. If you need to use your general knowledge because the context is insufficient, clearly indicate this by stating: "However, generally speaking..."
"""
            
            # Create system prompt if not provided
            if not system_prompt:
                # Check if this is a code-related query
                is_code_query = self._is_code_related_query(query)
                
                if is_code_query:
                    logger.info("Detected code-related query, using code generation system prompt")
                    system_prompt = CODE_GENERATION_SYSTEM_PROMPT
                    
                    # Add language-specific guidelines if detected
                    if re.search(r'\bpython\b', query.lower()):
                        system_prompt += "\n\n" + PYTHON_CODE_GENERATION_PROMPT
                    elif re.search(r'\bjavascript\b|\bjs\b', query.lower()):
                        system_prompt += "\n\n" + JAVASCRIPT_CODE_GENERATION_PROMPT
                else:
                    system_prompt = """You are a helpful assistant that provides accurate, factual responses based on the Metis RAG system.

ROLE AND CAPABILITIES:
- You have access to a Retrieval-Augmented Generation (RAG) system that can retrieve relevant documents to answer questions.
- Your primary function is to use the retrieved context to provide accurate, well-informed answers.
- You can cite sources using the numbers in square brackets like [1] or [2] when they are provided in the context.

STRICT GUIDELINES FOR USING CONTEXT:
- ONLY use information that is explicitly stated in the provided context.
- NEVER make up or hallucinate information that is not in the context.
- If the context doesn't contain the answer, explicitly state that the information is not available in the provided documents.
- Do not use your general knowledge unless the context is insufficient, and clearly indicate when you're doing so.
- Analyze the context carefully to find the most relevant information for the user's question.
- If multiple sources provide different information, synthesize them and explain any discrepancies.
- If the context includes metadata like filenames, tags, or folders, use this to understand the source and relevance of the information.

WHEN CONTEXT IS INSUFFICIENT:
- Clearly state: "Based on the provided documents, I don't have information about [topic]."
- Be specific about what information is missing.
- Only then provide a general response based on your knowledge, and clearly state: "However, generally speaking..." to distinguish this from information in the context.
- Never pretend to have information that isn't in the context.

CONVERSATION HANDLING:
- IMPORTANT: Only refer to previous conversations if they are explicitly provided in the conversation history.
- NEVER fabricate or hallucinate previous exchanges that weren't actually provided.
- If no conversation history is provided, treat the query as a new, standalone question.
- Only maintain continuity with previous exchanges when conversation history is explicitly provided.

RESPONSE STYLE:
- Be clear, direct, and helpful.
- Structure your responses logically.
- Use appropriate formatting to enhance readability.
- Maintain a consistent, professional tone throughout the conversation.
- For new conversations with no history, start fresh without referring to non-existent previous exchanges.
- DO NOT start your responses with phrases like "I've retrieved relevant context" or similar preambles.
- Answer questions directly without mentioning the retrieval process.
- Always cite your sources with numbers in square brackets [1] when using information from the context.
"""
            # Log the prompt and system prompt for debugging
            logger.debug(f"System prompt: {system_prompt[:200]}...")
            logger.debug(f"Full prompt: {full_prompt[:200]}...")
            
            # Generate response
            if stream:
                # For streaming, just return the stream response
                logger.info(f"Generating streaming response with model: {model}")
                
                # Create a wrapper for the stream that applies text normalization
                original_stream = await self.ollama_client.generate(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    stream=True,
                    parameters=model_parameters or {}
                )
                
                # Create a normalized stream wrapper
                async def normalized_stream():
                    buffer = ""
                    async for chunk in original_stream:
                        # Handle string chunks (from OllamaClient)
                        if isinstance(chunk, str):
                            buffer += chunk
                            # Apply normalization to the buffer periodically
                            # Only normalize when we have complete sentences or paragraphs
                            if any(buffer.endswith(c) for c in ['.', '!', '?', '\n']):
                                normalized_chunk = normalize_text(buffer)
                                buffer = ""
                                yield normalized_chunk
                            else:
                                yield chunk
                        # Handle dictionary chunks (for backward compatibility)
                        elif isinstance(chunk, dict) and "response" in chunk:
                            buffer += chunk["response"]
                            # Apply normalization to the buffer periodically
                            # Only normalize when we have complete sentences or paragraphs
                            if any(buffer.endswith(c) for c in ['.', '!', '?', '\n']):
                                normalized_chunk = normalize_text(buffer)
                                buffer = ""
                                yield normalized_chunk
                            else:
                                yield chunk["response"]
                        else:
                            yield chunk
                    
                    # Process any remaining text in the buffer
                    if buffer:
                        normalized_chunk = normalize_text(buffer)
                        yield normalized_chunk
                
                stream_response = normalized_stream()
                
                # Record analytics asynchronously
                response_time_ms = (time.time() - start_time) * 1000
                logger.info(f"Response time: {response_time_ms:.2f}ms")
                
                # Use await instead of async for with the coroutine
                await self._record_analytics(
                    query=query,
                    model=model,
                    use_rag=use_rag,
                    response_time_ms=response_time_ms,
                    document_ids=document_ids,
                    token_count=len(query.split())  # Approximate token count
                )
                
                return {
                    "query": query,
                    "stream": stream_response,
                    "sources": [Citation(**source) for source in sources] if sources else []
                }
            else:
                # For non-streaming, check cache first
                logger.info(f"Generating non-streaming response with model: {model}")
                
                # Create cache parameters
                temperature = model_parameters.get("temperature", 0.0) if model_parameters else 0.0
                max_tokens = model_parameters.get("max_tokens") if model_parameters else None
                
                # Check if response is in cache
                cached_response = self.cache_manager.llm_response_cache.get_response(
                    prompt=full_prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    additional_params={"system_prompt": system_prompt} if system_prompt else None
                )
                
                if cached_response:
                    logger.info("Using cached response")
                    response = cached_response
                    # Calculate response time (cache hit is very fast)
                    response_time_ms = (time.time() - start_time) * 1000
                    logger.info(f"Cache hit! Response time: {response_time_ms:.2f}ms")
                else:
                    # Generate new response
                    logger.info("Cache miss, generating new response")
                    response = await self.ollama_client.generate(
                        prompt=full_prompt,
                        model=model,
                        system_prompt=system_prompt,
                        stream=False,
                        parameters=model_parameters or {}
                    )
                    
                    # Calculate response time
                    response_time_ms = (time.time() - start_time) * 1000
                    logger.info(f"Response time: {response_time_ms:.2f}ms")
                    
                    # Cache the response if appropriate
                    if "error" not in response and self.cache_manager.llm_response_cache.should_cache_response(
                        prompt=full_prompt,
                        model=model,
                        temperature=temperature,
                        response=response
                    ):
                        self.cache_manager.llm_response_cache.set_response(
                            prompt=full_prompt,
                            model=model,
                            response=response,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            additional_params={"system_prompt": system_prompt} if system_prompt else None
                        )
                        logger.info("Response cached for future use")
                
                # Check if there was an error in the response
                if "error" in response:
                    error_message = response.get("error", "Unknown error")
                    logger.warning(f"Model returned an error: {error_message}")
                    response_text = response.get("response", f"Error: {error_message}")
                else:
                    # Get response text
                    response_text = response.get("response", "")
                    
                    # Apply text normalization to improve formatting
                    response_text = normalize_text(response_text)
                    response_text = format_code_blocks(response_text)
                
                logger.info(f"Response length: {len(response_text)} characters")
                
                # Log a preview of the response
                if response_text:
                    logger.debug(f"Response preview: {response_text[:100]}...")
                
                # Store assistant response in Mem0 if available
                if self.mem0_client and user_id:
                    await store_message(user_id, "assistant", response_text)
                    logger.info(f"Stored assistant response in Mem0 for user {user_id}")
                
                # Record analytics asynchronously
                await self._record_analytics(
                    query=query,
                    model=model,
                    use_rag=use_rag,
                    response_time_ms=response_time_ms,
                    document_ids=document_ids,
                    token_count=len(query.split()) + len(response_text.split())  # Approximate token count
                )
                
                return {
                    "query": query,
                    "answer": response_text,
                    "sources": [Citation(**source) for source in sources] if sources else []
                }
        except Exception as e:
            logger.error(f"Error querying RAG engine: {str(e)}")
            raise
    
    async def _enhanced_retrieval(
        self,
        query: str,
        conversation_context: str = "",
        top_k: int = 10,
        metadata_filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]], List[str]]:
        """
        Enhanced retrieval using the Retrieval Judge
        
        Args:
            query: The user query
            conversation_context: Optional conversation history context
            top_k: Number of chunks to retrieve
            metadata_filters: Optional filters for retrieval
            
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
                return "Note: No documents are available for retrieval. Please upload documents to use RAG effectively.", [], []
            
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
                filter_criteria=metadata_filters
            )
            
            if not search_results:
                logger.warning("No relevant documents found for the query")
                return "Note: No relevant documents found in the knowledge base for your query. The system cannot provide a specific answer based on the available documents.", [], []
            
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
                    filter_criteria=metadata_filters
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
            
            # Step 6: Optimize context assembly if we have enough chunks
            if len(relevant_results) > 3 and apply_reranking:
                logger.info("Optimizing context assembly with Retrieval Judge")
                optimized_results = await self.retrieval_judge.optimize_context(query, relevant_results)
                if optimized_results:
                    relevant_results = optimized_results
            
            # Step 7: Format context with source information
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
                        human_id=user_id,
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
                context = "Note: No sufficiently relevant documents found in the knowledge base for your query. The system cannot provide a specific answer based on the available documents."
            elif len(context.strip()) < 50:  # Very short context might not be useful
                logger.warning("Context is too short to be useful")
                context = "Note: The retrieved context is too limited to provide a comprehensive answer to your query. The system cannot provide a specific answer based on the available documents."
            
            return context, sources, document_ids
            
        except Exception as e:
            logger.error(f"Error in enhanced retrieval: {str(e)}")
            # Return empty context in case of error
            return "Note: An error occurred during retrieval. The system cannot provide a specific answer based on the available documents.", [], []
    
    def _is_code_related_query(self, query: str) -> bool:
        """
        Determine if a query is related to code or programming.
        
        Args:
            query: The user query
            
        Returns:
            True if the query is code-related, False otherwise
        """
        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower()
        
        # Check for code-related keywords
        code_keywords = [
            'code', 'program', 'function', 'class', 'method', 'variable',
            'algorithm', 'implement', 'python', 'javascript', 'java', 'c++', 'c#',
            'typescript', 'html', 'css', 'php', 'ruby', 'go', 'rust', 'swift',
            'kotlin', 'scala', 'perl', 'r', 'bash', 'shell', 'sql', 'database',
            'api', 'framework', 'library', 'package', 'module', 'import',
            'function', 'def ', 'return', 'for loop', 'while loop', 'if statement',
            'create a', 'write a', 'develop a', 'build a', 'implement a',
            'tic tac toe', 'tic-tac-toe', 'game', 'application', 'app',
            'script', 'syntax', 'error', 'debug', 'fix', 'optimize'
        ]
        
        # Check if any code keyword is in the query
        for keyword in code_keywords:
            if keyword in query_lower:
                return True
        
        # Check for code patterns
        code_patterns = [
            r'```[\s\S]*```',  # Code blocks
            r'def\s+\w+\s*\(',  # Python function definition
            r'function\s+\w+\s*\(',  # JavaScript function definition
            r'class\s+\w+',  # Class definition
            r'import\s+\w+',  # Import statement
            r'from\s+\w+\s+import',  # Python import
            r'<\w+>.*</\w+>',  # HTML tags
            r'\w+\s*=\s*function\(',  # JavaScript function assignment
            r'const\s+\w+\s*=',  # JavaScript const declaration
            r'let\s+\w+\s*=',  # JavaScript let declaration
            r'var\s+\w+\s*=',  # JavaScript var declaration
            r'public\s+\w+\s+\w+\(',  # Java method
            r'SELECT\s+.*\s+FROM',  # SQL query
            r'CREATE\s+TABLE',  # SQL create table
            r'@app\.route',  # Flask route
            r'npm\s+install',  # npm command
            r'pip\s+install',  # pip command
            r'git\s+\w+'  # git command
        ]
        
        # Check if any code pattern is in the query
        for pattern in code_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    async def optimize_memory(self) -> Dict[str, Any]:
        """
        Optimize memory usage by clearing unnecessary resources.
        This method should be called periodically to prevent memory leaks.
        
        Returns:
            Dictionary with memory optimization statistics
        """
        try:
            # Force garbage collection
            gc.collect()
            
            # Get cache statistics before optimization
            cache_stats_before = self.cache_manager.get_all_cache_stats()
            
            # Perform a second garbage collection pass for better results
            gc.collect()
            
            # Get cache statistics after optimization
            cache_stats_after = self.cache_manager.get_all_cache_stats()
            
            # Log memory optimization
            logger.info("Memory optimization performed")
            
            # Return memory usage statistics
            return {
                "cache_stats_before": cache_stats_before,
                "cache_stats_after": cache_stats_after
            }
        except Exception as e:
            logger.error(f"Error during memory optimization: {str(e)}")
            return {"error": str(e)}
    
    async def _record_analytics(
        self,
        query: str,
        model: str,
        use_rag: bool,
        response_time_ms: float,
        document_ids: List[str],
        token_count: int
    ) -> None:
        """
        Record query analytics asynchronously
        """
        try:
            # Prepare analytics data
            analytics_data = {
                "query": query,
                "model": model,
                "use_rag": use_rag,
                "timestamp": datetime.now().isoformat(),
                "response_time_ms": response_time_ms,
                "document_ids": document_ids,
                "token_count": token_count
            }
            
            # Send analytics data to the API
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8000/api/analytics/record_query",
                    json=analytics_data,
                    timeout=5.0
                )
            
            logger.debug(f"Recorded analytics for query: {query[:30]}...")
            
            # Periodically optimize memory after processing queries
            # This helps prevent memory leaks over time
            if random.random() < 0.1:  # 10% chance to optimize after each query
                await self.optimize_memory()
                
        except Exception as e:
            # Don't let analytics errors affect the main functionality
            logger.error(f"Error recording analytics: {str(e)}")