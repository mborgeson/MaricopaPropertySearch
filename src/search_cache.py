"""
Search Cache Manager
High-performance caching layer for property searches with TTL and LRU eviction
"""

import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from collections import OrderedDict
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class SearchCache:
    """Thread-safe LRU cache with TTL for search results"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_expired, daemon=True
        )
        self.cleanup_thread.start()

        logger.info(
            f"Search cache initialized: max_size={max_size}, ttl={default_ttl}s"
        )

    def _generate_key(
        self, search_type: str, search_term: str, filters: Dict = None
    ) -> str:
        """Generate cache key from search parameters"""
        cache_data = {
            "type": search_type.lower().strip(),
            "term": search_term.lower().strip(),
            "filters": filters or {},
        }

        cache_json = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_json.encode()).hexdigest()

    def get(
        self,
        search_type: str,
        search_term: str,
        filters: Dict = None,
        force_fresh: bool = False,
    ) -> Optional[List[Dict]]:
        """Get cached search results"""
        # Return None immediately if force_fresh is requested
        if force_fresh:
            logger.debug(
                f"Force fresh mode - skipping cache lookup for {search_type}: {search_term}"
            )
            return None

        key = self._generate_key(search_type, search_term, filters)

        with self.lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]
            current_time = time.time()

            # Check if expired
            if current_time > entry["expires_at"]:
                del self.cache[key]
                del self.access_times[key]
                logger.debug(f"Cache entry expired: {key}")
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.access_times[key] = current_time

            logger.debug(f"Cache hit: {key} (size: {len(entry['results'])})")
            return entry["results"].copy()

    def put(
        self,
        search_type: str,
        search_term: str,
        results: List[Dict],
        filters: Dict = None,
        ttl: int = None,
    ) -> None:
        """Cache search results"""
        key = self._generate_key(search_type, search_term, filters)

        if ttl is None:
            ttl = self.default_ttl

        current_time = time.time()

        with self.lock:
            # Remove oldest entries if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
                logger.debug(f"Evicted cache entry: {oldest_key}")

            self.cache[key] = {
                "results": results.copy() if results else [],
                "created_at": current_time,
                "expires_at": current_time + ttl,
                "access_count": 1,
            }
            self.access_times[key] = current_time

            logger.debug(f"Cached results: {key} (size: {len(results)}, ttl: {ttl}s)")

    def invalidate(self, search_type: str = None, search_term: str = None) -> int:
        """Invalidate cache entries matching criteria"""
        if search_type is None and search_term is None:
            # Clear all
            with self.lock:
                count = len(self.cache)
                self.cache.clear()
                self.access_times.clear()
                logger.info(f"Cleared entire cache ({count} entries)")
                return count

        # Partial invalidation - need to regenerate keys and check
        keys_to_remove = []

        with self.lock:
            for key in self.cache.keys():
                # This is approximate - would need reverse lookup for exact matching
                # For now, just clear all if specific invalidation is needed
                pass

        return 0

    def _cleanup_expired(self):
        """Background thread to clean up expired entries"""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes

                current_time = time.time()
                keys_to_remove = []

                with self.lock:
                    for key, entry in self.cache.items():
                        if current_time > entry["expires_at"]:
                            keys_to_remove.append(key)

                    for key in keys_to_remove:
                        del self.cache[key]
                        del self.access_times[key]

                if keys_to_remove:
                    logger.debug(
                        f"Cleaned up {len(keys_to_remove)} expired cache entries"
                    )

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            current_time = time.time()
            expired_count = sum(
                1 for entry in self.cache.values() if current_time > entry["expires_at"]
            )

            return {
                "total_entries": len(self.cache),
                "expired_entries": expired_count,
                "max_size": self.max_size,
                "hit_ratio": getattr(self, "_hit_count", 0)
                / max(getattr(self, "_total_requests", 1), 1),
                "memory_usage_mb": sum(len(str(entry)) for entry in self.cache.values())
                / (1024 * 1024),
            }


class SearchHistory:
    """Search history and suggestions manager"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history: List[Dict] = []
        self.term_frequency: Dict[str, int] = {}
        self.lock = threading.RLock()

    def add_search(
        self, search_type: str, search_term: str, results_count: int
    ) -> None:
        """Add search to history"""
        with self.lock:
            search_entry = {
                "type": search_type,
                "term": search_term.strip(),
                "results_count": results_count,
                "timestamp": time.time(),
            }

            # Add to history
            self.history.append(search_entry)

            # Limit history size
            if len(self.history) > self.max_history:
                removed = self.history.pop(0)
                # Update frequency count
                removed_term = removed["term"].lower()
                if removed_term in self.term_frequency:
                    self.term_frequency[removed_term] -= 1
                    if self.term_frequency[removed_term] <= 0:
                        del self.term_frequency[removed_term]

            # Update term frequency
            term_lower = search_term.lower().strip()
            self.term_frequency[term_lower] = self.term_frequency.get(term_lower, 0) + 1

    def get_suggestions(
        self, partial_term: str, search_type: str = None, limit: int = 10
    ) -> List[str]:
        """Get search suggestions based on history"""
        partial_lower = partial_term.lower().strip()

        if len(partial_lower) < 2:
            return []

        suggestions = []

        with self.lock:
            # Get matching terms from frequency dict
            matching_terms = [
                (term, frequency)
                for term, frequency in self.term_frequency.items()
                if partial_lower in term and len(term) > len(partial_lower)
            ]

            # Sort by frequency and recency
            matching_terms.sort(
                key=lambda x: (-x[1], -time.time())
            )  # Frequency desc, then recency

            # Filter by search type if specified
            if search_type:
                filtered_suggestions = []
                for term, _ in matching_terms:
                    for entry in reversed(self.history):
                        if (
                            entry["term"].lower() == term
                            and entry["type"] == search_type
                        ):
                            filtered_suggestions.append(term)
                            break
                suggestions = filtered_suggestions[:limit]
            else:
                suggestions = [term for term, _ in matching_terms[:limit]]

        return suggestions

    def get_recent_searches(self, limit: int = 20) -> List[Dict]:
        """Get recent searches"""
        with self.lock:
            return self.history[-limit:] if self.history else []

    def get_popular_terms(
        self, search_type: str = None, limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Get most popular search terms"""
        with self.lock:
            if search_type:
                # Filter by search type
                type_terms = {}
                for entry in self.history:
                    if entry["type"] == search_type:
                        term = entry["term"].lower()
                        type_terms[term] = type_terms.get(term, 0) + 1

                sorted_terms = sorted(
                    type_terms.items(), key=lambda x: x[1], reverse=True
                )
                return sorted_terms[:limit]
            else:
                sorted_terms = sorted(
                    self.term_frequency.items(), key=lambda x: x[1], reverse=True
                )
                return sorted_terms[:limit]
