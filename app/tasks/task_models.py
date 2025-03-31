"""
Task Models - Data models for the Background Task System
"""
import uuid
import enum
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Union, Callable, Awaitable

class TaskStatus(enum.Enum):
    """Task status enum"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"  # Waiting for dependencies

class TaskPriority(enum.Enum):
    """Task priority enum"""
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200

class TaskDependency:
    """
    Represents a dependency between tasks
    """
    def __init__(self, task_id: str, required_status: TaskStatus = TaskStatus.COMPLETED):
        self.task_id = task_id
        self.required_status = required_status

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "required_status": self.required_status.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskDependency":
        """Create from dictionary"""
        return cls(
            task_id=data["task_id"],
            required_status=TaskStatus(data["required_status"])
        )

class Task:
    """
    Model for background tasks
    """
    def __init__(
        self,
        name: str,
        task_type: str,
        params: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[TaskDependency] = None,
        schedule_time: Optional[datetime] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 0,
        task_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.id = task_id or str(uuid.uuid4())
        self.name = name
        self.task_type = task_type
        self.params = params or {}
        self.priority = priority
        self.dependencies = dependencies or []
        self.schedule_time = schedule_time
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.metadata = metadata or {}
        
        # Runtime attributes
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.scheduled_at = None
        self.started_at = None
        self.completed_at = None
        self.retry_count = 0
        self.result = None
        self.error = None
        self.progress = 0.0
        self.resource_usage = {}
        self.execution_time_ms = None
        
    def update_status(self, status: TaskStatus) -> None:
        """
        Update task status and related timestamps
        
        Args:
            status: New status
        """
        self.status = status
        
        # Update timestamps based on status
        now = datetime.now()
        if status == TaskStatus.SCHEDULED and not self.scheduled_at:
            self.scheduled_at = now
        elif status == TaskStatus.RUNNING and not self.started_at:
            self.started_at = now
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.completed_at = now
            if self.started_at:
                self.execution_time_ms = (now - self.started_at).total_seconds() * 1000
    
    def update_progress(self, progress: float) -> None:
        """
        Update task progress
        
        Args:
            progress: Progress value (0.0 to 100.0)
        """
        self.progress = max(0.0, min(100.0, progress))
    
    def update_resource_usage(self, resource_usage: Dict[str, Any]) -> None:
        """
        Update resource usage metrics
        
        Args:
            resource_usage: Resource usage metrics
        """
        self.resource_usage.update(resource_usage)
    
    def set_result(self, result: Any) -> None:
        """
        Set task result
        
        Args:
            result: Task result
        """
        self.result = result
        self.update_status(TaskStatus.COMPLETED)
    
    def set_error(self, error: str) -> None:
        """
        Set task error
        
        Args:
            error: Error message
        """
        self.error = error
        self.update_status(TaskStatus.FAILED)
    
    def can_execute(self, completed_task_ids: Set[str]) -> bool:
        """
        Check if task can be executed based on dependencies
        
        Args:
            completed_task_ids: Set of completed task IDs
            
        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        return all(dep.task_id in completed_task_ids for dep in self.dependencies)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert task to dictionary
        
        Returns:
            Dictionary representation of the task
        """
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "params": self.params,
            "priority": self.priority.value,
            "dependencies": [dep.to_dict() for dep in self.dependencies],
            "schedule_time": self.schedule_time.isoformat() if self.schedule_time else None,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "resource_usage": self.resource_usage,
            "execution_time_ms": self.execution_time_ms
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """
        Create task from dictionary
        
        Args:
            data: Dictionary representation of the task
            
        Returns:
            Task instance
        """
        task = cls(
            name=data["name"],
            task_type=data["task_type"],
            params=data.get("params", {}),
            priority=TaskPriority(data.get("priority", TaskPriority.NORMAL.value)),
            dependencies=[TaskDependency.from_dict(dep) for dep in data.get("dependencies", [])],
            schedule_time=datetime.fromisoformat(data["schedule_time"]) if data.get("schedule_time") else None,
            timeout_seconds=data.get("timeout_seconds"),
            max_retries=data.get("max_retries", 0),
            task_id=data.get("id"),
            metadata=data.get("metadata", {})
        )
        
        # Set runtime attributes
        task.status = TaskStatus(data.get("status", TaskStatus.PENDING.value))
        task.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        task.scheduled_at = datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None
        task.started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        task.completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        task.retry_count = data.get("retry_count", 0)
        task.result = data.get("result")
        task.error = data.get("error")
        task.progress = data.get("progress", 0.0)
        task.resource_usage = data.get("resource_usage", {})
        task.execution_time_ms = data.get("execution_time_ms")
        
        return task

# Type alias for task handler functions
TaskHandler = Callable[[Task], Awaitable[Any]]