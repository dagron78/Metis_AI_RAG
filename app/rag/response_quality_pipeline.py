"""
ResponseQualityPipeline - Integrates response quality components into a pipeline
"""
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from app.rag.response_synthesizer import ResponseSynthesizer
from app.rag.response_evaluator import ResponseEvaluator
from app.rag.response_refiner import ResponseRefiner
from app.rag.audit_report_generator import AuditReportGenerator
from app.rag.process_logger import ProcessLogger

class ResponseQualityPipeline:
    """
    Integrates response quality components into a pipeline
    
    The ResponseQualityPipeline combines the ResponseSynthesizer, ResponseEvaluator,
    ResponseRefiner, and AuditReportGenerator into a cohesive pipeline for generating
    high-quality responses with proper evaluation, refinement, and auditing.
    """
    
    def __init__(
        self,
        llm_provider,
        process_logger: Optional[ProcessLogger] = None,
        max_refinement_iterations: int = 2,
        quality_threshold: float = 8.0,
        enable_audit_reports: bool = True
    ):
        """
        Initialize the response quality pipeline
        
        Args:
            llm_provider: LLM provider for generating responses
            process_logger: ProcessLogger instance (optional)
            max_refinement_iterations: Maximum number of refinement iterations
            quality_threshold: Minimum quality score to accept a response (0-10)
            enable_audit_reports: Whether to generate audit reports
        """
        self.llm_provider = llm_provider
        self.process_logger = process_logger
        self.max_refinement_iterations = max_refinement_iterations
        self.quality_threshold = quality_threshold
        self.enable_audit_reports = enable_audit_reports
        
        # Initialize components
        self.synthesizer = ResponseSynthesizer(
            llm_provider=llm_provider,
            process_logger=process_logger
        )
        
        self.evaluator = ResponseEvaluator(
            llm_provider=llm_provider,
            process_logger=process_logger
        )
        
        self.refiner = ResponseRefiner(
            llm_provider=llm_provider,
            process_logger=process_logger,
            max_refinement_iterations=max_refinement_iterations
        )
        
        if enable_audit_reports and process_logger:
            self.audit_report_generator = AuditReportGenerator(
                process_logger=process_logger,
                llm_provider=llm_provider
            )
        else:
            self.audit_report_generator = None
        
        self.logger = logging.getLogger("app.rag.response_quality_pipeline")
    
    async def process(
        self,
        query: str,
        context: str,
        sources: List[Dict[str, Any]],
        execution_result: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_parameters: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query through the response quality pipeline
        
        Args:
            query: User query
            context: Retrieved context from documents
            sources: List of source information for citation
            execution_result: Result of plan execution (optional)
            conversation_context: Conversation history (optional)
            system_prompt: Custom system prompt (optional)
            model_parameters: Custom model parameters (optional)
            query_id: Unique query ID (optional, will be generated if not provided)
            
        Returns:
            Dictionary containing:
                - response: Final response text
                - sources: List of sources used in the response
                - evaluation: Evaluation results
                - audit_report: Audit report (if enabled)
                - execution_time: Total execution time
        """
        start_time = time.time()
        
        # Generate a query ID if not provided
        if not query_id:
            query_id = str(uuid.uuid4())
        
        # Start process logging
        if self.process_logger:
            self.process_logger.start_process(query_id=query_id, query=query)
            self.process_logger.log_step(
                query_id=query_id,
                step_name="response_quality_pipeline_start",
                step_data={
                    "query": query,
                    "context_length": len(context),
                    "sources_count": len(sources),
                    "has_execution_result": execution_result is not None,
                    "has_conversation_context": conversation_context is not None
                }
            )
        
        self.logger.info(f"Starting response quality pipeline for query: {query}")
        
        # Step 1: Synthesize initial response
        synthesis_result = await self.synthesizer.synthesize(
            query=query,
            query_id=query_id,
            context=context,
            sources=sources,
            execution_result=execution_result,
            conversation_context=conversation_context,
            system_prompt=system_prompt,
            model_parameters=model_parameters
        )
        
        response = synthesis_result["response"]
        used_sources = synthesis_result["sources"]
        
        self.logger.info(f"Initial response synthesized, length: {len(response)}")
        
        # Step 2: Evaluate the response
        evaluation_result = await self.evaluator.evaluate(
            query=query,
            query_id=query_id,
            response=response,
            context=context,
            sources=sources,
            execution_result=execution_result
        )
        
        overall_score = evaluation_result.get("overall_score", 0)
        hallucination_detected = evaluation_result.get("hallucination_detected", False)
        
        self.logger.info(f"Response evaluated, overall score: {overall_score}, hallucinations: {hallucination_detected}")
        
        # Step 3: Refine the response if needed
        current_response = response
        current_evaluation = evaluation_result
        refinement_iterations = 0
        
        # Refine if the quality is below threshold or hallucinations are detected
        if overall_score < self.quality_threshold or hallucination_detected:
            self.logger.info(f"Response quality below threshold ({overall_score} < {self.quality_threshold}) or hallucinations detected, refining...")
            
            # Iterative refinement
            for iteration in range(1, self.max_refinement_iterations + 1):
                refinement_result = await self.refiner.refine(
                    query=query,
                    query_id=query_id,
                    response=current_response,
                    evaluation=current_evaluation,
                    context=context,
                    sources=sources,
                    execution_result=execution_result,
                    iteration=iteration
                )
                
                # Update current response and re-evaluate
                current_response = refinement_result["refined_response"]
                refinement_iterations += 1
                
                # Re-evaluate the refined response
                current_evaluation = await self.evaluator.evaluate(
                    query=query,
                    query_id=query_id,
                    response=current_response,
                    context=context,
                    sources=sources,
                    execution_result=execution_result
                )
                
                new_score = current_evaluation.get("overall_score", 0)
                new_hallucination = current_evaluation.get("hallucination_detected", False)
                
                self.logger.info(f"Refinement iteration {iteration}, new score: {new_score}, hallucinations: {new_hallucination}")
                
                # Stop if quality is good enough
                if new_score >= self.quality_threshold and not new_hallucination:
                    self.logger.info(f"Refinement successful after {iteration} iterations")
                    break
        
        # Step 4: Generate audit report if enabled
        audit_report = None
        if self.enable_audit_reports and self.audit_report_generator and self.process_logger:
            try:
                self.logger.info(f"Generating audit report for query {query_id}")
                audit_report = await self.audit_report_generator.generate_report(
                    query_id=query_id,
                    include_llm_analysis=True
                )
            except Exception as e:
                self.logger.error(f"Error generating audit report: {str(e)}")
        
        # Log the final response
        if self.process_logger:
            self.process_logger.log_final_response(
                query_id=query_id,
                response=current_response,
                metadata={
                    "evaluation_score": current_evaluation.get("overall_score", 0),
                    "refinement_iterations": refinement_iterations,
                    "sources_count": len(used_sources)
                }
            )
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Response quality pipeline completed in {elapsed_time:.2f}s")
        
        # Log the completion of the pipeline
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name="response_quality_pipeline_complete",
                step_data={
                    "response_length": len(current_response),
                    "final_score": current_evaluation.get("overall_score", 0),
                    "refinement_iterations": refinement_iterations,
                    "execution_time": elapsed_time
                }
            )
        
        # Return the final result
        return {
            "query_id": query_id,
            "response": current_response,
            "sources": used_sources,
            "evaluation": current_evaluation,
            "refinement_iterations": refinement_iterations,
            "audit_report": audit_report,
            "execution_time": elapsed_time
        }