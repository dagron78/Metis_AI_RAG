"""
PlanExecutor - Executes query plans
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple

from app.rag.query_planner import QueryPlan
from app.rag.tools import ToolRegistry
from app.rag.process_logger import ProcessLogger

class PlanExecutor:
    """
    Executes query plans
    
    The PlanExecutor is responsible for executing the plans created by the QueryPlanner.
    It executes each step in the plan, records the results, and handles any errors that
    may occur during execution.
    """
    
    def __init__(
        self, 
        tool_registry: ToolRegistry,
        process_logger: Optional[ProcessLogger] = None,
        llm_provider = None
    ):
        """
        Initialize the plan executor
        
        Args:
            tool_registry: ToolRegistry instance
            process_logger: ProcessLogger instance (optional)
            llm_provider: LLM provider for generating responses (optional)
        """
        self.tool_registry = tool_registry
        self.process_logger = process_logger
        self.llm_provider = llm_provider
        self.logger = logging.getLogger("app.rag.plan_executor")
    
    async def execute_plan(self, plan: QueryPlan) -> Dict[str, Any]:
        """
        Execute a query plan
        
        Args:
            plan: QueryPlan instance
            
        Returns:
            Dictionary containing:
                - query_id: Query ID
                - response: Final response
                - steps: List of executed steps
                - execution_time: Total execution time
        """
        start_time = time.time()
        self.logger.info(f"Executing plan for query: {plan.query}")
        
        # Log the start of plan execution
        if self.process_logger:
            self.process_logger.log_step(
                query_id=plan.query_id,
                step_name="plan_execution_start",
                step_data=plan.to_dict()
            )
        
        # Execute each step in the plan
        while not plan.is_completed():
            step = plan.get_next_step()
            if not step:
                break
            
            step_result = await self._execute_step(plan.query_id, step)
            plan = self._update_plan(plan, step_result)
        
        # Generate the final response
        response = await self._generate_response(plan)
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Plan execution completed in {elapsed_time:.2f}s")
        
        # Log the completion of plan execution
        if self.process_logger:
            self.process_logger.log_step(
                query_id=plan.query_id,
                step_name="plan_execution_complete",
                step_data={
                    "execution_time": elapsed_time,
                    "response": response
                }
            )
            
            # Log the final response
            self.process_logger.log_final_response(
                query_id=plan.query_id,
                response=response,
                metadata={
                    "execution_time": elapsed_time,
                    "steps_executed": plan.current_step
                }
            )
        
        return {
            "query_id": plan.query_id,
            "response": response,
            "steps": plan.results,
            "execution_time": elapsed_time
        }
    
    async def _execute_step(self, query_id: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step in the plan
        
        Args:
            query_id: Query ID
            step: Step to execute
            
        Returns:
            Step execution result
        """
        step_type = step.get("type")
        step_description = step.get("description", "Unknown step")
        
        self.logger.info(f"Executing step: {step_description}")
        
        # Log the start of step execution
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name=f"step_start_{step_type}",
                step_data=step
            )
        
        start_time = time.time()
        result = {}
        
        try:
            if step_type == "tool":
                # Execute a tool
                tool_name = step.get("tool")
                tool_input = step.get("input", {})
                
                result = await self._execute_tool(tool_name, tool_input)
            elif step_type == "synthesize":
                # Synthesize results from previous steps
                result = await self._synthesize_results(query_id)
            else:
                # Unknown step type
                result = {
                    "error": f"Unknown step type: {step_type}"
                }
        except Exception as e:
            self.logger.error(f"Error executing step: {str(e)}")
            result = {
                "error": f"Error executing step: {str(e)}"
            }
        
        elapsed_time = time.time() - start_time
        result["execution_time"] = elapsed_time
        
        # Log the completion of step execution
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name=f"step_complete_{step_type}",
                step_data={
                    "step": step,
                    "result": result,
                    "execution_time": elapsed_time
                }
            )
        
        return result
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool
        
        Args:
            tool_name: Tool name
            tool_input: Tool input
            
        Returns:
            Tool execution result
        """
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return {
                "error": f"Tool not found: {tool_name}"
            }
        
        try:
            result = await tool.execute(tool_input)
            return result
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "error": f"Error executing tool {tool_name}: {str(e)}"
            }
    
    async def _synthesize_results(self, query_id: str) -> Dict[str, Any]:
        """
        Synthesize results from previous steps
        
        Args:
            query_id: Query ID
            
        Returns:
            Synthesis result
        """
        # In a real implementation, this would use the LLM to synthesize the results
        # For now, we'll just return a placeholder
        return {
            "synthesis": "Results synthesized successfully"
        }
    
    def _update_plan(self, plan: QueryPlan, step_result: Dict[str, Any]) -> QueryPlan:
        """
        Update the plan based on the result of a step
        
        Args:
            plan: QueryPlan instance
            step_result: Step execution result
            
        Returns:
            Updated QueryPlan
        """
        # Record the result of the step
        plan.record_step_result(step_result)
        
        # In a more sophisticated implementation, we might modify the plan
        # based on the results of previous steps
        
        return plan
    
    async def _generate_response(self, plan: QueryPlan) -> str:
        """
        Generate the final response based on the plan execution
        
        Args:
            plan: Executed QueryPlan
            
        Returns:
            Final response string
        """
        # In a real implementation, this would use the LLM to generate a response
        # based on the results of all the steps
        
        if not self.llm_provider:
            # If no LLM provider is available, generate a simple response
            return self._generate_simple_response(plan)
        
        # Create a prompt for the LLM
        prompt = self._create_response_prompt(plan)
        
        try:
            # Generate a response using the LLM
            response = await self.llm_provider.generate(prompt=prompt)
            return response.get("response", "No response generated")
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def _generate_simple_response(self, plan: QueryPlan) -> str:
        """
        Generate a simple response based on the plan execution
        
        Args:
            plan: Executed QueryPlan
            
        Returns:
            Simple response string
        """
        # Check if any steps failed
        for result in plan.results:
            if "error" in result:
                return f"I encountered an error while processing your query: {result['error']}"
        
        # Check if there are any RAG results
        rag_results = []
        for result in plan.results:
            if "chunks" in result:
                rag_results.extend(result["chunks"])
        
        if rag_results:
            # Return the content of the top chunk
            return f"Based on the information I found: {rag_results[0]['content']}"
        
        # Check if there are any calculator results
        for result in plan.results:
            if "result" in result and isinstance(result["result"], (int, float)):
                return f"The result of the calculation is: {result['result']}"
        
        # Check if there are any database results
        for result in plan.results:
            if "results" in result and isinstance(result["results"], list):
                return f"I found {len(result['results'])} records in the database."
        
        # Default response
        return "I processed your query, but I don't have a specific answer to provide."
    
    def _create_response_prompt(self, plan: QueryPlan) -> str:
        """
        Create a prompt for generating the final response
        
        Args:
            plan: Executed QueryPlan
            
        Returns:
            Prompt string
        """
        prompt = f"""
You are an AI assistant helping with a query. Based on the following information, please generate a comprehensive and helpful response.

Original query: {plan.query}

Steps executed:
"""
        
        for i, (step, result) in enumerate(zip(plan.steps[:plan.current_step], plan.results)):
            prompt += f"\nStep {i+1}: {step.get('description', 'Unknown step')}\n"
            
            if "error" in result:
                prompt += f"Error: {result['error']}\n"
            elif step.get("type") == "tool":
                tool_name = step.get("tool")
                if tool_name == "rag":
                    prompt += "Retrieved information:\n"
                    if "chunks" in result:
                        for chunk in result["chunks"]:
                            prompt += f"- {chunk.get('content', '')}\n"
                    else:
                        prompt += "No information retrieved.\n"
                elif tool_name == "calculator":
                    if "result" in result:
                        prompt += f"Calculation result: {result['result']}\n"
                    else:
                        prompt += "No calculation result.\n"
                elif tool_name == "database":
                    if "results" in result:
                        prompt += f"Database query returned {len(result['results'])} records.\n"
                        if result["results"]:
                            prompt += "Sample record:\n"
                            prompt += json.dumps(result["results"][0], indent=2) + "\n"
                    else:
                        prompt += "No database results.\n"
                else:
                    prompt += f"Tool result: {json.dumps(result, indent=2)}\n"
            elif step.get("type") == "synthesize":
                prompt += f"Synthesis result: {result.get('synthesis', 'No synthesis result.')}\n"
        
        prompt += """
Please generate a comprehensive and helpful response to the original query based on the information above.
Your response should be clear, concise, and directly address the user's query.
If there were any errors or missing information, please acknowledge them in your response.
"""
        
        return prompt