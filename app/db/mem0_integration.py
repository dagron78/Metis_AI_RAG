"""
Mem0 integration for Metis_RAG repositories
"""
import logging
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic, Union
from uuid import UUID
from datetime import datetime

from mem0ai import Mem0Client
from sqlalchemy.orm import Session

from app.db.session import Base
from app.core.config import SETTINGS

# Define a generic type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger("app.db.mem0_integration")

class Mem0Integration(Generic[ModelType]):
    """
    Mem0 integration for repositories
    
    This class provides memory-enhanced operations for repositories using mem0.
    It stores and retrieves memories related to database operations.
    """
    
    def __init__(self, model_class: Type[ModelType], session: Session):
        """
        Initialize mem0 integration
        
        Args:
            model_class: SQLAlchemy model class
            session: Database session
        """
        self.model_class = model_class
        self.session = session
        self.client = Mem0Client()
        self.model_name = model_class.__name__.lower()
        
    async def store_memory(self, operation: str, entity_id: Union[str, int, UUID], data: Dict[str, Any]) -> None:
        """
        Store a memory related to a database operation
        
        Args:
            operation: Operation type (create, read, update, delete)
            entity_id: Entity ID
            data: Memory data
        """
        try:
            memory = {
                "operation": operation,
                "entity_id": str(entity_id),
                "entity_type": self.model_name,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Store memory in mem0
            await self.client.add_memory(
                memory=memory,
                collection=f"{self.model_name}_operations"
            )
            
            logger.debug(f"Stored memory for {self.model_name} {entity_id} ({operation})")
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
    
    async def retrieve_memories(self, entity_id: Union[str, int, UUID], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve memories related to an entity
        
        Args:
            entity_id: Entity ID
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of memories
        """
        try:
            # Retrieve memories from mem0
            memories = await self.client.get_memories(
                query=f"entity_id:{str(entity_id)} AND entity_type:{self.model_name}",
                collection=f"{self.model_name}_operations",
                limit=limit
            )
            
            logger.debug(f"Retrieved {len(memories)} memories for {self.model_name} {entity_id}")
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
    async def retrieve_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve user preferences
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences
        """
        try:
            # Retrieve user preferences from mem0
            preferences = await self.client.get_memories(
                query=f"user_id:{user_id} AND type:preferences",
                collection="user_memory",
                limit=1
            )
            
            if preferences:
                return preferences[0].get("data", {})
            return {}
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {str(e)}")
            return {}
    
    async def store_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """
        Store user preferences
        
        Args:
            user_id: User ID
            preferences: User preferences
        """
        try:
            memory = {
                "user_id": user_id,
                "type": "preferences",
                "timestamp": datetime.utcnow().isoformat(),
                "data": preferences
            }
            
            # Store user preferences in mem0
            await self.client.add_memory(
                memory=memory,
                collection="user_memory"
            )
            
            logger.debug(f"Stored preferences for user {user_id}")
        except Exception as e:
            logger.error(f"Error storing user preferences: {str(e)}")
    
    async def retrieve_document_interactions(self, document_id: Union[str, UUID], user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve document interactions
        
        Args:
            document_id: Document ID
            user_id: Optional user ID to filter by
            
        Returns:
            List of document interactions
        """
        try:
            query = f"document_id:{str(document_id)}"
            if user_id:
                query += f" AND user_id:{user_id}"
                
            # Retrieve document interactions from mem0
            interactions = await self.client.get_memories(
                query=query,
                collection="document_memory",
                limit=20
            )
            
            logger.debug(f"Retrieved {len(interactions)} interactions for document {document_id}")
            return interactions
        except Exception as e:
            logger.error(f"Error retrieving document interactions: {str(e)}")
            return []
    
    async def store_document_interaction(self, document_id: Union[str, UUID], user_id: str, interaction_type: str, data: Dict[str, Any]) -> None:
        """
        Store a document interaction
        
        Args:
            document_id: Document ID
            user_id: User ID
            interaction_type: Interaction type (view, search, cite, etc.)
            data: Interaction data
        """
        try:
            memory = {
                "document_id": str(document_id),
                "user_id": user_id,
                "type": interaction_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Store document interaction in mem0
            await self.client.add_memory(
                memory=memory,
                collection="document_memory"
            )
            
            logger.debug(f"Stored {interaction_type} interaction for document {document_id} by user {user_id}")
        except Exception as e:
            logger.error(f"Error storing document interaction: {str(e)}")