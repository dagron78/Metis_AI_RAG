"""
LangGraph RAG Agent - Orchestrates the RAG process using a state machine
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Sequence, cast, Tuple
from enum import Enum

from langchain.schema import Document as LangchainDocument
from langgraph.graph import StateGraph, END
# langgraph 0.0.20 doesn't have ToolNode in prebuilt or MemorySaver

from app.models.document import Document, Chunk
from app.rag.ollama_client import OllamaClient
from app.rag.vector_store import VectorStore
from app.rag.agents.chunking_judge import ChunkingJudge
from app.rag.agents.retrieval_judge import RetrievalJudge
from app.rag.chunkers.semantic_chunker import SemanticChunker
from app.core.config import CHUNKING_JUDGE_MODEL, RETRIEVAL_JUDGE_MODEL, DEFAULT_MODEL

logger = logging.getLogger("app.rag.agents.langgraph_rag_agent")

# Define state types for the LangGraph state machine
class QueryAnalysisState(TypedDict):
    """State for query analysis"""
    query: str
    conversation_context: Optional[str]
    complexity: Optional[str]
    parameters: Optional[Dict[str, Any]]
    justification: Optional[str]

class RetrievalState(TypedDict):
    """State for retrieval"""
    query: str
    refined_query: Optional[str]
    conversation_context: Optional[str]
    parameters: Dict[str, Any]
    chunks: List[Dict[str, Any]]
    needs_refinement: bool
    relevance_scores: Optional[Dict[str, float]]

class GenerationState(TypedDict):
    """State for generation"""
    query: str
    conversation_context: Optional[str]
    context: str
    sources: List[Dict[str, Any]]
    document_ids: List[str]
    answer: Optional[str]

class RAGState(TypedDict):
    """Combined state for the RAG process"""
    query: str
    conversation_context: Optional[str]
    metadata_filters: Optional[Dict[str, Any]]
    model: str
    system_prompt: Optional[str]
    stream: bool
    model_parameters: Optional[Dict[str, Any]]
    query_analysis: Optional[QueryAnalysisState]
    retrieval: Optional[RetrievalState]
    generation: Optional[GenerationState]
    final_response: Optional[Dict[str, Any]]

class RAGStage(str, Enum):
    """Stages in the RAG process"""
    QUERY_ANALYSIS = "analyze_query_node"
    RETRIEVAL = "retrieve_chunks_node"
    QUERY_REFINEMENT = "refine_query_node"
    CONTEXT_OPTIMIZATION = "optimize_context_node"
    GENERATION = "generate_response_node"
    COMPLETE = "finalize_response_node"

class LangGraphRAGAgent:
    """
    LangGraph-based agent that orchestrates the RAG process using a state machine
    
    This agent integrates:
    - Chunking Judge for document analysis and chunking strategy selection
    - Semantic Chunker for intelligent text splitting
    - Retrieval Judge for query refinement and context optimization
    
    The state machine follows these stages:
    1. Query Analysis: Analyze the query to determine complexity and retrieval parameters
    2. Retrieval: Retrieve relevant chunks from the vector store
    3. Query Refinement: Refine the query if needed based on initial retrieval
    4. Context Optimization: Optimize the context assembly for generation
    5. Generation: Generate the final response using the optimized context
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        ollama_client: Optional[OllamaClient] = None,
        chunking_judge: Optional[ChunkingJudge] = None,
        retrieval_judge: Optional[RetrievalJudge] = None,
        semantic_chunker: Optional[SemanticChunker] = None
    ):
        """
        Initialize the LangGraphRAGAgent
        
        Args:
            vector_store: Vector store for retrieval
            ollama_client: Client for LLM interactions
            chunking_judge: Judge for document analysis and chunking strategy selection
            retrieval_judge: Judge for query refinement and context optimization
            semantic_chunker: Chunker for intelligent text splitting
        """
        self.vector_store = vector_store or VectorStore()
        self.ollama_client = ollama_client or OllamaClient()
        self.chunking_judge = chunking_judge or ChunkingJudge(ollama_client=self.ollama_client)
        self.retrieval_judge = retrieval_judge or RetrievalJudge(ollama_client=self.ollama_client)
        self.semantic_chunker = semantic_chunker or SemanticChunker(ollama_client=self.ollama_client)
        
        # Initialize and compile the state graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        
        logger.info("LangGraphRAGAgent initialized with state machine")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the state graph for the RAG process
        
        Returns:
            StateGraph: The state graph for the RAG process
        """
        # Create the state graph
        graph = StateGraph(RAGState)
        
        # Add nodes for each stage
        graph.add_node(RAGStage.QUERY_ANALYSIS, self._analyze_query)
        graph.add_node(RAGStage.RETRIEVAL, self._retrieve_chunks)
        graph.add_node(RAGStage.QUERY_REFINEMENT, self._refine_query)
        graph.add_node(RAGStage.CONTEXT_OPTIMIZATION, self._optimize_context)
        graph.add_node(RAGStage.GENERATION, self._generate_response)
        graph.add_node(RAGStage.COMPLETE, self._finalize_response)
        
        # Define the edges between nodes
        # Start with query analysis
        graph.add_edge(RAGStage.QUERY_ANALYSIS, RAGStage.RETRIEVAL)
        
        # After retrieval, decide whether to refine the query or optimize the context
        graph.add_conditional_edges(
            RAGStage.RETRIEVAL,
            self._needs_refinement,
            {
                True: RAGStage.QUERY_REFINEMENT,
                False: RAGStage.CONTEXT_OPTIMIZATION
            }
        )
        
        # After query refinement, go back to retrieval with the refined query
        graph.add_edge(RAGStage.QUERY_REFINEMENT, RAGStage.RETRIEVAL)
        
        # After context optimization, proceed to generation
        graph.add_edge(RAGStage.CONTEXT_OPTIMIZATION, RAGStage.GENERATION)
        
        # After generation, complete the process
        graph.add_edge(RAGStage.GENERATION, RAGStage.COMPLETE)
        
        # After completion, end the process
        graph.add_edge(RAGStage.COMPLETE, END)
        
        # Set the entry point
        graph.set_entry_point(RAGStage.QUERY_ANALYSIS)
        
        return graph
    
    async def query(
        self,
        query: str,
        model: str = DEFAULT_MODEL,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        model_parameters: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG agent with the state machine
        
        Args:
            query: The user query
            model: The model to use for generation
            system_prompt: Optional system prompt for generation
            stream: Whether to stream the response
            model_parameters: Optional parameters for the model
            conversation_context: Optional conversation context
            metadata_filters: Optional filters for retrieval
            
        Returns:
            Dict with keys:
            - query: The original query
            - answer: The generated answer (if not streaming)
            - stream: The response stream (if streaming)
            - sources: List of sources used in the response
        """
        # Initialize the state
        initial_state: RAGState = {
            "query": query,
            "conversation_context": conversation_context,
            "metadata_filters": metadata_filters,
            "model": model,
            "system_prompt": system_prompt,
            "stream": stream,
            "model_parameters": model_parameters or {},
            "query_analysis": None,
            "retrieval": None,
            "generation": None,
            "final_response": None
        }
        
        logger.info(f"Starting RAG query with LangGraph: {query[:50]}...")
        # Run the state machine
        # In langgraph 0.0.20, we need to use the compiled app with ainvoke
        result = await self.app.ainvoke(initial_state)
        
        # Return the final response
        return result["final_response"]
    
    async def _analyze_query(self, state: RAGState) -> RAGState:
        """
        Analyze the query to determine complexity and retrieval parameters
        
        Args:
            state: The current state
            
        Returns:
            Updated state with query analysis
        """
        logger.info(f"Analyzing query: {state['query'][:50]}...")
        
        # Use the retrieval judge to analyze the query
        query_analysis = await self.retrieval_judge.analyze_query(state["query"])
        
        # Update the state with the query analysis
        state["query_analysis"] = {
            "query": state["query"],
            "conversation_context": state["conversation_context"],
            "complexity": query_analysis.get("complexity"),
            "parameters": query_analysis.get("parameters"),
            "justification": query_analysis.get("justification")
        }
        
        logger.info(f"Query complexity: {query_analysis.get('complexity', 'unknown')}")
        
        return state
    
    async def _retrieve_chunks(self, state: RAGState) -> RAGState:
        """
        Retrieve relevant chunks from the vector store
        
        Args:
            state: The current state
            
        Returns:
            Updated state with retrieved chunks
        """
        # Get query and parameters from the state
        query = state["query"]
        query_analysis = state["query_analysis"]
        retrieval_state = state.get("retrieval", None)
        
        # If we have a refined query from a previous iteration, use it
        if retrieval_state and retrieval_state.get("refined_query"):
            query = retrieval_state["refined_query"]
            logger.info(f"Using refined query: {query[:50]}...")
        
        # Get recommended parameters from query analysis
        parameters = query_analysis["parameters"] if query_analysis else {}
        recommended_k = parameters.get("k", 10)
        
        # Combine the query with conversation context if available
        search_query = query
        if state["conversation_context"]:
            search_query = f"{query} {state['conversation_context'][-200:]}"
        
        logger.info(f"Retrieving chunks for query: {search_query[:50]}...")
        
        # Retrieve chunks from the vector store
        search_results = await self.vector_store.search(
            query=search_query,
            top_k=max(15, recommended_k + 5),  # Get a few extra for filtering
            filter_criteria=state["metadata_filters"]
        )
        
        logger.info(f"Retrieved {len(search_results)} chunks from vector store")
        
        # Evaluate chunks with the retrieval judge
        evaluation = await self.retrieval_judge.evaluate_chunks(query, search_results)
        
        # Extract relevance scores and refinement decision
        relevance_scores = evaluation.get("relevance_scores", {})
        needs_refinement = evaluation.get("needs_refinement", False)
        
        logger.info(f"Chunk evaluation complete, needs_refinement={needs_refinement}")
        
        # Update the state with retrieval results
        state["retrieval"] = {
            "query": query,
            "refined_query": retrieval_state["refined_query"] if retrieval_state else None,
            "conversation_context": state["conversation_context"],
            "parameters": parameters,
            "chunks": search_results,
            "needs_refinement": needs_refinement,
            "relevance_scores": relevance_scores
        }
        
        return state
    
    def _needs_refinement(self, state: RAGState) -> bool:
        """
        Determine if query refinement is needed based on retrieval results
        
        Args:
            state: The current state
            
        Returns:
            True if refinement is needed, False otherwise
        """
        retrieval = state["retrieval"]
        
        # If we've already refined the query once, don't refine again
        if retrieval and retrieval.get("refined_query"):
            logger.info("Query already refined, skipping further refinement")
            return False
        
        # Otherwise, use the needs_refinement flag from the retrieval judge
        needs_refinement = retrieval["needs_refinement"] if retrieval else False
        logger.info(f"Query refinement needed: {needs_refinement}")
        
        return needs_refinement
    
    async def _refine_query(self, state: RAGState) -> RAGState:
        """
        Refine the query based on initial retrieval results
        
        Args:
            state: The current state
            
        Returns:
            Updated state with refined query
        """
        retrieval = state["retrieval"]
        
        logger.info(f"Refining query: {retrieval['query'][:50]}...")
        
        # Refine the query using the retrieval judge
        refined_query = await self.retrieval_judge.refine_query(
            retrieval["query"], 
            retrieval["chunks"]
        )
        
        logger.info(f"Refined query: {refined_query[:50]}...")
        
        # Update the state with the refined query
        retrieval["refined_query"] = refined_query
        state["retrieval"] = retrieval
        
        return state
    
    async def _optimize_context(self, state: RAGState) -> RAGState:
        """
        Optimize the context assembly for generation
        
        Args:
            state: The current state
            
        Returns:
            Updated state with optimized context
        """
        retrieval = state["retrieval"]
        query = retrieval["refined_query"] or retrieval["query"]
        chunks = retrieval["chunks"]
        relevance_scores = retrieval["relevance_scores"] or {}
        parameters = retrieval["parameters"]
        
        logger.info(f"Optimizing context for query: {query[:50]}...")
        
        # Filter chunks based on relevance scores
        relevance_threshold = parameters.get("threshold", 0.4)
        apply_reranking = parameters.get("reranking", True)
        
        relevant_results = []
        for result in chunks:
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
        
        logger.info(f"Found {len(relevant_results)} relevant chunks after filtering")
        
        # Optimize context assembly if we have enough chunks
        if len(relevant_results) > 3 and apply_reranking:
            logger.info("Optimizing context assembly with Retrieval Judge")
            optimized_results = await self.retrieval_judge.optimize_context(query, relevant_results)
            if optimized_results:
                relevant_results = optimized_results
                logger.info(f"Context optimized to {len(relevant_results)} chunks")
        
        # Format context with source information
        context_pieces = []
        sources = []
        document_ids = []
        
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
        
        # Check if we have enough relevant context
        if len(relevant_results) == 0:
            logger.warning("No sufficiently relevant documents found for the query")
            context = "Note: No sufficiently relevant documents found in the knowledge base for your query. The system cannot provide a specific answer based on the available documents."
        elif len(context.strip()) < 50:  # Very short context might not be useful
            logger.warning("Context is too short to be useful")
            context = "Note: The retrieved context is too limited to provide a comprehensive answer to your query. The system cannot provide a specific answer based on the available documents."
        
        # Update the state with generation information
        state["generation"] = {
            "query": query,
            "conversation_context": state["conversation_context"],
            "context": context,
            "sources": sources,
            "document_ids": document_ids,
            "answer": None
        }
        
        return state
    
    async def _generate_response(self, state: RAGState) -> RAGState:
        """
        Generate the final response using the optimized context
        
        Args:
            state: The current state
            
        Returns:
            Updated state with generated response
        """
        generation = state["generation"]
        query = generation["query"]
        context = generation["context"]
        conversation_context = generation["conversation_context"]
        
        logger.info(f"Generating response for query: {query[:50]}...")
        
        # Create full prompt with context and conversation history
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
        system_prompt = state["system_prompt"]
        if not system_prompt:
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
        
        # Generate response
        if state["stream"]:
            # For streaming, just return the stream response
            logger.info(f"Generating streaming response with model: {state['model']}")
            stream_response = await self.ollama_client.generate(
                prompt=full_prompt,
                model=state["model"],
                system_prompt=system_prompt,
                stream=True,
                parameters=state["model_parameters"] or {}
            )
            
            # Update the state with the stream response
            generation["stream_response"] = stream_response
        else:
            # For non-streaming, get the complete response
            logger.info(f"Generating non-streaming response with model: {state['model']}")
            response = await self.ollama_client.generate(
                prompt=full_prompt,
                model=state["model"],
                system_prompt=system_prompt,
                stream=False,
                parameters=state["model_parameters"] or {}
            )
            
            # Check if there was an error in the response
            if "error" in response:
                error_message = response.get("error", "Unknown error")
                logger.warning(f"Model returned an error: {error_message}")
                response_text = f"Error: {error_message}"
            else:
                # Get response text
                response_text = response.get("response", "")
            
            logger.info(f"Response length: {len(response_text)} characters")
            
            # Update the state with the generated answer
            generation["answer"] = response_text
        
        # Update the state with the generation information
        state["generation"] = generation
        
        return state
    
    async def _finalize_response(self, state: RAGState) -> RAGState:
        """
        Finalize the response for return to the user
        
        Args:
            state: The current state
            
        Returns:
            Updated state with final response
        """
        generation = state["generation"]
        
        # Create the final response
        if state["stream"]:
            final_response = {
                "query": state["query"],
                "stream": generation.get("stream_response"),
                "sources": generation["sources"]
            }
        else:
            final_response = {
                "query": state["query"],
                "answer": generation["answer"],
                "sources": generation["sources"]
            }
        
        # Update the state with the final response
        state["final_response"] = final_response
        
        logger.info("RAG process complete")
        
        return state