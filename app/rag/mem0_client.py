"""
Mem0 client for Metis_RAG
"""
import os
import logging
from typing import Optional, Dict, Any, List, Union

# Import Mem0Client only if USE_MEM0 is True
from app.core.config import SETTINGS

# Define a dummy Mem0Client class to use when mem0 is not available
class DummyMem0Client:
    def __init__(self, *args, **kwargs):
        pass
    
    def get_agent(self, *args, **kwargs):
        return None
    
    def create_agent(self, *args, **kwargs):
        return None
    
    def get_human(self, *args, **kwargs):
        return None
    
    def create_human(self, *args, **kwargs):
        return None
    def append_message(self, *args, **kwargs):
        return None
    
    def store_message(self, *args, **kwargs):
        return None
    
    
    def get_recall_memory(self, *args, **kwargs):
        return []
    
    def create_archival_memory(self, *args, **kwargs):
        return None
    
    def get_archival_memory(self, *args, **kwargs):
        return []
    
    def search_archival_memory(self, *args, **kwargs):
        return []

# Try to import Mem0Client, fall back to dummy if not available
try:
    if SETTINGS.use_mem0:
        from mem0.client import Mem0Client
    else:
        Mem0Client = DummyMem0Client
except ImportError:
    logger = logging.getLogger("app.rag.mem0_client")
    logger.warning("mem0 module not found, using dummy implementation")
    Mem0Client = DummyMem0Client

logger = logging.getLogger("app.rag.mem0_client")

# Default agent ID for Metis RAG
METIS_AGENT_ID = "metis_rag_agent"

# Default persona for Metis RAG agent
METIS_PERSONA = """
You are Metis RAG, a helpful assistant that answers questions based on provided documents.
You provide accurate, concise, and helpful responses based on the information in your knowledge base.
When you don't know the answer, you clearly state that you don't have enough information.
"""

# Singleton instance of Mem0Client
_mem0_client: Optional[Mem0Client] = None

def get_mem0_client() -> Optional[Mem0Client]:
    """
    Get the Mem0Client instance
    
    Returns:
        Mem0Client instance or None if not configured
    """
    global _mem0_client
    
    # Always check if Mem0 is enabled, even if _mem0_client is already initialized
    # This allows the setting to be changed at runtime
    if not SETTINGS.use_mem0:
        if _mem0_client is not None:
            logger.info("Mem0 integration was disabled in configuration, returning None")
            _mem0_client = None  # Reset the client so it will be reinitialized if enabled again
        return None
    
    # Initialize the client if it doesn't exist
    if _mem0_client is None:
        try:
            # Initialize the client (API key is optional for local development)
            if SETTINGS.mem0_api_key:
                _mem0_client = Mem0Client(api_key=SETTINGS.mem0_api_key, endpoint=SETTINGS.mem0_endpoint)
                logger.info(f"Initialized Mem0 client with API key and endpoint: {SETTINGS.mem0_endpoint}")
            else:
                _mem0_client = Mem0Client(endpoint=SETTINGS.mem0_endpoint)
                logger.info(f"Initialized Mem0 client without API key at endpoint: {SETTINGS.mem0_endpoint}")
            
            # Ensure the Metis RAG agent exists
            if not _mem0_client.get_agent(METIS_AGENT_ID):
                _mem0_client.create_agent(
                    agent_id=METIS_AGENT_ID,
                    name="Metis RAG Agent",
                    persona=METIS_PERSONA
                )
                logger.info(f"Created Metis RAG agent with ID: {METIS_AGENT_ID}")
            
            logger.info(f"Initialized Mem0 client with endpoint: {SETTINGS.mem0_endpoint}")
        except Exception as e:
            logger.error(f"Error initializing Mem0 client: {str(e)}")
            return None
    
    return _mem0_client

def get_or_create_human(human_id: str, name: Optional[str] = None) -> bool:
    """
    Get or create a human in Mem0
    
    Args:
        human_id: Human ID (typically user ID or session ID)
        name: Human name (optional)
        
    Returns:
        True if successful, False otherwise
    """
    client = get_mem0_client()
    if not client:
        return False
    
    try:
        # Check if human exists
        if not client.get_human(human_id):
            # Create human
            client.create_human(
                human_id=human_id,
                name=name or f"User {human_id}"
            )
            logger.info(f"Created human with ID: {human_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error getting or creating human: {str(e)}")
        return False

def store_message(human_id: str, role: str, content: str) -> bool:
    """
    Store a message in recall memory
    
    Args:
        human_id: Human ID
        role: Message role (user, assistant, system)
        content: Message content
        
    Returns:
        True if successful, False otherwise
    """
    client = get_mem0_client()
    if not client:
        return False
    
    try:
        # Ensure human exists
        if not get_or_create_human(human_id):
            return False
        
        # Append message to recall memory
        client.append_message(
            agent_id=METIS_AGENT_ID,
            human_id=human_id,
            message={"role": role, "content": content}
        )
        
        logger.debug(f"Stored {role} message for human {human_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing message: {str(e)}")
        return False

def get_conversation_history(human_id: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Get conversation history from recall memory
    
    Args:
        human_id: Human ID
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of messages
    """
    client = get_mem0_client()
    if not client:
        return []
    
    try:
        # Get recall memory
        history = client.get_recall_memory(
            agent_id=METIS_AGENT_ID,
            human_id=human_id,
            limit=limit
        )
        
        return history
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        return []

def store_user_preferences(human_id: str, preferences: Dict[str, Any]) -> bool:
    """
    Store user preferences in archival memory
    
    Args:
        human_id: Human ID
        preferences: User preferences
        
    Returns:
        True if successful, False otherwise
    """
    client = get_mem0_client()
    if not client:
        return False
    
    try:
        # Ensure human exists
        if not get_or_create_human(human_id):
            return False
        
        # Store preferences in archival memory
        client.create_archival_memory(
            agent_id=METIS_AGENT_ID,
            human_id=human_id,
            data=preferences,
            kind="user_preferences",
            replace=True  # Replace existing preferences
        )
        
        logger.info(f"Stored preferences for human {human_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing user preferences: {str(e)}")
        return False

def get_user_preferences(human_id: str) -> Dict[str, Any]:
    """
    Get user preferences from archival memory
    
    Args:
        human_id: Human ID
        
    Returns:
        User preferences
    """
    client = get_mem0_client()
    if not client:
        return {}
    
    try:
        # Get preferences from archival memory
        preferences = client.get_archival_memory(
            agent_id=METIS_AGENT_ID,
            human_id=human_id,
            kind="user_preferences",
            limit=1  # Only get the most recent preferences
        )
        
        if preferences:
            return preferences[0]["data"]
        return {}
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        return {}

def store_document_interaction(
    human_id: str,
    document_id: str,
    interaction_type: str,
    data: Dict[str, Any]
) -> bool:
    """
    Store document interaction in archival memory
    
    Args:
        human_id: Human ID
        document_id: Document ID
        interaction_type: Interaction type (view, search, cite, etc.)
        data: Interaction data
        
    Returns:
        True if successful, False otherwise
    """
    client = get_mem0_client()
    if not client:
        return False
    
    try:
        # Ensure human exists
        if not get_or_create_human(human_id):
            return False
        
        # Prepare interaction data
        interaction = {
            "document_id": document_id,
            "interaction_type": interaction_type,
            **data
        }
        
        # Store interaction in archival memory
        client.create_archival_memory(
            agent_id=METIS_AGENT_ID,
            human_id=human_id,
            data=interaction,
            kind="document_interaction"
        )
        
        logger.debug(f"Stored {interaction_type} interaction for document {document_id} by human {human_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing document interaction: {str(e)}")
        return False

def get_document_interactions(
    human_id: str,
    document_id: Optional[str] = None,
    interaction_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get document interactions from archival memory
    
    Args:
        human_id: Human ID
        document_id: Optional document ID to filter by
        interaction_type: Optional interaction type to filter by
        limit: Maximum number of interactions to retrieve
        
    Returns:
        List of document interactions
    """
    client = get_mem0_client()
    if not client:
        return []
    
    try:
        # Build query
        query = ""
        if document_id:
            query += f"document_id:{document_id} "
        if interaction_type:
            query += f"interaction_type:{interaction_type} "
        
        # Get interactions from archival memory
        interactions = client.search_archival_memory(
            agent_id=METIS_AGENT_ID,
            human_id=human_id,
            query=query.strip() if query else None,
            kind="document_interaction",
            limit=limit
        )
        
        return [interaction["data"] for interaction in interactions]
    except Exception as e:
        logger.error(f"Error getting document interactions: {str(e)}")
        return []