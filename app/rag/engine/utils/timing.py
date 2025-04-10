"""
Timing Utility for RAG Engine

This module provides utilities for performance timing and monitoring
in the RAG Engine.
"""
import logging
import time
from typing import Dict, Any, Optional, List, Callable, TypeVar, Union
from functools import wraps
import asyncio
import contextlib

logger = logging.getLogger("app.rag.engine.utils.timing")

# Type variable for generic function return type
T = TypeVar('T')

class TimingStats:
    """
    Class for tracking and reporting timing statistics
    """
    def __init__(self):
        """Initialize the timing stats"""
        self.timings = {}
        self.start_times = {}
        self.total_start_time = None
    
    def start(self, name: str = "total"):
        """
        Start timing a step
        
        Args:
            name: Name of the step
        """
        self.start_times[name] = time.time()
        if name == "total":
            self.total_start_time = self.start_times[name]
    
    def stop(self, name: str = "total") -> float:
        """
        Stop timing a step and record the elapsed time
        
        Args:
            name: Name of the step
            
        Returns:
            Elapsed time in seconds
        """
        if name not in self.start_times:
            logger.warning(f"Timing for '{name}' was never started")
            return 0.0
        
        elapsed = time.time() - self.start_times[name]
        self.timings[name] = elapsed
        return elapsed
    
    def record_timing(self, name: str, elapsed: float):
        """
        Record a timing directly
        
        Args:
            name: Name of the step
            elapsed: Elapsed time in seconds
        """
        self.timings[name] = elapsed
    
    def get_timing(self, name: str) -> float:
        """
        Get the timing for a step
        
        Args:
            name: Name of the step
            
        Returns:
            Elapsed time in seconds
        """
        return self.timings.get(name, 0.0)
    
    def get_all_timings(self) -> Dict[str, float]:
        """
        Get all timings
        
        Returns:
            Dictionary of all timings
        """
        return self.timings.copy()
    
    def reset(self):
        """Reset all timings"""
        self.timings = {}
        self.start_times = {}
        self.total_start_time = None
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all timings
        
        Returns:
            Dictionary with timing summary
        """
        total_time = self.timings.get("total", 0.0)
        if total_time == 0.0 and self.total_start_time:
            # Calculate total time if not explicitly stopped
            total_time = time.time() - self.total_start_time
        
        # Calculate percentages
        percentages = {}
        for name, elapsed in self.timings.items():
            if name != "total" and total_time > 0:
                percentages[name] = (elapsed / total_time) * 100
        
        return {
            "timings": self.timings,
            "total_time": total_time,
            "percentages": percentages
        }
    
    def log_summary(self, level: int = logging.INFO):
        """
        Log a summary of all timings
        
        Args:
            level: Logging level
        """
        summary = self.get_summary()
        
        # Format the summary for logging
        log_lines = [f"Timing Summary (total: {summary['total_time']:.2f}s):"]
        
        # Sort by elapsed time (descending)
        sorted_timings = sorted(
            [(name, elapsed) for name, elapsed in summary["timings"].items() if name != "total"],
            key=lambda x: x[1],
            reverse=True
        )
        
        for name, elapsed in sorted_timings:
            percentage = summary["percentages"].get(name, 0.0)
            log_lines.append(f"  {name}: {elapsed:.2f}s ({percentage:.1f}%)")
        
        # Log the summary
        logger.log(level, "\n".join(log_lines))

def time_operation(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for timing function execution
    
    Args:
        func: Function to time
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
        return result
    
    return wrapper

def async_time_operation(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for timing async function execution
    
    Args:
        func: Async function to time
        
    Returns:
        Wrapped async function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
        return result
    
    return wrapper

@contextlib.contextmanager
def timing_context(name: str, stats: Optional[TimingStats] = None):
    """
    Context manager for timing a block of code
    
    Args:
        name: Name of the operation
        stats: Optional TimingStats object to record the timing
        
    Yields:
        None
    """
    start_time = time.time()
    
    if stats:
        stats.start(name)
    
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        
        if stats:
            stats.stop(name)
        
        logger.info(f"{name} completed in {elapsed:.2f}s")

@contextlib.asynccontextmanager
async def async_timing_context(name: str, stats: Optional[TimingStats] = None):
    """
    Async context manager for timing a block of code
    
    Args:
        name: Name of the operation
        stats: Optional TimingStats object to record the timing
        
    Yields:
        None
    """
    start_time = time.time()
    
    if stats:
        stats.start(name)
    
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        
        if stats:
            stats.stop(name)
        
        logger.info(f"{name} completed in {elapsed:.2f}s")

def get_performance_stats() -> Dict[str, Any]:
    """
    Get performance statistics for the system
    
    Returns:
        Dictionary with performance statistics
    """
    try:
        import psutil
        
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_total_gb = disk.total / (1024 * 1024 * 1024)
        
        # Get network stats
        net_io = psutil.net_io_counters()
        net_sent_mb = net_io.bytes_sent / (1024 * 1024)
        net_recv_mb = net_io.bytes_recv / (1024 * 1024)
        
        # Get process info
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / (1024 * 1024)
        process_cpu_percent = process.cpu_percent(interval=0.1)
        
        return {
            "cpu": {
                "percent": cpu_percent
            },
            "memory": {
                "percent": memory_percent,
                "used_mb": memory_used_mb,
                "total_mb": memory_total_mb
            },
            "disk": {
                "percent": disk_percent,
                "used_gb": disk_used_gb,
                "total_gb": disk_total_gb
            },
            "network": {
                "sent_mb": net_sent_mb,
                "recv_mb": net_recv_mb
            },
            "process": {
                "memory_mb": process_memory_mb,
                "cpu_percent": process_cpu_percent
            }
        }
    except ImportError:
        logger.warning("psutil not available, returning limited performance stats")
        
        # Return limited stats
        return {
            "warning": "psutil not available, limited stats provided",
            "process": {
                "time": time.time()
            }
        }
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        return {"error": str(e)}