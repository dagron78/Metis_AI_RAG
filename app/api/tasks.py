"""
API endpoints for background tasks
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from app.db.dependencies import get_db
from app.db.session import AsyncSession
from app.tasks.task_manager import TaskManager
from app.tasks.task_models import Task, TaskStatus, TaskPriority, TaskDependency
from app.tasks.task_repository import TaskRepository
from app.tasks.example_tasks import register_example_handlers

# Initialize router
router = APIRouter()

# Initialize logger
logger = logging.getLogger("app.api.tasks")

# Initialize task manager
task_manager = TaskManager()

# Register example task handlers
register_example_handlers(task_manager)

# Pydantic models for request/response
class TaskDependencyModel(BaseModel):
    """Model for task dependency"""
    task_id: str = Field(..., description="Task ID")
    required_status: str = Field("completed", description="Required status")

class TaskCreateRequest(BaseModel):
    """Request model for creating a task"""
    name: str = Field(..., description="Task name")
    task_type: str = Field(..., description="Task type")
    params: Dict[str, Any] = Field(default={}, description="Task parameters")
    priority: str = Field("normal", description="Task priority (low, normal, high, critical)")
    dependencies: List[TaskDependencyModel] = Field(default=[], description="Task dependencies")
    schedule_time: Optional[datetime] = Field(None, description="Schedule time")
    timeout_seconds: Optional[int] = Field(None, description="Timeout in seconds")
    max_retries: int = Field(0, description="Maximum number of retries")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class TaskResponse(BaseModel):
    """Response model for task"""
    id: str = Field(..., description="Task ID")
    name: str = Field(..., description="Task name")
    task_type: str = Field(..., description="Task type")
    params: Dict[str, Any] = Field(..., description="Task parameters")
    priority: str = Field(..., description="Task priority")
    dependencies: List[Dict[str, Any]] = Field(..., description="Task dependencies")
    schedule_time: Optional[str] = Field(None, description="Schedule time")
    timeout_seconds: Optional[int] = Field(None, description="Timeout in seconds")
    max_retries: int = Field(..., description="Maximum number of retries")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    status: str = Field(..., description="Task status")
    created_at: str = Field(..., description="Creation timestamp")
    scheduled_at: Optional[str] = Field(None, description="Scheduled timestamp")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    retry_count: int = Field(..., description="Retry count")
    result: Optional[Any] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message")
    progress: float = Field(..., description="Progress percentage")
    resource_usage: Dict[str, Any] = Field(..., description="Resource usage")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")

class TaskListResponse(BaseModel):
    """Response model for task list"""
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")

class TaskStatsResponse(BaseModel):
    """Response model for task statistics"""
    pending_tasks: int = Field(..., description="Number of pending tasks")
    scheduled_tasks: int = Field(..., description="Number of scheduled tasks")
    running_tasks: int = Field(..., description="Number of running tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    failed_tasks: int = Field(..., description="Number of failed tasks")
    cancelled_tasks: int = Field(..., description="Number of cancelled tasks")
    total_tasks: int = Field(..., description="Total number of tasks")
    system_load: float = Field(..., description="System load factor (0.0-1.0)")
    resource_alerts: List[Dict[str, Any]] = Field(..., description="Recent resource alerts")

# Startup event
@router.on_event("startup")
async def startup_event():
    """Start the task manager on startup"""
    await task_manager.start()
    logger.info("Task manager started")

# Shutdown event
@router.on_event("shutdown")
async def shutdown_event():
    """Stop the task manager on shutdown"""
    await task_manager.stop()
    logger.info("Task manager stopped")

@router.post("/tasks", response_model=TaskResponse, tags=["tasks"])
async def create_task(
    task_request: TaskCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new background task
    
    Args:
        task_request: Task request
        db: Database session
        
    Returns:
        Created task
    """
    try:
        # Convert priority string to enum
        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL
        }
        priority = priority_map.get(task_request.priority.lower(), TaskPriority.NORMAL)
        
        # Convert dependencies
        dependencies = []
        for dep in task_request.dependencies:
            status_map = {
                "pending": TaskStatus.PENDING,
                "scheduled": TaskStatus.SCHEDULED,
                "running": TaskStatus.RUNNING,
                "completed": TaskStatus.COMPLETED,
                "failed": TaskStatus.FAILED,
                "cancelled": TaskStatus.CANCELLED,
                "waiting": TaskStatus.WAITING
            }
            required_status = status_map.get(dep.required_status.lower(), TaskStatus.COMPLETED)
            dependencies.append(TaskDependency(task_id=dep.task_id, required_status=required_status))
        
        # Submit task
        task_id = await task_manager.submit(
            name=task_request.name,
            task_type=task_request.task_type,
            params=task_request.params,
            priority=priority,
            dependencies=dependencies,
            schedule_time=task_request.schedule_time,
            timeout_seconds=task_request.timeout_seconds,
            max_retries=task_request.max_retries,
            metadata=task_request.metadata
        )
        
        # Get task
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=500, detail="Task creation failed")
        
        # Save to database
        task_repo = TaskRepository(db)
        await task_repo.create(task)
        
        logger.info(f"Created task {task_id} of type {task_request.task_type}")
        
        # Return task
        return task.to_dict()
    except ValueError as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks", response_model=TaskListResponse, tags=["tasks"])
async def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List background tasks
    
    Args:
        status: Filter by status
        task_type: Filter by task type
        limit: Maximum number of tasks to return
        offset: Offset for pagination
        db: Database session
        
    Returns:
        List of tasks
    """
    try:
        # Convert status string to enum
        task_status = None
        if status:
            status_map = {
                "pending": TaskStatus.PENDING,
                "scheduled": TaskStatus.SCHEDULED,
                "running": TaskStatus.RUNNING,
                "completed": TaskStatus.COMPLETED,
                "failed": TaskStatus.FAILED,
                "cancelled": TaskStatus.CANCELLED,
                "waiting": TaskStatus.WAITING
            }
            task_status = status_map.get(status.lower())
            if not task_status:
                raise ValueError(f"Invalid status: {status}")
        
        # Get tasks from repository
        task_repo = TaskRepository(db)
        if task_status and task_type:
            tasks = await task_repo.get_by_type(task_type, task_status, limit, offset)
        elif task_status:
            tasks = await task_repo.get_by_status(task_status, limit, offset)
        elif task_type:
            tasks = await task_repo.get_by_type(task_type, None, limit, offset)
        else:
            # Get all tasks
            tasks = task_manager.get_tasks(limit=limit, offset=offset)
        
        # Count tasks
        status_counts = await task_repo.count_by_status()
        total = sum(status_counts.values())
        
        return {
            "tasks": [task.to_dict() for task in tasks],
            "total": total
        }
    except ValueError as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a task by ID
    
    Args:
        task_id: Task ID
        db: Database session
        
    Returns:
        Task
    """
    try:
        # Get task from repository
        task_repo = TaskRepository(db)
        task = await task_repo.get_by_id(task_id)
        
        if not task:
            # Try to get from task manager
            task = task_manager.get_task(task_id)
            
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse, tags=["tasks"])
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel a task
    
    Args:
        task_id: Task ID
        db: Database session
        
    Returns:
        Cancelled task
    """
    try:
        # Cancel task
        cancelled = await task_manager.cancel(task_id)
        if not cancelled:
            raise HTTPException(status_code=400, detail=f"Cannot cancel task {task_id}")
        
        # Get updated task
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Update in database
        task_repo = TaskRepository(db)
        await task_repo.update(task)
        
        logger.info(f"Cancelled task {task_id}")
        
        return task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/stats", response_model=TaskStatsResponse, tags=["tasks"])
async def get_task_stats(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get task statistics
    
    Args:
        db: Database session
        
    Returns:
        Task statistics
    """
    try:
        # Get stats from task manager
        stats = task_manager.get_stats()
        
        # Get status counts from repository
        task_repo = TaskRepository(db)
        status_counts = await task_repo.count_by_status()
        
        # Get resource alerts
        resource_alerts = task_manager.get_resource_alerts(limit=5)
        
        return {
            "pending_tasks": status_counts.get(TaskStatus.PENDING.value, 0),
            "scheduled_tasks": status_counts.get(TaskStatus.SCHEDULED.value, 0),
            "running_tasks": status_counts.get(TaskStatus.RUNNING.value, 0),
            "completed_tasks": status_counts.get(TaskStatus.COMPLETED.value, 0),
            "failed_tasks": status_counts.get(TaskStatus.FAILED.value, 0),
            "cancelled_tasks": status_counts.get(TaskStatus.CANCELLED.value, 0),
            "total_tasks": sum(status_counts.values()),
            "system_load": stats["resources"]["system_load"],
            "resource_alerts": resource_alerts
        }
    except Exception as e:
        logger.error(f"Error getting task stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))