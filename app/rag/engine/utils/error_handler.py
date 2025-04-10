"""
Error Handler Utility for RAG Engine

This module provides utilities for handling errors in the RAG Engine.
"""
import logging
import traceback
import sys
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
import json

logger = logging.getLogger("app.rag.engine.utils.error_handler")

class RAGError(Exception):
    """Base exception class for RAG Engine errors"""
    def __init__(self, message: str, code: str = "rag_error", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class RetrievalError(RAGError):
    """Exception raised for errors during retrieval"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="retrieval_error", details=details)

class GenerationError(RAGError):
    """Exception raised for errors during generation"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="generation_error", details=details)

class MemoryError(RAGError):
    """Exception raised for errors related to memory operations"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="memory_error", details=details)

class SecurityError(RAGError):
    """Exception raised for security-related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="security_error", details=details)

class ValidationError(RAGError):
    """Exception raised for validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="validation_error", details=details)

class ConfigurationError(RAGError):
    """Exception raised for configuration errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="configuration_error", details=details)

def handle_rag_error(error: Exception, 
                    default_message: str = "An error occurred during processing",
                    include_traceback: bool = False,
                    log_error: bool = True) -> Dict[str, Any]:
    """
    Handle a RAG Engine error and return a standardized error response
    
    Args:
        error: The exception that occurred
        default_message: Default message to use if error has no message
        include_traceback: Whether to include traceback in the response
        log_error: Whether to log the error
        
    Returns:
        Standardized error response dictionary
    """
    # Get error details
    error_type = type(error).__name__
    error_message = str(error) or default_message
    
    # Get traceback if requested
    tb = None
    if include_traceback:
        tb = traceback.format_exception(type(error), error, error.__traceback__)
    
    # Log the error if requested
    if log_error:
        if include_traceback:
            logger.error(f"{error_type}: {error_message}\n{''.join(tb)}")
        else:
            logger.error(f"{error_type}: {error_message}")
    
    # Create error response
    response = {
        "error": True,
        "error_type": error_type,
        "error_message": error_message,
        "error_code": getattr(error, "code", "unknown_error")
    }
    
    # Add details if available
    if hasattr(error, "details") and error.details:
        response["error_details"] = error.details
    
    # Add traceback if requested
    if include_traceback:
        response["traceback"] = tb
    
    return response

def format_user_facing_error(error: Exception, 
                            user_friendly: bool = True) -> str:
    """
    Format an error for user-facing display
    
    Args:
        error: The exception that occurred
        user_friendly: Whether to use user-friendly messages
        
    Returns:
        User-facing error message
    """
    # Get error type and message
    error_type = type(error).__name__
    error_message = str(error)
    
    # Define user-friendly messages for common errors
    user_friendly_messages = {
        "RetrievalError": "I couldn't find relevant information to answer your question.",
        "GenerationError": "I had trouble generating a response. Please try again.",
        "MemoryError": "I had trouble accessing conversation history.",
        "SecurityError": "I couldn't complete this action due to security restrictions.",
        "ValidationError": "There was an issue with the input provided.",
        "ConfigurationError": "There's a configuration issue that prevented me from responding properly.",
        "ConnectionError": "I couldn't connect to a required service. Please try again later.",
        "TimeoutError": "The operation timed out. Please try again with a simpler query."
    }
    
    if user_friendly and error_type in user_friendly_messages:
        # Use user-friendly message
        message = user_friendly_messages[error_type]
        
        # Add original error message for specific errors
        if error_type in ["ValidationError", "ConfigurationError"]:
            message += f" Details: {error_message}"
        
        return message
    else:
        # Use technical message
        return f"{error_type}: {error_message}"

def log_error_with_context(error: Exception, 
                          context: Dict[str, Any],
                          level: int = logging.ERROR) -> None:
    """
    Log an error with additional context
    
    Args:
        error: The exception that occurred
        context: Additional context for the error
        level: Logging level
    """
    # Format error message with context
    error_type = type(error).__name__
    error_message = str(error)
    
    # Format context as JSON
    try:
        context_json = json.dumps(context, indent=2)
    except (TypeError, ValueError):
        # If context can't be serialized to JSON, use str()
        context_json = str(context)
    
    # Log the error with context
    logger.log(level, f"{error_type}: {error_message}\nContext: {context_json}\nTraceback: {traceback.format_exc()}")

def create_error_response(error: Exception, 
                         include_traceback: bool = False) -> Dict[str, Any]:
    """
    Create a standardized error response for API endpoints
    
    Args:
        error: The exception that occurred
        include_traceback: Whether to include traceback in the response
        
    Returns:
        Standardized error response dictionary
    """
    # Get error details
    error_type = type(error).__name__
    error_message = str(error)
    
    # Create error response
    response = {
        "status": "error",
        "error": {
            "type": error_type,
            "message": error_message,
            "code": getattr(error, "code", "unknown_error")
        }
    }
    
    # Add details if available
    if hasattr(error, "details") and error.details:
        response["error"]["details"] = error.details
    
    # Add traceback if requested
    if include_traceback:
        response["error"]["traceback"] = traceback.format_exception(type(error), error, error.__traceback__)
    
    return response

def safe_execute(func: Callable, 
                *args, 
                default_return: Any = None,
                log_errors: bool = True,
                **kwargs) -> Any:
    """
    Safely execute a function and handle any exceptions
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        default_return: Default return value if an exception occurs
        log_errors: Whether to log errors
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Function result or default_return if an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {str(e)}\n{traceback.format_exc()}")
        return default_return

async def safe_execute_async(func: Callable, 
                           *args, 
                           default_return: Any = None,
                           log_errors: bool = True,
                           **kwargs) -> Any:
    """
    Safely execute an async function and handle any exceptions
    
    Args:
        func: Async function to execute
        *args: Arguments to pass to the function
        default_return: Default return value if an exception occurs
        log_errors: Whether to log errors
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Function result or default_return if an exception occurs
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {str(e)}\n{traceback.format_exc()}")
        return default_return

def get_error_context() -> Dict[str, Any]:
    """
    Get context information for the current error
    
    Returns:
        Dictionary with error context
    """
    # Get exception info
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    if not exc_type:
        return {}
    
    # Get traceback frames
    frames = traceback.extract_tb(exc_traceback)
    
    # Get local variables from the most recent frame
    local_vars = {}
    if frames:
        frame = frames[-1]
        try:
            # Get the frame object
            frame_obj = sys._current_frames().get(frame.lineno)
            if frame_obj:
                local_vars = frame_obj.f_locals
        except Exception:
            pass
    
    # Create context dictionary
    context = {
        "exception_type": exc_type.__name__,
        "exception_value": str(exc_value),
        "traceback": traceback.format_exc(),
        "frames": [
            {
                "filename": frame.filename,
                "lineno": frame.lineno,
                "name": frame.name,
                "line": frame.line
            }
            for frame in frames
        ]
    }
    
    # Add local variables if available
    if local_vars:
        # Filter out large objects and convert to strings
        filtered_vars = {}
        for key, value in local_vars.items():
            try:
                # Skip modules, functions, and classes
                if key.startswith('__') or callable(value) or isinstance(value, type):
                    continue
                
                # Convert to string with length limit
                str_value = str(value)
                if len(str_value) > 1000:
                    str_value = str_value[:1000] + "..."
                
                filtered_vars[key] = str_value
            except Exception:
                filtered_vars[key] = "<error getting value>"
        
        context["local_variables"] = filtered_vars
    
    return context