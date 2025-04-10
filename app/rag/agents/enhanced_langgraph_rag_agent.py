"""
Enhanced LangGraph RAG Agent - Orchestrates the RAG process using a state machine with planning and execution
"""
import logging
import json
import uuid
import time
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Sequence, cast, Tuple
from datetime import datetime

from langgraph.graph import StateGraph, END

from app.models.document import Document, Chunk
from app.rag.ollama_client import OllamaClient
from app.rag.vector_store import VectorStore
from app.rag.agents.chunking_judge import ChunkingJudge
from app.rag.agents.retrieval_judge import RetrievalJudge
from app.rag.chunkers.semantic_chunker import SemanticChunker
from app.rag.query_planner import QueryPlanner
from app.rag.plan_executor import PlanExecutor
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.tools import ToolRegistry
from app.rag.process_logger import ProcessLogger
from app.rag.langgraph_states import (
    QueryAnalysisState, PlanningState, ExecutionState, RetrievalState, 
    GenerationState, RAGState, RAGStage
)
from app.core.config import CHUNKING_JUDGE_MODEL, RETRIEVAL_JUDGE_MODEL, DEFAULT_MODEL

logger = logging.getLogger("app.rag.agents.enhanced_langgraph_rag_agent")

class EnhancedLangGraphRAGAgent:
    """
    Enhanced LangGraph-based agent that orchestrates the RAG process using a state machine
    with planning and execution capabilities
    
    This agent integrates:
    - QueryAnalyzer for analyzing query complexity and requirements
    - QueryPlanner for creating execution plans
    - PlanExecutor for executing multi-step plans
    - Retrieval Judge for query refinement and context optimization
    - Semantic Chunker for intelligent text splitting
    
    The state machine follows these stages:
    1. Query Analysis: Analyze the query to determine complexity and retrieval parameters
    2. Query Planning: Create a plan for complex queries that may require multiple tools
    3. Plan Execution: Execute the plan, which may involve multiple tools and steps
    4. Retrieval: Retrieve relevant chunks from the vector store
    5. Query Refinement: Refine the query if needed based on initial retrieval
    6. Context Optimization: Optimize the context assembly for generation
    7. Generation: Generate the final response using the optimized context
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        ollama_client: Optional[OllamaClient] = None,
        chunking_judge: Optional[ChunkingJudge] = None,
        retrieval_judge: Optional[RetrievalJudge] = None,
        semantic_chunker: Optional[SemanticChunker] = None,
        query_analyzer: Optional[QueryAnalyzer] = None,
        tool_registry: Optional[ToolRegistry] = None,
        process_logger: Optional[ProcessLogger] = None
    ):
        """
        Initialize the EnhancedLangGraphRAGAgent
        
        Args:
            vector_store: Vector store for retrieval
            ollama_client: Client for LLM interactions
            chunking_judge: Judge for document analysis and chunking strategy selection
            retrieval_judge: Judge for query refinement and context optimization
            semantic_chunker: Chunker for intelligent text splitting
            query_analyzer: Analyzer for query complexity and requirements
            tool_registry: Registry for available tools
            process_logger: Logger for process tracking
        """
        self.vector_store = vector_store or VectorStore()
        self.ollama_client = ollama_client or OllamaClient()
        self.chunking_judge = chunking_judge or ChunkingJudge(ollama_client=self.ollama_client)
        self.retrieval_judge = retrieval_judge or RetrievalJudge(ollama_client=self.ollama_client)
        self.semantic_chunker = semantic_chunker or SemanticChunker(ollama_client=self.ollama_client)
        
        # Initialize components for planning and execution
        self.tool_registry = tool_registry or ToolRegistry()
        self.query_analyzer = query_analyzer or QueryAnalyzer(llm_provider=self.ollama_client)
        self.query_planner = QueryPlanner(query_analyzer=self.query_analyzer, tool_registry=self.tool_registry)
        self.process_logger = process_logger or ProcessLogger()
        self.plan_executor = PlanExecutor(
            tool_registry=self.tool_registry,
            process_logger=self.process_logger,
            llm_provider=self.ollama_client
        )
        
        # Initialize and compile the state graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        
        logger.info("EnhancedLangGraphRAGAgent initialized with state machine")
    
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
        graph.add_node(RAGStage.QUERY_PLANNING, self._plan_query)
        graph.add_node(RAGStage.PLAN_EXECUTION, self._execute_plan)
        graph.add_node(RAGStage.RETRIEVAL, self._retrieve_chunks)
        graph.add_node(RAGStage.QUERY_REFINEMENT, self._refine_query)
        graph.add_node(RAGStage.CONTEXT_OPTIMIZATION, self._optimize_context)
        graph.add_node(RAGStage.GENERATION, self._generate_response)
        graph.add_node(RAGStage.COMPLETE, self._finalize_response)
        
        # Define the edges between nodes with conditional routing
        # Start with query analysis
        graph.add_conditional_edges(
            RAGStage.QUERY_ANALYSIS,
            self._needs_planning,
            {
                True: RAGStage.QUERY_PLANNING,
                False: RAGStage.RETRIEVAL
            }
        )
        
        # After planning, execute the plan
        graph.add_edge(RAGStage.QUERY_PLANNING, RAGStage.PLAN_EXECUTION)
        
        # After plan execution, proceed to retrieval
        graph.add_edge(RAGStage.PLAN_EXECUTION, RAGStage.RETRIEVAL)
        
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
            - execution_trace: Trace of the execution process (if available)
        """
        # Generate a unique query ID
        query_id = str(uuid.uuid4())
        
        # Initialize the state
        initial_state: RAGState = {
            "query": query,
            "query_id": query_id,
            "conversation_context": conversation_context,
            "metadata_filters": metadata_filters,
            "model": model,
            "system_prompt": system_prompt,
            "stream": stream,
            "model_parameters": model_parameters or {},
            "query_analysis": None,
            "planning": None,
            "execution": None,
            "retrieval": None,
            "generation": None,
            "final_response": None
        }
        
        logger.info(f"Starting enhanced RAG query with LangGraph: {query[:50]}...")
        
        # Log the start of the process
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name="process_start",
                step_data={
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "model": model,
                    "stream": stream
                }
            )
        
        # Run the state machine
        start_time = time.time()
        result = await self.app.ainvoke(initial_state)
        elapsed_time = time.time() - start_time
        
        # Log the completion of the process
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name="process_complete",
                step_data={
                    "execution_time": elapsed_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        logger.info(f"Enhanced RAG query completed in {elapsed_time:.2f}s")
        
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
        
        # Extract conversation context if available
        conversation_context = state.get("conversation_context")
        
        # Convert conversation context to chat history format if available
        chat_history = None
        if conversation_context:
            # Parse conversation context into a list of (user, assistant) tuples
            # Assuming format like "User: message\nAssistant: response\n..."
            lines = conversation_context.strip().split('\n')
            history = []
            user_msg = None
            
            for line in lines:
                if line.startswith("User: "):
                    if user_msg is not None and len(history) > 0:
                        # If we have a previous user message without a response, discard it
                        user_msg = line[6:]  # Remove "User: " prefix
                    else:
                        user_msg = line[6:]  # Remove "User: " prefix
                elif line.startswith("Assistant: ") and user_msg is not None:
                    ai_msg = line[11:]  # Remove "Assistant: " prefix
                    history.append((user_msg, ai_msg))
                    user_msg = None
            
            if history:
                chat_history = history
                logger.info(f"Extracted {len(chat_history)} conversation turns from context")
        
        # Use the query analyzer to analyze the query with chat history
        analysis = await self.query_analyzer.analyze(state["query"], chat_history)
        
        # Update the state with the query analysis
        state["query_analysis"] = {
            "query": state["query"],
            "conversation_context": state["conversation_context"],
            "complexity": analysis.get("complexity"),
            "parameters": analysis.get("parameters"),
            "justification": analysis.get("justification"),
            "requires_tools": analysis.get("requires_tools", []),
            "sub_queries": analysis.get("sub_queries", [])
        }
        
        # Log the query analysis
        if self.process_logger:
            self.process_logger.log_step(
                query_id=state["query_id"],
                step_name="query_analysis",
                step_data=state["query_analysis"]
            )
        
        logger.info(f"Query complexity: {analysis.get('complexity', 'unknown')}")
        logger.info(f"Required tools: {analysis.get('requires_tools', [])}")
        
        return state
    
    def _needs_planning(self, state: RAGState) -> bool:
        """
        Determine if query planning is needed based on query analysis
        
        Args:
            state: The current state
            
        Returns:
            True if planning is needed, False otherwise
        """
        query_analysis = state["query_analysis"]
        if not query_analysis:
            return False
        
        # Check if the query is complex or requires tools
        complexity = query_analysis.get("complexity", "simple")
        requires_tools = query_analysis.get("requires_tools", [])
        
        needs_planning = complexity == "complex" or len(requires_tools) > 0
        logger.info(f"Query planning needed: {needs_planning}")
        
        return needs_planning
    
    async def _plan_query(self, state: RAGState) -> RAGState:
        """
        Create a plan for executing a complex query
        
        Args:
            state: The current state
            
        Returns:
            Updated state with query plan
        """
        query = state["query"]
        query_id = state["query_id"]
        query_analysis = state["query_analysis"]
        
        logger.info(f"Planning query execution: {query[:50]}...")
        
        # Extract chat history from the state if available
        chat_history = None
        conversation_context = state.get("conversation_context")
        
        if conversation_context:
            # Parse conversation context into a list of (user, assistant) tuples
            # Assuming format like "User: message\nAssistant: response\n..."
            lines = conversation_context.strip().split('\n')
            history = []
            user_msg = None
            
            for line in lines:
                if line.startswith("User: "):
                    if user_msg is not None and len(history) > 0:
                        # If we have a previous user message without a response, discard it
                        user_msg = line[6:]  # Remove "User: " prefix
                    else:
                        user_msg = line[6:]  # Remove "User: " prefix
                elif line.startswith("Assistant: ") and user_msg is not None:
                    ai_msg = line[11:]  # Remove "Assistant: " prefix
                    history.append((user_msg, ai_msg))
                    user_msg = None
            
            if history:
                chat_history = history
                logger.info(f"Using {len(chat_history)} conversation turns for planning")
        
        # Create a plan using the query planner with chat history
        plan = await self.query_planner.create_plan(
            query_id=query_id,
            query=query,
            chat_history=chat_history
        )
        
        # Update the state with the planning information
        state["planning"] = {
            "query": query,
            "query_id": query_id,
            "analysis": query_analysis,
            "plan": plan.to_dict(),
            "steps": plan.steps,
            "current_step": plan.current_step,
            "completed": plan.completed
        }
        
        # Log the query plan
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name="query_planning",
                step_data=state["planning"]
            )
        
        logger.info(f"Created plan with {len(plan.steps)} steps")
        
        return state
    
    async def _execute_plan(self, state: RAGState) -> RAGState:
        """
        Execute the query plan
        
        Args:
            state: The current state
            
        Returns:
            Updated state with execution results
        """
        planning = state["planning"]
        query_id = state["query_id"]
        query = state["query"]
        
        logger.info(f"Executing query plan: {query[:50]}...")
        
        # Reconstruct the plan from the planning state
        from app.rag.query_planner import QueryPlan
        plan = QueryPlan(
            query_id=query_id,
            query=query,
            steps=planning["steps"]
        )
        plan.current_step = planning["current_step"]
        plan.completed = planning["completed"]
        
        # Execute the plan
        execution_result = await self.plan_executor.execute_plan(plan)
        
        # Update the state with the execution results
        state["execution"] = {
            "query": query,
            "query_id": query_id,
            "plan": planning["plan"],
            "results": execution_result,
            "execution_trace": execution_result.get("steps", []),
            "completed": True,
            "error": None
        }
        
        # Log the plan execution
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name="plan_execution",
                step_data=state["execution"]
            )
        
        logger.info(f"Plan execution completed with {len(execution_result.get('steps', []))} results")
        
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
        
        # Log the retrieval results
        if self.process_logger:
            self.process_logger.log_step(
                query_id=state["query_id"],
                step_name="retrieval",
                step_data={
                    "query": query,
                    "chunk_count": len(search_results),
                    "needs_refinement": needs_refinement
                }
            )
        
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
        
        # Log the query refinement
        if self.process_logger:
            self.process_logger.log_step(
                query_id=state["query_id"],
                step_name="query_refinement",
                step_data={
                    "original_query": retrieval["query"],
                    "refined_query": refined_query
                }
            )
        
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
        
        # Log the context optimization
        if self.process_logger:
            self.process_logger.log_step(
                query_id=state["query_id"],
                step_name="context_optimization",
                step_data={
                    "context_length": len(context),
                    "source_count": len(sources)
                }
            )
        
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
        
        # Log the response generation
        if self.process_logger:
            self.process_logger.log_step(
                query_id=state["query_id"],
                step_name="response_generation",
                step_data={
                    "streaming": state["stream"],
                    "model": state["model"],
                    "response_length": len(generation.get("answer", "")) if not state["stream"] else None
                }
            )
        
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
        execution = state.get("execution", None)
        
        # Create the final response
        if state["stream"]:
            final_response = {
                "query": state["query"],
                "stream": generation.get("stream_response"),
                "sources": generation["sources"],
                "execution_trace": execution["execution_trace"] if execution else None
            }
        else:
            final_response = {
                "query": state["query"],
                "answer": generation["answer"],
                "sources": generation["sources"],
                "execution_trace": execution["execution_trace"] if execution else None
            }
        
        # Update the state with the final response
        state["final_response"] = final_response
        
        # Log the final response
        if self.process_logger:
            self.process_logger.log_final_response(
                query_id=state["query_id"],
                response=generation.get("answer", ""),
                metadata={
                    "source_count": len(generation["sources"]),
                    "has_execution_trace": execution is not None
                }
            )
        
        logger.info("Enhanced RAG process complete")
        
        return state