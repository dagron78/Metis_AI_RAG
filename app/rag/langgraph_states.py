"""
LangGraph State Models - Defines the state models for the LangGraph RAG system
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Sequence, cast, Tuple
from enum import Enum

class QueryAnalysisState(TypedDict):
    """State for query analysis"""
    query: str
    conversation_context: Optional[str]
    complexity: Optional[str]
    parameters: Optional[Dict[str, Any]]
    justification: Optional[str]
    requires_tools: List[str]
    sub_queries: List[str]

class PlanningState(TypedDict):
    """State for query planning"""
    query: str
    query_id: str
    analysis: Dict[str, Any]
    plan: Optional[Dict[str, Any]]
    steps: List[Dict[str, Any]]
    current_step: int
    completed: bool

class ExecutionState(TypedDict):
    """State for plan execution"""
    query: str
    query_id: str
    plan: Dict[str, Any]
    results: Dict[str, Any]
    execution_trace: List[Dict[str, Any]]
    completed: bool
    error: Optional[str]

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
    stream_response: Optional[Any]

class RAGState(TypedDict):
    """Combined state for the RAG process"""
    query: str
    query_id: str
    conversation_context: Optional[str]
    metadata_filters: Optional[Dict[str, Any]]
    model: str
    system_prompt: Optional[str]
    stream: bool
    model_parameters: Optional[Dict[str, Any]]
    query_analysis: Optional[QueryAnalysisState]
    planning: Optional[PlanningState]
    execution: Optional[ExecutionState]
    retrieval: Optional[RetrievalState]
    generation: Optional[GenerationState]
    final_response: Optional[Dict[str, Any]]

class RAGStage(str, Enum):
    """Stages in the RAG process"""
    QUERY_ANALYSIS = "analyze_query_node"
    QUERY_PLANNING = "plan_query_node"
    PLAN_EXECUTION = "execute_plan_node"
    RETRIEVAL = "retrieve_chunks_node"
    QUERY_REFINEMENT = "refine_query_node"
    CONTEXT_OPTIMIZATION = "optimize_context_node"
    GENERATION = "generate_response_node"
    COMPLETE = "finalize_response_node"