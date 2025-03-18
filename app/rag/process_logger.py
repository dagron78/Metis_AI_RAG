"""
ProcessLogger - Logs the entire query processing workflow
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ProcessLogger:
    """
    Logs the entire query processing workflow
    
    The ProcessLogger maintains a detailed log of all steps in the query processing
    workflow, including query analysis, tool usage, and response generation. This
    information can be used for auditing, debugging, and improving the system.
    """
    
    def __init__(self, db_connection=None, log_dir: Optional[str] = None):
        """
        Initialize the process logger
        
        Args:
            db_connection: Database connection for persistent logging (optional)
            log_dir: Directory for storing log files (optional)
        """
        self.db_connection = db_connection
        self.log_dir = log_dir
        self.process_log: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("app.rag.process_logger")
        
        # Create log directory if specified and doesn't exist
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def start_process(self, query_id: str, query: str) -> None:
        """
        Start logging a new process
        
        Args:
            query_id: Unique query ID
            query: User query
        """
        self.logger.info(f"Starting process logging for query {query_id}")
        self.process_log[query_id] = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "steps": [],
            "final_response": None,
            "audit_report": None
        }
    
    def log_step(self, query_id: str, step_name: str, step_data: Dict[str, Any]) -> None:
        """
        Log a step in the process
        
        Args:
            query_id: Query ID
            step_name: Name of the step
            step_data: Data from the step
        """
        if query_id not in self.process_log:
            error_msg = f"Unknown query ID: {query_id}"
            self.logger.warning(error_msg)
            raise ValueError(error_msg)
            
        self.logger.info(f"Logging step '{step_name}' for query {query_id}")
        self.process_log[query_id]["steps"].append({
            "step_name": step_name,
            "timestamp": datetime.now().isoformat(),
            "data": step_data
        })
        
        # Save to database if available
        if self.db_connection:
            self._save_to_db(query_id)
        
        # Save to file if log directory is specified
        if self.log_dir:
            self._save_to_file(query_id)
    
    def log_tool_usage(self, query_id: str, tool_name: str, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> None:
        """
        Log tool usage
        
        Args:
            query_id: Query ID
            tool_name: Name of the tool
            input_data: Tool input data
            output_data: Tool output data
        """
        self.log_step(query_id, f"tool_{tool_name}", {
            "tool": tool_name,
            "input": input_data,
            "output": output_data
        })
    
    def log_final_response(self, query_id: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log the final response
        
        Args:
            query_id: Query ID
            response: Final response text
            metadata: Additional metadata (optional)
        """
        if query_id not in self.process_log:
            error_msg = f"Unknown query ID: {query_id}"
            self.logger.warning(error_msg)
            raise ValueError(error_msg)
            
        self.logger.info(f"Logging final response for query {query_id}")
        self.process_log[query_id]["final_response"] = {
            "text": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Save to database if available
        if self.db_connection:
            self._save_to_db(query_id)
        
        # Save to file if log directory is specified
        if self.log_dir:
            self._save_to_file(query_id)
    
    def get_process_log(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the process log for a query
        
        Args:
            query_id: Query ID
            
        Returns:
            Process log if found, None otherwise
        """
        return self.process_log.get(query_id)
    
    def get_step_data(self, query_id: str, step_name: str) -> List[Dict[str, Any]]:
        """
        Get data for a specific step
        
        Args:
            query_id: Query ID
            step_name: Step name
            
        Returns:
            List of step data dictionaries
        """
        log = self.get_process_log(query_id)
        if not log:
            return []
        
        return [
            step["data"] for step in log["steps"]
            if step["step_name"] == step_name
        ]
    
    def get_tool_usage(self, query_id: str, tool_name: str) -> List[Dict[str, Any]]:
        """
        Get tool usage data
        
        Args:
            query_id: Query ID
            tool_name: Tool name
            
        Returns:
            List of tool usage dictionaries
        """
        return self.get_step_data(query_id, f"tool_{tool_name}")
    
    def clear_log(self, query_id: Optional[str] = None) -> None:
        """
        Clear the process log
        
        Args:
            query_id: Query ID to clear (if None, clear all logs)
        """
        if query_id:
            if query_id in self.process_log:
                del self.process_log[query_id]
                self.logger.info(f"Cleared log for query {query_id}")
        else:
            self.process_log.clear()
            self.logger.info("Cleared all process logs")
    
    def _save_to_db(self, query_id: str) -> None:
        """
        Save the process log to the database
        
        Args:
            query_id: Query ID
        """
        # This is a placeholder - in a real implementation, this would save to the database
        # For now, we'll just log that we would save to the database
        self.logger.info(f"Would save process log for query {query_id} to database")
    
    def _save_to_file(self, query_id: str) -> None:
        """
        Save the process log to a file
        
        Args:
            query_id: Query ID
        """
        if not self.log_dir:
            return
        
        log_file = os.path.join(self.log_dir, f"query_{query_id}.json")
        try:
            with open(log_file, 'w') as f:
                json.dump(self.process_log[query_id], f, indent=2)
            self.logger.info(f"Saved process log for query {query_id} to {log_file}")
        except Exception as e:
            self.logger.error(f"Error saving process log to file: {str(e)}")