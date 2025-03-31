"""
ResponseRefiner - Refines responses based on evaluation results
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class ResponseRefiner:
    """
    Refines responses based on evaluation results
    
    The ResponseRefiner is responsible for improving responses based on the evaluation
    results from the ResponseEvaluator. It addresses issues such as factual inaccuracies,
    incompleteness, irrelevance, and hallucinations to produce higher-quality responses.
    """
    
    def __init__(
        self,
        llm_provider,
        process_logger = None,
        max_refinement_iterations: int = 3
    ):
        """
        Initialize the response refiner
        
        Args:
            llm_provider: LLM provider for refinement
            process_logger: ProcessLogger instance (optional)
            max_refinement_iterations: Maximum number of refinement iterations
        """
        self.llm_provider = llm_provider
        self.process_logger = process_logger
        self.max_refinement_iterations = max_refinement_iterations
        self.logger = logging.getLogger("app.rag.response_refiner")
    
    async def refine(
        self,
        query: str,
        query_id: str,
        response: str,
        evaluation: Dict[str, Any],
        context: str,
        sources: List[Dict[str, Any]],
        execution_result: Optional[Dict[str, Any]] = None,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Refine a response based on evaluation results
        
        Args:
            query: Original user query
            query_id: Unique query ID
            response: Original response to refine
            evaluation: Evaluation results from ResponseEvaluator
            context: Retrieved context from documents
            sources: List of source information for citation
            execution_result: Result of plan execution (optional)
            iteration: Current refinement iteration
            
        Returns:
            Dictionary containing:
                - refined_response: Refined response text
                - improvement_summary: Summary of improvements made
                - execution_time: Time taken to refine the response
                - iteration: Current refinement iteration
        """
        start_time = time.time()
        self.logger.info(f"Refining response for query: {query} (iteration {iteration})")
        
        # Check if we've reached the maximum number of iterations
        if iteration > self.max_refinement_iterations:
            self.logger.warning(f"Maximum refinement iterations ({self.max_refinement_iterations}) reached")
            return {
                "refined_response": response,
                "improvement_summary": "Maximum refinement iterations reached. No further improvements made.",
                "execution_time": 0,
                "iteration": iteration
            }
        
        # Check if the response already has a high score and doesn't need refinement
        overall_score = evaluation.get("overall_score", 0)
        if overall_score >= 9:
            self.logger.info(f"Response already has a high score ({overall_score}). No refinement needed.")
            return {
                "refined_response": response,
                "improvement_summary": "Response already meets quality standards. No refinement needed.",
                "execution_time": 0,
                "iteration": iteration
            }
        
        # Log the start of response refinement
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name=f"response_refinement_start_{iteration}",
                step_data={
                    "query": query,
                    "response_length": len(response),
                    "evaluation_score": overall_score,
                    "iteration": iteration
                }
            )
        
        # Create the refinement prompt
        prompt = self._create_refinement_prompt(
            query=query,
            response=response,
            evaluation=evaluation,
            context=context,
            sources=sources,
            execution_result=execution_result,
            iteration=iteration
        )
        
        # Create the system prompt
        system_prompt = self._create_system_prompt()
        
        try:
            # Generate the refined response using the LLM
            refinement_response = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Parse the refinement results
            refinement = self._parse_refinement(refinement_response.get("response", ""))
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Response refinement completed in {elapsed_time:.2f}s (iteration {iteration})")
            
            # Log the completion of response refinement
            if self.process_logger:
                self.process_logger.log_step(
                    query_id=query_id,
                    step_name=f"response_refinement_complete_{iteration}",
                    step_data={
                        "refined_response_length": len(refinement.get("refined_response", "")),
                        "improvement_summary": refinement.get("improvement_summary", ""),
                        "execution_time": elapsed_time,
                        "iteration": iteration
                    }
                )
            
            # Add execution time to the refinement results
            refinement["execution_time"] = elapsed_time
            refinement["iteration"] = iteration
            
            return refinement
        except Exception as e:
            self.logger.error(f"Error refining response: {str(e)}")
            
            # Log the error
            if self.process_logger:
                self.process_logger.log_step(
                    query_id=query_id,
                    step_name=f"response_refinement_error_{iteration}",
                    step_data={
                        "error": str(e),
                        "iteration": iteration
                    }
                )
            
            # Return the original response with error information
            return {
                "refined_response": response,
                "improvement_summary": f"Refinement failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "iteration": iteration
            }
    
    def _create_refinement_prompt(
        self,
        query: str,
        response: str,
        evaluation: Dict[str, Any],
        context: str,
        sources: List[Dict[str, Any]],
        execution_result: Optional[Dict[str, Any]] = None,
        iteration: int = 1
    ) -> str:
        """
        Create a prompt for response refinement
        
        Args:
            query: Original user query
            response: Original response to refine
            evaluation: Evaluation results from ResponseEvaluator
            context: Retrieved context from documents
            sources: List of source information for citation
            execution_result: Result of plan execution (optional)
            iteration: Current refinement iteration
            
        Returns:
            Refinement prompt
        """
        prompt = f"""
You are refining a response to the following query:

USER QUERY: {query}

ORIGINAL RESPONSE:
{response}

EVALUATION RESULTS:
{json.dumps(evaluation, indent=2)}

RETRIEVED CONTEXT:
{context}

"""
        
        # Add execution result if available
        if execution_result:
            prompt += f"""
EXECUTION RESULTS:
{json.dumps(execution_result, indent=2)}

"""
        
        # Add source information
        if sources:
            prompt += f"""
SOURCE INFORMATION:
{json.dumps(sources, indent=2)}

"""
        
        # Add instructions for refinement
        prompt += f"""
REFINEMENT INSTRUCTIONS:
You are performing refinement iteration {iteration} for this response. Please address the issues identified in the evaluation results to create an improved response.

Focus on the following areas:

1. Factual Accuracy:
   - Correct any factual inaccuracies identified in the evaluation.
   - Ensure all statements are supported by the provided context.
   - Fix any incorrect citations or add missing citations.

2. Completeness:
   - Address any aspects of the query that were not covered in the original response.
   - Include relevant information from the context that was missed.
   - Ensure the response fully answers the user's query.

3. Relevance:
   - Remove any irrelevant information that doesn't address the user's query.
   - Focus the response more directly on what the user was asking about.
   - Improve the structure and flow of the response.

4. Hallucination Removal:
   - Remove or correct any statements that were identified as hallucinations.
   - Ensure all information in the response is supported by the provided context.
   - If the context doesn't contain certain information, clearly state that it's not available.

5. Overall Quality:
   - Improve the structure and clarity of the response.
   - Enhance readability with appropriate formatting.
   - Ensure the response provides maximum value to the user.

FORMAT YOUR RESPONSE AS FOLLOWS:
```json
{{
  "refined_response": "Your complete refined response here",
  "improvement_summary": "A brief summary of the improvements you made"
}}
```

IMPORTANT: Your refined response must be factually accurate, complete, relevant, and free from hallucinations. It should directly address the user's query and be well-structured and easy to understand. When using information from the context, cite the sources using the format [n] where n is the source number.
"""
        
        return prompt
    
    def _create_system_prompt(self) -> str:
        """
        Create a system prompt for response refinement
        
        Returns:
            System prompt
        """
        return """You are a response refiner for a Retrieval-Augmented Generation (RAG) system.

Your role is to improve responses based on evaluation feedback, focusing on factual accuracy, completeness, relevance, and overall quality.

GUIDELINES:
1. Address all issues identified in the evaluation results.
2. Ensure factual accuracy by verifying all statements against the provided context.
3. Improve completeness by addressing all aspects of the user's query.
4. Enhance relevance by focusing directly on what the user was asking about.
5. Remove any hallucinations or statements not supported by the context.
6. Maintain proper source citations using the [n] format.
7. Improve the structure and clarity of the response.
8. Format your response according to the specified JSON structure.
9. Be thorough in your refinements while maintaining the core information.
10. If the context doesn't contain certain information, clearly state that it's not available rather than making up information.
"""
    
    def _parse_refinement(self, refinement_text: str) -> Dict[str, Any]:
        """
        Parse the refinement response from the LLM
        
        Args:
            refinement_text: Raw refinement text from the LLM
            
        Returns:
            Parsed refinement results
        """
        # Extract JSON from the response
        try:
            # Look for JSON block in markdown format
            import re
            json_match = re.search(r'```(?:json)?\s*({\s*".*})\s*```', refinement_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without markdown formatting
                json_match = re.search(r'({[\s\S]*"improvement_summary"[\s\S]*})', refinement_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Fallback: assume the entire text might be JSON
                    json_str = refinement_text
            
            # Parse the JSON
            refinement = json.loads(json_str)
            
            # Ensure all required fields are present
            required_fields = ["refined_response", "improvement_summary"]
            
            for field in required_fields:
                if field not in refinement:
                    if field == "refined_response":
                        # If the refined response is missing, use the raw text
                        refinement[field] = refinement_text
                    else:
                        refinement[field] = "Not provided"
            
            return refinement
        except Exception as e:
            self.logger.error(f"Error parsing refinement: {str(e)}")
            
            # Return a default refinement with the raw text as the response
            return {
                "refined_response": refinement_text,
                "improvement_summary": f"Failed to parse refinement: {str(e)}"
            }