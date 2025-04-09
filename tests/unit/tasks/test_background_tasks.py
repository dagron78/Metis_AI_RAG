"""
Unit tests for the Background Task System
"""
import asyncio
import time
import random
import pytest
from typing import List, Dict, Any

from app.tasks.task_manager import TaskManager
from app.tasks.task_models import Task, TaskStatus, TaskPriority
from app.tasks.resource_monitor import ResourceMonitor
from app.tasks.scheduler import Scheduler
from app.tasks.example_tasks import register_example_handlers

# Test task handler
async def test_task_handler(task: Task) -> Dict[str, Any]:
    """
    Test task handler that simulates work
    
    Args:
        task: Task to execute
        
    Returns:
        Task result
    """
    # Get parameters
    duration = task.params.get("duration", 1.0)
    should_fail = task.params.get("should_fail", False)
    
    # Update progress periodically
    total_steps = max(1, int(duration))
    for step in range(1, total_steps + 1):
        # Update progress
        progress = (step / total_steps) * 100
        task.update_progress(progress)
        
        # Simulate work
        await asyncio.sleep(1.0)
    
    # Simulate failure if requested
    if should_fail:
        raise ValueError("Task failed as requested")
    
    # Return result
    return {
        "duration": duration,
        "steps": total_steps
    }

@pytest.fixture
async def task_manager():
    """
    Fixture for task manager
    
    Returns:
        TaskManager instance
    """
    # Create task manager
    manager = TaskManager(max_concurrent_tasks=10)
    
    # Register test handler
    manager.register_task_handler("test", test_task_handler)
    
    # Register example handlers
    register_example_handlers(manager)
    
    # Start task manager
    await manager.start()
    
    yield manager
    
    # Stop task manager
    await manager.stop()

@pytest.mark.asyncio
async def test_task_execution(task_manager):
    """
    Test basic task execution
    
    Args:
        task_manager: TaskManager fixture
    """
    # Submit a task
    task_id = await task_manager.submit(
        name="Test Task",
        task_type="test",
        params={"duration": 2.0}
    )
    
    # Wait for task to complete
    for _ in range(10):
        task = task_manager.get_task(task_id)
        if task and task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            break
        await asyncio.sleep(0.5)
    
    # Check task status
    task = task_manager.get_task(task_id)
    assert task is not None
    assert task.status == TaskStatus.COMPLETED
    assert task.result is not None
    assert task.result["duration"] == 2.0
    assert task.result["steps"] == 2

@pytest.mark.asyncio
async def test_task_failure(task_manager):
    """
    Test task failure handling
    
    Args:
        task_manager: TaskManager fixture
    """
    # Submit a task that will fail
    task_id = await task_manager.submit(
        name="Failing Task",
        task_type="test",
        params={"duration": 1.0, "should_fail": True}
    )
    
    # Wait for task to complete
    for _ in range(10):
        task = task_manager.get_task(task_id)
        if task and task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            break
        await asyncio.sleep(0.5)
    
    # Check task status
    task = task_manager.get_task(task_id)
    assert task is not None
    assert task.status == TaskStatus.FAILED
    assert task.error is not None
    assert "Task failed as requested" in task.error

@pytest.mark.asyncio
async def test_task_cancellation(task_manager):
    """
    Test task cancellation
    
    Args:
        task_manager: TaskManager fixture
    """
    # Submit a long-running task
    task_id = await task_manager.submit(
        name="Long Task",
        task_type="test",
        params={"duration": 10.0}
    )
    
    # Wait for task to start
    await asyncio.sleep(1.0)
    
    # Cancel the task
    cancelled = await task_manager.cancel(task_id)
    
    # Check cancellation result
    assert cancelled
    
    # Check task status
    task = task_manager.get_task(task_id)
    assert task is not None
    assert task.status in (TaskStatus.CANCELLED, TaskStatus.FAILED)

@pytest.mark.asyncio
async def test_task_priorities(task_manager):
    """
    Test task priorities
    
    Args:
        task_manager: TaskManager fixture
    """
    # Submit tasks with different priorities
    low_task_id = await task_manager.submit(
        name="Low Priority Task",
        task_type="test",
        params={"duration": 1.0},
        priority=TaskPriority.LOW
    )
    
    normal_task_id = await task_manager.submit(
        name="Normal Priority Task",
        task_type="test",
        params={"duration": 1.0},
        priority=TaskPriority.NORMAL
    )
    
    high_task_id = await task_manager.submit(
        name="High Priority Task",
        task_type="test",
        params={"duration": 1.0},
        priority=TaskPriority.HIGH
    )
    
    critical_task_id = await task_manager.submit(
        name="Critical Priority Task",
        task_type="test",
        params={"duration": 1.0},
        priority=TaskPriority.CRITICAL
    )
    
    # Wait for tasks to complete
    for _ in range(20):
        tasks_completed = True
        for task_id in [low_task_id, normal_task_id, high_task_id, critical_task_id]:
            task = task_manager.get_task(task_id)
            if task and task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                tasks_completed = False
                break
        if tasks_completed:
            break
        await asyncio.sleep(0.5)
    
    # Check that all tasks completed
    for task_id in [low_task_id, normal_task_id, high_task_id, critical_task_id]:
        task = task_manager.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.COMPLETED

# Additional tests omitted for brevity - they remain unchanged