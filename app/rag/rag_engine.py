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
                    
                    # Log the search query
                    logger.info(f"Searching with query: {search_query[:100]}...")
                    
                    search_results = await self.vector_store.search(
                        query=search_query,
                        top_k=top_k,
                        filter_criteria=metadata_filters
                    )
                    
                    if search_results:
                        # Log the number of results
                        logger.info(f"Retrieved {len(search_results)} chunks from vector store")
                        
                        # Format context with source information
                        context_pieces = []
                        for i, result in enumerate(search_results):
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
                            
                            # Calculate relevance score (lower distance = higher relevance)
                            relevance_score = 1.0 - (result["distance"] if result["distance"] is not None else 0)
                            
                            # Log the relevance score for debugging
                            logger.debug(f"Chunk {i+1} relevance score: {relevance_score:.4f}")
                            
                            sources.append({
                                "document_id": doc_id,
                                "chunk_id": result["chunk_id"],
                                "relevance_score": relevance_score,
                                "excerpt": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                                "filename": filename,
                                "tags": tags,
                                "folder": folder
                            })
                        
                        # Join all context pieces
                        context = "\n\n".join(context_pieces)
                        
                        # Log the total context length
                        logger.info(f"Total context length: {len(context)} characters")
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

IMPORTANT INSTRUCTIONS:
1. Base your answer primarily on the information in the provided context.
2. When using information from the context, ALWAYS reference your sources with the number in square brackets, like [1] or [2].
3. If the context contains the answer, provide it clearly and concisely.
4. If the context doesn't contain enough information, explicitly state what's missing and then try to provide a helpful response based on what you know.
5. Do not make up information that isn't in the context or your general knowledge.
6. If you're unsure about something, be honest about your uncertainty.
7. Organize your answer in a clear, structured way.
"""
            
            # Create system prompt if not provided
            if not system_prompt:
                system_prompt = """You are a helpful assistant that provides accurate, factual responses based on the Metis RAG system.

ROLE AND CAPABILITIES:
- You have access to a Retrieval-Augmented Generation (RAG) system that can retrieve relevant documents to answer questions.
- Your primary function is to use the retrieved context to provide accurate, well-informed answers.
- You can cite sources using the numbers in square brackets like [1] or [2] when they are provided in the context.

GUIDELINES FOR USING CONTEXT:
- Always prioritize information from the retrieved context over your general knowledge.
- Analyze the context carefully to find the most relevant information for the user's question.
- If multiple sources provide different information, synthesize them and explain any discrepancies.
- If the context includes metadata like filenames, tags, or folders, use this to understand the source and relevance of the information.

WHEN CONTEXT IS INSUFFICIENT:
- Clearly state when the retrieved context doesn't contain enough information to fully answer the question.
- Be specific about what information is missing.
- Then provide a more general response based on your knowledge, but clearly distinguish this from information in the context.

CONVERSATION HANDLING:
- Maintain continuity with previous exchanges when conversation history is provided.
- Refer back to earlier parts of the conversation when relevant.

RESPONSE STYLE:
- Be clear, direct, and helpful.
- Structure your responses logically.
- Use appropriate formatting to enhance readability.
- Maintain a consistent, professional tone throughout the conversation.
"""
            # Log the prompt and system prompt for debugging
            logger.debug(f"System prompt: {system_prompt[:200]}...")
            logger.debug(f"Full prompt: {full_prompt[:200]}...")
            
            # Generate response
            if stream:
                # For streaming, just return the stream response
                logger.info(f"Generating streaming response with model: {model}")
                stream_response = await self.ollama_client.generate(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    stream=True,
                    parameters=model_parameters or {}
                )
                
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
                    "sources": [Citation(**source) for source in sources] if sources else None
                }
            else:
                # For non-streaming, get the complete response
                logger.info(f"Generating non-streaming response with model: {model}")
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
                
                # Check if there was an error in the response
                if "error" in response:
                    error_message = response.get("error", "Unknown error")
                    logger.warning(f"Model returned an error: {error_message}")
                    response_text = response.get("response", f"Error: {error_message}")
                else:
                    # Get response text
                    response_text = response.get("response", "")
                
                logger.info(f"Response length: {len(response_text)} characters")
                
                # Log a preview of the response
                if response_text:
                    logger.debug(f"Response preview: {response_text[:100]}...")
                
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