"""
QueryAnalyzer - Analyzes queries to determine their complexity and requirements
"""
import logging
import time
import re
import json
from typing import Dict, List, Any, Optional, Tuple

class QueryAnalyzer:
    """
    Analyzes queries to determine their complexity and requirements
    
    The QueryAnalyzer uses an LLM to analyze queries and determine:
    - Query complexity (simple vs. complex)
    - Required tools for answering the query
    - Potential sub-queries
    - Reasoning behind the analysis
    """
    
    def __init__(self, llm_provider):
        """
        Initialize the query analyzer
        
        Args:
            llm_provider: LLM provider for analysis
        """
        self.llm_provider = llm_provider
        self.logger = logging.getLogger("app.rag.query_analyzer")
    
    async def analyze(self, query: str,
                     chat_history: Optional[List[Tuple[str, str]]] = None) -> Dict[str, Any]:
        """
        Analyze a query to determine its complexity and requirements
        
        Args:
            query: Query string
            chat_history: Optional list of (user_message, ai_message) tuples
            
        Returns:
            Dict with keys:
            - complexity: "simple" or "complex"
            - requires_tools: list of required tools
            - sub_queries: list of potential sub-queries
            - reasoning: explanation of the analysis
        """
        start_time = time.time()
        self.logger.info(f"Analyzing query: {query}")
        
        prompt = self._create_analysis_prompt(query, chat_history)
        response = await self.llm_provider.generate(prompt=prompt)
        analysis = self._parse_analysis(response.get("response", ""))
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Query analysis completed in {elapsed_time:.2f}s. Complexity: {analysis.get('complexity')}")
        
        return analysis
    
    def _create_analysis_prompt(self, query: str,
                               chat_history: Optional[List[Tuple[str, str]]] = None) -> str:
        """
        Create a prompt for query analysis
        
        Args:
            query: Query string
            chat_history: Optional list of (user_message, ai_message) tuples
            
        Returns:
            Prompt string
        """
        # Format chat history if available
        history_str = ""
        if chat_history:
            history_lines = []
            for i, (user_msg, ai_msg) in enumerate(chat_history):
                history_lines.append(f"Turn {i+1}:")
                history_lines.append(f"User: {user_msg}")
                history_lines.append(f"AI: {ai_msg}")
            history_str = "\n".join(history_lines)

        return f"""
You are an expert query analyzer for a RAG (Retrieval-Augmented Generation) system. Your task is to analyze the following query, considering the preceding conversation history, and determine its complexity, required tools, and potential sub-queries.

Conversation History:
{history_str if history_str else "None"}

Current Query: "{query}"

Available tools:
1. rag - Retrieves information from documents using RAG
2. calculator - Performs mathematical calculations
3. database - Queries structured data from databases

Please analyze the query and provide your assessment in the following JSON format:
{{
  "complexity": "simple" or "complex",
  "requires_tools": ["tool1", "tool2", ...],
  "sub_queries": ["sub-query1", "sub-query2", ...],
  "reasoning": "Detailed explanation of your analysis"
}}

Where:
- "complexity" indicates whether the query is simple (can be answered with a single RAG lookup) or complex (requires multiple steps or tools)
- "requires_tools" lists the tools needed to answer the query
- "sub_queries" lists potential sub-queries if the main query needs to be broken down
- "reasoning" explains your analysis in detail

Analyze the query carefully, considering:
1. Does it require factual information retrieval? (use rag tool)
2. Does it involve calculations? (use calculator tool)
3. Does it need structured data lookup? (use database tool)
4. Does it require multiple steps or a combination of tools?
5. Would breaking it into sub-queries improve the response quality?
6. How does the conversation history affect the interpretation of the current query? Does the query refer back to previous turns (e.g., "like you mentioned before", "tell me more about that")?

Provide your analysis in valid JSON format.
"""
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract the analysis
        
        Args:
            response: LLM response string
            
        Returns:
            Dict with analysis results
        """
        # Try to extract JSON from the response
        try:
            # Look for JSON pattern in the response
            json_match = re.search(r'({[\s\S]*})', response)
            if json_match:
                analysis = json.loads(json_match.group(1))
                
                # Validate required fields
                if "complexity" in analysis and "requires_tools" in analysis:
                    return analysis
        except json.JSONDecodeError:
            self.logger.warning(f"Failed to parse JSON from response: {response}")
        
        # If JSON parsing fails, try to extract key information using regex
        complexity_match = re.search(r'complexity["\']?\s*:\s*["\']?(\w+)["\']?', response)
        tools_match = re.search(r'requires_tools["\']?\s*:\s*\[(.*?)\]', response)
        
        complexity = complexity_match.group(1) if complexity_match else "simple"
        
        tools = []
        if tools_match:
            tools_str = tools_match.group(1)
            tool_matches = re.findall(r'["\'](\w+)["\']', tools_str)
            tools = tool_matches if tool_matches else []
        
        # Default analysis if parsing fails
        return {
            "complexity": complexity,
            "requires_tools": tools,
            "sub_queries": [],
            "reasoning": "Extracted from LLM response with fallback parsing"
        }