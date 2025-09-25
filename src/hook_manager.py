"""
Hook Manager - Core event-driven hook system for Maricopa Property Search
Provides a comprehensive hook architecture for extending application functionality
"""
import asyncio
import functools
import inspect
import logging
import threading
import time
import traceback
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from logging_config import get_logger, log_exception

logger = get_logger(__name__)


class HookPriority(Enum):
    """Hook execution priority levels"""

    HIGHEST = 1000
    HIGH = 750
    NORMAL = 500
    LOW = 250
    LOWEST = 100


class HookStatus(Enum):
    """Hook execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class HookResult:
    """Result of hook execution"""

    status: HookStatus
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HookContext:
    """Context information passed to hooks"""

    event_name: str
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None


class Hook(ABC):
    """Base hook class for all hook implementations"""
    def __init__(self, name: str, priority: HookPriority = HookPriority.NORMAL):
        self.name = name
        self.priority = priority
        self.enabled = True
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None
        self.total_execution_time = 0.0

    @abstractmethod
    async def execute(self, context: HookContext) -> HookResult:
        """Execute the hook with given context"""
        pass
    def can_execute(self, context: HookContext) -> bool:
        """Check if hook can execute in given context"""
        return self.enabled
def __str__(self):
        return f"Hook({self.name}, priority={self.priority.value})"


class HookManager:
    """Central hook management system"""
    def __init__(self):
        self._hooks: Dict[str, List[Hook]] = defaultdict(list)
        self._middleware: List[Callable] = []
        self._hook_stats: Dict[str, Dict] = defaultdict(dict)
        self._lock = threading.RLock()
        self._event_history: List[Tuple[str, datetime, HookContext]] = []
        self._max_history = 1000
        self._error_handlers: List[Callable] = []

        logger.info("Hook Manager initialized")
def register_hook(self, event_name: str, hook: Hook):
        """Register a hook for specific event"""
        with self._lock:
            self._hooks[event_name].append(hook)
            # Sort by priority (highest first)
            self._hooks[event_name].sort(key=lambda h: h.priority.value, reverse=True)

            logger.info(
                f"Registered hook '{hook.name}' for event '{event_name}' with priority {hook.priority.name}"
            )
    def unregister_hook(self, event_name: str, hook_name: str) -> bool:
        """Unregister a hook by name"""
        with self._lock:
            hooks = self._hooks.get(event_name, [])
            for i, hook in enumerate(hooks):
                if hook.name == hook_name:
                    del hooks[i]
                    logger.info(
                        f"Unregistered hook '{hook_name}' from event '{event_name}'"
                    )
                    return True

            logger.warning(f"Hook '{hook_name}' not found for event '{event_name}'")
            return False
def add_middleware(self, middleware: Callable):
        """Add middleware that runs before all hooks"""
        self._middleware.append(middleware)
        logger.info(f"Added middleware: {middleware.__name__}")
def add_error_handler(self, handler: Callable):
        """Add global error handler for hook failures"""
        self._error_handlers.append(handler)
        logger.info(f"Added error handler: {handler.__name__}")

    async def emit(self, event_name: str, context: HookContext) -> List[HookResult]:
        """Emit an event and execute all registered hooks"""
        start_time = time.time()
        results = []

        # Record event in history
        self._record_event(event_name, context)

        logger.debug(f"Emitting event '{event_name}' with context: {context.source}")

        try:
            # Run middleware first
            for middleware in self._middleware:
                try:
                    context = await self._run_middleware(middleware, context)
                except Exception as e:
                    logger.error(f"Middleware error: {e}")
                    continue

            # Get hooks for this event
            hooks = self._hooks.get(event_name, [])
            if not hooks:
                logger.debug(f"No hooks registered for event '{event_name}'")
                return results

            # Execute hooks in priority order
            for hook in hooks:
                if not hook.can_execute(context):
                    logger.debug(f"Hook '{hook.name}' skipped (cannot execute)")
                    continue

                result = await self._execute_hook(hook, context)
                results.append(result)

                # Update hook statistics
                self._update_hook_stats(hook, result)

                # Handle hook failure
                if result.status == HookStatus.FAILED:
                    await self._handle_hook_error(hook, result, context)

            execution_time = time.time() - start_time
            logger.debug(
                f"Event '{event_name}' processed in {execution_time:.3f}s with {len(results)} hooks"
            )

        except Exception as e:
            logger.error(f"Error processing event '{event_name}': {e}")
            log_exception(logger, e, f"processing event '{event_name}'")

        return results
    def emit_sync(self, event_name: str, context: HookContext) -> List[HookResult]:
        """Synchronous version of emit for non-async contexts"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create new task if loop is running
                task = asyncio.create_task(self.emit(event_name, context))
                return asyncio.run_coroutine_threadsafe(task, loop).result(timeout=30)
            else:
                # Run in existing loop
                return loop.run_until_complete(self.emit(event_name, context))
        except Exception:
            # Fallback to new event loop
            return asyncio.run(self.emit(event_name, context))

    async def _execute_hook(self, hook: Hook, context: HookContext) -> HookResult:
        """Execute a single hook with timing and error handling"""
        start_time = time.time()

        try:
            logger.debug(
                f"Executing hook '{hook.name}' for event '{context.event_name}'"
            )

            result = await hook.execute(context)
            execution_time = time.time() - start_time

            # Update hook execution data
            hook.execution_count += 1
            hook.last_execution = datetime.now()
            hook.total_execution_time += execution_time

            if result.status == HookStatus.SUCCESS:
                logger.debug(
                    f"Hook '{hook.name}' completed successfully in {execution_time:.3f}s"
                )

            result.execution_time = execution_time
            return result

        except Exception as e:
            execution_time = time.time() - start_time

            logger.error(f"Hook '{hook.name}' failed after {execution_time:.3f}s: {e}")
            log_exception(logger, e, f"executing hook '{hook.name}'")

            return HookResult(
                status=HookStatus.FAILED,
                error=e,
                execution_time=execution_time,
                metadata={"traceback": traceback.format_exc()},
            )

    async def _run_middleware(
        self, middleware: Callable, context: HookContext
    ) -> HookContext:
        """Run middleware function"""
        if inspect.iscoroutinefunction(middleware):
            return await middleware(context)
        else:
            return middleware(context)

    async def _handle_hook_error(
        self, hook: Hook, result: HookResult, context: HookContext
    ):
        """Handle hook execution errors"""
        for handler in self._error_handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(hook, result, context)
                else:
                    handler(hook, result, context)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")
def _update_hook_stats(self, hook: Hook, result: HookResult):
        """Update hook execution statistics"""
        stats = self._hook_stats[hook.name]

        stats["total_executions"] = hook.execution_count
        stats["total_time"] = hook.total_execution_time
        stats["avg_time"] = (
            hook.total_execution_time / hook.execution_count
            if hook.execution_count > 0
            else 0
        )
        stats["last_execution"] = hook.last_execution
        stats["last_status"] = result.status.value

        if result.status == HookStatus.FAILED:
            stats["failure_count"] = stats.get("failure_count", 0) + 1
        else:
            stats["success_count"] = stats.get("success_count", 0) + 1
def _record_event(self, event_name: str, context: HookContext):
        """Record event in history"""
        self._event_history.append((event_name, datetime.now(), context))

        # Trim history if too long
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history :]
    def get_hook_stats(self, hook_name: Optional[str] = None) -> Dict:
        """Get hook execution statistics"""
        if hook_name:
            return self._hook_stats.get(hook_name, {})
        return dict(self._hook_stats)
    def get_registered_hooks(self) -> Dict[str, List[str]]:
        """Get all registered hooks by event"""
        return {
            event: [hook.name for hook in hooks] for event, hooks in self._hooks.items()
        }
    def get_event_history(self, limit: int = 100) -> List[Tuple[str, datetime, str]]:
        """Get recent event history"""
        return [
            (event, timestamp, context.source)
            for event, timestamp, context in self._event_history[-limit:]
        ]

    @contextmanager
def hook_scope(self, event_name: str, source: str, **data):
        """Context manager for scoped hook execution"""
        context = HookContext(
            event_name=event_name, timestamp=datetime.now(), source=source, data=data
        )

        # Emit pre-hook event
        try:
            self.emit_sync(f"{event_name}.before", context)
            yield context
            # Emit post-hook event
            self.emit_sync(f"{event_name}.after", context)
        except Exception as e:
            # Emit error event
            error_context = HookContext(
                event_name=f"{event_name}.error",
                timestamp=datetime.now(),
                source=source,
                data={**data, "error": str(e), "original_context": context},
            )
            self.emit_sync(f"{event_name}.error", error_context)
            raise
def clear_stats(self):
        """Clear all hook statistics"""
        self._hook_stats.clear()
        self._event_history.clear()
        logger.info("Hook statistics cleared")


# Global hook manager instance
_hook_manager = None
    def get_hook_manager() -> HookManager:
    """Get the global hook manager instance"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager
def hook(event_name: str, priority: HookPriority = HookPriority.NORMAL):
    """Decorator to register a function as a hook"""
    def decorator(func: Callable) -> Callable:
class FunctionHook(Hook):
    def __init__(self):
                super().__init__(func.__name__, priority)
                self.func = func

            async def execute(self, context: HookContext) -> HookResult:
                try:
                    if inspect.iscoroutinefunction(self.func):
                        result = await self.func(context)
                    else:
                        result = self.func(context)

                    return HookResult(status=HookStatus.SUCCESS, result=result)
                except Exception as e:
                    return HookResult(status=HookStatus.FAILED, error=e)

        hook_instance = FunctionHook()
        get_hook_manager().register_hook(event_name, hook_instance)

        return func

    return decorator
    def emit_hook(event_name: str, source: str, **data) -> List[HookResult]:
    """Convenience function to emit a hook"""
    context = HookContext(
        event_name=event_name, timestamp=datetime.now(), source=source, data=data
    )
    return get_hook_manager().emit_sync(event_name, context)


async def emit_hook_async(event_name: str, source: str, **data) -> List[HookResult]:
    """Convenience function to emit a hook asynchronously"""
    context = HookContext(
        event_name=event_name, timestamp=datetime.now(), source=source, data=data
    )
    return await get_hook_manager().emit(event_name, context)
