"""
Task Manager - Central manager for background tasks
"""
import os
import time
import uuid
import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Optional, Tuple, Callable, Awaitable, Union, Type

from app.tasks.task_models import Task, TaskStatus, TaskPriority, TaskDependency, TaskHandler
from app.tasks.resource_monitor import ResourceMonitor
from app.tasks.scheduler import Scheduler

class TaskManager:
    """
    Central manager for background tasks
    """
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        resource_check_interval: float = 5.0,
        scheduler_check_interval: float = 1.0,
        task_handlers: Dict[str, TaskHandler] = None
    ):
        # Initialize components
        self.resource_monitor = ResourceMonitor(check_interval_seconds=resource_check_interval)
        self.scheduler = Scheduler(
            resource_monitor=self.resource_monitor,
            check_interval_seconds=scheduler_check_interval
        )
        
        # Task handlers
        self.task_handlers: Dict[str, TaskHandler] = task_handlers or {}
        
        # Task execution
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # Task registry
        self.task_registry: Dict[str, Task] = {}
        
        # Execution state
        self.running = False
        self.executor_task = None
        
        # Logger
        self.logger = logging.getLogger("app.tasks.task_manager")
    
    async def start(self) -> None:
        """
        Start the task manager
        """
        if self.running:
            return
        
        # Start components
        await self.resource_monitor.start()
        await self.scheduler.start()
        
        # Start executor
        self.running = True
        self.executor_task = asyncio.create_task(self._executor_loop())
        
        self.logger.info(f"Task manager started with max concurrency {self.max_concurrent_tasks}")
    
    async def stop(self) -> None:
        """
        Stop the task manager
        """
        if not self.running:
            return
        
        # Stop executor
        self.running = False
        if self.executor_task:
            self.executor_task.cancel()
            try:
                await self.executor_task
            except asyncio.CancelledError:
                pass
            self.executor_task = None
        
        # Cancel all running tasks
        for task_id, task in list(self.running_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.running_tasks.clear()
        
        # Stop components
        await self.scheduler.stop()
        await self.resource_monitor.stop()
        
        self.logger.info("Task manager stopped")
    
    async def submit(
        self,
        name: str,
        task_type: str,
        params: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[Union[str, TaskDependency]] = None,
        schedule_time: Optional[datetime] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 0,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Submit a task for execution
        
        Args:
            name: Task name
            task_type: Task type (must be registered with a handler)
            params: Task parameters
            priority: Task priority
            dependencies: List of task dependencies (task IDs or TaskDependency objects)
            schedule_time: Time to schedule the task
            timeout_seconds: Task timeout in seconds
            max_retries: Maximum number of retries
            metadata: Additional metadata
            
        Returns:
            Task ID
        """
        # Validate task type
        if task_type not in self.task_handlers:
            raise ValueError(f"Unknown task type: {task_type}")
        
        # Process dependencies
        processed_dependencies = []
        if dependencies:
            for dep in dependencies:
                if isinstance(dep, str):
                    # Convert task ID to TaskDependency
                    processed_dependencies.append(TaskDependency(task_id=dep))
                else:
                    processed_dependencies.append(dep)
        
        # Create task
        task = Task(
            name=name,
            task_type=task_type,
            params=params or {},
            priority=priority,
            dependencies=processed_dependencies,
            schedule_time=schedule_time,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            metadata=metadata or {}
        )
        
        # Register task
        self.task_registry[task.id] = task
        
        # Schedule task
        await self.scheduler.schedule_task(task)
        
        self.logger.info(f"Submitted task {task.id} ({name}) of type {task_type}")
        
        return task.id
    
    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        # Try to cancel in scheduler
        cancelled = await self.scheduler.cancel_task(task_id)
        if cancelled:
            return True
        
        # Try to cancel running task
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            self.logger.info(f"Cancelled running task {task_id}")
            return True
        
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        # Check task registry
        if task_id in self.task_registry:
            return self.task_registry[task_id]
        
        # Check scheduler
        return self.scheduler.get_task(task_id)
    
    def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """
        Get tasks with optional filtering
        
        Args:
            status: Filter by status
            task_type: Filter by task type
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            
        Returns:
            List of tasks
        """
        # Get all tasks
        tasks = list(self.task_registry.values())
        
        # Filter by status
        if status:
            tasks = [task for task in tasks if task.status == status]
        
        # Filter by task type
        if task_type:
            tasks = [task for task in tasks if task.task_type == task_type]
        
        # Sort by created_at (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # Apply pagination
        if offset:
            tasks = tasks[offset:]
        if limit:
            tasks = tasks[:limit]
        
        return tasks
    
    def register_task_handler(self, task_type: str, handler: TaskHandler) -> None:
        """
        Register a task handler
        
        Args:
            task_type: Task type
            handler: Task handler function
        """
        self.task_handlers[task_type] = handler
        self.logger.info(f"Registered handler for task type: {task_type}")
    
    async def _executor_loop(self) -> None:
        """
        Main executor loop
        """
        while self.running:
            try:
                # Get tasks from scheduler
                ready_tasks = self.scheduler.get_tasks_by_status(TaskStatus.RUNNING)
                
                # Start execution for each task
                for task in ready_tasks:
                    # Skip tasks that are already being executed
                    if task.id in self.running_tasks:
                        continue
                    
                    # Start task execution
                    execution_task = asyncio.create_task(self._execute_task(task))
                    self.running_tasks[task.id] = execution_task
                    
                    # Set up completion callback
                    execution_task.add_done_callback(
                        lambda t, task_id=task.id: self._task_completed(task_id, t)
                    )
                
                # Wait for next check
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in executor loop: {str(e)}")
                await asyncio.sleep(1.0)
    
    async def _execute_task(self, task: Task) -> Any:
        """
        Execute a task
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        start_time = time.time()
        self.logger.info(f"Executing task {task.id} ({task.name}) of type {task.task_type}")
        
        try:
            # Get task handler
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Execute task with semaphore
            async with self.semaphore:
                # Update task status
                task.update_status(TaskStatus.RUNNING)
                
                # Set up timeout if specified
                if task.timeout_seconds:
                    result = await asyncio.wait_for(
                        handler(task),
                        timeout=task.timeout_seconds
                    )
                else:
                    result = await handler(task)
                
                # Update task with result
                elapsed_time = time.time() - start_time
                self.logger.info(f"Task {task.id} completed successfully in {elapsed_time:.2f}s")
                
                return result
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            error_msg = f"Task {task.id} timed out after {elapsed_time:.2f}s"
            self.logger.error(error_msg)
            raise TimeoutError(error_msg)
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Task {task.id} failed after {elapsed_time:.2f}s: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            raise
    
    def _task_completed(self, task_id: str, task: asyncio.Task) -> None:
        """
        Handle task completion
        
        Args:
            task_id: Task ID
            task: Asyncio task
        """
        # Remove from running tasks
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        try:
            # Get result or exception
            if task.cancelled():
                # Task was cancelled
                self.scheduler.task_failed(task_id, "Task was cancelled")
            elif task.exception():
                # Task raised an exception
                exception = task.exception()
                self.scheduler.task_failed(task_id, str(exception))
            else:
                # Task completed successfully
                result = task.result()
                self.scheduler.task_completed(task_id, result)
        except asyncio.CancelledError:
            # Task was cancelled
            self.scheduler.task_failed(task_id, "Task was cancelled")
        except Exception as e:
            # Error getting task result
            self.logger.error(f"Error handling task completion: {str(e)}")
            self.scheduler.task_failed(task_id, str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get task manager statistics
        
        Returns:
            Dictionary with task manager statistics
        """
        scheduler_stats = self.scheduler.get_stats()
        resource_stats = {
            "system_load": self.resource_monitor.get_system_load(),
            "recommended_concurrency": self.resource_monitor.get_recommended_concurrency(self.max_concurrent_tasks)
        }
        
        return {
            "scheduler": scheduler_stats,
            "resources": resource_stats,
            "task_types": list(self.task_handlers.keys()),
            "running_tasks": len(self.running_tasks),
            "registered_tasks": len(self.task_registry)
        }
    
    def get_resource_history(self) -> Dict[str, List[float]]:
        """
        Get resource usage history
        
        Returns:
            Dictionary with resource history
        """
        return self.resource_monitor.get_resource_history()
    
    def get_resource_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent resource alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alerts
        """
        return self.resource_monitor.get_alerts(limit=limit)