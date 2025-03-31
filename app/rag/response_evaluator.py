"""
ResponseEvaluator - Evaluates the quality of synthesized responses
"""
import logging
import time
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class ResponseEvaluator:
    """
    Evaluates the quality of synthesized responses
    
    The ResponseEvaluator is responsible for assessing the quality of responses generated
    by the ResponseSynthesizer. It evaluates factual accuracy, completeness, relevance,
    and other quality metrics to ensure that the responses meet the required standards.
    """
    
    def __init__(
        self,
        llm_provider,
        process_logger = None
    ):
        """
        Initialize the response evaluator
        
        Args:
            llm_provider: LLM provider for evaluation
            process_logger: ProcessLogger instance (optional)
        """
        self.llm_provider = llm_provider
        self.process_logger = process_logger
        self.logger = logging.getLogger("app.rag.response_evaluator")
    
    async def evaluate(
        self,
        query: str,
        query_id: str,
        response: str,
        context: str,
        sources: List[Dict[str, Any]],
        execution_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate the quality of a response
        
        Args:
            query: Original user query
            query_id: Unique query ID
            response: Synthesized response to evaluate
            context: Retrieved context from documents
            sources: List of source information for citation
            execution_result: Result of plan execution (optional)
            
        Returns:
            Dictionary containing evaluation results:
                - factual_accuracy: Score for factual accuracy (0-10)
                - completeness: Score for completeness (0-10)
                - relevance: Score for relevance to the query (0-10)
                - hallucination_detected: Whether hallucinations were detected
                - hallucination_details: Details about any hallucinations
                - overall_score: Overall quality score (0-10)
                - strengths: List of response strengths
                - weaknesses: List of response weaknesses
                - improvement_suggestions: Suggestions for improvement
        """
        start_time = time.time()
        self.logger.info(f"Evaluating response for query: {query}")
        
        # Log the start of response evaluation
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name="response_evaluation_start",
                step_data={
                    "query": query,
                    "response_length": len(response),
                    "context_length": len(context),
                    "sources_count": len(sources)
                }
            )
        
        # Create the evaluation prompt
        prompt = self._create_evaluation_prompt(
            query=query,
            response=response,
            context=context,
            sources=sources,
            execution_result=execution_result
        )
        
        # Create the system prompt
        system_prompt = self._create_system_prompt()
        
        try:
            # Generate the evaluation using the LLM
            eval_response = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Parse the evaluation results
            evaluation = self._parse_evaluation(eval_response.get("response", ""))
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Response evaluation completed in {elapsed_time:.2f}s. Overall score: {evaluation.get('overall_score')}")
            
            # Log the completion of response evaluation
            if self.process_logger:
                self.process_logger.log_step(
                    query_id=query_id,
                    step_name="response_evaluation_complete",
                    step_data={
                        "evaluation": evaluation,
                        "execution_time": elapsed_time
                    }
                )
            
            # Add execution time to the evaluation results
            evaluation["execution_time"] = elapsed_time
            
            return evaluation
        except Exception as e:
            self.logger.error(f"Error evaluating response: {str(e)}")
            
            # Log the error
            if self.process_logger:
                self.process_logger.log_step(
                    query_id=query_id,
                    step_name="response_evaluation_error",
                    step_data={
                        "error": str(e)
                    }
                )
            
            # Return a default evaluation with error information
            return {
                "factual_accuracy": 0,
                "completeness": 0,
                "relevance": 0,
                "hallucination_detected": True,
                "hallucination_details": f"Evaluation failed: {str(e)}",
                "overall_score": 0,
                "strengths": [],
                "weaknesses": [f"Evaluation failed: {str(e)}"],
                "improvement_suggestions": ["Unable to provide suggestions due to evaluation failure"],
                "execution_time": time.time() - start_time
            }
    
    def _create_evaluation_prompt(
        self,
        query: str,
        response: str,
        context: str,
        sources: List[Dict[str, Any]],
        execution_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a prompt for response evaluation
        
        Args:
            query: Original user query
            response: Synthesized response to evaluate
            context: Retrieved context from documents
            sources: List of source information for citation
            execution_result: Result of plan execution (optional)
            
        Returns:
            Evaluation prompt
        """
        prompt = f"""
You are evaluating the quality of a response to the following query:

USER QUERY: {query}

RESPONSE TO EVALUATE:
{response}

RETRIEVED CONTEXT USED FOR GENERATING THE RESPONSE:
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
        
        # Add instructions for evaluation
        prompt += """
EVALUATION INSTRUCTIONS:
Please evaluate the response based on the following criteria:

1. Factual Accuracy (0-10):
   - Does the response contain only information that is supported by the context?
   - Are all citations [n] correctly used and do they reference relevant information?
   - Are there any statements that contradict the provided context?

2. Completeness (0-10):
   - Does the response fully address the user's query?
   - Are there important aspects of the query that were not addressed?
   - Does the response include all relevant information from the context?

3. Relevance (0-10):
   - How directly does the response address the user's query?
   - Is there irrelevant information included in the response?
   - Is the response focused on what the user was asking about?

4. Hallucination Detection:
   - Identify any statements in the response that are not supported by the provided context.
   - For each potential hallucination, provide the statement and explain why it's not supported.

5. Overall Quality (0-10):
   - Considering all factors, what is the overall quality of the response?
   - Is the response well-structured and easy to understand?
   - Does it provide value to the user?

6. Strengths and Weaknesses:
   - List the main strengths of the response.
   - List the main weaknesses of the response.

7. Improvement Suggestions:
   - Provide specific suggestions for how the response could be improved.

FORMAT YOUR EVALUATION AS FOLLOWS:
```json
{
  "factual_accuracy": <score 0-10>,
  "completeness": <score 0-10>,
  "relevance": <score 0-10>,
  "hallucination_detected": <true/false>,
  "hallucination_details": "<details about any hallucinations>",
  "overall_score": <score 0-10>,
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
  "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
}
```

IMPORTANT: Your evaluation must be fair, objective, and based solely on the provided context and query. The evaluation must be returned in the exact JSON format specified above.
"""
        
        return prompt
    
    def _create_system_prompt(self) -> str:
        """
        Create a system prompt for response evaluation
        
        Returns:
            System prompt
        """
        return """You are a response evaluator for a Retrieval-Augmented Generation (RAG) system.

Your role is to critically evaluate responses based on factual accuracy, completeness, relevance, and overall quality.

GUIDELINES:
1. Be objective and fair in your evaluation.
2. Base your assessment solely on the provided context, sources, and query.
3. Check for hallucinations - statements that are not supported by the provided context.
4. Verify that citations are used correctly and reference relevant information.
5. Assess whether the response fully addresses the user's query.
6. Evaluate the structure and clarity of the response.
7. Provide constructive feedback and specific suggestions for improvement.
8. Use the full range of scores (0-10) appropriately:
   - 0-2: Very poor, major issues
   - 3-4: Poor, significant issues
   - 5-6: Average, some issues
   - 7-8: Good, minor issues
   - 9-10: Excellent, minimal to no issues
9. Format your evaluation in the exact JSON format specified in the prompt.
10. Be thorough and detailed in your evaluation, especially when identifying hallucinations or weaknesses.
"""
    
    def _parse_evaluation(self, evaluation_text: str) -> Dict[str, Any]:
        """
        Parse the evaluation response from the LLM
        
        Args:
            evaluation_text: Raw evaluation text from the LLM
            
        Returns:
            Parsed evaluation results
        """
        # Extract JSON from the response
        try:
            # Look for JSON block in markdown format
            json_match = re.search(r'```(?:json)?\s*({\s*".*})\s*```', evaluation_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without markdown formatting
                json_match = re.search(r'({[\s\S]*"improvement_suggestions"[\s\S]*})', evaluation_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Fallback: assume the entire text might be JSON
                    json_str = evaluation_text
            
            # Parse the JSON
            evaluation = json.loads(json_str)
            
            # Ensure all required fields are present
            required_fields = [
                "factual_accuracy", "completeness", "relevance", 
                "hallucination_detected", "hallucination_details", 
                "overall_score", "strengths", "weaknesses", 
                "improvement_suggestions"
            ]
            
            for field in required_fields:
                if field not in evaluation:
                    if field in ["strengths", "weaknesses", "improvement_suggestions"]:
                        evaluation[field] = []
                    elif field in ["factual_accuracy", "completeness", "relevance", "overall_score"]:
                        evaluation[field] = 0
                    elif field == "hallucination_detected":
                        evaluation[field] = True
                    else:
                        evaluation[field] = "Not provided"
            
            return evaluation
        except Exception as e:
            self.logger.error(f"Error parsing evaluation: {str(e)}")
            
            # Return a default evaluation
            return {
                "factual_accuracy": 0,
                "completeness": 0,
                "relevance": 0,
                "hallucination_detected": True,
                "hallucination_details": f"Failed to parse evaluation: {str(e)}",
                "overall_score": 0,
                "strengths": [],
                "weaknesses": [f"Failed to parse evaluation: {str(e)}"],
                "improvement_suggestions": ["Unable to provide suggestions due to parsing failure"]
            }