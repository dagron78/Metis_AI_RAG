## Phase 4: Planning and Execution (Weeks 7-8)

### Week 7: Query Planner and Plan Executor

#### Query Planner
```python
class QueryPlanner:
    """
    Creates execution plans for complex queries
    """
    def __init__(self, llm_provider, tool_registry):
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.logger = logging.getLogger("app.services.query_planner")
        
    async def create_plan(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an execution plan for a complex query
        
        Returns:
            Dict with keys:
            - steps: list of execution steps
            - tools: list of required tools
            - reasoning: explanation of the plan
        """
        start_time = time.time()
        self.logger.info(f"Creating plan for query: {query}")
        
        available_tools = self.tool_registry.list_tools()
        prompt = self._create_planning_prompt(query, analysis, available_tools)
        response = await self.llm_provider.generate(prompt=prompt)
        plan = self._parse_plan(response.get("response", ""))
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Plan creation completed in {elapsed_time:.2f}s. Steps: {len(plan.get('steps', []))}")
        
        return plan
```

#### Plan Executor
```python
class PlanExecutor:
    """
    Executes query plans
    """
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.logger = logging.getLogger("app.services.plan_executor")
        
    async def execute_plan(self, plan: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Execute a query plan
        
        Args:
            plan: Query plan
            query: Original query
            
        Returns:
            Dict with execution results
        """
        start_time = time.time()
        self.logger.info(f"Executing plan with {len(plan['steps'])} steps")
        
        results = {}
        
        for step in plan["steps"]:
            step_id = step["step_id"]
            tool_name = step.get("tool")
            step_start_time = time.time()
            
            self.logger.info(f"Executing step {step_id}: {step.get('action')} with tool {tool_name}")
            
            if tool_name:
                # Execute tool
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    error_msg = f"Tool not found: {tool_name}"
                    self.logger.error(error_msg)
                    results[step_id] = {"error": error_msg}
                    continue
                    
                try:
                    tool_input = self._prepare_input(step["input"], results)
                    tool_output = await tool.execute(tool_input)
                    results[step_id] = {"output": tool_output}
                    self.logger.info(f"Step {step_id} completed successfully")
                except Exception as e:
                    error_msg = f"Error executing tool {tool_name}: {str(e)}"
                    self.logger.error(error_msg)
                    results[step_id] = {"error": error_msg}
            else:
                # No tool, just record the action
                results[step_id] = {"action": step["action"]}
                self.logger.info(f"Recorded action for step {step_id}")
                
            step_elapsed_time = time.time() - step_start_time
            self.logger.info(f"Step {step_id} took {step_elapsed_time:.2f}s")
                
        total_elapsed_time = time.time() - start_time
        self.logger.info(f"Plan execution completed in {total_elapsed_time:.2f}s")
        
        return {
            "query": query,
            "plan": plan,
            "results": results,
            "execution_time": total_elapsed_time
        }
```

### Week 8: LangGraph Integration

#### LangGraph State Definitions
```python
class QueryAnalysisState(BaseModel):
    """State for query analysis"""
    query: str
    analysis: Optional[Dict[str, Any]] = None
    
class RetrievalState(BaseModel):
    """State for retrieval operations"""
    query: str
    refined_query: Optional[str] = None
    chunks: List[Dict[str, Any]] = []
    needs_refinement: bool = False
    
class GenerationState(BaseModel):
    """State for response generation"""
    query: str
    context: str
    response: Optional[str] = None
    
class RAGState(BaseModel):
    """Combined state for the RAG process"""
    query: str
    analysis: Optional[Dict[str, Any]] = None
    refined_query: Optional[str] = None
    chunks: List[Dict[str, Any]] = []
    context: Optional[str] = None
    response: Optional[str] = None
    needs_refinement: bool = False
    needs_reranking: bool = False
    execution_trace: List[Dict[str, Any]] = []
```

#### LangGraph Integration
```python
def _build_graph(self) -> StateGraph:
    """
    Build the state graph for the Agentic RAG process
    """
    # Create the state graph
    graph = StateGraph(AgenticRAGState)
    
    # Add nodes for each stage
    graph.add_node(RAGStage.QUERY_ANALYSIS, self._analyze_query)
    graph.add_node(RAGStage.QUERY_PLANNING, self._plan_query)
    graph.add_node(RAGStage.PLAN_EXECUTION, self._execute_plan)
    graph.add_node(RAGStage.RETRIEVAL, self._retrieve_chunks)
    graph.add_node(RAGStage.QUERY_REFINEMENT, self._refine_query)
    graph.add_node(RAGStage.CONTEXT_OPTIMIZATION, self._optimize_context)
    graph.add_node(RAGStage.GENERATION, self._generate_response)
    graph.add_node(RAGStage.RESPONSE_EVALUATION, self._evaluate_response)
    graph.add_node(RAGStage.RESPONSE_REFINEMENT, self._refine_response)
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
    
    # After generation, evaluate the response
    graph.add_edge(RAGStage.GENERATION, RAGStage.RESPONSE_EVALUATION)
    
    # After evaluation, decide whether to refine the response or complete
    graph.add_conditional_edges(
        RAGStage.RESPONSE_EVALUATION,
        self._needs_response_refinement,
        {
            True: RAGStage.RESPONSE_REFINEMENT,
            False: RAGStage.COMPLETE
        }
    )
    
    # After response refinement, re-evaluate
    graph.add_edge(RAGStage.RESPONSE_REFINEMENT, RAGStage.RESPONSE_EVALUATION)
    
    # After completion, end the process
    graph.add_edge(RAGStage.COMPLETE, END)
    
    # Set the entry point
    graph.set_entry_point(RAGStage.QUERY_ANALYSIS)
    
    return graph
```

## Phase 5: Response Quality (Weeks 9-10)

### Week 9: Response Synthesizer and Evaluator

#### Response Synthesizer
```python
class ResponseSynthesizer:
    """
    Synthesizes a response from execution results
    """
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.logger = logging.getLogger("app.services.response_synthesizer")
        
    async def synthesize(self, execution_result: Dict[str, Any]) -> str:
        """
        Synthesize a response from execution results
        
        Args:
            execution_result: Result of plan execution
            
        Returns:
            Synthesized response
        """
        start_time = time.time()
        self.logger.info("Synthesizing response from execution results")
        
        prompt = self._create_synthesis_prompt(execution_result)
        response = await self.llm_provider.generate(prompt=prompt)
        synthesized_response = response.get("response", "")
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Response synthesis completed in {elapsed_time:.2f}s")
        
        return synthesized_response
```

#### Response Evaluator
```python
class ResponseEvaluator:
    """
    Evaluates response quality
    """
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.logger = logging.getLogger("app.services.response_evaluator")
        
    async def evaluate(self, query: str, response: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate response quality
        
        Args:
            query: Original query
            response: Synthesized response
            execution_result: Result of plan execution
            
        Returns:
            Dict with evaluation results
        """
        start_time = time.time()
        self.logger.info(f"Evaluating response for query: {query}")
        
        prompt = self._create_evaluation_prompt(query, response, execution_result)
        eval_response = await self.llm_provider.generate(prompt=prompt)
        evaluation = self._parse_evaluation(eval_response.get("response", ""))
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Response evaluation completed in {elapsed_time:.2f}s. Overall score: {evaluation.get('overall_score')}")
        
        return evaluation
```

### Week 10: Response Refiner and Audit Report Generator

#### Response Refiner
```python
class ResponseRefiner:
    """
    Refines responses based on evaluation
    """
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.logger = logging.getLogger("app.services.response_refiner")
        
    async def refine(self, query: str, response: str, evaluation: Dict[str, Any], execution_result: Dict[str, Any]) -> str:
        """
        Refine a response based on evaluation
        
        Args:
            query: Original query
            response: Original response
            evaluation: Evaluation results
            execution_result: Result of plan execution
            
        Returns:
            Refined response
        """
        start_time = time.time()
        self.logger.info(f"Refining response for query: {query}")
        
        prompt = self._create_refinement_prompt(query, response, evaluation, execution_result)
        refined_response_result = await self.llm_provider.generate(prompt=prompt)
        refined_response = refined_response_result.get("response", "")
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Response refinement completed in {elapsed_time:.2f}s")
        
        return refined_response
```

#### Audit Report Generator
```python
class AuditReportGenerator:
    """
    Generates audit reports for query processing
    """
    def __init__(self, process_logger):
        self.process_logger = process_logger
        self.logger = logging.getLogger("app.services.audit_report_generator")
        
    async def generate_report(self, query_id: str) -> Dict[str, Any]:
        """
        Generate an audit report for a query
        
        Args:
            query_id: Query ID
            
        Returns:
            Audit report
        """
        start_time = time.time()
        self.logger.info(f"Generating audit report for query {query_id}")
        
        process_log = self.process_logger.get_process_log(query_id)
        if not process_log:
            error_msg = f"No process log found for query {query_id}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Extract information from process log
        query = process_log["query"]
        steps = process_log["steps"]
        final_response = process_log["final_response"]
        
        # Generate report
        report = {
            "query_id": query_id,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "process_summary": self._generate_process_summary(steps),
            "information_sources": self._extract_information_sources(steps),
            "reasoning_trace": self._extract_reasoning_trace(steps),
            "hallucination_assessment": self._assess_hallucination(steps),
            "verification_status": self._determine_verification_status(steps)
        }
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Audit report generation completed in {elapsed_time:.2f}s")
        
        return report