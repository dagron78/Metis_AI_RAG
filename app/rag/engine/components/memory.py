"""
Memory Component for RAG Engine

This module provides the MemoryComponent class for handling
memory operations in the RAG Engine.
"""
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from uuid import UUID
import json

from app.rag.engine.utils.error_handler import MemoryError, safe_execute_async
from app.rag.engine.utils.timing import async_timing_context, TimingStats
from app.rag.engine.utils.query_processor import process_query

logger = logging.getLogger("app.rag.engine.components.memory")

class MemoryComponent:
    """
    Component for handling memory operations in the RAG Engine
    
    This component is responsible for storing, retrieving, and managing
    conversation memory, including short-term context and long-term memory.
    """
    
    def __init__(self, mem0_client=None, db=None):
        """
        Initialize the memory component
        
        Args:
            mem0_client: Mem0 client instance for long-term memory
            db: Database session for memory operations
        """
        self.mem0_client = mem0_client
        self.db = db
        self.timing_stats = TimingStats()
        self.conversation_memory = {}
    
    async def process_memory_operations(self,
                                       query: str,
                                       user_id: Optional[str] = None,
                                       conversation_id: Optional[str] = None) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Process memory operations in a query
        
        Args:
            query: User query
            user_id: User ID
            conversation_id: Conversation ID
            
        Returns:
            Tuple of (processed_query, memory_response, memory_operation)
        """
        self.timing_stats.start("total")
        
        try:
            # Process the query for memory operations
            processed_query, memory_response, memory_operation = await process_query(
                query=query,
                user_id=user_id,
                conversation_id=conversation_id,
                db=self.db
            )
            
            # Log memory operation
            if memory_operation:
                logger.info(f"Processed memory operation: {memory_operation}")
            
            self.timing_stats.stop("total")
            logger.info(f"Processed memory operations in {self.timing_stats.get_timing('total'):.2f}s")
            
            return processed_query, memory_response, memory_operation
        
        except Exception as e:
            self.timing_stats.stop("total")
            logger.error(f"Error processing memory operations: {str(e)}")
            raise MemoryError(f"Error processing memory operations: {str(e)}")
    
    async def store_message(self,
                           role: str,
                           content: str,
                           user_id: Optional[str] = None,
                           conversation_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a message in memory
        
        Args:
            role: Message role (user or assistant)
            content: Message content
            user_id: User ID
            conversation_id: Conversation ID
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store in conversation memory
            if conversation_id:
                if conversation_id not in self.conversation_memory:
                    self.conversation_memory[conversation_id] = []
                
                self.conversation_memory[conversation_id].append({
                    "role": role,
                    "content": content,
                    "timestamp": time.time(),
                    "metadata": metadata or {}
                })
                
                # Limit conversation memory to last 20 messages
                if len(self.conversation_memory[conversation_id]) > 20:
                    self.conversation_memory[conversation_id] = self.conversation_memory[conversation_id][-20:]
            
            # Store in Mem0 if available
            if self.mem0_client and user_id:
                await self.mem0_client.store_message(
                    human_id=user_id,
                    role=role,
                    content=content,
                    metadata=metadata
                )
                logger.info(f"Stored message in Mem0 for user {user_id}")
            
            # Store in database if available
            if self.db and conversation_id:
                # Import models
                from app.models.chat import Message
                
                # Create message
                message = Message(
                    role=role,
                    content=content,
                    conversation_id=conversation_id,
                    metadata=json.dumps(metadata) if metadata else None
                )
                
                # Add to database
                self.db.add(message)
                await self.db.commit()
                logger.info(f"Stored message in database for conversation {conversation_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            return False
    
    async def get_conversation_history(self,
                                      conversation_id: Optional[str] = None,
                                      user_id: Optional[str] = None,
                                      limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        try:
            # Check conversation memory first
            if conversation_id and conversation_id in self.conversation_memory:
                history = self.conversation_memory[conversation_id]
                return history[-limit:] if limit > 0 else history
            
            # Check database if available
            if self.db and conversation_id:
                # Import models
                from app.models.chat import Message
                from sqlalchemy import select
                
                # Query messages
                query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit)
                result = await self.db.execute(query)
                messages = result.scalars().all()
                
                # Format messages
                history = [
                    {
                        "role": message.role,
                        "content": message.content,
                        "timestamp": message.created_at.isoformat(),
                        "metadata": json.loads(message.metadata) if message.metadata else {}
                    }
                    for message in messages
                ]
                
                # Reverse to get chronological order
                history.reverse()
                
                return history
            
            # Check Mem0 if available
            if self.mem0_client and user_id:
                history = await self.mem0_client.get_conversation_history(
                    human_id=user_id,
                    limit=limit
                )
                
                return history
            
            # No history found
            return []
        
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    async def store_memory(self,
                          content: str,
                          user_id: Optional[str] = None,
                          conversation_id: Optional[str] = None) -> bool:
        """
        Store a memory
        
        Args:
            content: Memory content
            user_id: User ID
            conversation_id: Conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import memory buffer functions
            from app.rag.memory_buffer import store_memory as buffer_store_memory
            
            # Store memory
            if user_id and conversation_id and self.db:
                success = await buffer_store_memory(
                    content=content,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    db=self.db
                )
                
                if success:
                    logger.info(f"Stored memory for user {user_id}")
                    return True
                else:
                    logger.warning(f"Failed to store memory for user {user_id}")
                    return False
            else:
                logger.warning("Missing required parameters for storing memory")
                return False
        
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return False
    
    async def recall_memory(self,
                           topic: str,
                           user_id: Optional[str] = None,
                           conversation_id: Optional[str] = None) -> Optional[str]:
        """
        Recall a memory
        
        Args:
            topic: Memory topic
            user_id: User ID
            conversation_id: Conversation ID
            
        Returns:
            Recalled memory content or None
        """
        try:
            # Import memory buffer functions
            from app.rag.memory_buffer import recall_memory as buffer_recall_memory
            
            # Recall memory
            if user_id and conversation_id and self.db:
                memory = await buffer_recall_memory(
                    topic=topic,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    db=self.db
                )
                
                if memory:
                    logger.info(f"Recalled memory for topic '{topic}'")
                    return memory
                else:
                    logger.info(f"No memory found for topic '{topic}'")
                    return None
            else:
                logger.warning("Missing required parameters for recalling memory")
                return None
        
        except Exception as e:
            logger.error(f"Error recalling memory: {str(e)}")
            return None
    
    async def forget_memory(self,
                           topic: str,
                           user_id: Optional[str] = None,
                           conversation_id: Optional[str] = None) -> bool:
        """
        Forget a memory
        
        Args:
            topic: Memory topic
            user_id: User ID
            conversation_id: Conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import memory buffer functions
            from app.rag.memory_buffer import forget_memory as buffer_forget_memory
            
            # Forget memory
            if user_id and conversation_id and self.db:
                success = await buffer_forget_memory(
                    topic=topic,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    db=self.db
                )
                
                if success:
                    logger.info(f"Forgot memory for topic '{topic}'")
                    return True
                else:
                    logger.info(f"No memory found for topic '{topic}'")
                    return False
            else:
                logger.warning("Missing required parameters for forgetting memory")
                return False
        
        except Exception as e:
            logger.error(f"Error forgetting memory: {str(e)}")
            return False
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences or None
        """
        try:
            # Check Mem0 if available
            if self.mem0_client and user_id:
                preferences = await self.mem0_client.get_user_preferences(user_id)
                
                if preferences:
                    logger.info(f"Retrieved user preferences for user {user_id}")
                    return preferences
            
            # Check database if available
            if self.db and user_id:
                # Import models
                from app.models.user import User
                from sqlalchemy import select
                
                # Query user
                query = select(User).where(User.id == user_id)
                result = await self.db.execute(query)
                user = result.scalar_one_or_none()
                
                if user and user.preferences:
                    try:
                        preferences = json.loads(user.preferences)
                        logger.info(f"Retrieved user preferences from database for user {user_id}")
                        return preferences
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid preferences JSON for user {user_id}")
            
            # No preferences found
            return None
        
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return None
    
    async def store_document_interaction(self,
                                        document_id: str,
                                        interaction_type: str,
                                        user_id: Optional[str] = None,
                                        data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a document interaction
        
        Args:
            document_id: Document ID
            interaction_type: Interaction type (e.g., retrieval, view, like)
            user_id: User ID
            data: Additional data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store in Mem0 if available
            if self.mem0_client and user_id:
                await self.mem0_client.store_document_interaction(
                    human_id=user_id,
                    document_id=document_id,
                    interaction_type=interaction_type,
                    data=data
                )
                logger.info(f"Stored document interaction in Mem0 for user {user_id}")
                return True
            
            # Store in database if available
            if self.db and user_id:
                # Import models
                from app.models.document import DocumentInteraction
                
                # Create interaction
                interaction = DocumentInteraction(
                    document_id=document_id,
                    user_id=user_id,
                    interaction_type=interaction_type,
                    data=json.dumps(data) if data else None
                )
                
                # Add to database
                self.db.add(interaction)
                await self.db.commit()
                logger.info(f"Stored document interaction in database for user {user_id}")
                return True
            
            logger.warning("No storage available for document interaction")
            return False
        
        except Exception as e:
            logger.error(f"Error storing document interaction: {str(e)}")
            return False
    
    async def cleanup_memory(self) -> None:
        """
        Perform memory cleanup to reduce memory usage
        """
        try:
            # Import necessary modules
            import gc
            import psutil
            import sys
            
            # Get current memory usage before cleanup
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            
            # Force garbage collection with more aggressive settings
            gc.collect(2)  # Full collection with the highest generation
            
            # Clear any large temporary variables
            self.conversation_memory = {}
            
            # Get memory usage after cleanup
            memory_after = process.memory_info().rss / (1024 * 1024)  # Convert to MB
            memory_freed = memory_before - memory_after
            
            # Log memory usage statistics
            logger.info(f"Memory cleanup performed: {memory_freed:.2f} MB freed")
            logger.info(f"Current memory usage: {memory_after:.2f} MB")
        
        except Exception as e:
            logger.warning(f"Error during memory cleanup: {str(e)}")