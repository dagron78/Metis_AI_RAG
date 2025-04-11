"""
Retrieval Judge - LLM-based agent that analyzes queries and retrieved chunks to improve retrieval quality
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional

from app.models.document import Chunk
from app.rag.ollama_client import OllamaClient
from app.core.config import SETTINGS

logger = logging.getLogger("app.rag.agents.retrieval_judge")

class RetrievalJudge:
    """
    LLM-based agent that analyzes queries and retrieved chunks to improve retrieval quality
    """
    def __init__(self, ollama_client: Optional[OllamaClient] = None, model: str = None):
        model = model or SETTINGS.retrieval_judge_model
        self.ollama_client = ollama_client or OllamaClient()
        self.model = model
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query and recommend retrieval parameters
        
        Returns:
            Dict with keys:
            - complexity: The assessed complexity of the query (simple, moderate, complex)
            - parameters: Dict of recommended retrieval parameters (k, threshold, etc.)
            - justification: Explanation of the recommendation
        """
        # Create prompt for the LLM
        prompt = self._create_query_analysis_prompt(query)
        
        # Get recommendation from LLM
        response = await self.ollama_client.generate(
            prompt=prompt,
            model=self.model,
            stream=False
        )
        
        # Parse the response
        analysis = self._parse_query_analysis(response.get("response", ""))
        
        logger.info(f"Retrieval Judge analyzed query complexity as '{analysis.get('complexity', 'unknown')}' with k={analysis.get('parameters', {}).get('k', 'default')}")
        
        return analysis
    
    async def evaluate_chunks(self, query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate retrieved chunks for relevance to the query
        
        Args:
            query: The user query
            chunks: List of chunks from the vector store search results
            
        Returns:
            Dict with keys:
            - relevance_scores: Dict mapping chunk IDs to relevance scores (0-1)
            - needs_refinement: Boolean indicating if query refinement is needed
            - justification: Explanation of the evaluation
        """
        # Extract a sample of chunks to avoid exceeding context window
        chunks_sample = self._extract_chunks_sample(chunks)
        
        # Create prompt for the LLM
        prompt = self._create_chunks_evaluation_prompt(query, chunks_sample)
        
        # Get evaluation from LLM
        response = await self.ollama_client.generate(
            prompt=prompt,
            model=self.model,
            stream=False
        )
        
        # Parse the response
        evaluation = self._parse_chunks_evaluation(response.get("response", ""), chunks)
        
        logger.info(f"Retrieval Judge evaluated {len(chunks)} chunks, needs_refinement={evaluation.get('needs_refinement', False)}")
        
        return evaluation
    
    async def refine_query(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Refine a query based on retrieved chunks to improve retrieval precision
        
        Args:
            query: The original user query
            chunks: List of chunks from the initial retrieval
            
        Returns:
            Refined query string
        """
        # Extract a sample of chunks to avoid exceeding context window
        chunks_sample = self._extract_chunks_sample(chunks)
        
        # Create prompt for the LLM
        prompt = self._create_query_refinement_prompt(query, chunks_sample)
        
        # Get refined query from LLM
        response = await self.ollama_client.generate(
            prompt=prompt,
            model=self.model,
            stream=False
        )
        
        # Parse the response
        refined_query = self._parse_refined_query(response.get("response", ""), query)
        
        logger.info(f"Retrieval Judge refined query from '{query}' to '{refined_query}'")
        
        return refined_query
    
    async def optimize_context(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize the assembly of chunks into a context for the LLM
        
        Args:
            query: The user query
            chunks: List of chunks from the vector store search results
            
        Returns:
            Reordered and filtered list of chunks optimized for context assembly
        """
        # If we have too few chunks, no need to optimize
        if len(chunks) <= 3:
            logger.info(f"Too few chunks ({len(chunks)}) to optimize, returning as is")
            return chunks
        
        # Extract a sample of chunks to avoid exceeding context window
        chunks_sample = self._extract_chunks_sample(chunks)
        
        # Create prompt for the LLM
        prompt = self._create_context_optimization_prompt(query, chunks_sample)
        
        # Get optimization from LLM
        response = await self.ollama_client.generate(
            prompt=prompt,
            model=self.model,
            stream=False
        )
        
        # Parse the response
        optimized_chunks = self._parse_context_optimization(response.get("response", ""), chunks)
        
        logger.info(f"Retrieval Judge optimized context from {len(chunks)} to {len(optimized_chunks)} chunks")
        
        return optimized_chunks
    
    def _extract_chunks_sample(self, chunks: List[Dict[str, Any]], max_chunks: int = 5, max_length: int = 5000) -> List[Dict[str, Any]]:
        """
        Extract a representative sample of chunks to avoid exceeding context window
        
        Args:
            chunks: List of chunks from the vector store search results
            max_chunks: Maximum number of chunks to include
            max_length: Maximum total length of chunk content
            
        Returns:
            List of sample chunks with truncated content if necessary
        """
        if not chunks:
            return []
        
        # Sort chunks by distance (if available) to prioritize most relevant chunks
        sorted_chunks = sorted(
            chunks, 
            key=lambda x: x.get("distance", 1.0) if x.get("distance") is not None else 1.0
        )
        
        # Take top chunks
        sample_chunks = sorted_chunks[:max_chunks]
        
        # Calculate total content length
        total_length = sum(len(chunk.get("content", "")) for chunk in sample_chunks)
        
        # If total length exceeds max_length, truncate each chunk proportionally
        if total_length > max_length:
            # Calculate scaling factor
            scale_factor = max_length / total_length
            
            # Truncate each chunk
            for chunk in sample_chunks:
                content = chunk.get("content", "")
                max_chunk_length = int(len(content) * scale_factor)
                if len(content) > max_chunk_length:
                    chunk["content"] = content[:max_chunk_length] + "..."
        
        return sample_chunks
    
    def _create_query_analysis_prompt(self, query: str) -> str:
        """Create a prompt for the LLM to analyze the query"""
        return f"""You are a query analysis expert for a RAG (Retrieval Augmented Generation) system. Your task is to analyze the following user query and recommend optimal retrieval parameters.

User Query: {query}

Analyze the query complexity, specificity, and intent. Consider:
1. Is this a simple factual question or a complex analytical query?
2. Does it require specific knowledge from documents or general knowledge?
3. Is it ambiguous or clear in its intent?
4. Does it contain multiple sub-questions or a single focused question?
5. Would it benefit from a broader or narrower retrieval approach?

Based on your analysis, recommend retrieval parameters:
- k: Number of chunks to retrieve (5-15)
- threshold: Relevance threshold for filtering (0.0-1.0)
- reranking: Whether to apply reranking (true/false)

Output your analysis in JSON format:
{{
    "complexity": "...",  // One of: simple, moderate, complex
    "parameters": {{
        "k": ...,  // Recommended number of chunks to retrieve
        "threshold": ...,  // Recommended relevance threshold
        "reranking": ...  // Whether to apply reranking (true/false)
    }},
    "justification": "..." // Explanation of your reasoning
}}
"""
    
    def _create_chunks_evaluation_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Create a prompt for the LLM to evaluate retrieved chunks"""
        chunks_text = ""
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            chunks_text += f"[{i+1}] Source: {filename}\n{content}\n\n"
        
        return f"""You are a relevance evaluation expert for a RAG (Retrieval Augmented Generation) system. Your task is to evaluate the relevance of retrieved chunks to the user's query.

User Query: {query}

Retrieved Chunks:
{chunks_text}

Evaluate each chunk's relevance to the query on a scale of 0.0 to 1.0, where:
- 1.0: Directly answers the query with high precision
- 0.7-0.9: Contains information highly relevant to the query
- 0.4-0.6: Contains information somewhat relevant to the query
- 0.1-0.3: Contains information tangentially related to the query
- 0.0: Contains no information relevant to the query

Also determine if the query needs refinement based on the retrieved chunks:
- If the chunks are all low relevance, the query might need refinement
- If the chunks contain relevant information but are too broad, the query might need refinement
- If the chunks contain contradictory information, the query might need refinement

Output your evaluation in JSON format:
{{
    "relevance_scores": {{
        "1": 0.8,  // Relevance score for chunk 1
        "2": 0.5,  // Relevance score for chunk 2
        ...
    }},
    "needs_refinement": true/false,  // Whether the query needs refinement
    "justification": "..." // Explanation of your evaluation
}}
"""
    
    def _create_query_refinement_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Create a prompt for the LLM to refine the query"""
        chunks_text = ""
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            chunks_text += f"[{i+1}] Source: {filename}\n{content}\n\n"
        
        return f"""You are a query refinement expert for a RAG (Retrieval Augmented Generation) system. Your task is to refine the user's query based on the initially retrieved chunks to improve retrieval precision.

Original User Query: {query}

Initially Retrieved Chunks:
{chunks_text}

Analyze the query and the retrieved chunks to identify:
1. Ambiguities in the original query that could be clarified
2. Missing specific terms that would improve retrieval
3. Domain-specific terminology from the chunks that could be incorporated
4. Potential reformulations that would better match the document content

Create a refined query that:
- Maintains the original intent of the user's question
- Adds specificity based on the retrieved chunks
- Incorporates relevant terminology from the documents
- Is formulated to maximize the chance of retrieving more relevant chunks

Output your refined query as plain text without any JSON formatting or explanations. The output should be ONLY the refined query text that can be directly used for retrieval.
"""
    
    def _create_context_optimization_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Create a prompt for the LLM to optimize context assembly"""
        chunks_text = ""
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            chunks_text += f"[{i+1}] Source: {filename}\n{content}\n\n"
        
        return f"""You are a context optimization expert for a RAG (Retrieval Augmented Generation) system. Your task is to optimize the assembly of retrieved chunks into a context for the LLM.

User Query: {query}

Retrieved Chunks:
{chunks_text}

Analyze the chunks and determine the optimal order and selection for providing context to the LLM. Consider:
1. Relevance to the query
2. Information completeness
3. Logical flow of information
4. Removal of redundant information
5. Inclusion of diverse perspectives if available

Output your optimization in JSON format:
{{
    "optimized_order": [3, 1, 5, ...],  // Chunk numbers in optimal order
    "excluded_chunks": [2, 4, ...],  // Chunk numbers to exclude (if any)
    "justification": "..." // Explanation of your optimization
}}
"""
    
    def _parse_query_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response to extract the query analysis"""
        try:
            # Extract JSON from the response
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                json_str = json_match.group(1)
                analysis = json.loads(json_str)
                
                # Validate the analysis
                if "complexity" not in analysis:
                    raise ValueError("Missing 'complexity' in analysis")
                
                # Validate complexity is one of the allowed values
                allowed_complexity = ["simple", "moderate", "complex"]
                if analysis["complexity"] not in allowed_complexity:
                    logger.warning(f"Invalid complexity '{analysis['complexity']}', falling back to 'moderate'")
                    analysis["complexity"] = "moderate"
                
                # Set defaults if missing
                if "parameters" not in analysis:
                    analysis["parameters"] = {}
                if "k" not in analysis["parameters"]:
                    analysis["parameters"]["k"] = 10
                if "threshold" not in analysis["parameters"]:
                    analysis["parameters"]["threshold"] = 0.4
                if "reranking" not in analysis["parameters"]:
                    analysis["parameters"]["reranking"] = True
                
                return analysis
            else:
                raise ValueError("Could not find JSON in response")
        except Exception as e:
            logger.error(f"Error parsing query analysis: {str(e)}")
            # Return default analysis
            return {
                "complexity": "moderate",
                "parameters": {
                    "k": 10,
                    "threshold": 0.4,
                    "reranking": True
                },
                "justification": "Failed to parse LLM recommendation, using default parameters."
            }
    
    def _parse_chunks_evaluation(self, response_text: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse the LLM response to extract the chunks evaluation"""
        try:
            # Extract JSON from the response
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                json_str = json_match.group(1)
                evaluation = json.loads(json_str)
                
                # Validate the evaluation
                if "relevance_scores" not in evaluation:
                    raise ValueError("Missing 'relevance_scores' in evaluation")
                
                # Convert string keys to integers if needed
                relevance_scores = {}
                for key, value in evaluation["relevance_scores"].items():
                    # Convert key to int if it's a string representation of an int
                    try:
                        idx = int(key)
                        # Map the score to the actual chunk ID
                        if 1 <= idx <= len(chunks):
                            chunk_id = chunks[idx-1].get("chunk_id")
                            relevance_scores[chunk_id] = value
                    except (ValueError, IndexError):
                        # If key can't be converted to int or is out of range, use as is
                        relevance_scores[key] = value
                
                evaluation["relevance_scores"] = relevance_scores
                
                # Set defaults if missing
                if "needs_refinement" not in evaluation:
                    evaluation["needs_refinement"] = False
                
                return evaluation
            else:
                raise ValueError("Could not find JSON in response")
        except Exception as e:
            logger.error(f"Error parsing chunks evaluation: {str(e)}")
            # Return default evaluation
            default_scores = {}
            for chunk in chunks:
                chunk_id = chunk.get("chunk_id")
                if chunk_id:
                    default_scores[chunk_id] = 0.5
            
            return {
                "relevance_scores": default_scores,
                "needs_refinement": False,
                "justification": "Failed to parse LLM evaluation, using default relevance scores."
            }
    
    def _parse_refined_query(self, response_text: str, original_query: str) -> str:
        """Parse the LLM response to extract the refined query"""
        try:
            # Clean up the response text
            refined_query = response_text.strip()
            
            # If the response is empty or too short, return the original query
            if not refined_query or len(refined_query) < 5:
                logger.warning("Refined query is empty or too short, using original query")
                return original_query
            
            # If the response is too long (likely includes explanations), try to extract just the query
            if len(refined_query) > len(original_query) * 3:
                # Look for patterns that might indicate the actual query
                query_patterns = [
                    r'(?:refined query|new query|improved query)[:\s]+(.+?)(?:\n|$)',
                    r'(?:query|q)[:\s]+(.+?)(?:\n|$)',
                    r'"(.+?)"'
                ]
                
                for pattern in query_patterns:
                    match = re.search(pattern, refined_query, re.IGNORECASE)
                    if match:
                        extracted_query = match.group(1).strip()
                        if extracted_query and len(extracted_query) >= 5:
                            logger.info(f"Extracted refined query using pattern: {pattern}")
                            return extracted_query
            
            return refined_query
        except Exception as e:
            logger.error(f"Error parsing refined query: {str(e)}")
            return original_query
    
    def _parse_context_optimization(self, response_text: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse the LLM response to extract the context optimization"""
        try:
            # Extract JSON from the response
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                json_str = json_match.group(1)
                optimization = json.loads(json_str)
                
                # Validate the optimization
                if "optimized_order" not in optimization:
                    raise ValueError("Missing 'optimized_order' in optimization")
                
                # Get the optimized order
                optimized_order = optimization["optimized_order"]
                
                # Get excluded chunks
                excluded_chunks = optimization.get("excluded_chunks", [])
                
                # Create the optimized chunks list
                optimized_chunks = []
                for idx in optimized_order:
                    # Convert to 0-based index if needed
                    try:
                        idx_0based = int(idx) - 1
                        if 0 <= idx_0based < len(chunks) and idx_0based not in excluded_chunks:
                            optimized_chunks.append(chunks[idx_0based])
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid chunk index in optimized order: {idx}")
                
                # If no valid chunks were found, return the original chunks
                if not optimized_chunks:
                    logger.warning("No valid chunks in optimized order, returning original chunks")
                    return chunks
                
                return optimized_chunks
            else:
                raise ValueError("Could not find JSON in response")
        except Exception as e:
            logger.error(f"Error parsing context optimization: {str(e)}")
            # Return the original chunks
            return chunks