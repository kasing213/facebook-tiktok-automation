# app/services/task_queue.py
"""
Async task queue system for background processing.
"""
import asyncio
import json
import uuid
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
import logging
import traceback

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import get_settings
from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        data['status'] = self.status.value
        return data


@dataclass
class TaskDefinition:
    """Task definition"""
    task_id: str
    func_name: str
    args: tuple
    kwargs: dict
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'func_name': self.func_name,
            'args': self.args,
            'kwargs': self.kwargs,
            'priority': self.priority.value,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'timeout': self.timeout,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskDefinition':
        """Create from dictionary"""
        return cls(
            task_id=data['task_id'],
            func_name=data['func_name'],
            args=tuple(data['args']),
            kwargs=data['kwargs'],
            priority=TaskPriority(data['priority']),
            max_retries=data['max_retries'],
            retry_delay=data['retry_delay'],
            timeout=data.get('timeout'),
            created_at=datetime.fromisoformat(data['created_at'])
        )


class TaskQueue(ABC):
    """Abstract task queue interface"""

    @abstractmethod
    async def enqueue(self, task: TaskDefinition) -> str:
        """Enqueue a task"""
        pass

    @abstractmethod
    async def dequeue(self, timeout: float = 1.0) -> Optional[TaskDefinition]:
        """Dequeue a task"""
        pass

    @abstractmethod
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result"""
        pass

    @abstractmethod
    async def set_task_result(self, result: TaskResult) -> None:
        """Set task result"""
        pass

    @abstractmethod
    async def get_queue_info(self) -> Dict[str, Any]:
        """Get queue information"""
        pass


class MemoryTaskQueue(TaskQueue):
    """In-memory task queue implementation"""

    def __init__(self, max_size: int = 10000):
        self.pending_tasks: List[TaskDefinition] = []
        self.running_tasks: Dict[str, TaskDefinition] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.max_size = max_size
        self._lock = asyncio.Lock()

    async def enqueue(self, task: TaskDefinition) -> str:
        """Enqueue a task"""
        async with self._lock:
            if len(self.pending_tasks) >= self.max_size:
                raise ServiceError(f"Task queue full (max: {self.max_size})")

            # Insert based on priority
            self.pending_tasks.append(task)
            self.pending_tasks.sort(key=lambda t: t.priority.value, reverse=True)

            logger.debug(f"Enqueued task {task.task_id} with priority {task.priority.name}")
            return task.task_id

    async def dequeue(self, timeout: float = 1.0) -> Optional[TaskDefinition]:
        """Dequeue a task"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            async with self._lock:
                if self.pending_tasks:
                    task = self.pending_tasks.pop(0)
                    self.running_tasks[task.task_id] = task
                    logger.debug(f"Dequeued task {task.task_id}")
                    return task

            await asyncio.sleep(0.1)

        return None

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result"""
        async with self._lock:
            return self.task_results.get(task_id)

    async def set_task_result(self, result: TaskResult) -> None:
        """Set task result"""
        async with self._lock:
            self.task_results[result.task_id] = result
            # Remove from running tasks
            if result.task_id in self.running_tasks:
                del self.running_tasks[result.task_id]

    async def get_queue_info(self) -> Dict[str, Any]:
        """Get queue information"""
        async with self._lock:
            return {
                "pending_tasks": len(self.pending_tasks),
                "running_tasks": len(self.running_tasks),
                "completed_tasks": len([r for r in self.task_results.values() if r.status == TaskStatus.COMPLETED]),
                "failed_tasks": len([r for r in self.task_results.values() if r.status == TaskStatus.FAILED]),
                "max_size": self.max_size
            }


class RedisTaskQueue(TaskQueue):
    """Redis-based task queue implementation"""

    def __init__(self, redis_url: str = None):
        self.redis_client = None
        self._initialize_redis(redis_url)

    def _initialize_redis(self, redis_url: str = None):
        """Initialize Redis connection"""
        try:
            settings = get_settings()
            url = redis_url or getattr(settings, 'REDIS_URL', None)

            if url:
                self.redis_client = redis.from_url(
                    url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis task queue initialized successfully")
            else:
                logger.warning("Redis URL not configured for task queue")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis task queue: {e}")
            self.redis_client = None

    async def enqueue(self, task: TaskDefinition) -> str:
        """Enqueue a task in Redis"""
        if not self.redis_client:
            raise ServiceError("Redis task queue not available")

        try:
            # Store task data
            task_key = f"task:{task.task_id}"
            self.redis_client.hset(task_key, mapping=task.to_dict())
            self.redis_client.expire(task_key, 3600)  # 1 hour TTL

            # Add to priority queue
            self.redis_client.zadd("pending_tasks", {task.task_id: task.priority.value})

            logger.debug(f"Enqueued task {task.task_id} in Redis")
            return task.task_id
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.task_id}: {e}")
            raise ServiceError(f"Failed to enqueue task: {str(e)}")

    async def dequeue(self, timeout: float = 1.0) -> Optional[TaskDefinition]:
        """Dequeue a task from Redis"""
        if not self.redis_client:
            return None

        try:
            # Get highest priority task
            result = self.redis_client.zpopmax("pending_tasks", 1)
            if not result:
                return None

            task_id, _ = result[0]

            # Get task data
            task_key = f"task:{task_id}"
            task_data = self.redis_client.hgetall(task_key)
            if not task_data:
                return None

            # Convert back to TaskDefinition
            task = TaskDefinition.from_dict(task_data)

            # Mark as running
            self.redis_client.sadd("running_tasks", task_id)

            logger.debug(f"Dequeued task {task_id} from Redis")
            return task
        except Exception as e:
            logger.error(f"Failed to dequeue task: {e}")
            return None

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result from Redis"""
        if not self.redis_client:
            return None

        try:
            result_key = f"result:{task_id}"
            result_data = self.redis_client.hgetall(result_key)
            if not result_data:
                return None

            # Convert back to TaskResult
            return TaskResult(
                task_id=result_data['task_id'],
                status=TaskStatus(result_data['status']),
                result=json.loads(result_data.get('result', 'null')),
                error=result_data.get('error'),
                started_at=datetime.fromisoformat(result_data['started_at']) if result_data.get('started_at') else None,
                completed_at=datetime.fromisoformat(result_data['completed_at']) if result_data.get('completed_at') else None,
                execution_time=float(result_data['execution_time']) if result_data.get('execution_time') else None
            )
        except Exception as e:
            logger.error(f"Failed to get task result {task_id}: {e}")
            return None

    async def set_task_result(self, result: TaskResult) -> None:
        """Set task result in Redis"""
        if not self.redis_client:
            return

        try:
            result_key = f"result:{result.task_id}"
            result_data = result.to_dict()
            result_data['result'] = json.dumps(result_data['result'])

            self.redis_client.hset(result_key, mapping=result_data)
            self.redis_client.expire(result_key, 3600)  # 1 hour TTL

            # Remove from running tasks
            self.redis_client.srem("running_tasks", result.task_id)

            logger.debug(f"Set task result for {result.task_id}")
        except Exception as e:
            logger.error(f"Failed to set task result {result.task_id}: {e}")

    async def get_queue_info(self) -> Dict[str, Any]:
        """Get queue information from Redis"""
        if not self.redis_client:
            return {"error": "Redis not available"}

        try:
            return {
                "pending_tasks": self.redis_client.zcard("pending_tasks"),
                "running_tasks": self.redis_client.scard("running_tasks"),
                "redis_available": True
            }
        except Exception as e:
            logger.error(f"Failed to get queue info: {e}")
            return {"error": str(e)}


class TaskWorker:
    """Task worker that processes tasks from the queue"""

    def __init__(self, queue: TaskQueue, worker_id: str = None):
        self.queue = queue
        self.worker_id = worker_id or str(uuid.uuid4())[:8]
        self.running = False
        self.task_registry: Dict[str, Callable] = {}
        self.current_task: Optional[str] = None
        self.stats = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "started_at": None
        }

    def register_task(self, name: str, func: Callable):
        """Register a task function"""
        self.task_registry[name] = func
        logger.info(f"Worker {self.worker_id} registered task: {name}")

    async def start(self):
        """Start the worker"""
        self.running = True
        self.stats["started_at"] = datetime.utcnow()
        logger.info(f"Task worker {self.worker_id} started")

        while self.running:
            try:
                await self._process_next_task()
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                await asyncio.sleep(1)

    async def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info(f"Task worker {self.worker_id} stopping")

    async def _process_next_task(self):
        """Process the next task from the queue"""
        task = await self.queue.dequeue(timeout=5.0)
        if not task:
            return

        self.current_task = task.task_id
        logger.info(f"Worker {self.worker_id} processing task {task.task_id}")

        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow()
        )

        try:
            # Get the task function
            if task.func_name not in self.task_registry:
                raise ValueError(f"Unknown task function: {task.func_name}")

            func = self.task_registry[task.func_name]

            # Execute with timeout if specified
            if task.timeout:
                task_result = await asyncio.wait_for(
                    self._execute_task(func, task.args, task.kwargs),
                    timeout=task.timeout
                )
            else:
                task_result = await self._execute_task(func, task.args, task.kwargs)

            # Success
            result.status = TaskStatus.COMPLETED
            result.result = task_result
            result.completed_at = datetime.utcnow()
            result.execution_time = (result.completed_at - result.started_at).total_seconds()

            self.stats["tasks_processed"] += 1
            logger.info(f"Task {task.task_id} completed successfully")

        except Exception as e:
            # Failure
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.utcnow()
            if result.started_at:
                result.execution_time = (result.completed_at - result.started_at).total_seconds()

            self.stats["tasks_failed"] += 1
            logger.error(f"Task {task.task_id} failed: {e}")

        finally:
            await self.queue.set_task_result(result)
            self.current_task = None

    async def _execute_task(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Execute task function"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        uptime = None
        if self.stats["started_at"]:
            uptime = (datetime.utcnow() - self.stats["started_at"]).total_seconds()

        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "current_task": self.current_task,
            "uptime_seconds": uptime,
            **self.stats,
            "registered_tasks": list(self.task_registry.keys())
        }


class TaskManager:
    """High-level task management interface"""

    def __init__(self, use_redis: bool = True):
        # Initialize queue
        if use_redis and REDIS_AVAILABLE:
            self.queue = RedisTaskQueue()
        else:
            self.queue = MemoryTaskQueue()

        self.workers: List[TaskWorker] = []
        self.task_registry: Dict[str, Callable] = {}

    def register_task(self, name: str = None):
        """Decorator to register a task function"""
        def decorator(func: Callable) -> Callable:
            task_name = name or func.__name__
            self.task_registry[task_name] = func

            # Register with all workers
            for worker in self.workers:
                worker.register_task(task_name, func)

            logger.info(f"Registered task: {task_name}")
            return func

        return decorator

    async def enqueue_task(
        self,
        func_name: str,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout: float = None,
        **kwargs
    ) -> str:
        """Enqueue a task for processing"""
        task_id = str(uuid.uuid4())
        task = TaskDefinition(
            task_id=task_id,
            func_name=func_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )

        await self.queue.enqueue(task)
        logger.info(f"Enqueued task {func_name} with ID {task_id}")
        return task_id

    async def get_task_result(self, task_id: str, timeout: float = None) -> Optional[TaskResult]:
        """Get task result, optionally waiting for completion"""
        if timeout is None:
            return await self.queue.get_task_result(task_id)

        # Wait for result with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = await self.queue.get_task_result(task_id)
            if result and result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return result
            await asyncio.sleep(0.5)

        return None

    async def start_workers(self, num_workers: int = 2):
        """Start worker processes"""
        for i in range(num_workers):
            worker = TaskWorker(self.queue, f"worker-{i+1}")

            # Register all tasks with worker
            for name, func in self.task_registry.items():
                worker.register_task(name, func)

            self.workers.append(worker)

            # Start worker in background
            asyncio.create_task(worker.start())

        logger.info(f"Started {num_workers} task workers")

    async def stop_workers(self):
        """Stop all workers"""
        for worker in self.workers:
            await worker.stop()

        self.workers.clear()
        logger.info("Stopped all task workers")

    async def get_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        queue_info = await self.queue.get_queue_info()
        worker_stats = [worker.get_stats() for worker in self.workers]

        return {
            "queue": queue_info,
            "workers": worker_stats,
            "registered_tasks": list(self.task_registry.keys()),
            "total_workers": len(self.workers)
        }


# Global task manager instance
task_manager = TaskManager()


def background_task(
    name: str = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3,
    timeout: float = None
):
    """Decorator to mark a function as a background task"""
    def decorator(func: Callable) -> Callable:
        # Register the task
        task_name = name or func.__name__
        task_manager.register_task(task_name)(func)

        # Create an async wrapper that enqueues the task
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await task_manager.enqueue_task(
                task_name,
                *args,
                priority=priority,
                max_retries=max_retries,
                timeout=timeout,
                **kwargs
            )

        # For sync functions, provide a sync interface
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # This would require an event loop
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            except RuntimeError:
                return asyncio.run(async_wrapper(*args, **kwargs))

        # Mark as background task
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper._is_background_task = True
        wrapper._original_func = func
        wrapper._task_name = task_name

        return wrapper

    return decorator