"""
Vector Store Mixin for RAG Engine

This module provides the VectorStoreMixin class that adds vector store
functionality to the RAG Engine.
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

logger = logging.getLogger("app.rag.engine.base.vector_store_mixin")

class VectorStoreMixin:
    """
    Mixin class that adds vector store functionality to the RAG Engine
    
    This mixin provides methods for interacting with the vector store,
    including searching, adding, updating, and deleting documents.
    """
    
    async def search_vector_store(self, 
                                 query: str,
                                 top_k: int = 5,
                                 filters: Optional[Dict[str, Any]] = None,
                                 user_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """
        Search the vector store for relevant documents
        
        Args:
            query: Query string
            top_k: Number of results to return
            filters: Additional filters to apply
            user_id: User ID for permission filtering
            
        Returns:
            List of relevant documents
        """
        try:
            # Use provided user_id or fall back to the instance's user_id
            effective_user_id = user_id or getattr(self, 'user_id', None)
            
            # Log the search request
            logger.info(f"Searching vector store for query: {query[:50]}...")
            
            # Search for relevant documents with permission filtering
            search_results = await self.vector_store.search(
                query=query,
                top_k=top_k,
                filter_criteria=filters,
                user_id=effective_user_id
            )
            
            # Log the number of results
            logger.info(f"Found {len(search_results)} documents in vector store")
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    async def add_document(self, 
                          document: Dict[str, Any],
                          user_id: Optional[UUID] = None) -> str:
        """
        Add a document to the vector store
        
        Args:
            document: Document to add
            user_id: User ID for permission filtering
            
        Returns:
            Document ID
        """
        try:
            # Use provided user_id or fall back to the instance's user_id
            effective_user_id = user_id or getattr(self, 'user_id', None)
            
            # Log the add request
            logger.info(f"Adding document to vector store: {document.get('metadata', {}).get('filename', 'Unknown')}")
            
            # Add document to vector store
            document_id = await self.vector_store.add_document(
                document=document,
                user_id=effective_user_id
            )
            
            logger.info(f"Added document with ID: {document_id}")
            
            return document_id
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            raise
    
    async def update_document(self, 
                             document_id: str,
                             document: Dict[str, Any],
                             user_id: Optional[UUID] = None) -> bool:
        """
        Update a document in the vector store
        
        Args:
            document_id: ID of the document to update
            document: Updated document
            user_id: User ID for permission filtering
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use provided user_id or fall back to the instance's user_id
            effective_user_id = user_id or getattr(self, 'user_id', None)
            
            # Log the update request
            logger.info(f"Updating document in vector store: {document_id}")
            
            # Update document in vector store
            success = await self.vector_store.update_document(
                document_id=document_id,
                document=document,
                user_id=effective_user_id
            )
            
            if success:
                logger.info(f"Updated document with ID: {document_id}")
            else:
                logger.warning(f"Failed to update document with ID: {document_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating document in vector store: {str(e)}")
            return False
    
    async def delete_document(self, 
                             document_id: str,
                             user_id: Optional[UUID] = None) -> bool:
        """
        Delete a document from the vector store
        
        Args:
            document_id: ID of the document to delete
            user_id: User ID for permission filtering
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use provided user_id or fall back to the instance's user_id
            effective_user_id = user_id or getattr(self, 'user_id', None)
            
            # Log the delete request
            logger.info(f"Deleting document from vector store: {document_id}")
            
            # Delete document from vector store
            success = await self.vector_store.delete_document(
                document_id=document_id,
                user_id=effective_user_id
            )
            
            if success:
                logger.info(f"Deleted document with ID: {document_id}")
            else:
                logger.warning(f"Failed to delete document with ID: {document_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {str(e)}")
            return False
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        
        Returns:
            Dictionary of statistics
        """
        try:
            # Get statistics from vector store
            stats = self.vector_store.get_stats()
            
            logger.info(f"Vector store stats: {stats}")
            
            return stats
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            return {"error": str(e)}