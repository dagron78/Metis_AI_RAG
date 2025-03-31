"""
Performance tests for the Background Task System
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

@pytest.mark.asyncio
async def test_concurrent_tasks(task_manager):
    """
    Test concurrent task execution
    
    Args:
        task_manager: TaskManager fixture
    """
    # Number of tasks to submit
    num_tasks = 20
    
    # Submit multiple tasks
    task_ids = []
    for i in range(num_tasks):
        task_id = await task_manager.submit(
            name=f"Concurrent Task {i}",
            task_type="test",
            params={"duration": random.uniform(0.5, 2.0)}
        )
        task_ids.append(task_id)
    
    # Wait for tasks to complete
    for _ in range(30):
        tasks_completed = True
        for task_id in task_ids:
            task = task_manager.get_task(task_id)
            if task and task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                tasks_completed = False
                break
        if tasks_completed:
            break
        await asyncio.sleep(0.5)
    
    # Check that all tasks completed
    completed_count = 0
    for task_id in task_ids:
        task = task_manager.get_task(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            completed_count += 1
    
    # At least 80% of tasks should complete successfully
    assert completed_count >= int(num_tasks * 0.8)

@pytest.mark.asyncio
async def test_resource_monitor():
    """
    Test resource monitor
    """
    # Create resource monitor
    monitor = ResourceMonitor()
    
    # Start monitoring
    await monitor.start()
    
    try:
        # Get resource usage
        usage = monitor.get_resource_usage()
        
        # Check that resource usage is reported
        assert "cpu_percent" in usage
        assert "memory_percent" in usage
        assert "disk_percent" in usage
        
        # Get system load
        load = monitor.get_system_load()
        
        # Check that system load is between 0 and 1
        assert 0.0 <= load <= 1.0
        
        # Get recommended concurrency
        concurrency = monitor.get_recommended_concurrency(max_concurrency=10)
        
        # Check that recommended concurrency is reasonable
        assert 1 <= concurrency <= 10
    finally:
        # Stop monitoring
        await monitor.stop()

@pytest.mark.asyncio
async def test_example_tasks(task_manager):
    """
    Test example task handlers
    
    Args:
        task_manager: TaskManager fixture
    """
    # Submit document processing task
    doc_task_id = await task_manager.submit(
        name="Process Document",
        task_type="document_processing",
        params={"document_id": "doc123"}
    )
    
    # Submit vector store update task
    vector_task_id = await task_manager.submit(
        name="Update Vector Store",
        task_type="vector_store_update",
        params={"document_ids": ["doc123", "doc456", "doc789"]}
    )
    
    # Submit report generation task
    report_task_id = await task_manager.submit(
        name="Generate Report",
        task_type="report_generation",
        params={"report_type": "summary", "document_ids": ["doc123", "doc456"]}
    )
    
    # Submit system maintenance task
    maintenance_task_id = await task_manager.submit(
        name="System Maintenance",
        task_type="system_maintenance",
        params={"maintenance_type": "cleanup"}
    )
    
    # Wait for tasks to complete
    task_ids = [doc_task_id, vector_task_id, report_task_id, maintenance_task_id]
    for _ in range(30):
        tasks_completed = True
        for task_id in task_ids:
            task = task_manager.get_task(task_id)
            if task and task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                tasks_completed = False
                break
        if tasks_completed:
            break
        await asyncio.sleep(1.0)
    
    # Check that all tasks completed
    for task_id in task_ids:
        task = task_manager.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.result is not None

@pytest.mark.asyncio
async def test_task_dependencies(task_manager):
    """
    Test task dependencies
    
    Args:
        task_manager: TaskManager fixture
    """
    # Submit first task
    first_task_id = await task_manager.submit(
        name="First Task",
        task_type="test",
        params={"duration": 1.0}
    )
    
    # Submit second task that depends on first task
    second_task_id = await task_manager.submit(
        name="Second Task",
        task_type="test",
        params={"duration": 1.0},
        dependencies=[first_task_id]
    )
    
    # Submit third task that depends on second task
    third_task_id = await task_manager.submit(
        name="Third Task",
        task_type="test",
        params={"duration": 1.0},
        dependencies=[second_task_id]
    )
    
    # Wait for tasks to complete
    for _ in range(30):
        tasks_completed = True
        for task_id in [first_task_id, second_task_id, third_task_id]:
            task = task_manager.get_task(task_id)
            if task and task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                tasks_completed = False
                break
        if tasks_completed:
            break
        await asyncio.sleep(0.5)
    
    # Check that all tasks completed
    for task_id in [first_task_id, second_task_id, third_task_id]:
        task = task_manager.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.COMPLETED

@pytest.mark.asyncio
async def test_performance():
    """
    Test system performance under load
    """
    # Create task manager with high concurrency
    manager = TaskManager(max_concurrent_tasks=20)
    
    # Register test handler
    manager.register_task_handler("test", test_task_handler)
    
    # Start task manager
    await manager.start()
    
    try:
        # Number of tasks to submit
        num_tasks = 100
        
        # Submit multiple tasks
        start_time = time.time()
        task_ids = []
        for i in range(num_tasks):
            task_id = await manager.submit(
                name=f"Performance Task {i}",
                task_type="test",
                params={"duration": random.uniform(0.1, 0.5)}
            )
            task_ids.append(task_id)
        
        # Wait for tasks to complete
        for _ in range(60):
            tasks_completed = True
            for task_id in task_ids:
                task = manager.get_task(task_id)
                if task and task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    tasks_completed = False
                    break
            if tasks_completed:
                break
            await asyncio.sleep(0.5)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Check that all tasks completed
        completed_count = 0
        for task_id in task_ids:
            task = manager.get_task(task_id)
            if task and task.status == TaskStatus.COMPLETED:
                completed_count += 1
        
        # At least 90% of tasks should complete successfully
        assert completed_count >= int(num_tasks * 0.9)
        
        # Calculate throughput
        throughput = completed_count / elapsed_time
        print(f"Throughput: {throughput:.2f} tasks/second")
        
        # Get task manager stats
        stats = manager.get_stats()
        print(f"Task manager stats: {stats}")
    finally:
        # Stop task manager
        await manager.stop()