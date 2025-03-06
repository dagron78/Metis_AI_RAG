import logging
import time
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.core.config import DEFAULT_MODEL
from app.models.chat import Citation, Message
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient

logger = logging.getLogger("app.rag.rag_engine")

class RAGEngine:
    """
    RAG (Retrieval Augmented Generation) Engine
    """
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        ollama_client: Optional[OllamaClient] = None
    ):
        self.vector_store = vector_store or VectorStore()
        self.ollama_client = ollama_client or OllamaClient()
    
    async def query(
        self,
        query: str,
        model: str = DEFAULT_MODEL,
        use_rag: bool = True,
        top_k: int = 5,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        model_parameters: Dict[str, Any] = None,
        conversation_history: Optional[List[Message]] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
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
            
            # Format conversation history if provided
            conversation_context = ""
            if conversation_history and len(conversation_history) > 0:
                # Get the last few messages (up to 5) to keep context manageable
                recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
                
                # Format the conversation history
                history_pieces = []
                for msg in recent_history:
                    role_prefix = "User" if msg.role == "user" else "Assistant"
                    history_pieces.append(f"{role_prefix}: {msg.content}")
                
                conversation_context = "\n".join(history_pieces)
                logger.info(f"Including conversation history with {len(recent_history)} messages")
            
            if use_rag:
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
                    
                    search_results = await self.vector_store.search(
                        query=search_query,
                        top_k=top_k,
                        filter_criteria=metadata_filters
                    )
                    
                    if search_results:
                        # Format context with source information
                        context_pieces = []
                        for i, result in enumerate(search_results):
                            context_piece = f"[{i+1}] {result['content']}"
                            context_pieces.append(context_piece)
                            
                            # Track the source for citation
                            doc_id = result["metadata"]["document_id"]
                            document_ids.append(doc_id)
                            
                            sources.append({
                                "document_id": doc_id,
                                "chunk_id": result["chunk_id"],
                                "relevance_score": 1.0 - (result["distance"] if result["distance"] is not None else 0),
                                "excerpt": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                            })
                        
                        # Join all context pieces
                        context = "\n\n".join(context_pieces)
                    else:
                        logger.warning("No relevant documents found for the query")
                        context = "Note: No relevant documents found for your query. The response will be based on the model's general knowledge."
            
            # Create full prompt with context and conversation history
            full_prompt = query
            
            # If we have conversation history, include it
            if conversation_context:
                full_prompt = f"""Previous conversation:
{conversation_context}

User's new question: {query}"""
            
            # If we have context from RAG, include it
            if context:
                full_prompt = f"""I'll provide you with some relevant context to help answer the user's question.

Context:
{context}

{"Previous conversation:" if conversation_context else ""}
{conversation_context if conversation_context else ""}

{"User's new question" if conversation_context else "User Question"}: {query}

Use the provided context to answer the question. If the context doesn't contain enough information, say so, but try to provide a helpful response based on what you know. When using information from the context, reference your sources with the number in square brackets, like [1] or [2].
"""
            
            # Create system prompt if not provided
            if not system_prompt:
                system_prompt = """You are a helpful assistant that provides accurate, factual responses.

When provided with context from documents, use it to give specific, well-informed answers. Only cite sources using the numbers in square brackets like [1] or [2] if they were provided in the context.

When provided with conversation history, maintain continuity with previous exchanges and refer back to earlier parts of the conversation when relevant.

If you don't have enough information from the context or conversation history, acknowledge that and provide more general guidance based on what you know.

Your responses should be clear, direct, and helpful. Maintain a consistent tone throughout the conversation.
"""
            
            # Generate response
            if stream:
                # For streaming, just return the stream response
                stream_response = await self.ollama_client.generate(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    stream=True,
                    parameters=model_parameters or {}
                )
                
                # Record analytics asynchronously
                response_time_ms = (time.time() - start_time) * 1000
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
                    "sources": [Citation(**source) for source in sources] if sources else None
                }
            else:
                # For non-streaming, get the complete response
                response = await self.ollama_client.generate(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    stream=False,
                    parameters=model_parameters or {}
                )
                
                # Calculate response time
                response_time_ms = (time.time() - start_time) * 1000
                
                # Get response text
                response_text = response.get("response", "")
                
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
                    "sources": [Citation(**source) for source in sources] if sources else None
                }
        except Exception as e:
            logger.error(f"Error querying RAG engine: {str(e)}")
            raise
    
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
        except Exception as e:
            # Don't let analytics errors affect the main functionality
            logger.error(f"Error recording analytics: {str(e)}")