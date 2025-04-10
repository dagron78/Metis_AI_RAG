"""
Base Formatter

This module provides the BaseFormatter abstract class that defines
the common interface for all text formatters.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union


class BaseFormatter(ABC):
    """
    Abstract base class for text formatters
    
    This class defines the common interface that all formatters must implement.
    """
    
    @abstractmethod
    def format(self, text: str, **kwargs) -> str:
        """
        Format the given text according to formatter-specific rules
        
        Args:
            text: The text to format
            **kwargs: Additional formatting options
            
        Returns:
            Formatted text
        """
        pass
    
    @abstractmethod
    def can_format(self, text: str) -> bool:
        """
        Check if this formatter can handle the given text
        
        Args:
            text: The text to check
            
        Returns:
            True if this formatter can handle the text, False otherwise
        """
        pass