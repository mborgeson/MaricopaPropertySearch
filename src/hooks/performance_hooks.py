"""
Performance Monitoring Hooks
Comprehensive performance tracking, profiling, and optimization suggestions
"""
import asyncio
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, NamedTuple, Optional

import psutil

from hook_manager import (
    Hook,
    HookContext,
    HookPriority,
    HookResult,
    HookStatus,
    get_hook_manager,
)
from logging_config import get_logger, log_exception

logger = get_logger(__name__)


class PerformanceMetric(NamedTuple):
    """Performance metric data structure"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any]


class PerformanceTrackingHook(Hook):
    """Hook for tracking general performance metrics"""
    def __init__(self):
        super().__init__("performance_tracking", HookPriority.NORMAL)
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.operation_times = defaultdict(list)
        self.active_operations = {}
        self.performance_thresholds = {
            "slow_operation": 5.0,  # seconds
            "very_slow_operation": 10.0,  # seconds
            "memory_warning": 500,  # MB
            "memory_critical": 1000,  # MB
            "cpu_warning": 80,  # percent
            "cpu_critical": 95,  # percent
        }

    async def execute(self, context: HookContext) -> HookResult:
        """Track performance metrics"""
        try:
            event_type = context.event_name.split(".")[-1]
            perf_data = context.data

            if event_type == "start":
                return await self._handle_operation_start(context, perf_data)
            elif event_type == "end":
                return await self._handle_operation_end(context, perf_data)
            elif event_type == "metric":
                return await self._handle_metric_update(context, perf_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"Performance tracking hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _handle_operation_start(
        self, context: HookContext, perf_data: Dict
    ) -> HookResult:
        """Handle operation start tracking"""
        operation_id = perf_data.get("operation_id", f"op_{int(time.time())}")
        operation_name = perf_data.get("operation_name", "unknown")
        start_time = time.time()

        # Record operation start
        self.active_operations[operation_id] = {
            "name": operation_name,
            "start_time": start_time,
            "source": context.source,
            "metadata": perf_data.get("metadata", {}),
        }

        # Capture system metrics at start
        system_metrics = self._capture_system_metrics()

        logger.debug(f"Performance tracking started: {operation_name} [{operation_id}]")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "operation_id": operation_id,
                "start_time": start_time,
                "system_metrics": system_metrics,
            },
        )

    async def _handle_operation_end(
        self, context: HookContext, perf_data: Dict
    ) -> HookResult:
        """Handle operation end tracking"""
        operation_id = perf_data.get("operation_id")
        end_time = time.time()

        if operation_id not in self.active_operations:
            logger.warning(f"End tracking for unknown operation: {operation_id}")
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "Unknown operation"}
            )

        op_info = self.active_operations[operation_id]
        execution_time = end_time - op_info["start_time"]

        # Capture end system metrics
        end_system_metrics = self._capture_system_metrics()

        # Create performance record
        perf_record = {
            "operation_name": op_info["name"],
            "execution_time": execution_time,
            "start_time": op_info["start_time"],
            "end_time": end_time,
            "timestamp": datetime.now(),
            "source": op_info["source"],
            "metadata": op_info["metadata"],
            "system_metrics": end_system_metrics,
            "success": perf_data.get("success", True),
        }

        # Store metrics
        self.operation_times[op_info["name"]].append(execution_time)
        self.metrics_history[op_info["name"]].append(perf_record)

        # Analyze performance
        performance_analysis = self._analyze_performance(
            op_info["name"], execution_time, end_system_metrics
        )

        # Log performance
        self._log_performance(op_info["name"], execution_time, performance_analysis)

        # Clean up
        del self.active_operations[operation_id]

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "operation_id": operation_id,
                "execution_time": execution_time,
                "performance_record": perf_record,
                "analysis": performance_analysis,
            },
            metadata={
                "execution_time": execution_time,
                "performance_level": performance_analysis["level"],
            },
        )

    async def _handle_metric_update(
        self, context: HookContext, perf_data: Dict
    ) -> HookResult:
        """Handle custom metric updates"""
        metric_name = perf_data.get("metric_name")
        metric_value = perf_data.get("metric_value")
        metric_unit = perf_data.get("metric_unit", "")
        metadata = perf_data.get("metadata", {})

        if not metric_name or metric_value is None:
            return HookResult(
                status=HookStatus.FAILED,
                result={"error": "Missing metric name or value"},
            )

        # Create metric record
        metric = PerformanceMetric(
            name=metric_name,
            value=float(metric_value),
            unit=metric_unit,
            timestamp=datetime.now(),
            metadata=metadata,
        )

        # Store metric
        self.metrics_history[metric_name].append(metric)

        logger.debug(
            f"Performance metric updated: {metric_name} = {metric_value} {metric_unit}"
        )

        return HookResult(
            status=HookStatus.SUCCESS,
            result={"metric_recorded": True, "metric": metric._asdict()},
        )
    def _capture_system_metrics(self) -> Dict[str, Any]:
        """Capture current system performance metrics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            # System-wide metrics
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent()

            return {
                "timestamp": time.time(),
                "process": {
                    "memory_rss_mb": memory_info.rss / (1024 * 1024),
                    "memory_vms_mb": memory_info.vms / (1024 * 1024),
                    "cpu_percent": cpu_percent,
                    "num_threads": process.num_threads(),
                },
                "system": {
                    "memory_percent": system_memory.percent,
                    "memory_available_gb": system_memory.available / (1024**3),
                    "cpu_percent": system_cpu,
                    "disk_usage_percent": psutil.disk_usage("/").percent,
                },
            }
        except Exception as e:
            logger.warning(f"Failed to capture system metrics: {e}")
            return {"error": str(e)}
    def _analyze_performance(
        self, operation_name: str, execution_time: float, system_metrics: Dict
    ) -> Dict[str, Any]:
        """Analyze operation performance"""
        analysis = {"level": "good", "issues": [], "suggestions": []}

        # Analyze execution time
        if execution_time > self.performance_thresholds["very_slow_operation"]:
            analysis["level"] = "very_poor"
            analysis["issues"].append(
                f"Very slow execution time: {execution_time:.2f}s"
            )
            analysis["suggestions"].append(
                "Consider optimization or breaking into smaller operations"
            )
        elif execution_time > self.performance_thresholds["slow_operation"]:
            analysis["level"] = "poor"
            analysis["issues"].append(f"Slow execution time: {execution_time:.2f}s")
            analysis["suggestions"].append("Consider performance optimization")

        # Analyze memory usage
        if "process" in system_metrics:
            memory_mb = system_metrics["process"].get("memory_rss_mb", 0)
            if memory_mb > self.performance_thresholds["memory_critical"]:
                analysis["level"] = "very_poor"
                analysis["issues"].append(f"Critical memory usage: {memory_mb:.1f} MB")
                analysis["suggestions"].append(
                    "Investigate memory leaks or reduce memory usage"
                )
            elif memory_mb > self.performance_thresholds["memory_warning"]:
                if analysis["level"] == "good":
                    analysis["level"] = "warning"
                analysis["issues"].append(f"High memory usage: {memory_mb:.1f} MB")
                analysis["suggestions"].append("Monitor memory usage trends")

        # Analyze CPU usage
        if "process" in system_metrics:
            cpu_percent = system_metrics["process"].get("cpu_percent", 0)
            if cpu_percent > self.performance_thresholds["cpu_critical"]:
                analysis["level"] = "very_poor"
                analysis["issues"].append(f"Critical CPU usage: {cpu_percent:.1f}%")
                analysis["suggestions"].append("Optimize CPU-intensive operations")
            elif cpu_percent > self.performance_thresholds["cpu_warning"]:
                if analysis["level"] == "good":
                    analysis["level"] = "warning"
                analysis["issues"].append(f"High CPU usage: {cpu_percent:.1f}%")

        # Historical comparison
        if len(self.operation_times[operation_name]) > 5:
            avg_time = sum(self.operation_times[operation_name]) / len(
                self.operation_times[operation_name]
            )
            if execution_time > avg_time * 2:
                analysis["issues"].append(
                    f"Execution time is {execution_time/avg_time:.1f}x slower than average"
                )
                analysis["suggestions"].append("Compare with historical performance")

        return analysis
    def _log_performance(
        self, operation_name: str, execution_time: float, analysis: Dict
    ):
        """Log performance based on analysis"""
        level = analysis["level"]

        if level == "very_poor":
            logger.error(
                f"VERY POOR PERFORMANCE: {operation_name} ({execution_time:.3f}s) - Issues: {analysis['issues']}"
            )
        elif level == "poor":
            logger.warning(
                f"POOR PERFORMANCE: {operation_name} ({execution_time:.3f}s) - Issues: {analysis['issues']}"
            )
        elif level == "warning":
            logger.warning(
                f"Performance warning: {operation_name} ({execution_time:.3f}s) - Issues: {analysis['issues']}"
            )
        else:
            logger.debug(f"Performance: {operation_name} ({execution_time:.3f}s)")
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        summary = {
            "time_period_hours": hours,
            "operations": {},
            "system_metrics": self._get_system_metrics_summary(),
            "performance_issues": 0,
        }

        for operation_name, records in self.metrics_history.items():
            recent_records = [r for r in records if r["timestamp"] > cutoff_time]

            if recent_records:
                execution_times = [r["execution_time"] for r in recent_records]
                successful_ops = [r for r in recent_records if r.get("success", True)]

                summary["operations"][operation_name] = {
                    "total_executions": len(recent_records),
                    "successful_executions": len(successful_ops),
                    "success_rate": (len(successful_ops) / len(recent_records)) * 100,
                    "avg_execution_time": sum(execution_times) / len(execution_times),
                    "min_execution_time": min(execution_times),
                    "max_execution_time": max(execution_times),
                    "slow_operations": len(
                        [
                            t
                            for t in execution_times
                            if t > self.performance_thresholds["slow_operation"]
                        ]
                    ),
                }

                summary["performance_issues"] += summary["operations"][operation_name][
                    "slow_operations"
                ]

        return summary
    def _get_system_metrics_summary(self) -> Dict[str, Any]:
        """Get system metrics summary"""
        current_metrics = self._capture_system_metrics()

        return {"current": current_metrics, "thresholds": self.performance_thresholds}


class MemoryProfilerHook(Hook):
    """Hook for memory profiling and leak detection"""
    def __init__(self):
        super().__init__("memory_profiler", HookPriority.LOW)
        self.memory_snapshots = deque(maxlen=100)
        self.memory_growth_threshold = 50  # MB
        self.snapshot_interval = 60  # seconds
        self.last_snapshot_time = 0

    async def execute(self, context: HookContext) -> HookResult:
        """Profile memory usage"""
        try:
            current_time = time.time()

            # Take snapshot if enough time has passed
            if current_time - self.last_snapshot_time >= self.snapshot_interval:
                snapshot = self._take_memory_snapshot()
                self.memory_snapshots.append(snapshot)
                self.last_snapshot_time = current_time

                # Analyze for memory leaks
                leak_analysis = self._analyze_memory_leaks()

                logger.debug(f"Memory snapshot taken: {snapshot['memory_mb']:.1f} MB")

                if leak_analysis["potential_leak"]:
                    logger.warning(f"Potential memory leak detected: {leak_analysis}")

                return HookResult(
                    status=HookStatus.SUCCESS,
                    result={
                        "snapshot_taken": True,
                        "memory_snapshot": snapshot,
                        "leak_analysis": leak_analysis,
                    },
                    metadata={"potential_leak": leak_analysis["potential_leak"]},
                )

            return HookResult(
                status=HookStatus.SUCCESS, result={"snapshot_taken": False}
            )

        except Exception as e:
            logger.error(f"Memory profiler hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)
    def _take_memory_snapshot(self) -> Dict[str, Any]:
        """Take a memory usage snapshot"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "timestamp": datetime.now(),
                "memory_mb": memory_info.rss / (1024 * 1024),
                "virtual_memory_mb": memory_info.vms / (1024 * 1024),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, "num_fds") else 0,
            }
        except Exception as e:
            logger.warning(f"Failed to take memory snapshot: {e}")
            return {"error": str(e)}
    def _analyze_memory_leaks(self) -> Dict[str, Any]:
        """Analyze memory snapshots for potential leaks"""
        if len(self.memory_snapshots) < 5:
            return {"potential_leak": False, "reason": "Insufficient data"}

        # Get recent snapshots
        recent_snapshots = list(self.memory_snapshots)[-5:]
        memory_values = [s["memory_mb"] for s in recent_snapshots if "memory_mb" in s]

        if len(memory_values) < 5:
            return {"potential_leak": False, "reason": "Insufficient valid snapshots"}

        # Check for consistent growth
        growth_trend = []
        for i in range(1, len(memory_values)):
            growth_trend.append(memory_values[i] - memory_values[i - 1])

        total_growth = memory_values[-1] - memory_values[0]
        avg_growth = sum(growth_trend) / len(growth_trend)

        potential_leak = (
            total_growth > self.memory_growth_threshold
            and avg_growth > 0
            and sum(1 for g in growth_trend if g > 0)
            >= len(growth_trend) * 0.8  # 80% positive growth
        )

        return {
            "potential_leak": potential_leak,
            "total_growth_mb": total_growth,
            "avg_growth_mb": avg_growth,
            "current_memory_mb": memory_values[-1],
            "snapshots_analyzed": len(memory_values),
        }
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory usage report"""
        if not self.memory_snapshots:
            return {"no_data": True}

        snapshots = [s for s in self.memory_snapshots if "memory_mb" in s]

        if not snapshots:
            return {"no_valid_data": True}

        memory_values = [s["memory_mb"] for s in snapshots]

        return {
            "total_snapshots": len(snapshots),
            "time_range_hours": (
                snapshots[-1]["timestamp"] - snapshots[0]["timestamp"]
            ).total_seconds()
            / 3600,
            "current_memory_mb": memory_values[-1],
            "min_memory_mb": min(memory_values),
            "max_memory_mb": max(memory_values),
            "avg_memory_mb": sum(memory_values) / len(memory_values),
            "total_growth_mb": memory_values[-1] - memory_values[0],
            "leak_analysis": self._analyze_memory_leaks(),
        }


# Register performance hooks
def register_performance_hooks():
    """Register all performance hooks with the hook manager"""
    hook_manager = get_hook_manager()

    # Register hooks
    hook_manager.register_hook("performance.start", PerformanceTrackingHook())
    hook_manager.register_hook("performance.end", PerformanceTrackingHook())
    hook_manager.register_hook("performance.metric", PerformanceTrackingHook())
    hook_manager.register_hook("system.monitor", MemoryProfilerHook())

    logger.info("Performance monitoring hooks registered successfully")


# Convenience functions and decorators
def performance_monitor(operation_name: str):
    """Decorator to monitor function performance"""
def decorator(func):
        async def async_wrapper(*args, **kwargs):
            from hook_manager import emit_hook

            operation_id = f"{operation_name}_{int(time.time())}"

            # Start monitoring
            emit_hook(
                "performance.start",
                "performance_monitor",
                operation_id=operation_id,
                operation_name=operation_name,
            )

            try:
                result = await func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                # End monitoring
                emit_hook(
                    "performance.end",
                    "performance_monitor",
                    operation_id=operation_id,
                    success=success,
                )

            return result
def sync_wrapper(*args, **kwargs):
            from hook_manager import emit_hook

            operation_id = f"{operation_name}_{int(time.time())}"

            # Start monitoring
            emit_hook(
                "performance.start",
                "performance_monitor",
                operation_id=operation_id,
                operation_name=operation_name,
            )

            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                # End monitoring
                emit_hook(
                    "performance.end",
                    "performance_monitor",
                    operation_id=operation_id,
                    success=success,
                )

            return result
import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def performance_scope(operation_name: str, metadata: Dict = None):
    """Context manager for performance monitoring"""
    from hook_manager import emit_hook

    operation_id = f"{operation_name}_{int(time.time())}"

    # Start monitoring
    emit_hook(
        "performance.start",
        "performance_scope",
        operation_id=operation_id,
        operation_name=operation_name,
        metadata=metadata or {},
    )

    try:
        yield operation_id
        success = True
    except Exception as e:
        success = False
        raise
    finally:
        # End monitoring
        emit_hook(
            "performance.end",
            "performance_scope",
            operation_id=operation_id,
            success=success,
        )
    def track_metric(
    metric_name: str, metric_value: float, unit: str = "", metadata: Dict = None
):
    """Track custom performance metric"""
    from hook_manager import emit_hook

    emit_hook(
        "performance.metric",
        "metric_tracker",
        metric_name=metric_name,
        metric_value=metric_value,
        metric_unit=unit,
        metadata=metadata or {},
    )
