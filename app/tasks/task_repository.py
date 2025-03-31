"""
Task Repository - Database operations for the Background Task System
"""
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

from sqlalchemy import select, update, delete, desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.repositories.base import BaseRepository
from app.db.models import BackgroundTask
from app.tasks.task_models import Task, TaskStatus, TaskPriority, TaskDependency

class TaskRepository(BaseRepository):
    """
    Repository for background tasks
    """
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session)
    
    async def create(self, task: Task) -> Task:
        """
        Create a new task in the database
        
        Args:
            task: Task to create
            
        Returns:
            Created task
        """
        # Convert task to database model
        db_task = BackgroundTask(
            id=task.id,
            name=task.name,
            task_type=task.task_type,
            params=task.params,
            priority=task.priority.value,
            dependencies=json.dumps([dep.to_dict() for dep in task.dependencies]),
            schedule_time=task.schedule_time,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries,
            metadata=task.metadata,
            status=task.status.value,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            retry_count=task.retry_count,
            result=json.dumps(task.result) if task.result is not None else None,
            error=task.error,
            progress=task.progress,
            resource_usage=task.resource_usage,
            execution_time_ms=task.execution_time_ms
        )
        
        # Add to database
        self.session.add(db_task)
        await self.session.commit()
        
        return task
    
    async def update(self, task: Task) -> Task:
        """
        Update a task in the database
        
        Args:
            task: Task to update
            
        Returns:
            Updated task
        """
        # Update database model
        stmt = update(BackgroundTask).where(BackgroundTask.id == task.id).values(
            name=task.name,
            task_type=task.task_type,
            params=task.params,
            priority=task.priority.value,
            dependencies=json.dumps([dep.to_dict() for dep in task.dependencies]),
            schedule_time=task.schedule_time,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries,
            metadata=task.metadata,
            status=task.status.value,
            scheduled_at=task.scheduled_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            retry_count=task.retry_count,
            result=json.dumps(task.result) if task.result is not None else None,
            error=task.error,
            progress=task.progress,
            resource_usage=task.resource_usage,
            execution_time_ms=task.execution_time_ms
        )
        
        # Execute update
        await self.session.execute(stmt)
        await self.session.commit()
        
        return task
    
    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: str = None,
        progress: float = None
    ) -> bool:
        """
        Update task status
        
        Args:
            task_id: Task ID
            status: New status
            result: Task result (for completed tasks)
            error: Error message (for failed tasks)
            progress: Task progress
            
        Returns:
            True if task was updated, False otherwise
        """
        # Build update values
        values = {"status": status.value}
        
        # Set timestamps based on status
        now = datetime.now()
        if status == TaskStatus.SCHEDULED:
            values["scheduled_at"] = now
        elif status == TaskStatus.RUNNING:
            values["started_at"] = now
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            values["completed_at"] = now
        
        # Set result or error
        if result is not None:
            values["result"] = json.dumps(result)
        if error is not None:
            values["error"] = error
        if progress is not None:
            values["progress"] = progress
        
        # Update database model
        stmt = update(BackgroundTask).where(BackgroundTask.id == task_id).values(**values)
        
        # Execute update
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        # Query database
        stmt = select(BackgroundTask).where(BackgroundTask.id == task_id)
        result = await self.session.execute(stmt)
        db_task = result.scalars().first()
        
        # Convert to task model
        if db_task:
            return self._db_to_task(db_task)
        
        return None
    
    async def get_by_status(
        self,
        status: Union[TaskStatus, List[TaskStatus]],
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """
        Get tasks by status
        
        Args:
            status: Task status or list of statuses
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            
        Returns:
            List of tasks
        """
        # Convert status to list
        if isinstance(status, TaskStatus):
            status_values = [status.value]
        else:
            status_values = [s.value for s in status]
        
        # Query database
        stmt = select(BackgroundTask).where(BackgroundTask.status.in_(status_values))
        
        # Apply pagination
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        
        # Order by created_at
        stmt = stmt.order_by(desc(BackgroundTask.created_at))
        
        # Execute query
        result = await self.session.execute(stmt)
        db_tasks = result.scalars().all()
        
        # Convert to task models
        return [self._db_to_task(db_task) for db_task in db_tasks]
    
    async def get_by_type(
        self,
        task_type: str,
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """
        Get tasks by type
        
        Args:
            task_type: Task type
            status: Optional status filter
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            
        Returns:
            List of tasks
        """
        # Build query
        stmt = select(BackgroundTask).where(BackgroundTask.task_type == task_type)
        
        # Add status filter if specified
        if status:
            if isinstance(status, TaskStatus):
                stmt = stmt.where(BackgroundTask.status == status.value)
            else:
                status_values = [s.value for s in status]
                stmt = stmt.where(BackgroundTask.status.in_(status_values))
        
        # Apply pagination
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        
        # Order by created_at
        stmt = stmt.order_by(desc(BackgroundTask.created_at))
        
        # Execute query
        result = await self.session.execute(stmt)
        db_tasks = result.scalars().all()
        
        # Convert to task models
        return [self._db_to_task(db_task) for db_task in db_tasks]
    
    async def search(
        self,
        query: str,
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        task_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """
        Search tasks
        
        Args:
            query: Search query
            status: Optional status filter
            task_type: Optional task type filter
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            
        Returns:
            List of tasks
        """
        # Build query
        conditions = []
        
        # Add search condition
        search_term = f"%{query}%"
        conditions.append(or_(
            BackgroundTask.name.ilike(search_term),
            BackgroundTask.task_type.ilike(search_term),
            BackgroundTask.id.ilike(search_term)
        ))
        
        # Add status filter if specified
        if status:
            if isinstance(status, TaskStatus):
                conditions.append(BackgroundTask.status == status.value)
            else:
                status_values = [s.value for s in status]
                conditions.append(BackgroundTask.status.in_(status_values))
        
        # Add task type filter if specified
        if task_type:
            conditions.append(BackgroundTask.task_type == task_type)
        
        # Build final query
        stmt = select(BackgroundTask).where(and_(*conditions))
        
        # Apply pagination
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        
        # Order by created_at
        stmt = stmt.order_by(desc(BackgroundTask.created_at))
        
        # Execute query
        result = await self.session.execute(stmt)
        db_tasks = result.scalars().all()
        
        # Convert to task models
        return [self._db_to_task(db_task) for db_task in db_tasks]
    
    async def count_by_status(self) -> Dict[str, int]:
        """
        Count tasks by status
        
        Returns:
            Dictionary with counts by status
        """
        # Query database
        stmt = select(
            BackgroundTask.status,
            func.count(BackgroundTask.id)
        ).group_by(BackgroundTask.status)
        
        # Execute query
        result = await self.session.execute(stmt)
        counts = {status: count for status, count in result.all()}
        
        # Ensure all statuses are included
        for status in TaskStatus:
            if status.value not in counts:
                counts[status.value] = 0
        
        return counts
    
    async def delete(self, task_id: str) -> bool:
        """
        Delete a task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was deleted, False otherwise
        """
        # Delete from database
        stmt = delete(BackgroundTask).where(BackgroundTask.id == task_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def clean_old_tasks(self, days: int = 30) -> int:
        """
        Clean up old completed/failed/cancelled tasks
        
        Args:
            days: Age in days
            
        Returns:
            Number of tasks deleted
        """
        # Calculate cutoff date
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        
        # Delete old tasks
        stmt = delete(BackgroundTask).where(
            and_(
                BackgroundTask.completed_at < cutoff_date,
                BackgroundTask.status.in_([
                    TaskStatus.COMPLETED.value,
                    TaskStatus.FAILED.value,
                    TaskStatus.CANCELLED.value
                ])
            )
        )
        
        # Execute delete
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount
    
    def _db_to_task(self, db_task: BackgroundTask) -> Task:
        """
        Convert database model to task model
        
        Args:
            db_task: Database task model
            
        Returns:
            Task model
        """
        # Parse dependencies
        dependencies = []
        if db_task.dependencies:
            try:
                deps_data = json.loads(db_task.dependencies)
                dependencies = [TaskDependency.from_dict(dep) for dep in deps_data]
            except Exception:
                # Invalid dependencies JSON
                pass
        
        # Parse result
        result = None
        if db_task.result:
            try:
                result = json.loads(db_task.result)
            except Exception:
                # Invalid result JSON
                result = db_task.result
        
        # Create task
        task = Task(
            name=db_task.name,
            task_type=db_task.task_type,
            params=db_task.params,
            priority=TaskPriority(db_task.priority),
            dependencies=dependencies,
            schedule_time=db_task.schedule_time,
            timeout_seconds=db_task.timeout_seconds,
            max_retries=db_task.max_retries,
            task_id=db_task.id,
            metadata=db_task.metadata
        )
        
        # Set runtime attributes
        task.status = TaskStatus(db_task.status)
        task.created_at = db_task.created_at
        task.scheduled_at = db_task.scheduled_at
        task.started_at = db_task.started_at
        task.completed_at = db_task.completed_at
        task.retry_count = db_task.retry_count
        task.result = result
        task.error = db_task.error
        task.progress = db_task.progress
        task.resource_usage = db_task.resource_usage or {}
        task.execution_time_ms = db_task.execution_time_ms
        
        return task