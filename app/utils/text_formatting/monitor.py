"""
Text Formatting Monitor

This module provides the TextFormattingMonitor class for monitoring
text formatting operations.
"""
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger("app.utils.text_formatting.monitor")

class FormattingApproach(str, Enum):
    """Enum for formatting approaches"""
    RULE_BASED = "rule_based"
    STRUCTURED_OUTPUT = "structured_output"
    HYBRID = "hybrid"

class FormattingEvent(str, Enum):
    """Enum for formatting events"""
    SUCCESS = "success"
    ERROR = "error"
    FALLBACK = "fallback"
    SKIP = "skip"

class TextFormattingMonitor:
    """
    Monitor for text formatting operations
    
    This class records and tracks formatting events, providing statistics
    and insights into the performance of different formatting approaches.
    """
    
    def __init__(self):
        """Initialize the text formatting monitor"""
        self.events = []
        self.stats = {
            "total_events": 0,
            "success_count": 0,
            "error_count": 0,
            "fallback_count": 0,
            "skip_count": 0,
            "approaches": {}
        }
    
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
        # Create event record
        event_record = {
            "approach": approach,
            "event": event,
            "timestamp": time.time(),
            "details": details or {},
        }
        
        # Add error message if provided
        if error_message:
            event_record["error_message"] = error_message
        
        # Add to events list
        self.events.append(event_record)
        
        # Update statistics
        self.stats["total_events"] += 1
        
        # Update event type counts
        if event == FormattingEvent.SUCCESS:
            self.stats["success_count"] += 1
        elif event == FormattingEvent.ERROR:
            self.stats["error_count"] += 1
        elif event == FormattingEvent.FALLBACK:
            self.stats["fallback_count"] += 1
        elif event == FormattingEvent.SKIP:
            self.stats["skip_count"] += 1
        
        # Update approach statistics
        if approach not in self.stats["approaches"]:
            self.stats["approaches"][approach] = {
                "total": 0,
                "success": 0,
                "error": 0,
                "fallback": 0,
                "skip": 0
            }
        
        self.stats["approaches"][approach]["total"] += 1
        self.stats["approaches"][approach][event.value] += 1
        
        # Log the event
        log_message = f"Formatting event: {approach.value} - {event.value}"
        if error_message:
            log_message += f" - Error: {error_message}"
        
        logger.info(log_message)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about formatting events
        
        Returns:
            Dictionary with statistics
        """
        # Calculate success rates
        stats = self.stats.copy()
        
        if stats["total_events"] > 0:
            stats["success_rate"] = stats["success_count"] / stats["total_events"]
            stats["error_rate"] = stats["error_count"] / stats["total_events"]
            stats["fallback_rate"] = stats["fallback_count"] / stats["total_events"]
            stats["skip_rate"] = stats["skip_count"] / stats["total_events"]
        
        # Calculate approach success rates
        for approach, approach_stats in stats["approaches"].items():
            if approach_stats["total"] > 0:
                approach_stats["success_rate"] = approach_stats["success"] / approach_stats["total"]
                approach_stats["error_rate"] = approach_stats["error"] / approach_stats["total"]
                approach_stats["fallback_rate"] = approach_stats["fallback"] / approach_stats["total"]
                approach_stats["skip_rate"] = approach_stats["skip"] / approach_stats["total"]
        
        return stats
    
    def get_events(self) -> List[Dict[str, Any]]:
        """
        Get all recorded events
        
        Returns:
            List of events
        """
        return self.events
    
    def clear(self) -> None:
        """Clear all recorded events"""
        self.events = []
        self.stats = {
            "total_events": 0,
            "success_count": 0,
            "error_count": 0,
            "fallback_count": 0,
            "skip_count": 0,
            "approaches": {}
        }
        
        logger.info("Cleared all formatting events")

# Singleton instance
_monitor = TextFormattingMonitor()

def get_monitor() -> TextFormattingMonitor:
    """
    Get the singleton monitor instance
    
    Returns:
        TextFormattingMonitor instance
    """
    return _monitor