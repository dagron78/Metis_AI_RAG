"""
Context Builder Component for RAG Engine

This module provides the ContextBuilder class for assembling context
from retrieved documents in the RAG Engine.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
import re

from app.rag.engine.utils.error_handler import safe_execute_async
from app.rag.engine.utils.timing import async_timing_context, TimingStats

logger = logging.getLogger("app.rag.engine.components.context_builder")

class ContextBuilder:
    """
    Component for assembling context from retrieved documents
    
    This component is responsible for formatting and assembling context
    from retrieved documents, including handling citations and formatting.
    """
    
    def __init__(self):
        """Initialize the context builder"""
        self.timing_stats = TimingStats()
    
    async def build_context(self,
                           documents: List[Dict[str, Any]],
                           query: str,
                           max_context_length: int = 8000) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build context from retrieved documents
        
        Args:
            documents: Retrieved documents
            query: User query
            max_context_length: Maximum context length
            
        Returns:
            Tuple of (context, sources)
        """
        self.timing_stats.start("total")
        
        try:
            # Check if there are any documents
            if not documents:
                logger.info("No documents provided for context building")
                return "", []
            
            # Format documents into context pieces
            async with async_timing_context("format_documents", self.timing_stats):
                context_pieces, sources = self._format_documents(documents)
            
            # Assemble context
            async with async_timing_context("assemble_context", self.timing_stats):
                context = self._assemble_context(context_pieces, max_context_length)
            
            # Log context stats
            self.timing_stats.stop("total")
            logger.info(f"Built context with {len(documents)} documents in {self.timing_stats.get_timing('total'):.2f}s")
            logger.info(f"Context length: {len(context)} characters")
            
            return context, sources
        
        except Exception as e:
            self.timing_stats.stop("total")
            logger.error(f"Error building context: {str(e)}")
            return "", []
    
    def _format_documents(self, documents: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Format documents into context pieces
        
        Args:
            documents: Retrieved documents
            
        Returns:
            Tuple of (context_pieces, sources)
        """
        context_pieces = []
        sources = []
        
        for i, doc in enumerate(documents):
            # Extract metadata
            metadata = doc.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            tags = metadata.get("tags", [])
            folder = metadata.get("folder", "/")
            
            # Format the context piece with metadata
            context_piece = f"[{i+1}] Source: {filename}, Tags: {tags}, Folder: {folder}\n\n{doc.get('content', '')}"
            context_pieces.append(context_piece)
            
            # Create source info for citation
            source_info = {
                "document_id": doc.get("document_id", ""),
                "chunk_id": doc.get("chunk_id", ""),
                "relevance_score": doc.get("relevance_score", 0.0),
                "excerpt": doc.get("excerpt", ""),
                "metadata": metadata
            }
            
            sources.append(source_info)
        
        return context_pieces, sources
    
    def _assemble_context(self, context_pieces: List[str], max_context_length: int) -> str:
        """
        Assemble context from context pieces
        
        Args:
            context_pieces: Context pieces
            max_context_length: Maximum context length
            
        Returns:
            Assembled context
        """
        # Join all context pieces
        context = "\n\n".join(context_pieces)
        
        # Check if context is too long
        if len(context) > max_context_length:
            logger.warning(f"Context too long ({len(context)} chars), truncating to {max_context_length} chars")
            
            # Truncate context
            context = self._truncate_context(context, max_context_length)
        
        return context
    
    def _truncate_context(self, context: str, max_length: int) -> str:
        """
        Truncate context to maximum length
        
        Args:
            context: Context to truncate
            max_length: Maximum length
            
        Returns:
            Truncated context
        """
        # If context is already short enough, return it
        if len(context) <= max_length:
            return context
        
        # Split context into chunks by source
        chunks = re.split(r'(\[\d+\] Source:.*?\n\n)', context)
        
        # Recombine chunks until we reach the maximum length
        truncated_context = ""
        current_length = 0
        
        # Process chunks in pairs (header + content)
        for i in range(0, len(chunks) - 1, 2):
            if i + 1 >= len(chunks):
                break
            
            header = chunks[i]
            content = chunks[i + 1]
            
            # Check if adding this chunk would exceed the maximum length
            if current_length + len(header) + len(content) > max_length:
                # If this is the first chunk, we need to truncate it
                if current_length == 0:
                    available_length = max_length - len(header)
                    truncated_content = content[:available_length]
                    truncated_context = header + truncated_content
                
                # Otherwise, we've added enough chunks
                break
            
            # Add this chunk
            truncated_context += header + content
            current_length += len(header) + len(content)
        
        return truncated_context
    
    async def build_conversation_context(self,
                                        messages: List[Dict[str, Any]],
                                        max_messages: int = 10,
                                        max_length: int = 2000) -> str:
        """
        Build conversation context from messages
        
        Args:
            messages: Conversation messages
            max_messages: Maximum number of messages to include
            max_length: Maximum context length
            
        Returns:
            Conversation context
        """
        try:
            # Check if there are any messages
            if not messages:
                logger.info("No messages provided for conversation context building")
                return ""
            
            # Limit to recent messages
            recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
            
            # Format messages
            formatted_messages = []
            for msg in recent_messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                # Format based on role
                if role == "user":
                    formatted_messages.append(f"User: {content}")
                elif role == "assistant":
                    formatted_messages.append(f"Assistant: {content}")
                else:
                    formatted_messages.append(f"{role.capitalize()}: {content}")
            
            # Join messages
            conversation_context = "\n".join(formatted_messages)
            
            # Truncate if too long
            if len(conversation_context) > max_length:
                logger.warning(f"Conversation context too long ({len(conversation_context)} chars), truncating")
                
                # Keep the most recent messages that fit within the limit
                truncated_messages = []
                current_length = 0
                
                for msg in reversed(formatted_messages):
                    if current_length + len(msg) + 1 <= max_length:  # +1 for newline
                        truncated_messages.insert(0, msg)
                        current_length += len(msg) + 1
                    else:
                        break
                
                conversation_context = "\n".join(truncated_messages)
            
            return conversation_context
        
        except Exception as e:
            logger.error(f"Error building conversation context: {str(e)}")
            return ""
    
    def format_sources_for_prompt(self, sources: List[Dict[str, Any]], max_sources: int = 5) -> str:
        """
        Format sources for inclusion in a prompt
        
        Args:
            sources: Sources to format
            max_sources: Maximum number of sources to include
            
        Returns:
            Formatted sources
        """
        if not sources:
            return ""
        
        # Limit to top sources
        top_sources = sources[:max_sources]
        
        # Format sources
        formatted_sources = []
        for i, source in enumerate(top_sources):
            metadata = source.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            title = metadata.get("title", filename)
            
            excerpt = source.get("excerpt", "")
            if len(excerpt) > 100:
                excerpt = excerpt[:100] + "..."
            
            formatted_source = f"Source {i+1}: {title}\nExcerpt: {excerpt}"
            formatted_sources.append(formatted_source)
        
        return "\n\n".join(formatted_sources)
    
    def create_context_summary(self, context: str, max_length: int = 200) -> str:
        """
        Create a summary of the context
        
        Args:
            context: Context to summarize
            max_length: Maximum summary length
            
        Returns:
            Context summary
        """
        if not context:
            return ""
        
        # Count sources
        source_count = len(re.findall(r'\[\d+\] Source:', context))
        
        # Extract topics
        topics = set()
        for match in re.finditer(r'Tags: \[(.*?)\]', context):
            tags = match.group(1)
            if tags:
                for tag in re.findall(r"'([^']*)'", tags):
                    topics.add(tag)
        
        # Create summary
        summary = f"Context includes {source_count} sources"
        
        if topics:
            topic_list = ", ".join(list(topics)[:5])
            if len(topics) > 5:
                topic_list += f", and {len(topics) - 5} more"
            
            summary += f" covering topics: {topic_list}"
        
        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."
        
        return summary