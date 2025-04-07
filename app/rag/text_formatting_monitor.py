"""
Monitoring and analytics for text formatting
"""
import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

# Configure logging
logger = logging.getLogger("app.rag.text_formatting_monitor")

class FormattingApproach(Enum):
    """Enum for different text formatting approaches"""
    STRUCTURED_OUTPUT = "structured_output"
    BACKEND_PROCESSING = "backend_processing"
    FRONTEND_PARSING = "frontend_parsing"
    CSS_FORMATTING = "css_formatting"


class FormattingEvent(Enum):
    """Enum for different text formatting events"""
    SUCCESS = "success"
    FALLBACK = "fallback"
    ERROR = "error"


class TextFormattingMonitor:
    """
    Monitor and analyze text formatting performance
    """
    
    def __init__(self, log_dir: str = None):
        """
        Initialize the text formatting monitor
        
        Args:
            log_dir: Directory to store logs (defaults to app/logs/text_formatting)
        """
        self.log_dir = log_dir or "app/logs/text_formatting"
        self.events = []
        self.start_time = time.time()
        
        # Ensure log directory exists
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TextFormattingMonitor initialized with log directory: {self.log_dir}")
    
    def record_event(self,
                    approach: FormattingApproach,
                    event: FormattingEvent,
                    details: Dict[str, Any] = None,
                    error_message: str = None) -> None:
        """
        Record a text formatting event
        
        Args:
            approach: The formatting approach used
            event: The event type
            details: Additional details about the event
            error_message: Error message if applicable
        """
        timestamp = datetime.now().isoformat()
        
        event_data = {
            "timestamp": timestamp,
            "approach": approach.value,
            "event": event.value,
            "details": details or {},
        }
        
        if error_message:
            event_data["error_message"] = error_message
        
        self.events.append(event_data)
        
        # Log the event
        if event == FormattingEvent.ERROR:
            logger.error(f"Text formatting error with {approach.value}: {error_message}")
        elif event == FormattingEvent.FALLBACK:
            logger.warning(f"Text formatting fallback from {approach.value} to {details.get('fallback_to')}")
        else:
            logger.info(f"Text formatting success with {approach.value}")
        
        # Periodically save events to disk
        if len(self.events) >= 100:
            self.save_events()
    
    def record_structured_output_success(self, response_size: int, content_types: List[str]) -> None:
        """
        Record a successful structured output formatting
        
        Args:
            response_size: Size of the response in bytes
            content_types: Types of content in the response (e.g., code, table, image)
        """
        self.record_event(
            approach=FormattingApproach.STRUCTURED_OUTPUT,
            event=FormattingEvent.SUCCESS,
            details={
                "response_size": response_size,
                "content_types": content_types,
                "processing_time_ms": round((time.time() - self.start_time) * 1000)
            }
        )
    
    def record_structured_output_error(self, error_message: str, processing_stage: str) -> None:
        """
        Record an error in structured output formatting
        
        Args:
            error_message: The error message
            processing_stage: The stage where the error occurred
        """
        self.record_event(
            approach=FormattingApproach.STRUCTURED_OUTPUT,
            event=FormattingEvent.ERROR,
            details={
                "processing_stage": processing_stage,
                "processing_time_ms": round((time.time() - self.start_time) * 1000)
            },
            error_message=error_message
        )
    
    def record_fallback(self,
                       from_approach: FormattingApproach,
                       to_approach: FormattingApproach,
                       reason: str) -> None:
        """
        Record a fallback from one formatting approach to another
        
        Args:
            from_approach: The original formatting approach
            to_approach: The fallback formatting approach
            reason: The reason for the fallback
        """
        self.record_event(
            approach=from_approach,
            event=FormattingEvent.FALLBACK,
            details={
                "fallback_to": to_approach.value,
                "reason": reason,
                "processing_time_ms": round((time.time() - self.start_time) * 1000)
            }
        )
    
    def save_events(self) -> None:
        """Save events to disk"""
        if not self.events:
            return
        
        # Create a filename with the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.log_dir}/text_formatting_events_{timestamp}.json"
        
        # Save events to file
        with open(filename, "w") as f:
            json.dump(self.events, f, indent=2)
        
        logger.info(f"Saved {len(self.events)} text formatting events to {filename}")
        
        # Clear events
        self.events = []
    
    def generate_report(self, time_period: str = "day") -> Dict[str, Any]:
        """
        Generate a report of text formatting performance
        
        Args:
            time_period: Time period for the report (day, week, month)
            
        Returns:
            Report data
        """
        # Load events from disk
        events = self._load_events(time_period)
        
        # Calculate statistics
        total_events = len(events)
        success_count = sum(1 for e in events if e["event"] == FormattingEvent.SUCCESS.value)
        fallback_count = sum(1 for e in events if e["event"] == FormattingEvent.FALLBACK.value)
        error_count = sum(1 for e in events if e["event"] == FormattingEvent.ERROR.value)
        
        # Calculate success rate
        success_rate = (success_count / total_events) * 100 if total_events > 0 else 0
        
        # Calculate approach usage
        approach_usage = {}
        for approach in FormattingApproach:
            approach_count = sum(1 for e in events if e["approach"] == approach.value)
            approach_usage[approach.value] = {
                "count": approach_count,
                "percentage": (approach_count / total_events) * 100 if total_events > 0 else 0
            }
        
        # Calculate common error messages
        error_messages = {}
        for event in events:
            if event["event"] == FormattingEvent.ERROR.value and "error_message" in event:
                error_message = event["error_message"]
                error_messages[error_message] = error_messages.get(error_message, 0) + 1
        
        # Sort error messages by frequency
        common_errors = sorted(
            [{"message": msg, "count": count} for msg, count in error_messages.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]  # Top 10 errors
        
        # Calculate fallback patterns
        fallback_patterns = {}
        for event in events:
            if event["event"] == FormattingEvent.FALLBACK.value:
                from_approach = event["approach"]
                to_approach = event["details"].get("fallback_to")
                if from_approach and to_approach:
                    key = f"{from_approach} -> {to_approach}"
                    fallback_patterns[key] = fallback_patterns.get(key, 0) + 1
        
        # Sort fallback patterns by frequency
        common_fallbacks = sorted(
            [{"pattern": pattern, "count": count} for pattern, count in fallback_patterns.items()],
            key=lambda x: x["count"],
            reverse=True
        )
        
        # Calculate content type statistics
        content_types = {}
        for event in events:
            if event["event"] == FormattingEvent.SUCCESS.value:
                for content_type in event["details"].get("content_types", []):
                    content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Create the report
        report = {
            "time_period": time_period,
            "total_events": total_events,
            "success_count": success_count,
            "fallback_count": fallback_count,
            "error_count": error_count,
            "success_rate": success_rate,
            "approach_usage": approach_usage,
            "common_errors": common_errors,
            "common_fallbacks": common_fallbacks,
            "content_types": content_types,
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def _load_events(self, time_period: str) -> List[Dict[str, Any]]:
        """
        Load events from disk for a specific time period
        
        Args:
            time_period: Time period (day, week, month)
            
        Returns:
            List of events
        """
        # Calculate the start date based on the time period
        now = datetime.now()
        if time_period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "week":
            # Start of the week (Monday)
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = start_date.replace(day=start_date.day - start_date.weekday())
        elif time_period == "month":
            # Start of the month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to day
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Load all event files
        events = []
        for file_path in Path(self.log_dir).glob("text_formatting_events_*.json"):
            try:
                with open(file_path, "r") as f:
                    file_events = json.load(f)
                    
                    # Filter events by time period
                    for event in file_events:
                        event_time = datetime.fromisoformat(event["timestamp"])
                        if event_time >= start_date:
                            events.append(event)
            except Exception as e:
                logger.error(f"Error loading events from {file_path}: {str(e)}")
        
        return events


# Singleton instance
_monitor_instance = None

def get_monitor() -> TextFormattingMonitor:
    """
    Get the singleton instance of the text formatting monitor
    
    Returns:
        TextFormattingMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = TextFormattingMonitor()
    return _monitor_instance