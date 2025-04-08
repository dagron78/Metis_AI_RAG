"""
Security Mixin for RAG Engine

This module provides the SecurityMixin class that adds security
functionality to the RAG Engine.
"""
import logging
import re
from typing import Dict, Any, Optional, List, Set, Tuple
from uuid import UUID

logger = logging.getLogger("app.rag.engine.base.security_mixin")

class SecurityMixin:
    """
    Mixin class that adds security functionality to the RAG Engine
    
    This mixin provides methods for handling security-related functionality,
    including permission checking, content filtering, and input validation.
    """
    
    def check_document_permissions(self,
                                  document_id: str,
                                  user_id: Optional[UUID] = None,
                                  action: str = "read") -> bool:
        """
        Check if a user has permission to access a document
        
        Args:
            document_id: Document ID
            user_id: User ID
            action: Action to check (read, write, delete)
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Use provided user_id or fall back to the instance's user_id
            effective_user_id = user_id or getattr(self, 'user_id', None)
            
            # If no user ID is provided, deny access
            if not effective_user_id:
                logger.warning(f"No user ID provided for permission check on document: {document_id}")
                return False
            
            # Check permissions using vector store's permission system
            has_permission = self.vector_store.check_permission(
                document_id=document_id,
                user_id=effective_user_id,
                action=action
            )
            
            if has_permission:
                logger.debug(f"User {effective_user_id} has {action} permission for document {document_id}")
            else:
                logger.warning(f"User {effective_user_id} does not have {action} permission for document {document_id}")
            
            return has_permission
        except Exception as e:
            logger.error(f"Error checking document permissions: {str(e)}")
            # Default to denying access on error
            return False
    
    def filter_sensitive_content(self, content: str) -> str:
        """
        Filter sensitive content from text
        
        Args:
            content: Text content to filter
            
        Returns:
            Filtered content
        """
        try:
            # Define patterns for sensitive information
            patterns = {
                # Credit card numbers
                "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                # Social Security Numbers
                "ssn": r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
                # API keys (generic pattern)
                "api_key": r'\b[A-Za-z0-9_\-]{20,40}\b',
                # Email addresses
                "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                # Phone numbers
                "phone": r'\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
                # IP addresses
                "ip": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                # URLs with credentials
                "url_with_creds": r'https?://[^:]+:[^@]+@[^\s]+'
            }
            
            # Replace sensitive information with placeholders
            filtered_content = content
            for name, pattern in patterns.items():
                replacement = f"[REDACTED {name.upper()}]"
                filtered_content = re.sub(pattern, replacement, filtered_content)
            
            # Check if content was modified
            if filtered_content != content:
                logger.info("Sensitive content was filtered from text")
            
            return filtered_content
        except Exception as e:
            logger.error(f"Error filtering sensitive content: {str(e)}")
            # Return original content on error
            return content
    
    def validate_input(self, input_text: str) -> Tuple[bool, str]:
        """
        Validate user input for security issues
        
        Args:
            input_text: User input text
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Check for empty input
            if not input_text or input_text.strip() == "":
                return False, "Input cannot be empty"
            
            # Check for excessive length
            if len(input_text) > 10000:
                return False, "Input exceeds maximum length of 10,000 characters"
            
            # Check for potential injection attacks
            injection_patterns = [
                # SQL injection
                r'(?i)(\b(select|insert|update|delete|drop|alter|create|truncate)\b.*\b(from|into|table|database)\b)',
                # Command injection
                r'(?i)(\b(system|exec|shell|cmd|powershell|bash|sh)\b.*\(.*\))',
                # Path traversal
                r'(?:\.\./|\.\.\\)',
                # XML/HTML injection
                r'(?:<script.*?>.*?</script>|<.*?onload=.*?>)',
                # Server-side includes
                r'(?:<!--#include|<!--#exec)'
            ]
            
            for pattern in injection_patterns:
                if re.search(pattern, input_text):
                    return False, "Input contains potentially malicious content"
            
            # Input is valid
            return True, ""
        except Exception as e:
            logger.error(f"Error validating input: {str(e)}")
            # Default to rejecting input on error
            return False, f"Error validating input: {str(e)}"
    
    def get_user_permissions(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get permissions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of user permissions
        """
        try:
            # Use provided user_id or fall back to the instance's user_id
            effective_user_id = user_id or getattr(self, 'user_id', None)
            
            # If no user ID is provided, return empty permissions
            if not effective_user_id:
                logger.warning("No user ID provided for permission check")
                return {}
            
            # Get user permissions from the database
            # This is a placeholder - actual implementation would depend on the application's
            # permission system
            from app.core.security import get_user_permissions
            permissions = get_user_permissions(effective_user_id)
            
            logger.info(f"Retrieved permissions for user {effective_user_id}")
            
            return permissions
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            return {}
    
    def sanitize_query(self, query: str) -> str:
        """
        Sanitize a query for security
        
        Args:
            query: Query string
            
        Returns:
            Sanitized query
        """
        try:
            # Remove any control characters
            sanitized = re.sub(r'[\x00-\x1F\x7F]', '', query)
            
            # Remove any script tags
            sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove any on* event handlers
            sanitized = re.sub(r'\bon\w+\s*=', '', sanitized, flags=re.IGNORECASE)
            
            # Remove any javascript: protocol
            sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
            
            # Remove any data: protocol
            sanitized = re.sub(r'data:', '', sanitized, flags=re.IGNORECASE)
            
            # Check if query was modified
            if sanitized != query:
                logger.warning("Query was sanitized for security")
            
            return sanitized
        except Exception as e:
            logger.error(f"Error sanitizing query: {str(e)}")
            # Return original query on error
            return query