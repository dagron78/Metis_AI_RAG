"""
Text Formatting Monitor

@deprecated This file is deprecated and will be removed in a future version.
Please use the new modular structure in app/utils/text_formatting/ instead.
"""
import logging
import warnings
from enum import Enum
from typing import Dict, Any, Optional, List, Union

from app.utils.text_formatting.monitor import (
    TextFormattingMonitor as ModularTextFormattingMonitor,
    FormattingApproach,
    FormattingEvent
)

# Show deprecation warning
warnings.warn(
    "DEPRECATION WARNING: app/utils/text_formatting_monitor.py is deprecated and will be removed in a future version. "
    "Please use the new modular structure in app/utils/text_formatting/ instead.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger("app.utils.text_formatting_monitor")

# Re-export enums for backward compatibility
FormattingApproach = FormattingApproach
FormattingEvent = FormattingEvent

class TextFormattingMonitor:
    """
    Monitor for text formatting operations
    
    @deprecated This class is deprecated and will be removed in a future version.
    Please use app.utils.text_formatting.monitor.TextFormattingMonitor instead.
    """
    
    def __init__(self):
        """Initialize the text formatting monitor"""
        # Log deprecation warning
        logger.warning(
            "DEPRECATION WARNING: TextFormattingMonitor is deprecated and will be removed in a future version. "
            "Please use the new modular structure in app/utils/text_formatting/ instead."
        )
        
        # Initialize the modular monitor
        self._monitor = ModularTextFormattingMonitor()
    
    def record_event(self,
                    approach: FormattingApproach,
                    event: FormattingEvent,
                    details: Optional[Dict[str, Any]] = None,
                    error_message: Optional[str] = None) -> None:
        """
        Record a formatting event
        
        Args:
            approach: The formatting approach used
            event: The event that occurred
            details: Optional details about the event
            error_message: Optional error message
        """
        # Delegate to the modular monitor
        self._monitor.record_event(
            approach=approach,
            event=event,
            details=details,
            error_message=error_message
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about formatting events
        
        Returns:
            Dictionary with statistics
        """
        # Delegate to the modular monitor
        return self._monitor.get_stats()
    
    def get_events(self) -> List[Dict[str, Any]]:
        """
        Get all recorded events
        
        Returns:
            List of events
        """
        # Delegate to the modular monitor
        return self._monitor.get_events()
    
    def clear(self) -> None:
        """Clear all recorded events"""
        # Delegate to the modular monitor
        self._monitor.clear()

# Singleton instance for backward compatibility
_monitor = TextFormattingMonitor()

def get_monitor() -> TextFormattingMonitor:
    """
    Get the singleton monitor instance
    
    Returns:
        TextFormattingMonitor instance
    """
    return _monitor