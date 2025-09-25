"""
Database Lifecycle Hooks
Handles database connection lifecycle, transaction management, and optimization
"""
import asyncio
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import psycopg2

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


class DatabaseConnectionHook(Hook):
    """Hook for database connection lifecycle management"""
    def __init__(self):
        super().__init__("database_connection", HookPriority.HIGH)
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "connection_times": [],
        }
        self.connection_registry = {}

    async def execute(self, context: HookContext) -> HookResult:
        """Handle database connection events"""
        try:
            event_type = context.event_name.split(".")[-1]
            connection_data = context.data

            if event_type == "connect":
                return await self._handle_connection_start(context, connection_data)
            elif event_type == "connected":
                return await self._handle_connection_success(context, connection_data)
            elif event_type == "disconnect":
                return await self._handle_disconnection(context, connection_data)
            elif event_type == "error":
                return await self._handle_connection_error(context, connection_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"Database connection hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _handle_connection_start(
        self, context: HookContext, connection_data: Dict
    ) -> HookResult:
        """Handle connection attempt start"""
        connection_id = connection_data.get("connection_id", f"conn_{int(time.time())}")
        start_time = time.time()

        self.connection_registry[connection_id] = {
            "start_time": start_time,
            "source": context.source,
            "database": connection_data.get("database"),
            "host": connection_data.get("host"),
            "port": connection_data.get("port"),
        }

        self.connection_stats["total_connections"] += 1

        logger.debug(f"Database connection attempt started: {connection_id}")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={"connection_id": connection_id, "start_time": start_time},
        )

    async def _handle_connection_success(
        self, context: HookContext, connection_data: Dict
    ) -> HookResult:
        """Handle successful connection"""
        connection_id = connection_data.get("connection_id")
        current_time = time.time()

        if connection_id in self.connection_registry:
            conn_info = self.connection_registry[connection_id]
            connection_time = current_time - conn_info["start_time"]

            # Update statistics
            self.connection_stats["active_connections"] += 1
            self.connection_stats["connection_times"].append(connection_time)

            # Keep only last 100 connection times for average calculation
            if len(self.connection_stats["connection_times"]) > 100:
                self.connection_stats["connection_times"] = self.connection_stats[
                    "connection_times"
                ][-100:]

            # Update connection info
            conn_info.update(
                {
                    "connected_at": current_time,
                    "connection_time": connection_time,
                    "status": "active",
                }
            )

            logger.debug(
                f"Database connection successful: {connection_id} ({connection_time:.3f}s)"
            )

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    "connection_id": connection_id,
                    "connection_time": connection_time,
                    "active_connections": self.connection_stats["active_connections"],
                },
                metadata={"connection_time": connection_time},
            )
        else:
            logger.warning(
                f"Connection success for unknown connection: {connection_id}"
            )
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "Unknown connection"}
            )

    async def _handle_disconnection(
        self, context: HookContext, connection_data: Dict
    ) -> HookResult:
        """Handle connection disconnection"""
        connection_id = connection_data.get("connection_id")

        if connection_id in self.connection_registry:
            conn_info = self.connection_registry[connection_id]
            disconnect_time = time.time()

            # Calculate connection duration
            if "connected_at" in conn_info:
                duration = disconnect_time - conn_info["connected_at"]
                conn_info["duration"] = duration
            else:
                duration = 0

            # Update statistics
            if self.connection_stats["active_connections"] > 0:
                self.connection_stats["active_connections"] -= 1

            conn_info.update(
                {"disconnected_at": disconnect_time, "status": "disconnected"}
            )

            logger.debug(
                f"Database connection closed: {connection_id} (duration: {duration:.3f}s)"
            )

            # Clean up old connections
            self._cleanup_old_connections()

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    "connection_id": connection_id,
                    "duration": duration,
                    "active_connections": self.connection_stats["active_connections"],
                },
                metadata={"connection_duration": duration},
            )
        else:
            logger.warning(f"Disconnect for unknown connection: {connection_id}")
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "Unknown connection"}
            )

    async def _handle_connection_error(
        self, context: HookContext, connection_data: Dict
    ) -> HookResult:
        """Handle connection error"""
        connection_id = connection_data.get("connection_id")
        error = connection_data.get("error")

        self.connection_stats["failed_connections"] += 1

        if connection_id in self.connection_registry:
            conn_info = self.connection_registry[connection_id]
            conn_info.update(
                {"error": str(error), "status": "failed", "failed_at": time.time()}
            )

        logger.error(f"Database connection failed: {connection_id} - {error}")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "connection_id": connection_id,
                "error": str(error),
                "failed_connections": self.connection_stats["failed_connections"],
            },
            metadata={"connection_failed": True},
        )
def _cleanup_old_connections(self):
        """Clean up old connection entries"""
        cutoff_time = time.time() - 3600  # Keep connections from last hour

        to_remove = []
        for conn_id, conn_info in self.connection_registry.items():
            last_activity = conn_info.get("disconnected_at") or conn_info.get(
                "failed_at"
            )
            if last_activity and last_activity < cutoff_time:
                to_remove.append(conn_id)

        for conn_id in to_remove:
            del self.connection_registry[conn_id]
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        avg_connection_time = 0
        if self.connection_stats["connection_times"]:
            avg_connection_time = sum(self.connection_stats["connection_times"]) / len(
                self.connection_stats["connection_times"]
            )

        return {
            "total_connections": self.connection_stats["total_connections"],
            "active_connections": self.connection_stats["active_connections"],
            "failed_connections": self.connection_stats["failed_connections"],
            "success_rate": (
                (
                    self.connection_stats["total_connections"]
                    - self.connection_stats["failed_connections"]
                )
                / max(1, self.connection_stats["total_connections"])
            )
            * 100,
            "avg_connection_time": avg_connection_time,
            "recent_connections": len(self.connection_registry),
        }


class DatabaseTransactionHook(Hook):
    """Hook for database transaction management"""
    def __init__(self):
        super().__init__("database_transaction", HookPriority.HIGH)
        self.transaction_stats = {
            "total_transactions": 0,
            "committed_transactions": 0,
            "rolled_back_transactions": 0,
            "transaction_times": [],
        }
        self.active_transactions = {}

    async def execute(self, context: HookContext) -> HookResult:
        """Handle database transaction events"""
        try:
            event_type = context.event_name.split(".")[-1]
            transaction_data = context.data

            if event_type == "begin":
                return await self._handle_transaction_begin(context, transaction_data)
            elif event_type == "commit":
                return await self._handle_transaction_commit(context, transaction_data)
            elif event_type == "rollback":
                return await self._handle_transaction_rollback(
                    context, transaction_data
                )
            elif event_type == "error":
                return await self._handle_transaction_error(context, transaction_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"Database transaction hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _handle_transaction_begin(
        self, context: HookContext, transaction_data: Dict
    ) -> HookResult:
        """Handle transaction begin"""
        transaction_id = transaction_data.get(
            "transaction_id", f"txn_{int(time.time())}"
        )
        start_time = time.time()

        self.active_transactions[transaction_id] = {
            "start_time": start_time,
            "source": context.source,
            "operations": [],
        }

        self.transaction_stats["total_transactions"] += 1

        logger.debug(f"Database transaction began: {transaction_id}")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={"transaction_id": transaction_id, "start_time": start_time},
        )

    async def _handle_transaction_commit(
        self, context: HookContext, transaction_data: Dict
    ) -> HookResult:
        """Handle transaction commit"""
        transaction_id = transaction_data.get("transaction_id")
        commit_time = time.time()

        if transaction_id in self.active_transactions:
            txn_info = self.active_transactions[transaction_id]
            duration = commit_time - txn_info["start_time"]

            # Update statistics
            self.transaction_stats["committed_transactions"] += 1
            self.transaction_stats["transaction_times"].append(duration)

            # Keep only last 100 transaction times
            if len(self.transaction_stats["transaction_times"]) > 100:
                self.transaction_stats["transaction_times"] = self.transaction_stats[
                    "transaction_times"
                ][-100:]

            logger.debug(
                f"Database transaction committed: {transaction_id} ({duration:.3f}s)"
            )

            # Clean up
            del self.active_transactions[transaction_id]

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    "transaction_id": transaction_id,
                    "duration": duration,
                    "operations": len(txn_info.get("operations", [])),
                },
                metadata={"transaction_duration": duration},
            )
        else:
            logger.warning(f"Commit for unknown transaction: {transaction_id}")
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "Unknown transaction"}
            )

    async def _handle_transaction_rollback(
        self, context: HookContext, transaction_data: Dict
    ) -> HookResult:
        """Handle transaction rollback"""
        transaction_id = transaction_data.get("transaction_id")
        rollback_time = time.time()
        reason = transaction_data.get("reason", "Unknown")

        if transaction_id in self.active_transactions:
            txn_info = self.active_transactions[transaction_id]
            duration = rollback_time - txn_info["start_time"]

            # Update statistics
            self.transaction_stats["rolled_back_transactions"] += 1

            logger.warning(
                f"Database transaction rolled back: {transaction_id} ({duration:.3f}s) - Reason: {reason}"
            )

            # Clean up
            del self.active_transactions[transaction_id]

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    "transaction_id": transaction_id,
                    "duration": duration,
                    "reason": reason,
                    "operations": len(txn_info.get("operations", [])),
                },
                metadata={"transaction_rolled_back": True},
            )
        else:
            logger.warning(f"Rollback for unknown transaction: {transaction_id}")
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "Unknown transaction"}
            )

    async def _handle_transaction_error(
        self, context: HookContext, transaction_data: Dict
    ) -> HookResult:
        """Handle transaction error"""
        transaction_id = transaction_data.get("transaction_id")
        error = transaction_data.get("error")

        logger.error(f"Database transaction error: {transaction_id} - {error}")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={"transaction_id": transaction_id, "error": str(error)},
            metadata={"transaction_error": True},
        )
    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics"""
        avg_transaction_time = 0
        if self.transaction_stats["transaction_times"]:
            avg_transaction_time = sum(
                self.transaction_stats["transaction_times"]
            ) / len(self.transaction_stats["transaction_times"])

        total_completed = (
            self.transaction_stats["committed_transactions"]
            + self.transaction_stats["rolled_back_transactions"]
        )
        success_rate = (
            self.transaction_stats["committed_transactions"] / max(1, total_completed)
        ) * 100

        return {
            "total_transactions": self.transaction_stats["total_transactions"],
            "committed_transactions": self.transaction_stats["committed_transactions"],
            "rolled_back_transactions": self.transaction_stats[
                "rolled_back_transactions"
            ],
            "active_transactions": len(self.active_transactions),
            "success_rate": success_rate,
            "avg_transaction_time": avg_transaction_time,
        }


class DatabaseQueryOptimizationHook(Hook):
    """Hook for database query optimization and monitoring"""
    def __init__(self):
        super().__init__("database_query_optimization", HookPriority.NORMAL)
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # seconds
        self.query_cache = {}
        self.max_cache_size = 100

    async def execute(self, context: HookContext) -> HookResult:
        """Handle database query optimization"""
        try:
            event_type = context.event_name.split(".")[-1]
            query_data = context.data

            if event_type == "before":
                return await self._handle_query_start(context, query_data)
            elif event_type == "after":
                return await self._handle_query_complete(context, query_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"Database query optimization hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _handle_query_start(
        self, context: HookContext, query_data: Dict
    ) -> HookResult:
        """Handle query start - analyze and optimize if possible"""
        query = query_data.get("query", "")
        query_hash = self._get_query_hash(query)

        # Check for slow query patterns
        optimization_suggestions = self._analyze_query(query)

        # Check query cache for execution plan
        cached_plan = self.query_cache.get(query_hash)

        start_time = time.time()

        result_data = {
            "query_hash": query_hash,
            "start_time": start_time,
            "optimization_suggestions": optimization_suggestions,
            "cached_plan": cached_plan is not None,
        }

        if optimization_suggestions:
            logger.warning(
                f"Query optimization suggestions: {optimization_suggestions}"
            )

        return HookResult(
            status=HookStatus.SUCCESS,
            result=result_data,
            metadata={"has_suggestions": len(optimization_suggestions) > 0},
        )

    async def _handle_query_complete(
        self, context: HookContext, query_data: Dict
    ) -> HookResult:
        """Handle query completion - record performance"""
        query = query_data.get("query", "")
        query_hash = self._get_query_hash(query)
        execution_time = query_data.get("execution_time", 0)
        row_count = query_data.get("row_count", 0)
        success = query_data.get("success", True)

        # Update query statistics
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                "query_pattern": self._get_query_pattern(query),
                "execution_count": 0,
                "total_time": 0,
                "min_time": float("inf"),
                "max_time": 0,
                "total_rows": 0,
                "error_count": 0,
            }

        stats = self.query_stats[query_hash]
        stats["execution_count"] += 1

        if success:
            stats["total_time"] += execution_time
            stats["min_time"] = min(stats["min_time"], execution_time)
            stats["max_time"] = max(stats["max_time"], execution_time)
            stats["total_rows"] += row_count
        else:
            stats["error_count"] += 1

        # Check for slow query
        is_slow = execution_time > self.slow_query_threshold
        if is_slow:
            logger.warning(f"SLOW QUERY detected: {query_hash} ({execution_time:.3f}s)")

        # Cache query execution plan for future optimization
        if success and execution_time < 0.1:  # Cache fast queries
            self._cache_query_plan(query_hash, query_data)

        avg_time = stats["total_time"] / max(
            1, stats["execution_count"] - stats["error_count"]
        )

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "query_hash": query_hash,
                "execution_time": execution_time,
                "is_slow": is_slow,
                "avg_time": avg_time,
                "execution_count": stats["execution_count"],
            },
            metadata={"is_slow": is_slow},
        )
    def _get_query_hash(self, query: str) -> str:
        """Generate hash for query identification"""
import hashlib

        return hashlib.md5(query.encode()).hexdigest()[:8]
    def _get_query_pattern(self, query: str) -> str:
        """Extract query pattern by removing specific values"""
import re

        # Convert to lowercase and normalize whitespace
        pattern = re.sub(r"\s+", " ", query.lower().strip())

        # Replace specific values with placeholders
        pattern = re.sub(r"'[^']*'", "'?'", pattern)  # String literals
        pattern = re.sub(r"\b\d+\b", "?", pattern)  # Numbers

        return pattern
    def _analyze_query(self, query: str) -> List[str]:
        """Analyze query for optimization opportunities"""
        suggestions = []
        query_lower = query.lower()

        # Check for common issues
        if "select *" in query_lower:
            suggestions.append(
                "Consider selecting only needed columns instead of SELECT *"
            )

        if "order by" in query_lower and "limit" not in query_lower:
            suggestions.append(
                "Consider adding LIMIT when using ORDER BY for large datasets"
            )

        if query_lower.count("join") > 3:
            suggestions.append(
                "Complex query with multiple JOINs - consider breaking into smaller queries"
            )

        if "like" in query_lower and query_lower.count("%") > 0:
            suggestions.append(
                "LIKE with wildcards can be slow - consider full-text search if available"
            )

        if "where" not in query_lower and (
            "update" in query_lower or "delete" in query_lower
        ):
            suggestions.append(
                "UPDATE/DELETE without WHERE clause detected - ensure this is intentional"
            )

        return suggestions
def _cache_query_plan(self, query_hash: str, query_data: Dict):
        """Cache query execution plan"""
        if len(self.query_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]

        self.query_cache[query_hash] = {
            "execution_time": query_data.get("execution_time"),
            "row_count": query_data.get("row_count"),
            "cached_at": datetime.now().isoformat(),
        }
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        if not self.query_stats:
            return {"no_queries": True}

        total_queries = sum(
            stats["execution_count"] for stats in self.query_stats.values()
        )
        total_errors = sum(stats["error_count"] for stats in self.query_stats.values())

        slow_queries = [
            hash_id
            for hash_id, stats in self.query_stats.items()
            if stats["total_time"]
            / max(1, stats["execution_count"] - stats["error_count"])
            > self.slow_query_threshold
        ]

        return {
            "total_queries": total_queries,
            "unique_patterns": len(self.query_stats),
            "total_errors": total_errors,
            "error_rate": (total_errors / max(1, total_queries)) * 100,
            "slow_query_patterns": len(slow_queries),
            "cached_plans": len(self.query_cache),
        }


# Register database hooks
def register_database_hooks():
    """Register all database hooks with the hook manager"""
    hook_manager = get_hook_manager()

    # Register hooks
    hook_manager.register_hook("database.connect", DatabaseConnectionHook())
    hook_manager.register_hook("database.connected", DatabaseConnectionHook())
    hook_manager.register_hook("database.disconnect", DatabaseConnectionHook())
    hook_manager.register_hook("database.error", DatabaseConnectionHook())

    hook_manager.register_hook("database.transaction.begin", DatabaseTransactionHook())
    hook_manager.register_hook("database.transaction.commit", DatabaseTransactionHook())
    hook_manager.register_hook(
        "database.transaction.rollback", DatabaseTransactionHook()
    )
    hook_manager.register_hook("database.transaction.error", DatabaseTransactionHook())

    hook_manager.register_hook("database.query.before", DatabaseQueryOptimizationHook())
    hook_manager.register_hook("database.query.after", DatabaseQueryOptimizationHook())

    logger.info("Database hooks registered successfully")


# Convenience functions for triggering database events
def trigger_connection_start(connection_id: str, database: str, host: str, port: int):
    """Trigger database connection start hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "database.connect",
        "database_manager",
        connection_id=connection_id,
        database=database,
        host=host,
        port=port,
    )
def trigger_connection_success(connection_id: str):
    """Trigger database connection success hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "database.connected", "database_manager", connection_id=connection_id
    )
def trigger_connection_error(connection_id: str, error: Exception):
    """Trigger database connection error hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "database.error", "database_manager", connection_id=connection_id, error=error
    )
def trigger_transaction_begin(transaction_id: str):
    """Trigger database transaction begin hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "database.transaction.begin", "database_manager", transaction_id=transaction_id
    )
def trigger_transaction_commit(transaction_id: str):
    """Trigger database transaction commit hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "database.transaction.commit", "database_manager", transaction_id=transaction_id
    )
def trigger_query_start(query: str, params: Dict = None):
    """Trigger database query start hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "database.query.before", "database_manager", query=query, params=params
    )
    def trigger_query_complete(
    query: str, execution_time: float, row_count: int, success: bool = True
):
    """Trigger database query completion hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "database.query.after",
        "database_manager",
        query=query,
        execution_time=execution_time,
        row_count=row_count,
        success=success,
    )
