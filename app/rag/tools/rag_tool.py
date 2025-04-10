"""
RAGTool - Tool for retrieving information using RAG
"""
import logging
import time
from typing import Any, Dict, List, Optional

from app.rag.tools.base import Tool
from app.rag.engine.rag_engine import RAGEngine

class RAGTool(Tool):
    """
    Tool for retrieving information using RAG
    
    This tool uses the RAG engine to retrieve information from the document store
    based on a query.
    """
    
    def __init__(self, rag_engine: RAGEngine):
        """
        Initialize the RAG tool
        
        Args:
            rag_engine: RAG engine instance
        """
        super().__init__(
            name="rag",
            description="Retrieves information from documents using RAG"
        )
        self.rag_engine = rag_engine
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the RAG tool
        
        Args:
            input_data: Dictionary containing:
                - query: Query string
                - top_k: Number of results to return (optional)
                - filters: Filters to apply (optional)
                
        Returns:
            Dictionary containing:
                - chunks: List of retrieved chunks
                - sources: List of source documents
                - execution_time: Time taken to execute the query
        """
        start_time = time.time()
        self.logger.info(f"Executing RAG query: {input_data.get('query')}")
        
        # Extract parameters
        query = input_data.get("query")
        top_k = input_data.get("top_k", 5)
        filters = input_data.get("filters", {})
        
        # Validate input
        if not query:
            error_msg = "Query is required"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        try:
            # Execute RAG query
            results = await self.rag_engine.retrieve(
                query=query,
                top_k=top_k,
                filters=filters
            )
            
            # Process results
            chunks = []
            sources = set()
            
            for result in results:
                chunks.append({
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0)
                })
                
                # Extract source document information
                doc_id = result.get("metadata", {}).get("document_id")
                if doc_id:
                    sources.add(doc_id)
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"RAG query completed in {elapsed_time:.2f}s. Found {len(chunks)} chunks from {len(sources)} sources")
            
            return {
                "chunks": chunks,
                "sources": list(sources),
                "execution_time": elapsed_time
            }
        except Exception as e:
            error_msg = f"Error executing RAG query: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Get the input schema for the RAG tool
        
        Returns:
            JSON Schema for tool input
        """
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query string"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 100
                },
                "filters": {
                    "type": "object",
                    "description": "Filters to apply to the search",
                    "additionalProperties": True
                }
            },
            "required": ["query"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the output schema for the RAG tool
        
        Returns:
            JSON Schema for tool output
        """
        return {
            "type": "object",
            "properties": {
                "chunks": {
                    "type": "array",
                    "description": "List of retrieved chunks",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Chunk content"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Chunk metadata"
                            },
                            "score": {
                                "type": "number",
                                "description": "Relevance score"
                            }
                        }
                    }
                },
                "sources": {
                    "type": "array",
                    "description": "List of source document IDs",
                    "items": {
                        "type": "string"
                    }
                },
                "execution_time": {
                    "type": "number",
                    "description": "Time taken to execute the query in seconds"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if the query failed"
                }
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """
        Get examples of RAG tool usage
        
        Returns:
            List of example input/output pairs
        """
        return [
            {
                "input": {
                    "query": "What is the capital of France?",
                    "top_k": 3
                },
                "output": {
                    "chunks": [
                        {
                            "content": "Paris is the capital and most populous city of France.",
                            "metadata": {
                                "document_id": "doc123",
                                "page": 1
                            },
                            "score": 0.92
                        },
                        {
                            "content": "France is a country in Western Europe. Its capital is Paris.",
                            "metadata": {
                                "document_id": "doc456",
                                "page": 5
                            },
                            "score": 0.85
                        }
                    ],
                    "sources": ["doc123", "doc456"],
                    "execution_time": 0.15
                }
            },
            {
                "input": {
                    "query": "Explain the process of photosynthesis",
                    "top_k": 5,
                    "filters": {
                        "document_type": "textbook",
                        "subject": "biology"
                    }
                },
                "output": {
                    "chunks": [
                        {
                            "content": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods with carbon dioxide and water.",
                            "metadata": {
                                "document_id": "bio101",
                                "page": 42
                            },
                            "score": 0.95
                        }
                    ],
                    "sources": ["bio101"],
                    "execution_time": 0.22
                }
            }
        ]