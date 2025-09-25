"""
Search Operation Hooks
Handles search operation lifecycle, validation, and optimization for property searches
"""
import asyncio
import hashlib
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

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


class SearchValidationHook(Hook):
    """Hook for validating search inputs before execution"""
    def __init__(self):
        super().__init__("search_validation", HookPriority.HIGHEST)
        self.validation_rules = {
            "apn": {
                "pattern": r"^\d{3}-\d{2}-\d{3}$",
                "description": "APN format: XXX-XX-XXX",
            },
            "address": {
                "min_length": 5,
                "max_length": 200,
                "description": "Address must be 5-200 characters",
            },
            "owner": {
                "min_length": 2,
                "max_length": 100,
                "description": "Owner name must be 2-100 characters",
            },
        }

    async def execute(self, context: HookContext) -> HookResult:
        """Validate search parameters"""
        try:
            search_data = context.data
            search_type = search_data.get("search_type", "unknown")
            search_term = search_data.get("search_term", "")

            validation_errors = []
            warnings = []

            logger.debug(f"Validating {search_type} search: '{search_term}'")

            # Validate based on search type
            if search_type == "apn":
                errors = self._validate_apn(search_term)
                validation_errors.extend(errors)
            elif search_type == "address":
                errors = self._validate_address(search_term)
                validation_errors.extend(errors)
            elif search_type == "owner":
                errors = self._validate_owner(search_term)
                validation_errors.extend(errors)
            else:
                # Auto-detect search type
                detected_type, confidence = self._detect_search_type(search_term)
                warnings.append(
                    f"Auto-detected search type: {detected_type} (confidence: {confidence:.0%})"
                )
                search_data["detected_type"] = detected_type
                search_data["type_confidence"] = confidence

            # General validations
            if not search_term or not search_term.strip():
                validation_errors.append("Search term cannot be empty")

            if len(search_term.strip()) > 500:
                validation_errors.append("Search term too long (max 500 characters)")

            # Check for potentially dangerous characters
            dangerous_chars = ["<", ">", ";", "|", "&", "$", "`"]
            if any(char in search_term for char in dangerous_chars):
                validation_errors.append(
                    "Search term contains potentially dangerous characters"
                )

            # Sanitize search term
            sanitized_term = self._sanitize_search_term(search_term)
            if sanitized_term != search_term:
                warnings.append("Search term was sanitized")
                search_data["sanitized_term"] = sanitized_term

            result_data = {
                "is_valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "warnings": warnings,
                "search_type": search_type,
                "sanitized_term": sanitized_term,
            }

            if validation_errors:
                logger.warning(f"Search validation failed: {validation_errors}")
                return HookResult(
                    status=HookStatus.FAILED,
                    result=result_data,
                    metadata={"validation_errors": validation_errors},
                )
            else:
                if warnings:
                    logger.info(f"Search validation passed with warnings: {warnings}")
                else:
                    logger.debug("Search validation passed")

                return HookResult(
                    status=HookStatus.SUCCESS,
                    result=result_data,
                    metadata={"warnings_count": len(warnings)},
                )

        except Exception as e:
            logger.error(f"Search validation error: {e}")
            log_exception(logger, e, "search validation")
            return HookResult(status=HookStatus.FAILED, error=e)
    def _validate_apn(self, apn: str) -> List[str]:
        """Validate APN format"""
        errors = []
        apn_rule = self.validation_rules["apn"]

        if not re.match(apn_rule["pattern"], apn):
            errors.append(f"Invalid APN format. {apn_rule['description']}")

        return errors
    def _validate_address(self, address: str) -> List[str]:
        """Validate address format"""
        errors = []
        addr_rule = self.validation_rules["address"]

        if len(address) < addr_rule["min_length"]:
            errors.append(
                f"Address too short (minimum {addr_rule['min_length']} characters)"
            )

        if len(address) > addr_rule["max_length"]:
            errors.append(
                f"Address too long (maximum {addr_rule['max_length']} characters)"
            )

        return errors
    def _validate_owner(self, owner: str) -> List[str]:
        """Validate owner name format"""
        errors = []
        owner_rule = self.validation_rules["owner"]

        if len(owner) < owner_rule["min_length"]:
            errors.append(
                f"Owner name too short (minimum {owner_rule['min_length']} characters)"
            )

        if len(owner) > owner_rule["max_length"]:
            errors.append(
                f"Owner name too long (maximum {owner_rule['max_length']} characters)"
            )

        return errors
    def _detect_search_type(self, search_term: str) -> Tuple[str, float]:
        """Auto-detect search type from term"""
        term = search_term.strip()

        # APN pattern
        if re.match(r"^\d{3}-\d{2}-\d{3}$", term):
            return "apn", 0.95

        # Number-heavy (likely APN without dashes)
        if re.match(r"^\d{7,10}$", term):
            return "apn", 0.7

        # Address patterns
        if re.search(
            r"\d+.*\w+.*(st|street|ave|avenue|dr|drive|ln|lane|blvd|boulevard|rd|road|way|ct|court|pl|place)",
            term.lower(),
        ):
            return "address", 0.9

        # Contains numbers (likely address)
        if re.search(r"\d+", term):
            return "address", 0.6

        # All letters (likely owner name)
        if re.match(r"^[a-zA-Z\s,.-]+$", term):
            return "owner", 0.8

        return "unknown", 0.0
    def _sanitize_search_term(self, term: str) -> str:
        """Sanitize search term"""
        # Remove dangerous characters
        sanitized = re.sub(r"[<>;|&$`]", "", term)

        # Normalize whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        return sanitized


class SearchPerformanceHook(Hook):
    """Hook for monitoring search performance"""
    def __init__(self):
        super().__init__("search_performance", HookPriority.LOW)
        self.search_metrics = {}
        self.slow_search_threshold = 5.0  # seconds

    async def execute(self, context: HookContext) -> HookResult:
        """Monitor search performance"""
        try:
            search_data = context.data
            event_type = context.event_name.split(".")[-1]  # 'before' or 'after'

            if event_type == "before":
                return await self._handle_search_start(context, search_data)
            elif event_type == "after":
                return await self._handle_search_complete(context, search_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"Search performance monitoring error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _handle_search_start(
        self, context: HookContext, search_data: Dict
    ) -> HookResult:
        """Handle search start event"""
        search_id = self._generate_search_id(search_data)
        start_time = time.time()

        self.search_metrics[search_id] = {
            "start_time": start_time,
            "search_type": search_data.get("search_type"),
            "search_term": search_data.get("search_term"),
            "source": context.source,
        }

        logger.debug(f"Search performance tracking started for: {search_id}")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={"search_id": search_id, "start_time": start_time},
        )

    async def _handle_search_complete(
        self, context: HookContext, search_data: Dict
    ) -> HookResult:
        """Handle search completion event"""
        search_id = self._generate_search_id(search_data)
        end_time = time.time()

        if search_id not in self.search_metrics:
            logger.warning(f"No start time found for search: {search_id}")
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "No start time found"}
            )

        metrics = self.search_metrics[search_id]
        execution_time = end_time - metrics["start_time"]

        # Update metrics
        metrics.update(
            {
                "end_time": end_time,
                "execution_time": execution_time,
                "result_count": search_data.get("result_count", 0),
                "success": search_data.get("success", True),
                "error": search_data.get("error"),
            }
        )

        # Performance analysis
        performance_level = self._analyze_performance(execution_time)

        # Log performance
        log_message = (
            f"Search completed - ID: {search_id}, "
            f"Time: {execution_time:.3f}s, "
            f"Results: {metrics['result_count']}, "
            f"Level: {performance_level}"
        )

        if execution_time > self.slow_search_threshold:
            logger.warning(f"SLOW SEARCH - {log_message}")
        else:
            logger.debug(log_message)

        # Clean up metrics
        del self.search_metrics[search_id]

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "search_id": search_id,
                "execution_time": execution_time,
                "performance_level": performance_level,
                "metrics": metrics,
            },
            metadata={"is_slow": execution_time > self.slow_search_threshold},
        )
    def _generate_search_id(self, search_data: Dict) -> str:
        """Generate unique search ID"""
        search_string = (
            f"{search_data.get('search_type', '')}:{search_data.get('search_term', '')}"
        )
        return hashlib.md5(search_string.encode()).hexdigest()[:8]
    def _analyze_performance(self, execution_time: float) -> str:
        """Analyze search performance level"""
        if execution_time < 1.0:
            return "excellent"
        elif execution_time < 3.0:
            return "good"
        elif execution_time < 5.0:
            return "acceptable"
        elif execution_time < 10.0:
            return "slow"
        else:
            return "very_slow"


class SearchCacheHook(Hook):
    """Hook for search result caching"""
    def __init__(self):
        super().__init__("search_cache", HookPriority.HIGH)
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)  # Cache for 1 hour
        self.max_cache_size = 1000

    async def execute(self, context: HookContext) -> HookResult:
        """Handle search caching"""
        try:
            search_data = context.data
            event_type = context.event_name.split(".")[-1]

            if event_type == "before":
                return await self._check_cache(context, search_data)
            elif event_type == "after":
                return await self._store_cache(context, search_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"Search cache error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _check_cache(self, context: HookContext, search_data: Dict) -> HookResult:
        """Check if search results are cached"""
        cache_key = self._generate_cache_key(search_data)

        if cache_key in self.cache:
            cached_item = self.cache[cache_key]

            # Check if cache is still valid
            if datetime.now() - cached_item["timestamp"] < self.cache_ttl:
                logger.debug(f"Cache HIT for search: {cache_key}")

                return HookResult(
                    status=HookStatus.SUCCESS,
                    result={
                        "cache_hit": True,
                        "cached_results": cached_item["results"],
                        "cached_at": cached_item["timestamp"].isoformat(),
                    },
                    metadata={"cache_hit": True},
                )
            else:
                # Cache expired, remove it
                del self.cache[cache_key]
                logger.debug(f"Cache EXPIRED for search: {cache_key}")

        logger.debug(f"Cache MISS for search: {cache_key}")
        return HookResult(
            status=HookStatus.SUCCESS,
            result={"cache_hit": False},
            metadata={"cache_hit": False},
        )

    async def _store_cache(self, context: HookContext, search_data: Dict) -> HookResult:
        """Store search results in cache"""
        cache_key = self._generate_cache_key(search_data)
        results = search_data.get("results", [])

        # Don't cache empty results or errors
        if not results or search_data.get("error"):
            return HookResult(status=HookStatus.SUCCESS, result={"cached": False})

        # Manage cache size
        self._manage_cache_size()

        # Store in cache
        self.cache[cache_key] = {
            "results": results,
            "timestamp": datetime.now(),
            "search_data": {
                "search_type": search_data.get("search_type"),
                "search_term": search_data.get("search_term"),
            },
        }

        logger.debug(f"Cached search results: {cache_key} ({len(results)} results)")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "cached": True,
                "cache_key": cache_key,
                "result_count": len(results),
            },
            metadata={"cached": True},
        )
    def _generate_cache_key(self, search_data: Dict) -> str:
        """Generate cache key from search parameters"""
        key_parts = [
            search_data.get("search_type", ""),
            search_data.get("search_term", ""),
            str(search_data.get("include_tax_history", False)),
            str(search_data.get("include_sales_history", False)),
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

            logger.debug(f"Cache cleanup: removed {remove_count} old entries")


class SearchAuditHook(Hook):
    """Hook for auditing search operations"""
    def __init__(self):
        super().__init__("search_audit", HookPriority.LOW)
        self.audit_log = []
        self.max_audit_entries = 10000

    async def execute(self, context: HookContext) -> HookResult:
        """Audit search operations"""
        try:
            search_data = context.data
            event_type = context.event_name.split(".")[-1]

            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "search_type": search_data.get("search_type"),
                "search_term": self._mask_sensitive_data(
                    search_data.get("search_term", "")
                ),
                "source": context.source,
                "user_context": search_data.get("user_context", {}),
                "success": search_data.get("success", True),
                "result_count": search_data.get("result_count", 0),
                "execution_time": search_data.get("execution_time", 0),
            }

            # Add to audit log
            self.audit_log.append(audit_entry)

            # Manage audit log size
            if len(self.audit_log) > self.max_audit_entries:
                self.audit_log = self.audit_log[-self.max_audit_entries :]

            logger.debug(
                f"Search audited: {event_type} - {search_data.get('search_type')}"
            )

            return HookResult(
                status=HookStatus.SUCCESS,
                result={"audited": True, "audit_entry": audit_entry},
            )

        except Exception as e:
            logger.error(f"Search audit error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)
    def _mask_sensitive_data(self, search_term: str) -> str:
        """Mask potentially sensitive search data"""
        if len(search_term) > 20:
            return search_term[:10] + "***" + search_term[-5:]
        return search_term
    def get_audit_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get audit summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_entries = [
            entry
            for entry in self.audit_log
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]

        if not recent_entries:
            return {"total_searches": 0}

        # Calculate statistics
        total_searches = len(recent_entries)
        successful_searches = sum(1 for e in recent_entries if e["success"])
        search_types = {}

        for entry in recent_entries:
            search_type = entry["search_type"]
            if search_type in search_types:
                search_types[search_type] += 1
            else:
                search_types[search_type] = 1

        return {
            "total_searches": total_searches,
            "successful_searches": successful_searches,
            "success_rate": (
                (successful_searches / total_searches) * 100
                if total_searches > 0
                else 0
            ),
            "search_types": search_types,
            "time_period_hours": hours,
        }


# Register search hooks
def register_search_hooks():
    """Register all search hooks with the hook manager"""
    hook_manager = get_hook_manager()

    # Register hooks
    hook_manager.register_hook("search.before", SearchValidationHook())
    hook_manager.register_hook("search.before", SearchPerformanceHook())
    hook_manager.register_hook("search.before", SearchCacheHook())
    hook_manager.register_hook("search.before", SearchAuditHook())

    hook_manager.register_hook("search.after", SearchPerformanceHook())
    hook_manager.register_hook("search.after", SearchCacheHook())
    hook_manager.register_hook("search.after", SearchAuditHook())

    logger.info("Search hooks registered successfully")


# Convenience functions for triggering search events
def trigger_search_start(search_type: str, search_term: str, **kwargs):
    """Trigger search start hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "search.before",
        "search_manager",
        search_type=search_type,
        search_term=search_term,
        **kwargs,
    )
    def trigger_search_complete(
    search_type: str,
    search_term: str,
    results: List,
    success: bool = True,
    error: str = None,
    **kwargs,
):
    """Trigger search completion hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "search.after",
        "search_manager",
        search_type=search_type,
        search_term=search_term,
        results=results,
        result_count=len(results) if results else 0,
        success=success,
        error=error,
        **kwargs,
    )
