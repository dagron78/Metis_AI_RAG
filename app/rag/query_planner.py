"""
QueryPlanner - Plans the execution of complex queries
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple

class QueryPlan:
    """
    Represents a plan for executing a complex query
    
    A QueryPlan consists of a sequence of steps, each of which may involve
    executing a tool, retrieving information, or performing some other action.
    The plan can also store conversation history to provide context for the execution.
    """
    
    def __init__(self, query_id: str, query: str, steps: List[Dict[str, Any]],
                 chat_history: Optional[List[Tuple[str, str]]] = None):
        """
        Initialize a query plan
        
        Args:
            query_id: Unique query ID
            query: Original query string
            steps: List of execution steps
            chat_history: Optional list of (user_message, ai_message) tuples representing
                          the conversation history
        """
        self.query_id = query_id
        self.query = query
        self.steps = steps
        self.current_step = 0
        self.results = []
        self.completed = False
        self.chat_history = chat_history
    
    def get_next_step(self) -> Optional[Dict[str, Any]]:
        """
        Get the next step in the plan
        
        Returns:
            Next step if available, None if plan is completed
        """
        if self.current_step >= len(self.steps):
            self.completed = True
            return None
        
        return self.steps[self.current_step]
    
    def record_step_result(self, result: Dict[str, Any]) -> None:
        """
        Record the result of a step
        
        Args:
            result: Step execution result
        """
        self.results.append(result)
        self.current_step += 1
    
    def is_completed(self) -> bool:
        """
        Check if the plan is completed
        
        Returns:
            True if all steps have been executed, False otherwise
        """
        return self.completed or self.current_step >= len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the plan to a dictionary
        
        Returns:
            Dictionary representation of the plan
        """
        return {
            "query_id": self.query_id,
            "query": self.query,
            "steps": self.steps,
            "current_step": self.current_step,
            "results": self.results,
            "completed": self.completed,
            "chat_history": self.chat_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryPlan':
        """
        Create a plan from a dictionary
        
        Args:
            data: Dictionary representation of the plan
            
        Returns:
            QueryPlan instance
        """
        plan = cls(
            query_id=data["query_id"],
            query=data["query"],
            steps=data["steps"],
            chat_history=data.get("chat_history")
        )
        plan.current_step = data.get("current_step", 0)
        plan.results = data.get("results", [])
        plan.completed = data.get("completed", False)
        return plan


class QueryPlanner:
    """
    Plans the execution of complex queries
    
    The QueryPlanner analyzes queries and creates execution plans that may involve
    multiple steps and tools. It uses the QueryAnalyzer to determine the complexity
    and requirements of a query, then creates a plan for executing it.
    """
    
    def __init__(self, query_analyzer, tool_registry):
        """
        Initialize the query planner
        
        Args:
            query_analyzer: QueryAnalyzer instance
            tool_registry: ToolRegistry instance
        """
        self.query_analyzer = query_analyzer
        self.tool_registry = tool_registry
        self.logger = logging.getLogger("app.rag.query_planner")
    
    async def create_plan(self, query_id: str, query: str,
                         chat_history: Optional[List[Tuple[str, str]]] = None) -> QueryPlan:
        """
        Create a plan for executing a query
        
        Args:
            query_id: Unique query ID
            query: Query string
            chat_history: Optional list of (user_message, ai_message) tuples
            
        Returns:
            QueryPlan instance
        """
        self.logger.info(f"Creating plan for query: {query}")
        
        # Analyze the query with chat history context
        analysis = await self.query_analyzer.analyze(query, chat_history)
        
        # Determine if the query is simple or complex
        complexity = analysis.get("complexity", "simple")
        required_tools = analysis.get("requires_tools", [])
        sub_queries = analysis.get("sub_queries", [])
        
        # Create plan steps
        steps = []
        
        if complexity == "simple":
            # Simple query - just use RAG
            steps.append({
                "type": "tool",
                "tool": "rag",
                "input": {
                    "query": query,
                    "top_k": 5
                },
                "description": "Retrieve information using RAG"
            })
        else:
            # Complex query - may require multiple steps
            
            # First, add steps for any required tools
            for tool_name in required_tools:
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    self.logger.warning(f"Required tool not found: {tool_name}")
                    continue
                
                # Create a step for this tool
                tool_input = self._create_tool_input(tool_name, query)
                steps.append({
                    "type": "tool",
                    "tool": tool_name,
                    "input": tool_input,
                    "description": f"Execute {tool_name} tool"
                })
            
            # If there are sub-queries, add steps for them
            for sub_query in sub_queries:
                steps.append({
                    "type": "tool",
                    "tool": "rag",
                    "input": {
                        "query": sub_query,
                        "top_k": 3
                    },
                    "description": f"Retrieve information for sub-query: {sub_query}"
                })
            
            # Add a final step to synthesize the results with chat history
            steps.append({
                "type": "synthesize",
                "description": "Synthesize results from previous steps with conversation history",
                "with_history": True  # Flag to indicate this step should use history
            })
        
        # Create the plan with chat history
        plan = QueryPlan(
            query_id=query_id,
            query=query,
            steps=steps,
            chat_history=chat_history  # Pass chat history to the plan
        )
        
        self.logger.info(f"Created plan with {len(steps)} steps for query: {query}")
        return plan
    
    def _create_tool_input(self, tool_name: str, query: str) -> Dict[str, Any]:
        """
        Create input for a tool based on the query
        
        Args:
            tool_name: Tool name
            query: Query string
            
        Returns:
            Tool input dictionary
        """
        if tool_name == "rag":
            return {
                "query": query,
                "top_k": 5
            }
        elif tool_name == "calculator":
            # Extract mathematical expression from the query
            # This is a simple implementation - in a real system, you would use
            # more sophisticated NLP techniques to extract the expression
            import re
            expression_match = re.search(r'calculate\s+(.+)', query, re.IGNORECASE)
            if expression_match:
                expression = expression_match.group(1)
            else:
                expression = query
            
            return {
                "expression": expression
            }
        elif tool_name == "database":
            # For database queries, we would need more sophisticated parsing
            # This is a placeholder implementation
            return {
                "query": "SELECT * FROM relevant_table LIMIT 5",
                "source": "default.db"
            }
        else:
            # Default to passing the query as-is
            return {
                "query": query
            }
    
    def update_plan(self, plan: QueryPlan, step_result: Dict[str, Any]) -> QueryPlan:
        """
        Update a plan based on the result of a step
        
        Args:
            plan: QueryPlan instance
            step_result: Result of the current step
            
        Returns:
            Updated QueryPlan
        """
        # Record the result of the current step
        plan.record_step_result(step_result)
        
        # Check if we need to modify the plan based on the result
        current_step = plan.current_step - 1  # The step that just completed
        if current_step < 0 or current_step >= len(plan.steps):
            return plan
        
        step = plan.steps[current_step]
        
        # If the step was a tool execution and it failed, we might want to try an alternative
        if step["type"] == "tool" and "error" in step_result:
            self.logger.warning(f"Tool execution failed: {step_result.get('error')}")
            
            # We could insert a fallback step here if needed
            # For now, we'll just continue with the plan
        
        return plan