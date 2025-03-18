## Phase 6: Performance Optimization (Weeks 11-12)

### Week 11: Caching Implementation

#### Cache Interface
```python
class Cache(Generic[T]):
    """
    Generic cache implementation with disk persistence
    """
    def __init__(
        self,
        name: str,
        ttl: int = 3600,
        max_size: int = 1000,
        persist: bool = True,
        persist_dir: str = "data/cache"
    ):
        self.name = name
        self.ttl = ttl
        self.max_size = max_size
        self.persist = persist
        self.persist_dir = persist_dir
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0
        self.logger = logging.getLogger(f"app.cache.{name}")
        
        # Create persist directory if needed
        if self.persist:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._load_from_disk()
            self.logger.info(f"Loaded {len(self.cache)} items from disk cache")
    
    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                self.hits += 1
                self.logger.debug(f"Cache hit for key: {key}")
                return entry["value"]
            else:
                # Expired, remove from cache
                del self.cache[key]
                self.logger.debug(f"Cache entry expired for key: {key}")
        
        self.misses += 1
        self.logger.debug(f"Cache miss for key: {key}")
        return None
    
    def set(self, key: str, value: T) -> None:
        """Set a value in the cache"""
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        self.logger.debug(f"Cache set for key: {key}")
        
        # Prune cache if it gets too large
        if len(self.cache) > self.max_size:
            self._prune()
            
        # Persist to disk if enabled
        if self.persist:
            self._save_to_disk()
```

#### Cache Implementations
1. Implement VectorSearchCache for caching vector search results
2. Implement DocumentCache for caching document content and metadata
3. Implement LLMResponseCache for caching LLM responses
4. Add cache monitoring and statistics collection

### Week 12: Background Task System

#### Background Task System Architecture

The Background Task System consists of several key components:

1. **TaskManager**: Central manager for background tasks
2. **ResourceMonitor**: Monitors system resources and provides adaptive throttling
3. **Scheduler**: Handles task scheduling, prioritization, and dependencies
4. **Task Models**: Represents tasks and their properties
5. **Task Repository**: Handles database operations for tasks

#### Task Models

```python
class TaskStatus(Enum):
    """Task status enum"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"

class TaskPriority(Enum):
    """Task priority enum"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class TaskDependency:
    """Task dependency model"""
    def __init__(self, task_id: str, required_status: TaskStatus = TaskStatus.COMPLETED):
        self.task_id = task_id
        self.required_status = required_status

class Task:
    """Task model"""
    def __init__(
        self,
        id: str,
        name: str,
        task_type: str,
        params: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[TaskDependency] = None,
        schedule_time: Optional[datetime] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 0,
        metadata: Dict[str, Any] = None
    ):
        self.id = id
        self.name = name
        self.task_type = task_type
        self.params = params or {}
        self.priority = priority
        self.dependencies = dependencies or []
        self.schedule_time = schedule_time
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.metadata = metadata or {}
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
```

#### Task Manager

```python
class TaskManager:
    """
    Manager for background tasks
    """
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        resource_monitor: Optional["ResourceMonitor"] = None,
        scheduler: Optional["Scheduler"] = None
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.resource_monitor = resource_monitor or ResourceMonitor()
        self.scheduler = scheduler or Scheduler(self.resource_monitor)
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_handlers: Dict[str, Callable[[Task], Awaitable[Any]]] = {}
        self.lock = asyncio.Lock()
        self.running = False
        self.logger = logging.getLogger("app.tasks.task_manager")
        
    async def start(self) -> None:
        """Start the task manager"""
        async with self.lock:
            if self.running:
                return
            
            self.running = True
            self.logger.info("Starting task manager")
            
            # Start resource monitor
            await self.resource_monitor.start()
            
            # Start scheduler
            await self.scheduler.start()
            
            # Start task processing loop
            asyncio.create_task(self._process_tasks())
    
    async def stop(self) -> None:
        """Stop the task manager"""
        async with self.lock:
            if not self.running:
                return
            
            self.running = False
            self.logger.info("Stopping task manager")
            
            # Stop scheduler
            await self.scheduler.stop()
            
            # Stop resource monitor
            await self.resource_monitor.stop()
            
            # Cancel all running tasks
            for task_id, task in self.running_tasks.items():
                task.cancel()
            
            # Wait for tasks to complete
            if self.running_tasks:
                await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
    
    async def submit(
        self,
        name: str,
        task_type: str,
        params: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[TaskDependency] = None,
        schedule_time: Optional[datetime] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 0,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Submit a task for execution
        
        Args:
            name: Task name
            task_type: Task type
            params: Task parameters
            priority: Task priority
            dependencies: Task dependencies
            schedule_time: Schedule time
            timeout_seconds: Timeout in seconds
            max_retries: Maximum number of retries
            metadata: Additional metadata
            
        Returns:
            Task ID
        """
        # Validate task type
        if task_type not in self.task_handlers:
            raise ValueError(f"Unknown task type: {task_type}")
        
        # Create task
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            task_type=task_type,
            params=params,
            priority=priority,
            dependencies=dependencies,
            schedule_time=schedule_time,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            metadata=metadata
        )
        
        # Add task to scheduler
        await self.scheduler.schedule_task(task)
        
        # Add task to tasks dict
        self.tasks[task_id] = task
        
        self.logger.info(f"Submitted task {task_id} of type {task_type}")
        
        return task_id
    
    def register_task_handler(
        self,
        task_type: str,
        handler: Callable[[Task], Awaitable[Any]]
    ) -> None:
        """
        Register a task handler
        
        Args:
            task_type: Task type
            handler: Task handler function
        """
        self.task_handlers[task_type] = handler
        self.logger.info(f"Registered handler for task type: {task_type}")
    
    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        # Get task
        task = self.tasks.get(task_id)
        if not task:
            self.logger.warning(f"Cannot cancel task {task_id}: Task not found")
            return False
        
        # Check if task can be cancelled
        if task.status not in (TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.RUNNING):
            self.logger.warning(f"Cannot cancel task {task_id}: Task is in {task.status} state")
            return False
        
        # Cancel running task
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            self.logger.info(f"Cancelled running task {task_id}")
        
        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        self.logger.info(f"Cancelled task {task_id}")
        
        return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
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
        # Filter tasks
        filtered_tasks = self.tasks.values()
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t.status == status]
        
        if task_type:
            filtered_tasks = [t for t in filtered_tasks if t.task_type == task_type]
        
        # Sort tasks by creation time (newest first)
        sorted_tasks = sorted(filtered_tasks, key=lambda t: t.created_at, reverse=True)
        
        # Apply pagination
        paginated_tasks = sorted_tasks[offset:offset + limit]
        
        return paginated_tasks
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get task manager statistics
        
        Returns:
            Statistics dictionary
        """
        # Count tasks by status
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len([t for t in self.tasks.values() if t.status == status])
        
        # Get resource usage
        resources = {
            "cpu_percent": self.resource_monitor.get_cpu_percent(),
            "memory_percent": self.resource_monitor.get_memory_percent(),
            "disk_percent": self.resource_monitor.get_disk_percent(),
            "system_load": self.resource_monitor.get_system_load()
        }
        
        return {
            "tasks": status_counts,
            "resources": resources,
            "registered_handlers": list(self.task_handlers.keys()),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "current_concurrent_tasks": len(self.running_tasks)
        }
    
    def get_resource_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent resource alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of resource alerts
        """
        return self.resource_monitor.get_recent_alerts(limit)
    
    async def _process_tasks(self) -> None:
        """Process scheduled tasks"""
        while self.running:
            try:
                # Get recommended concurrency based on system load
                recommended_concurrency = self.resource_monitor.get_recommended_concurrency(
                    self.max_concurrent_tasks
                )
                
                # Get next batch of tasks to execute
                available_slots = recommended_concurrency - len(self.running_tasks)
                if available_slots > 0:
                    # Get tasks from scheduler
                    tasks_to_run = await self.scheduler.get_next_tasks(available_slots)
                    
                    # Execute tasks
                    for task in tasks_to_run:
                        asyncio.create_task(self._execute_task(task))
                
                # Wait before checking again
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in task processing loop: {str(e)}")
                await asyncio.sleep(1.0)
    
    async def _execute_task(self, task: Task) -> None:
        """
        Execute a task
        
        Args:
            task: Task to execute
        """
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        # Get task handler
        handler = self.task_handlers.get(task.task_type)
        if not handler:
            task.status = TaskStatus.FAILED
            task.error = f"No handler registered for task type: {task.task_type}"
            task.completed_at = datetime.now()
            self.logger.error(f"Task {task.id} failed: {task.error}")
            return
        
        # Create task future
        task_future = asyncio.create_task(self._run_task_with_timeout(task, handler))
        self.running_tasks[task.id] = task_future
        
        try:
            # Wait for task to complete
            await task_future
        except asyncio.CancelledError:
            # Task was cancelled
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            self.logger.info(f"Task {task.id} was cancelled")
        except Exception as e:
            # Task failed with exception
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            self.logger.error(f"Task {task.id} failed: {str(e)}")
        finally:
            # Remove task from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    async def _run_task_with_timeout(
        self,
        task: Task,
        handler: Callable[[Task], Awaitable[Any]]
    ) -> None:
        """
        Run a task with timeout
        
        Args:
            task: Task to run
            handler: Task handler function
        """
        start_time = time.time()
        
        try:
            # Run task with timeout if specified
            if task.timeout_seconds:
                task.result = await asyncio.wait_for(
                    handler(task),
                    timeout=task.timeout_seconds
                )
            else:
                task.result = await handler(task)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
        except asyncio.TimeoutError:
            # Task timed out
            task.status = TaskStatus.FAILED
            task.error = f"Task timed out after {task.timeout_seconds} seconds"
            self.logger.error(f"Task {task.id} timed out")
        except Exception as e:
            # Task failed
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.logger.error(f"Task {task.id} failed: {str(e)}")
            
            # Retry if retries are available
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.error = None
                task.progress = 0.0
                
                # Add exponential backoff
                backoff_seconds = 2 ** task.retry_count
                retry_time = datetime.now() + timedelta(seconds=backoff_seconds)
                
                # Reschedule task
                task.schedule_time = retry_time
                await self.scheduler.schedule_task(task)
                
                self.logger.info(f"Retrying task {task.id} in {backoff_seconds} seconds (retry {task.retry_count}/{task.max_retries})")
                return
        finally:
            # Update task completion time and execution time
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                task.completed_at = datetime.now()
                task.execution_time_ms = (time.time() - start_time) * 1000
```

#### Resource Monitor

```python
class ResourceMonitor:
    """
    Monitor system resources
    """
    def __init__(
        self,
        thresholds: Optional["ResourceThreshold"] = None,
        check_interval: float = 5.0
    ):
        self.thresholds = thresholds or ResourceThreshold()
        self.check_interval = check_interval
        self.alerts: List[Dict[str, Any]] = []
        self.running = False
        self.task = None
        self.logger = logging.getLogger("app.tasks.resource_monitor")
    
    async def start(self) -> None:
        """Start resource monitoring"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Starting resource monitor")
        self.task = asyncio.create_task(self._monitor_resources())
    
    async def stop(self) -> None:
        """Stop resource monitoring"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Stopping resource monitor")
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    def get_resource_usage(self) -> Dict[str, float]:
        """
        Get current resource usage
        
        Returns:
            Resource usage dictionary
        """
        return {
            "cpu_percent": self.get_cpu_percent(),
            "memory_percent": self.get_memory_percent(),
            "disk_percent": self.get_disk_percent(),
            "io_wait_percent": self.get_io_wait_percent()
        }
    
    def get_cpu_percent(self) -> float:
        """
        Get CPU usage percentage
        
        Returns:
            CPU usage percentage
        """
        return psutil.cpu_percent()
    
    def get_memory_percent(self) -> float:
        """
        Get memory usage percentage
        
        Returns:
            Memory usage percentage
        """
        return psutil.virtual_memory().percent
    
    def get_disk_percent(self) -> float:
        """
        Get disk usage percentage
        
        Returns:
            Disk usage percentage
        """
        return psutil.disk_usage("/").percent
    
    def get_io_wait_percent(self) -> float:
        """
        Get I/O wait percentage
        
        Returns:
            I/O wait percentage
        """
        cpu_times = psutil.cpu_times_percent()
        return getattr(cpu_times, "iowait", 0.0)
    
    def get_system_load(self) -> float:
        """
        Get system load factor (0.0-1.0)
        
        Returns:
            System load factor
        """
        # Calculate load factor based on CPU, memory, and disk usage
        cpu_load = self.get_cpu_percent() / 100.0
        memory_load = self.get_memory_percent() / 100.0
        disk_load = self.get_disk_percent() / 100.0
        io_wait_load = self.get_io_wait_percent() / 100.0
        
        # Weight the different factors
        weighted_load = (
            cpu_load * 0.4 +
            memory_load * 0.3 +
            disk_load * 0.1 +
            io_wait_load * 0.2
        )
        
        return min(1.0, max(0.0, weighted_load))
    
    def get_recommended_concurrency(self, max_concurrency: int) -> int:
        """
        Get recommended concurrency based on system load
        
        Args:
            max_concurrency: Maximum concurrency
            
        Returns:
            Recommended concurrency
        """
        load = self.get_system_load()
        
        # Calculate recommended concurrency
        if load < 0.5:
            # Low load, use full concurrency
            return max_concurrency
        elif load < 0.7:
            # Medium load, reduce concurrency by 25%
            return max(1, int(max_concurrency * 0.75))
        elif load < 0.9:
            # High load, reduce concurrency by 50%
            return max(1, int(max_concurrency * 0.5))
        else:
            # Very high load, reduce concurrency by 75%
            return max(1, int(max_concurrency * 0.25))
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent resource alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of resource alerts
        """
        return sorted(self.alerts, key=lambda a: a["timestamp"], reverse=True)[:limit]
    
    async def _monitor_resources(self) -> None:
        """Monitor system resources"""
        while self.running:
            try:
                # Get resource usage
                usage = self.get_resource_usage()
                
                # Check thresholds
                self._check_thresholds(usage)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error monitoring resources: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    def _check_thresholds(self, usage: Dict[str, float]) -> None:
        """
        Check resource thresholds and generate alerts
        
        Args:
            usage: Resource usage dictionary
        """
        timestamp = time.time()
        
        # Check CPU usage
        if usage["cpu_percent"] > self.thresholds.cpu_percent:
            self._add_alert(
                timestamp=timestamp,
                resource_type="cpu",
                current_value=usage["cpu_percent"],
                threshold=self.thresholds.cpu_percent,
                message=f"CPU usage is high: {usage['cpu_percent']:.1f}% (threshold: {self.thresholds.cpu_percent:.1f}%)"
            )
        
        # Check memory usage
        if usage["memory_percent"] > self.thresholds.memory_percent:
            self._add_alert(
                timestamp=timestamp,
                resource_type="memory",
                current_value=usage["memory_percent"],
                threshold=self.thresholds.memory_percent,
                message=f"Memory usage is high: {usage['memory_percent']:.1f}% (threshold: {self.thresholds.memory_percent:.1f}%)"
            )
        
        # Check disk usage
        if usage["disk_percent"] > self.thresholds.disk_percent:
            self._add_alert(
                timestamp=timestamp,
                resource_type="disk",
                current_value=usage["disk_percent"],
                threshold=self.thresholds.disk_percent,
                message=f"Disk usage is high: {usage['disk_percent']:.1f}% (threshold: {self.thresholds.disk_percent:.1f}%)"
            )
        
        # Check I/O wait
        if usage["io_wait_percent"] > self.thresholds.io_wait_percent:
            self._add_alert(
                timestamp=timestamp,
                resource_type="io_wait",
                current_value=usage["io_wait_percent"],
                threshold=self.thresholds.io_wait_percent,
                message=f"I/O wait is high: {usage['io_wait_percent']:.1f}% (threshold: {self.thresholds.io_wait_percent:.1f}%)"
            )
    
    def _add_alert(
        self,
        timestamp: float,
        resource_type: str,
        current_value: float,
        threshold: float,
        message: str
    ) -> None:
        """
        Add a resource alert
        
        Args:
            timestamp: Alert timestamp
            resource_type: Resource type
            current_value: Current value
            threshold: Threshold value
            message: Alert message
        """
        alert = {
            "timestamp": timestamp,
            "resource_type": resource_type,
            "current_value": current_value,
            "threshold": threshold,
            "message": message
        }
        
        self.alerts.append(alert)
        
        # Limit number of alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        self.logger.warning(message)
```

#### Scheduler

```python
class Scheduler:
    """
    Task scheduler
    """
    def __init__(self, resource_monitor: Optional["ResourceMonitor"] = None):
        self.resource_monitor = resource_monitor
        self.pending_tasks: Dict[str, Task] = {}
        self.scheduled_tasks: Dict[str, Task] = {}
        self.waiting_tasks: Dict[str, Task] = {}
        self.lock = asyncio.Lock()
        self.running = False
        self.task = None
        self.logger = logging.getLogger("app.tasks.scheduler")
    
    async def start(self) -> None:
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Starting scheduler")
        self.task = asyncio.create_task(self._schedule_tasks())
    
    async def stop(self) -> None:
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Stopping scheduler")
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def schedule_task(self, task: Task) -> None:
        """
        Schedule a task
        
        Args:
            task: Task to schedule
        """
        async with self.lock:
            # Check if task has dependencies
            if task.dependencies:
                # Add to waiting tasks
                task.status = TaskStatus.WAITING
                self.waiting_tasks[task.id] = task
                self.logger.info(f"Task {task.id} is waiting for dependencies")
            elif task.schedule_time and task.schedule_time > datetime.now():
                # Add to scheduled tasks
                task.status = TaskStatus.SCHEDULED
                task.scheduled_at = task.schedule_time
                self.scheduled_tasks[task.id] = task
                self.logger.info(f"Task {task.id} scheduled for {task.schedule_time}")
            else:
                # Add to pending tasks
                task.status = TaskStatus.PENDING
                self.pending_tasks[task.id] = task
                self.logger.info(f"Task {task.id} added to pending tasks")
    
    async def get_next_tasks(self, max_tasks: int) -> List[Task]:
        """
        Get next tasks to execute
        
        Args:
            max_tasks: Maximum number of tasks to return
            
        Returns:
            List of tasks to execute
        """
        async with self.lock:
            # Check scheduled tasks
            now = datetime.now()
            for task_id, task in list(self.scheduled_tasks.items()):
                if task.schedule_time <= now:
                    # Move to pending tasks
                    self.pending_tasks[task_id] = task
                    del self.scheduled_tasks[task_id]
                    self.logger.info(f"Scheduled task {task_id} is now pending")
            
            # Check waiting tasks
            for task_id, task in list(self.waiting_tasks.items()):
                # Check if dependencies are satisfied
                dependencies_satisfied = True
                for dependency in task.dependencies:
                    # Get dependency task
                    dependency_task = self._get_task_by_id(dependency.task_id)
                    if not dependency_task:
                        self.logger.warning(f"Dependency task {dependency.task_id} not found for task {task_id}")
                        dependencies_satisfied = False
                        break
                    
                    # Check dependency status
                    if dependency_task.status != dependency.required_status:
                        dependencies_satisfied = False
                        break
                
                if dependencies_satisfied:
                    # Move to pending tasks
                    self.pending_tasks[task_id] = task
                    del self.waiting_tasks[task_id]
                    task.status = TaskStatus.PENDING
                    self.logger.info(f"Waiting task {task_id} dependencies satisfied, now pending")
            
            # Get pending tasks sorted by priority and creation time
            sorted_tasks = sorted(
                self.pending_tasks.values(),
                key=lambda t: (
                    # Sort by priority (higher first)
                    -self._get_priority_value(t.priority),
                    # Then by creation time (older first)
                    t.created_at
                )
            )
            
            # Get tasks to execute
            tasks_to_execute = sorted_tasks[:max_tasks]
            
            # Remove tasks from pending tasks
            for task in tasks_to_execute:
                del self.pending_tasks[task.id]
            
            return tasks_to_execute
    
    def _get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID from any task list
        
        Args:
            task_id: Task ID
            
        Returns:
            Task or None if not found
        """
        if task_id in self.pending_tasks:
            return self.pending_tasks[task_id]
        elif task_id in self.scheduled_tasks:
            return self.scheduled_tasks[task_id]
        elif task_id in self.waiting_tasks:
            return self.waiting_tasks[task_id]
        return None
    
    def _get_priority_value(self, priority: TaskPriority) -> int:
        """
        Get numeric priority value
        
        Args:
            priority: Task priority
            
        Returns:
            Numeric priority value
        """
        priority_values = {
            TaskPriority.LOW: 0,
            TaskPriority.NORMAL: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.CRITICAL: 3
        }
        return priority_values.get(priority, 1)
    
    async def _schedule_tasks(self) -> None:
        """Schedule tasks periodically"""
        while self.running:
            try:
                # Check scheduled tasks
                now = datetime.now()
                async with self.lock:
                    for task_id, task in list(self.scheduled_tasks.items()):
                        if task.schedule_time <= now:
                            # Move to pending tasks
                            self.pending_tasks[task_id] = task
                            del self.scheduled_tasks[task_id]
                            self.logger.info(f"Scheduled task {task_id} is now pending")
                
                # Wait before checking again
                await asyncio.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Error in scheduling loop: {str(e)}")
                await asyncio.sleep(1.0)
```

#### Performance Monitoring and Dashboards

The Background Task System includes comprehensive performance monitoring and dashboards:

1. **Resource Monitoring**:
   - CPU, memory, disk, and I/O usage tracking
   - Adaptive throttling based on system load
   - Resource alerts for high usage

2. **Task Monitoring**:
   - Task status tracking
   - Progress reporting
   - Execution time measurement
   - Error tracking and retry management

3. **Performance Dashboards**:
   - Real-time task statistics
   - System resource usage visualization
   - Task execution history
   - Resource alerts display

4. **Adaptive Resource Management**:
   - Dynamic concurrency adjustment based on system load
   - Task prioritization for optimal resource allocation
   - Backoff strategies for retries

## Testing Infrastructure

### Unit Tests
```python
class TestDocumentRepository(unittest.TestCase):
    """Test the DocumentRepository class"""
    
    def setUp(self):
        """Set up test database"""
        self.engine = create_engine("postgresql://postgres:postgres@localhost:5432/metis_test")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
    def tearDown(self):
        """Clean up test database"""
        self.session.close()
        
    def test_create_document(self):
        """Test creating a document"""
        repo = DocumentRepository(self.session)
        document = repo.create_document(
            filename="test.txt",
            tags=["test", "document"],
            folder="/test"
        )
        
        self.assertIsNotNone(document.id)
        self.assertEqual(document.filename, "test.txt")
        self.assertEqual(document.folder, "/test")
        self.assertEqual(len(document.tags), 2)
```

### Integration Tests
```python
class TestDocumentAPI(TestCase):
    """Test the document API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = TestClient(app)
        
    def test_upload_document(self):
        """Test uploading a document"""
        # Create test file
        with open("test_file.txt", "w") as f:
            f.write("Test content")
        
        # Upload document
        with open("test_file.txt", "rb") as f:
            response = self.app.post(
                "/api/documents/upload",
                files={"file": ("test_file.txt", f, "text/plain")},
                data={"tags": "test,document", "folder": "/test"}
            )
        
        # Clean up
        os.remove("test_file.txt")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("document_id", response.json())
```

### Performance Tests
```python
class TestRAGPerformance(TestCase):
    """Test RAG performance"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = TestClient(app)
        
        # Create test documents
        self._create_test_documents(100)  # Create 100 test documents
        
    def tearDown(self):
        """Clean up test environment"""
        self._cleanup_test_documents()
        
    def test_simple_query_performance(self):
        """Test performance of simple queries"""
        # Send query
        start_time = time.time()
        response = self.app.post(
            "/api/chat/query",
            json={
                "message": "What is artificial intelligence?",
                "use_rag": True
            }
        )
        elapsed_time = time.time() - start_time
        
        # Check response time
        self.assertLess(elapsed_time, 6.0)  # Should be under 6 seconds
        self.assertEqual(response.status_code, 200)
```

## Dependencies

1. **Database**:
   - SQLAlchemy (ORM for database access)
   - Alembic (database migrations)
   - psycopg2-binary (PostgreSQL driver)

2. **LLM Integration**:
   - httpx (async HTTP client for API calls)
   - tiktoken (token counting for LLMs)
   - langgraph (for state machine implementation)

3. **Document Processing**:
   - PyPDF2 (PDF processing)
   - python-docx (DOCX processing)
   - unstructured (general document processing)
   - langchain (document chunking strategies)

4. **Vector Storage**:
   - chromadb (vector database)
   - sentence-transformers (embedding models)

5. **Web Framework**:
   - FastAPI (API framework)
   - Pydantic (data validation)
   - Jinja2 (templating)
   - uvicorn (ASGI server)

6. **Testing**:
   - pytest (testing framework)
   - pytest-asyncio (async testing)
   - pytest-cov (coverage reporting)
   - pytest-benchmark (performance testing)

7. **Monitoring and Logging**:
   - prometheus-client (metrics)
   - structlog (structured logging)

8. **Memory Management**:
   - mem0 (memory layer for AI applications)

9. **Utilities**:
   - python-multipart (file uploads)
   - python-dotenv (environment variables)
   - cachetools (in-memory caching)

## Deployment

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.10-slim as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/uploads data/chroma_db data/cache

# Expose port
EXPOSE 8000

# Set health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Set entrypoint
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  metis-rag:
    build:
      context: .
      target: ${METIS_BUILD_TARGET:-production}
    image: metis-rag:${METIS_VERSION:-latest}
    container_name: metis-rag
    restart: unless-stopped
    ports:
      - "${METIS_PORT:-8000}:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - METIS_CONFIG_FILE=/app/config/settings.json
      - METIS_DB_TYPE=postgresql
      - METIS_POSTGRES_DSN=postgresql://postgres:postgres@postgres:5432/metis
      - METIS_LLM_PROVIDER_TYPE=ollama
    networks:
      - metis-network
    depends_on:
      - postgres
      - ollama

  postgres:
    image: postgres:15-alpine
    container_name: metis-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=metis
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - metis-network

  ollama:
    image: ollama/ollama:latest
    container_name: metis-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ./data/ollama:/root/.ollama
    networks:
      - metis-network

networks:
  metis-network:
    driver: bridge

volumes:
  postgres-data:
```

## Revised Timeline (More Granular)

### Phase 1: Database Integration (Weeks 1-2)

#### Week 1:
- Choose database backend (PostgreSQL for both development and production)
- Create database schema with all required tables
- Implement DocumentRepository and migrate document storage
- Update document API endpoints to use the database

#### Week 2:
- Implement AnalyticsRepository and migrate analytics storage
- Update analytics API endpoints to use the database
- Implement ConversationRepository and migrate conversation storage
- Update chat API endpoints to use the database

### Phase 2: Intelligent Document Processing (Weeks 3-4)

#### Week 3:
- Implement DocumentAnalysisService with LLM prompt and response parsing
- Create detailed prompts for document analysis
- Integrate with DocumentProcessor
- Add unit and integration tests

#### Week 4:
- Implement ProcessingJob model and DocumentProcessingService
- Create WorkerPool for parallel processing
- Add API endpoints for job management
- Implement progress tracking and cancellation

### Phase 3: Agentic Capabilities Foundation (Weeks 5-6)

#### Week 5:
- Define Tool interface and implement ToolRegistry
- Implement RAGTool, CalculatorTool, and DatabaseTool
- Add unit tests for tools
- Create tool documentation

#### Week 6:
- Implement QueryAnalyzer with LLM-based query analysis
- Create ProcessLogger for comprehensive logging
- Add audit trail capabilities
- Implement API endpoints for query analysis

### Phase 4: Planning and Execution (Weeks 7-8)

#### Week 7:
- Implement QueryPlanner with LLM-based plan generation
- Create PlanExecutor for executing multi-step plans
- Add unit tests for planning and execution
- Create API endpoints for plan management

#### Week 8:
- Define LangGraph state models
  - Implemented QueryAnalysisState, PlanningState, ExecutionState, RetrievalState, GenerationState, and RAGState
  - Created state transitions and conditional edges for adaptive workflows
  - Added state validation and serialization
- Implement LangGraph integration with state machine
  - Created EnhancedLangGraphRAGAgent with state graph construction
  - Integrated QueryPlanner and PlanExecutor for complex queries
  - Added streaming support and execution trace tracking
  - Implemented error handling and recovery mechanisms
- Create conditional edges for adaptive workflows
  - Added complexity-based routing for simple vs. complex queries
  - Implemented tool selection based on query requirements
  - Created feedback loops for query refinement
  - Added context optimization for better responses
- Add API endpoints for LangGraph RAG
  - Created /enhanced_langgraph_query endpoint with streaming support
  - Added configuration flags for enabling/disabling LangGraph features
  - Implemented comprehensive error handling
  - Added detailed API documentation
- Comprehensive testing
  - Created integration tests for all LangGraph components
  - Implemented mock components for testing
  - Added tests for initialization, simple queries, complex queries, streaming, and error handling
  - Ensured all tests pass successfully

### Phase 5: Response Quality (Weeks 9-10)

#### Week 9:
- Implement ResponseSynthesizer for combining results
- Create ResponseEvaluator for quality assessment
- Add unit tests for response quality
- Implement metrics for response quality

#### Week 10:
- Implement ResponseRefiner for improving responses
- Create AuditReportGenerator for verification
- Add API endpoints for audit reports
- Implement visualization for audit trails

### Phase 6: Performance Optimization (Weeks 11-12)

#### Week 11:
- Implement Cache interface and cache implementations
- Add disk-based persistence for caches
- Create cache invalidation strategies
- Add cache statistics and monitoring

#### Week 12:
- Implement TaskManager for background processing
- Add resource monitoring and adaptive scheduling
- Create task prioritization and dependencies
- Implement comprehensive performance testing