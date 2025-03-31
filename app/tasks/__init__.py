"""
Background Task System for Metis_RAG

This package provides a comprehensive background task system for executing
resource-intensive operations asynchronously, improving responsiveness and scalability.

Key components:
- TaskManager: Central manager for background tasks
- ResourceMonitor: Monitors system resources and provides adaptive throttling
- Scheduler: Handles task scheduling, prioritization, and dependencies
- Task: Model for representing background tasks
"""

from app.tasks.task_manager import TaskManager
from app.tasks.resource_monitor import ResourceMonitor
from app.tasks.scheduler import Scheduler
from app.tasks.task_models import Task, TaskStatus, TaskPriority, TaskDependency

__all__ = [
    "TaskManager",
    "ResourceMonitor",
    "Scheduler",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskDependency"
]