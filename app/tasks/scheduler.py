"""
Scheduler - Handles task scheduling, prioritization, and dependencies
"""
import time
import asyncio
import logging
import heapq
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Optional, Tuple, Callable, Awaitable

from app.tasks.task_models import Task, TaskStatus, TaskPriority, TaskDependency
from app.tasks.resource_monitor import ResourceMonitor

class ScheduleEntry:
    """
    Entry in the scheduler queue
    """
    def __init__(self, task: Task, scheduled_time: float, score: float):
        self.task = task
        self.scheduled_time = scheduled_time
        self.score = score
        
    def __lt__(self, other):
        # First compare by score (higher score = higher priority)
        if self.score != other.score:
            return self.score > other.score
        # Then compare by scheduled time (earlier time = higher priority)
        return self.scheduled_time < other.scheduled_time

class Scheduler:
    """
    Handles task scheduling, prioritization, and dependencies
    """
    def __init__(
        self,
        resource_monitor: ResourceMonitor,
        check_interval_seconds: float = 1.0,
        max_lookahead_seconds: float = 60.0
    ):
        self.resource_monitor = resource_monitor
        self.check_interval_seconds = check_interval_seconds
        self.max_lookahead_seconds = max_lookahead_seconds
        
        # Task queues
        self.pending_tasks: Dict[str, Task] = {}
        self.scheduled_queue: List[ScheduleEntry] = []  # Priority queue
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        
        # Scheduling state
        self.running = False
        self.scheduler_task = None
        
        # Logger
        self.logger = logging.getLogger("app.tasks.scheduler")
    
    async def start(self) -> None:
        """
        Start the scheduler
        """
        if self.running:
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """
        Stop the scheduler
        """
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
            self.scheduler_task = None
        
        self.logger.info("Scheduler stopped")
    
    async def schedule_task(self, task: Task) -> str:
        """
        Schedule a task for execution
        
        Args:
            task: Task to schedule
            
        Returns:
            Task ID
        """
        # Add task to pending queue
        self.pending_tasks[task.id] = task
        self.logger.info(f"Task {task.id} ({task.name}) added to pending queue")
        
        # If task has a specific schedule time, update its status
        if task.schedule_time:
            task.update_status(TaskStatus.SCHEDULED)
            self.logger.info(f"Task {task.id} scheduled for {task.schedule_time.isoformat()}")
        
        return task.id
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        # Check pending tasks
        if task_id in self.pending_tasks:
            task = self.pending_tasks.pop(task_id)
            task.update_status(TaskStatus.CANCELLED)
            self.completed_tasks[task_id] = task
            self.logger.info(f"Cancelled pending task {task_id}")
            return True
        
        # Check scheduled queue
        for i, entry in enumerate(self.scheduled_queue):
            if entry.task.id == task_id:
                # Remove from scheduled queue
                self.scheduled_queue.pop(i)
                heapq.heapify(self.scheduled_queue)
                
                # Update task status
                entry.task.update_status(TaskStatus.CANCELLED)
                self.completed_tasks[task_id] = entry.task
                self.logger.info(f"Cancelled scheduled task {task_id}")
                return True
        
        # Cannot cancel running tasks directly
        self.logger.warning(f"Cannot cancel task {task_id}: not found or already running")
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        # Check all task collections
        if task_id in self.pending_tasks:
            return self.pending_tasks[task_id]
        if task_id in self.running_tasks:
            return self.running_tasks[task_id]
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        
        # Check scheduled queue
        for entry in self.scheduled_queue:
            if entry.task.id == task_id:
                return entry.task
        
        return None
    
    def get_tasks_by_status(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """
        Get tasks by status
        
        Args:
            status: Task status filter (optional)
            
        Returns:
            List of tasks
        """
        tasks = []
        
        # Collect from all collections
        all_tasks = list(self.pending_tasks.values())
        all_tasks.extend(self.running_tasks.values())
        all_tasks.extend(self.completed_tasks.values())
        all_tasks.extend(entry.task for entry in self.scheduled_queue)
        
        # Filter by status if specified
        if status:
            return [task for task in all_tasks if task.status == status]
        
        return all_tasks
    
    async def _scheduler_loop(self) -> None:
        """
        Main scheduler loop
        """
        while self.running:
            try:
                # Process pending tasks
                await self._process_pending_tasks()
                
                # Check for tasks ready to run
                ready_tasks = self._get_ready_tasks()
                
                # Update task statuses
                for task in ready_tasks:
                    task.update_status(TaskStatus.RUNNING)
                    self.running_tasks[task.id] = task
                    self.logger.info(f"Task {task.id} ({task.name}) is now running")
                
                # Wait for next check
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(self.check_interval_seconds)
    
    async def _process_pending_tasks(self) -> None:
        """
        Process pending tasks and update the scheduled queue
        """
        # Get current time
        now = time.time()
        
        # Process each pending task
        pending_task_ids = list(self.pending_tasks.keys())
        for task_id in pending_task_ids:
            task = self.pending_tasks[task_id]
            
            # Skip tasks that are waiting for dependencies
            if task.dependencies and not self._check_dependencies(task):
                task.update_status(TaskStatus.WAITING)
                continue
            
            # Calculate scheduled time
            scheduled_time = now
            if task.schedule_time:
                scheduled_time = task.schedule_time.timestamp()
            
            # Calculate priority score
            score = self._calculate_priority_score(task)
            
            # Add to scheduled queue
            entry = ScheduleEntry(task, scheduled_time, score)
            heapq.heappush(self.scheduled_queue, entry)
            
            # Remove from pending queue
            del self.pending_tasks[task_id]
            
            # Update task status
            task.update_status(TaskStatus.SCHEDULED)
            self.logger.info(f"Task {task_id} ({task.name}) moved to scheduled queue with score {score:.2f}")
    
    def _get_ready_tasks(self) -> List[Task]:
        """
        Get tasks that are ready to run
        
        Returns:
            List of ready tasks
        """
        # Get current time
        now = time.time()
        
        # Get recommended concurrency
        max_concurrency = 10  # Default
        recommended_concurrency = self.resource_monitor.get_recommended_concurrency(max_concurrency)
        available_slots = max(0, recommended_concurrency - len(self.running_tasks))
        
        # Check if we should throttle
        should_throttle, reason = self.resource_monitor.should_throttle()
        if should_throttle:
            self.logger.warning(f"Throttling task execution: {reason}")
            return []
        
        # Get tasks ready to run
        ready_tasks = []
        lookahead_time = now + self.max_lookahead_seconds
        
        while self.scheduled_queue and len(ready_tasks) < available_slots:
            # Peek at the highest priority task
            entry = self.scheduled_queue[0]
            
            # Check if it's time to run the task
            if entry.scheduled_time > lookahead_time:
                # Not yet time to run this task
                break
            
            # Remove from scheduled queue
            heapq.heappop(self.scheduled_queue)
            
            # Add to ready tasks
            ready_tasks.append(entry.task)
        
        return ready_tasks
    
    def _check_dependencies(self, task: Task) -> bool:
        """
        Check if all task dependencies are satisfied
        
        Args:
            task: Task to check
            
        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        if not task.dependencies:
            return True
        
        for dependency in task.dependencies:
            # Get dependent task
            dependent_task = self.get_task(dependency.task_id)
            if not dependent_task:
                # Dependency not found
                self.logger.warning(f"Task {task.id} depends on missing task {dependency.task_id}")
                return False
            
            # Check status
            if dependent_task.status != dependency.required_status:
                # Dependency not satisfied
                return False
        
        # All dependencies satisfied
        return True
    
    def _calculate_priority_score(self, task: Task) -> float:
        """
        Calculate priority score for a task
        
        Args:
            task: Task to score
            
        Returns:
            Priority score (higher = higher priority)
        """
        # Base score from priority enum
        base_score = task.priority.value
        
        # Adjust for wait time
        wait_time = 0
        if task.created_at:
            wait_time = (datetime.now() - task.created_at).total_seconds()
        
        # Adjust for dependencies
        dependency_factor = 1.0
        if task.dependencies:
            # Tasks with dependencies get a slight priority boost
            dependency_factor = 1.1
        
        # Calculate final score
        # Formula: base_score * dependency_factor + (wait_time / 60)
        # This gives a small boost to tasks that have been waiting longer
        score = base_score * dependency_factor + (wait_time / 60.0)
        
        return score
    
    def task_completed(self, task_id: str, result: Any = None) -> None:
        """
        Mark a task as completed
        
        Args:
            task_id: Task ID
            result: Task result
        """
        if task_id in self.running_tasks:
            task = self.running_tasks.pop(task_id)
            task.set_result(result)
            self.completed_tasks[task_id] = task
            self.logger.info(f"Task {task_id} ({task.name}) completed")
    
    def task_failed(self, task_id: str, error: str) -> None:
        """
        Mark a task as failed
        
        Args:
            task_id: Task ID
            error: Error message
        """
        if task_id in self.running_tasks:
            task = self.running_tasks.pop(task_id)
            
            # Check if we should retry
            if task.retry_count < task.max_retries:
                # Increment retry count
                task.retry_count += 1
                
                # Calculate backoff delay
                backoff_seconds = 2 ** task.retry_count  # Exponential backoff
                
                # Schedule for retry
                task.schedule_time = datetime.now() + timedelta(seconds=backoff_seconds)
                task.status = TaskStatus.PENDING
                self.pending_tasks[task_id] = task
                
                self.logger.info(f"Task {task_id} ({task.name}) failed, retrying in {backoff_seconds}s (attempt {task.retry_count}/{task.max_retries})")
            else:
                # Mark as failed
                task.set_error(error)
                self.completed_tasks[task_id] = task
                self.logger.error(f"Task {task_id} ({task.name}) failed: {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scheduler statistics
        
        Returns:
            Dictionary with scheduler statistics
        """
        return {
            "pending_tasks": len(self.pending_tasks),
            "scheduled_tasks": len(self.scheduled_queue),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "total_tasks": len(self.pending_tasks) + len(self.scheduled_queue) + len(self.running_tasks) + len(self.completed_tasks),
            "resource_load": self.resource_monitor.get_system_load()
        }