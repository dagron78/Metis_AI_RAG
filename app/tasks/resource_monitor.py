"""
Resource Monitor - Monitors system resources and provides adaptive throttling
"""
import os
import time
import asyncio
import logging
import platform
import psutil
from typing import Dict, Any, List, Optional, Callable, Tuple

class ResourceThreshold:
    """Resource threshold configuration"""
    def __init__(
        self,
        cpu_percent: float = 80.0,
        memory_percent: float = 80.0,
        disk_percent: float = 90.0,
        io_wait_percent: float = 30.0
    ):
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.disk_percent = disk_percent
        self.io_wait_percent = io_wait_percent

class ResourceAlert:
    """Resource alert model"""
    def __init__(
        self,
        resource_type: str,
        current_value: float,
        threshold: float,
        message: str,
        timestamp: float = None
    ):
        self.resource_type = resource_type
        self.current_value = current_value
        self.threshold = threshold
        self.message = message
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "resource_type": self.resource_type,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "message": self.message,
            "timestamp": self.timestamp
        }

class ResourceMonitor:
    """
    Monitors system resources and provides adaptive throttling
    """
    def __init__(
        self,
        thresholds: ResourceThreshold = None,
        check_interval_seconds: float = 5.0,
        history_size: int = 60,  # Keep 5 minutes of history with 5-second intervals
        alert_callbacks: List[Callable[[ResourceAlert], None]] = None
    ):
        self.thresholds = thresholds or ResourceThreshold()
        self.check_interval_seconds = check_interval_seconds
        self.history_size = history_size
        self.alert_callbacks = alert_callbacks or []
        
        # Resource history
        self.cpu_history: List[float] = []
        self.memory_history: List[float] = []
        self.disk_history: List[float] = []
        self.io_history: List[float] = []
        
        # Alert history
        self.alerts: List[ResourceAlert] = []
        
        # Monitoring state
        self.running = False
        self.monitor_task = None
        
        # Logger
        self.logger = logging.getLogger("app.tasks.resource_monitor")
    
    async def start(self) -> None:
        """
        Start resource monitoring
        """
        if self.running:
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_resources())
        self.logger.info("Resource monitor started")
    
    async def stop(self) -> None:
        """
        Stop resource monitoring
        """
        if not self.running:
            return
        
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        
        self.logger.info("Resource monitor stopped")
    
    async def _monitor_resources(self) -> None:
        """
        Monitor system resources periodically
        """
        while self.running:
            try:
                # Get current resource usage
                usage = self.get_resource_usage()
                
                # Update history
                self._update_history(usage)
                
                # Check thresholds and generate alerts
                self._check_thresholds(usage)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                self.logger.error(f"Error monitoring resources: {str(e)}")
                await asyncio.sleep(self.check_interval_seconds)
    
    def get_resource_usage(self) -> Dict[str, float]:
        """
        Get current resource usage
        
        Returns:
            Dictionary with resource usage metrics
        """
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Get disk usage for the main disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Get I/O wait (platform-specific)
        io_wait_percent = 0.0
        if platform.system() != 'Windows':  # Not available on Windows
            try:
                # Get CPU times including I/O wait
                cpu_times = psutil.cpu_times_percent(interval=0.1)
                io_wait_percent = getattr(cpu_times, 'iowait', 0.0)
            except Exception:
                io_wait_percent = 0.0
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "io_wait_percent": io_wait_percent
        }
    
    def _update_history(self, usage: Dict[str, float]) -> None:
        """
        Update resource usage history
        
        Args:
            usage: Current resource usage
        """
        # Update CPU history
        self.cpu_history.append(usage["cpu_percent"])
        if len(self.cpu_history) > self.history_size:
            self.cpu_history.pop(0)
        
        # Update memory history
        self.memory_history.append(usage["memory_percent"])
        if len(self.memory_history) > self.history_size:
            self.memory_history.pop(0)
        
        # Update disk history
        self.disk_history.append(usage["disk_percent"])
        if len(self.disk_history) > self.history_size:
            self.disk_history.pop(0)
        
        # Update I/O history
        self.io_history.append(usage["io_wait_percent"])
        if len(self.io_history) > self.history_size:
            self.io_history.pop(0)
    
    def _check_thresholds(self, usage: Dict[str, float]) -> None:
        """
        Check resource thresholds and generate alerts
        
        Args:
            usage: Current resource usage
        """
        # Check CPU threshold
        if usage["cpu_percent"] > self.thresholds.cpu_percent:
            alert = ResourceAlert(
                resource_type="cpu",
                current_value=usage["cpu_percent"],
                threshold=self.thresholds.cpu_percent,
                message=f"CPU usage is high: {usage['cpu_percent']:.1f}% (threshold: {self.thresholds.cpu_percent:.1f}%)"
            )
            self._add_alert(alert)
        
        # Check memory threshold
        if usage["memory_percent"] > self.thresholds.memory_percent:
            alert = ResourceAlert(
                resource_type="memory",
                current_value=usage["memory_percent"],
                threshold=self.thresholds.memory_percent,
                message=f"Memory usage is high: {usage['memory_percent']:.1f}% (threshold: {self.thresholds.memory_percent:.1f}%)"
            )
            self._add_alert(alert)
        
        # Check disk threshold
        if usage["disk_percent"] > self.thresholds.disk_percent:
            alert = ResourceAlert(
                resource_type="disk",
                current_value=usage["disk_percent"],
                threshold=self.thresholds.disk_percent,
                message=f"Disk usage is high: {usage['disk_percent']:.1f}% (threshold: {self.thresholds.disk_percent:.1f}%)"
            )
            self._add_alert(alert)
        
        # Check I/O wait threshold
        if usage["io_wait_percent"] > self.thresholds.io_wait_percent:
            alert = ResourceAlert(
                resource_type="io_wait",
                current_value=usage["io_wait_percent"],
                threshold=self.thresholds.io_wait_percent,
                message=f"I/O wait is high: {usage['io_wait_percent']:.1f}% (threshold: {self.thresholds.io_wait_percent:.1f}%)"
            )
            self._add_alert(alert)
    
    def _add_alert(self, alert: ResourceAlert) -> None:
        """
        Add an alert and notify callbacks
        
        Args:
            alert: Resource alert
        """
        self.alerts.append(alert)
        if len(self.alerts) > self.history_size:
            self.alerts.pop(0)
        
        # Log alert
        self.logger.warning(alert.message)
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {str(e)}")
    
    def get_resource_history(self) -> Dict[str, List[float]]:
        """
        Get resource usage history
        
        Returns:
            Dictionary with resource history
        """
        return {
            "cpu_history": self.cpu_history.copy(),
            "memory_history": self.memory_history.copy(),
            "disk_history": self.disk_history.copy(),
            "io_history": self.io_history.copy()
        }
    
    def get_alerts(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get recent alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alerts
        """
        alerts = self.alerts.copy()
        if limit:
            alerts = alerts[-limit:]
        return [alert.to_dict() for alert in alerts]
    
    def get_system_load(self) -> float:
        """
        Get overall system load factor (0.0 to 1.0)
        
        Returns:
            System load factor
        """
        if not self.cpu_history or not self.memory_history:
            return 0.0
        
        # Calculate average CPU and memory usage over recent history
        recent_cpu = sum(self.cpu_history[-5:]) / min(5, len(self.cpu_history))
        recent_memory = sum(self.memory_history[-5:]) / min(5, len(self.memory_history))
        
        # Calculate load factor (weighted average of CPU and memory)
        load_factor = (recent_cpu * 0.7 + recent_memory * 0.3) / 100.0
        return min(1.0, max(0.0, load_factor))
    
    def get_recommended_concurrency(self, max_concurrency: int) -> int:
        """
        Get recommended concurrency based on system load
        
        Args:
            max_concurrency: Maximum concurrency
            
        Returns:
            Recommended concurrency
        """
        load_factor = self.get_system_load()
        
        # Calculate recommended concurrency
        if load_factor < 0.5:
            # Low load, use full concurrency
            return max_concurrency
        elif load_factor < 0.7:
            # Medium load, reduce concurrency by 25%
            return max(1, int(max_concurrency * 0.75))
        elif load_factor < 0.9:
            # High load, reduce concurrency by 50%
            return max(1, int(max_concurrency * 0.5))
        else:
            # Very high load, reduce concurrency by 75%
            return max(1, int(max_concurrency * 0.25))
    
    def should_throttle(self) -> Tuple[bool, str]:
        """
        Check if task execution should be throttled
        
        Returns:
            Tuple of (should_throttle, reason)
        """
        load_factor = self.get_system_load()
        
        if load_factor > 0.95:
            return True, "System load is very high"
        
        # Check for critical resource alerts
        for alert in self.alerts[-5:]:  # Check recent alerts
            if alert.current_value > alert.threshold * 1.2:  # 20% over threshold
                return True, f"Critical resource alert: {alert.message}"
        
        return False, ""