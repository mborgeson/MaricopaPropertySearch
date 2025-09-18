"""
API Operation Hooks
Handles API request/response lifecycle, rate limiting, and monitoring
"""

import asyncio
import hashlib
import json
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Deque

from hook_manager import (
    Hook,
    HookContext,
    HookResult,
    HookStatus,
    HookPriority,
    get_hook_manager,
)
from logging_config import get_logger, log_exception

logger = get_logger(__name__)


class APIRateLimitHook(Hook):
    """Hook for API rate limiting and throttling"""

    def __init__(self):
        super().__init__("api_rate_limit", HookPriority.HIGHEST)
        self.request_history: Deque[float] = deque(maxlen=1000)
        self.rate_limits = {
            "requests_per_second": 10,
            "requests_per_minute": 300,
            "requests_per_hour": 5000,
        }
        self.blocked_until = None
        self.violation_count = 0

    async def execute(self, context: HookContext) -> HookResult:
        """Check and enforce rate limits"""
        try:
            current_time = time.time()
            request_data = context.data

            # Check if we're currently blocked
            if self.blocked_until and current_time < self.blocked_until:
                wait_time = self.blocked_until - current_time
                logger.warning(
                    f"API rate limit active - blocked for {wait_time:.1f}s more"
                )

                return HookResult(
                    status=HookStatus.FAILED,
                    result={
                        "rate_limited": True,
                        "wait_time": wait_time,
                        "reason": "Rate limit active",
                    },
                    metadata={"rate_limited": True, "wait_time": wait_time},
                )

            # Add current request to history
            self.request_history.append(current_time)

            # Check rate limits
            violations = self._check_rate_limits(current_time)

            if violations:
                self.violation_count += 1

                # Calculate backoff time based on violation severity
                backoff_time = self._calculate_backoff(violations)
                self.blocked_until = current_time + backoff_time

                logger.warning(
                    f"API rate limit exceeded: {violations} - backing off for {backoff_time}s"
                )

                return HookResult(
                    status=HookStatus.FAILED,
                    result={
                        "rate_limited": True,
                        "violations": violations,
                        "backoff_time": backoff_time,
                        "violation_count": self.violation_count,
                    },
                    metadata={"rate_limited": True, "backoff_time": backoff_time},
                )

            # Rate limit check passed
            rate_info = self._get_rate_limit_info(current_time)

            logger.debug(f"API rate limit check passed - current rates: {rate_info}")

            return HookResult(
                status=HookStatus.SUCCESS,
                result={"rate_limited": False, "rate_info": rate_info},
                metadata={"rate_limited": False},
            )

        except Exception as e:
            logger.error(f"API rate limit hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    def _check_rate_limits(self, current_time: float) -> List[str]:
        """Check if any rate limits are violated"""
        violations = []

        # Check requests per second
        recent_requests = [t for t in self.request_history if current_time - t <= 1.0]
        if len(recent_requests) > self.rate_limits["requests_per_second"]:
            violations.append(
                f"requests_per_second: {len(recent_requests)}/{self.rate_limits['requests_per_second']}"
            )

        # Check requests per minute
        recent_requests = [t for t in self.request_history if current_time - t <= 60.0]
        if len(recent_requests) > self.rate_limits["requests_per_minute"]:
            violations.append(
                f"requests_per_minute: {len(recent_requests)}/{self.rate_limits['requests_per_minute']}"
            )

        # Check requests per hour
        recent_requests = [
            t for t in self.request_history if current_time - t <= 3600.0
        ]
        if len(recent_requests) > self.rate_limits["requests_per_hour"]:
            violations.append(
                f"requests_per_hour: {len(recent_requests)}/{self.rate_limits['requests_per_hour']}"
            )

        return violations

    def _calculate_backoff(self, violations: List[str]) -> float:
        """Calculate backoff time based on violations"""
        base_backoff = 1.0

        # Increase backoff based on violation count
        backoff_multiplier = min(2**self.violation_count, 60)  # Max 60x

        # Increase backoff based on violation severity
        severity_multiplier = len(violations)

        return base_backoff * backoff_multiplier * severity_multiplier

    def _get_rate_limit_info(self, current_time: float) -> Dict[str, int]:
        """Get current rate limit usage"""
        return {
            "requests_last_second": len(
                [t for t in self.request_history if current_time - t <= 1.0]
            ),
            "requests_last_minute": len(
                [t for t in self.request_history if current_time - t <= 60.0]
            ),
            "requests_last_hour": len(
                [t for t in self.request_history if current_time - t <= 3600.0]
            ),
        }

    def reset_violations(self):
        """Reset violation count (for testing or manual intervention)"""
        self.violation_count = 0
        self.blocked_until = None
        logger.info("API rate limit violations reset")

    def update_rate_limits(self, new_limits: Dict[str, int]):
        """Update rate limits"""
        self.rate_limits.update(new_limits)
        logger.info(f"API rate limits updated: {self.rate_limits}")


class APIRequestResponseHook(Hook):
    """Hook for monitoring API requests and responses"""

    def __init__(self):
        super().__init__("api_request_response", HookPriority.NORMAL)
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": deque(maxlen=100),
            "status_codes": {},
            "endpoints": {},
        }
        self.active_requests = {}

    async def execute(self, context: HookContext) -> HookResult:
        """Monitor API requests and responses"""
        try:
            event_type = context.event_name.split(".")[-1]
            request_data = context.data

            if event_type == "request":
                return await self._handle_request_start(context, request_data)
            elif event_type == "response":
                return await self._handle_response(context, request_data)
            elif event_type == "error":
                return await self._handle_request_error(context, request_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"API request/response hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _handle_request_start(
        self, context: HookContext, request_data: Dict
    ) -> HookResult:
        """Handle API request start"""
        request_id = request_data.get("request_id", f"req_{int(time.time())}")
        url = request_data.get("url", "")
        method = request_data.get("method", "GET")
        start_time = time.time()

        # Store request info
        self.active_requests[request_id] = {
            "start_time": start_time,
            "url": url,
            "method": method,
            "source": context.source,
        }

        # Update endpoint statistics
        endpoint = self._extract_endpoint(url)
        if endpoint not in self.request_stats["endpoints"]:
            self.request_stats["endpoints"][endpoint] = {
                "count": 0,
                "success_count": 0,
                "avg_response_time": 0,
                "total_time": 0,
            }

        self.request_stats["total_requests"] += 1
        self.request_stats["endpoints"][endpoint]["count"] += 1

        logger.debug(f"API request started: {method} {url} [{request_id}]")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "request_id": request_id,
                "start_time": start_time,
                "endpoint": endpoint,
            },
        )

    async def _handle_response(
        self, context: HookContext, request_data: Dict
    ) -> HookResult:
        """Handle API response"""
        request_id = request_data.get("request_id")
        status_code = request_data.get("status_code", 0)
        response_time = request_data.get("response_time", 0)
        response_size = request_data.get("response_size", 0)

        if request_id not in self.active_requests:
            logger.warning(f"Response for unknown request: {request_id}")
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "Unknown request"}
            )

        req_info = self.active_requests[request_id]

        # Calculate actual response time if not provided
        if not response_time:
            response_time = time.time() - req_info["start_time"]

        # Update statistics
        self.request_stats["response_times"].append(response_time)

        if 200 <= status_code < 300:
            self.request_stats["successful_requests"] += 1
            success = True
        else:
            self.request_stats["failed_requests"] += 1
            success = False

        # Update status code stats
        status_key = f"{status_code // 100}xx"
        self.request_stats["status_codes"][status_key] = (
            self.request_stats["status_codes"].get(status_key, 0) + 1
        )

        # Update endpoint stats
        endpoint = self._extract_endpoint(req_info["url"])
        if endpoint in self.request_stats["endpoints"]:
            endpoint_stats = self.request_stats["endpoints"][endpoint]
            if success:
                endpoint_stats["success_count"] += 1
            endpoint_stats["total_time"] += response_time
            endpoint_stats["avg_response_time"] = (
                endpoint_stats["total_time"] / endpoint_stats["count"]
            )

        # Log response
        log_level = "debug" if success else "warning"
        getattr(logger, log_level)(
            f"API response: {status_code} {req_info['method']} {req_info['url']} "
            f"({response_time:.3f}s, {response_size} bytes) [{request_id}]"
        )

        # Clean up
        del self.active_requests[request_id]

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "request_id": request_id,
                "status_code": status_code,
                "response_time": response_time,
                "response_size": response_size,
                "success": success,
                "endpoint": endpoint,
            },
            metadata={"response_time": response_time, "success": success},
        )

    async def _handle_request_error(
        self, context: HookContext, request_data: Dict
    ) -> HookResult:
        """Handle API request error"""
        request_id = request_data.get("request_id")
        error = request_data.get("error")

        self.request_stats["failed_requests"] += 1

        if request_id in self.active_requests:
            req_info = self.active_requests[request_id]
            error_time = time.time() - req_info["start_time"]

            logger.error(
                f"API request error: {req_info['method']} {req_info['url']} "
                f"after {error_time:.3f}s - {error} [{request_id}]"
            )

            del self.active_requests[request_id]

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    "request_id": request_id,
                    "error": str(error),
                    "error_time": error_time,
                },
                metadata={"request_error": True},
            )
        else:
            logger.error(f"Error for unknown request: {request_id} - {error}")
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "Unknown request"}
            )

    def _extract_endpoint(self, url: str) -> str:
        """Extract endpoint pattern from URL"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            path = parsed.path

            # Remove trailing slash
            if path.endswith("/") and len(path) > 1:
                path = path[:-1]

            # Replace IDs with placeholder
            import re

            path = re.sub(r"/\d+", "/{id}", path)

            return path or "/"
        except Exception:
            return url

    def get_api_stats(self) -> Dict[str, Any]:
        """Get API statistics"""
        total_requests = self.request_stats["total_requests"]
        success_rate = (
            self.request_stats["successful_requests"] / max(1, total_requests)
        ) * 100

        avg_response_time = 0
        if self.request_stats["response_times"]:
            avg_response_time = sum(self.request_stats["response_times"]) / len(
                self.request_stats["response_times"]
            )

        return {
            "total_requests": total_requests,
            "successful_requests": self.request_stats["successful_requests"],
            "failed_requests": self.request_stats["failed_requests"],
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "active_requests": len(self.active_requests),
            "status_codes": dict(self.request_stats["status_codes"]),
            "top_endpoints": self._get_top_endpoints(),
        }

    def _get_top_endpoints(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top endpoints by request count"""
        sorted_endpoints = sorted(
            self.request_stats["endpoints"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )

        return [
            {
                "endpoint": endpoint,
                "count": stats["count"],
                "success_rate": (stats["success_count"] / max(1, stats["count"])) * 100,
                "avg_response_time": stats["avg_response_time"],
            }
            for endpoint, stats in sorted_endpoints[:limit]
        ]


class APICacheHook(Hook):
    """Hook for API response caching"""

    def __init__(self):
        super().__init__("api_cache", HookPriority.HIGH)
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)  # Cache for 15 minutes
        self.max_cache_size = 500
        self.cache_stats = {"hits": 0, "misses": 0, "size": 0}

    async def execute(self, context: HookContext) -> HookResult:
        """Handle API response caching"""
        try:
            event_type = context.event_name.split(".")[-1]
            request_data = context.data

            if event_type == "request":
                return await self._check_cache(context, request_data)
            elif event_type == "response":
                return await self._store_cache(context, request_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"API cache hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _check_cache(
        self, context: HookContext, request_data: Dict
    ) -> HookResult:
        """Check if response is cached"""
        cache_key = self._generate_cache_key(request_data)

        if cache_key in self.cache:
            cached_item = self.cache[cache_key]

            # Check if cache is still valid
            if datetime.now() - cached_item["timestamp"] < self.cache_ttl:
                self.cache_stats["hits"] += 1
                logger.debug(f"API cache HIT: {cache_key}")

                return HookResult(
                    status=HookStatus.SUCCESS,
                    result={
                        "cache_hit": True,
                        "cached_response": cached_item["response"],
                        "cached_at": cached_item["timestamp"].isoformat(),
                    },
                    metadata={"cache_hit": True},
                )
            else:
                # Cache expired
                del self.cache[cache_key]
                self.cache_stats["size"] = len(self.cache)

        self.cache_stats["misses"] += 1
        logger.debug(f"API cache MISS: {cache_key}")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={"cache_hit": False},
            metadata={"cache_hit": False},
        )

    async def _store_cache(
        self, context: HookContext, request_data: Dict
    ) -> HookResult:
        """Store API response in cache"""
        # Only cache successful GET requests
        if request_data.get("method", "GET").upper() != "GET" or not (
            200 <= request_data.get("status_code", 0) < 300
        ):
            return HookResult(status=HookStatus.SUCCESS, result={"cached": False})

        cache_key = self._generate_cache_key(request_data)
        response_data = request_data.get("response_data")

        if not response_data:
            return HookResult(status=HookStatus.SUCCESS, result={"cached": False})

        # Manage cache size
        self._manage_cache_size()

        # Store in cache
        self.cache[cache_key] = {
            "response": response_data,
            "timestamp": datetime.now(),
            "url": request_data.get("url"),
            "status_code": request_data.get("status_code"),
        }

        self.cache_stats["size"] = len(self.cache)

        logger.debug(f"API response cached: {cache_key}")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={"cached": True, "cache_key": cache_key},
            metadata={"cached": True},
        )

    def _generate_cache_key(self, request_data: Dict) -> str:
        """Generate cache key from request parameters"""
        key_parts = [
            request_data.get("method", "GET"),
            request_data.get("url", ""),
            json.dumps(request_data.get("params", {}), sort_keys=True),
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _manage_cache_size(self):
        """Manage cache size by removing oldest entries"""
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest 10% of cache
            remove_count = max(1, self.max_cache_size // 10)

            # Sort by timestamp
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1]["timestamp"])

            for i in range(remove_count):
                key = sorted_items[i][0]
                del self.cache[key]

            logger.debug(f"API cache cleanup: removed {remove_count} old entries")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / max(1, total_requests)) * 100

        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": hit_rate,
            "cache_size": self.cache_stats["size"],
            "max_cache_size": self.max_cache_size,
        }

    def clear_cache(self):
        """Clear all cached responses"""
        self.cache.clear()
        self.cache_stats["size"] = 0
        logger.info("API cache cleared")


# Register API hooks
def register_api_hooks():
    """Register all API hooks with the hook manager"""
    hook_manager = get_hook_manager()

    # Register hooks
    hook_manager.register_hook("api.request", APIRateLimitHook())
    hook_manager.register_hook("api.request", APIRequestResponseHook())
    hook_manager.register_hook("api.request", APICacheHook())

    hook_manager.register_hook("api.response", APIRequestResponseHook())
    hook_manager.register_hook("api.response", APICacheHook())

    hook_manager.register_hook("api.error", APIRequestResponseHook())

    logger.info("API hooks registered successfully")


# Convenience functions for triggering API events
def trigger_api_request(
    request_id: str, url: str, method: str = "GET", params: Dict = None
):
    """Trigger API request hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "api.request",
        "api_client",
        request_id=request_id,
        url=url,
        method=method,
        params=params or {},
    )


def trigger_api_response(
    request_id: str,
    status_code: int,
    response_data: Any,
    response_time: float,
    response_size: int = 0,
):
    """Trigger API response hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "api.response",
        "api_client",
        request_id=request_id,
        status_code=status_code,
        response_data=response_data,
        response_time=response_time,
        response_size=response_size,
    )


def trigger_api_error(request_id: str, error: Exception):
    """Trigger API error hook"""
    from hook_manager import emit_hook

    return emit_hook("api.error", "api_client", request_id=request_id, error=error)
