"""
ResponseSynthesizer - Synthesizes responses from retrieval results and tool outputs
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class ResponseSynthesizer:
    """
    Synthesizes responses from retrieval results and tool outputs
    
    The ResponseSynthesizer is responsible for combining retrieval results and tool outputs
    into coherent, well-structured responses with proper source attribution. It uses the
    LLM to generate responses based on the available context and ensures that the responses
    are accurate, complete, and properly formatted.
    """
    
    def __init__(
        self,
        llm_provider,
        process_logger = None
    ):
        """
        Initialize the response synthesizer
        
        Args:
            llm_provider: LLM provider for generating responses
            process_logger: ProcessLogger instance (optional)
        """
        self.llm_provider = llm_provider
        self.process_logger = process_logger
        self.logger = logging.getLogger("app.rag.response_synthesizer")
    
    async def synthesize(
        self,
        query: str,
        query_id: str,
        context: str,
        sources: List[Dict[str, Any]],
        execution_result: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize a response from retrieval results and tool outputs
        
        Args:
            query: Original user query
            query_id: Unique query ID
            context: Retrieved context from documents
            sources: List of source information for citation
            execution_result: Result of plan execution (optional)
            conversation_context: Conversation history (optional)
            system_prompt: Custom system prompt (optional)
            model_parameters: Custom model parameters (optional)
            
        Returns:
            Dictionary containing:
                - response: Synthesized response text
                - sources: List of sources used in the response
                - execution_time: Time taken to synthesize the response
        """
        start_time = time.time()
        self.logger.info(f"Synthesizing response for query: {query}")
        
        # Log the start of response synthesis
        if self.process_logger:
            self.process_logger.log_step(
                query_id=query_id,
                step_name="response_synthesis_start",
                step_data={
                    "query": query,
                    "context_length": len(context),
                    "sources_count": len(sources),
                    "has_execution_result": execution_result is not None
                }
            )
        
        # Create the synthesis prompt
        prompt = self._create_synthesis_prompt(
            query=query,
            context=context,
            sources=sources,
            execution_result=execution_result,
            conversation_context=conversation_context
        )
        
        # Create or use the provided system prompt
        if not system_prompt:
            system_prompt = self._create_system_prompt()
        
        # Generate the response using the LLM
        try:
            response = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                parameters=model_parameters or {}
            )
            
            synthesized_response = response.get("response", "")
            
            # Extract and validate sources used in the response
            used_sources = self._extract_used_sources(synthesized_response, sources)
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Response synthesis completed in {elapsed_time:.2f}s")
            
            # Log the completion of response synthesis
            if self.process_logger:
                self.process_logger.log_step(
                    query_id=query_id,
                    step_name="response_synthesis_complete",
                    step_data={
                        "response_length": len(synthesized_response),
                        "used_sources_count": len(used_sources),
                        "execution_time": elapsed_time
                    }
                )
            
            return {
                "response": synthesized_response,
                "sources": used_sources,
                "execution_time": elapsed_time
            }
        except Exception as e:
            self.logger.error(f"Error synthesizing response: {str(e)}")
            
            # Log the error
            if self.process_logger:
                self.process_logger.log_step(
                    query_id=query_id,
                    step_name="response_synthesis_error",
                    step_data={
                        "error": str(e)
                    }
                )
            
            # Return a fallback response
            return {
                "response": f"I encountered an error while generating a response: {str(e)}",
                "sources": [],
                "execution_time": time.time() - start_time
            }
    
    def _create_synthesis_prompt(
        self,
        query: str,
        context: str,
        sources: List[Dict[str, Any]],
        execution_result: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None
    ) -> str:
        """
        Create a prompt for response synthesis
        
        Args:
            query: Original user query
            context: Retrieved context from documents
            sources: List of source information for citation
            execution_result: Result of plan execution (optional)
            conversation_context: Conversation history (optional)
            
        Returns:
            Synthesis prompt
        """
        prompt = f"""
You are synthesizing a response to the following query:

USER QUERY: {query}

"""
        
        # Add conversation context if available
        if conversation_context:
            prompt += f"""
CONVERSATION CONTEXT:
{conversation_context}

"""
        
        # Add retrieved context if available
        if context:
            prompt += f"""
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
        
        # Add instructions for response synthesis
        prompt += """
INSTRUCTIONS:
1. Synthesize a comprehensive response to the user's query using the provided information.
2. When using information from the retrieved context, cite the sources using the format [n] where n is the source number.
3. If the context doesn't contain the answer, clearly state that the information is not available in the provided documents.
4. If execution results are available, incorporate them into your response.
5. Ensure your response is well-structured, clear, and directly addresses the user's query.
6. Do not include phrases like "Based on the provided context" or "According to the retrieved information" - just provide the answer directly.
7. Format your response appropriately with headings, bullet points, or numbered lists as needed for clarity.
8. If you need to use your general knowledge because the context is insufficient, clearly indicate this by stating: "However, generally speaking..."
"""
        
        return prompt
    
    def _create_system_prompt(self) -> str:
        """
        Create a system prompt for response synthesis
        
        Returns:
            System prompt
        """
        return """You are a response synthesizer for a Retrieval-Augmented Generation (RAG) system.

Your role is to create comprehensive, accurate responses based on the provided context, sources, and execution results.

GUIDELINES:
1. Always prioritize information from the provided context and execution results.
2. Cite sources properly using the [n] format when using information from the retrieved context.
3. Be clear and direct in your responses - don't use phrases like "Based on the provided context" or "According to the retrieved information".
4. Structure your responses logically with appropriate formatting (headings, bullet points, etc.) for clarity.
5. If the context doesn't contain the answer, explicitly state that the information is not available in the provided documents.
6. If you need to use your general knowledge because the context is insufficient, clearly indicate this by stating: "However, generally speaking..."
7. Never fabricate information or citations.
8. Ensure your response directly addresses the user's query.
9. If execution results are available, incorporate them seamlessly into your response.
10. Maintain a professional, helpful tone throughout your response.
"""
    
    def _extract_used_sources(
        self,
        response: str,
        available_sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract sources that were actually used in the response
        
        Args:
            response: Synthesized response
            available_sources: List of available sources
            
        Returns:
            List of sources used in the response
        """
        used_sources = []
        used_indices = set()
        
        # Extract source citations from the response (format: [n])
        import re
        citation_pattern = r'\[(\d+)\]'
        citations = re.findall(citation_pattern, response)
        
        # Convert to integers and remove duplicates
        for citation in citations:
            try:
                index = int(citation)
                used_indices.add(index)
            except ValueError:
                continue
        
        # Collect the used sources
        for index in used_indices:
            if 1 <= index <= len(available_sources):
                used_sources.append(available_sources[index - 1])
        
        return used_sources