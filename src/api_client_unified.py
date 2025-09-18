"""
Unified Maricopa County API Client
Consolidated from 8 variants with best features from each:
- Comprehensive logging (from api_client.py)
- Parallel processing & async support (from parallel_api_client.py)
- Batch operations & connection pooling (from batch_api_client.py)
- Performance optimizations (from performance patch)
- Thread safety and caching
- Adaptive rate limiting
- Connection pool management
"""

import asyncio
import aiohttp
import requests
import time
import logging
import json
import threading
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock, RLock, Semaphore
import queue

from .logging_config import get_api_logger

logger = logging.getLogger(__name__)
api_logger = get_api_logger(__name__)

# API Configuration
API_TOKEN = "ca1a11a6-adc4-4e0c-a584-36cbb6eb35e5"


@dataclass
class PropertyDataCache:
    """Cache entry for property data with TTL"""

    data: Dict[str, Any]
    timestamp: float
    ttl: float = 300.0  # 5 minutes default TTL

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl


@dataclass
class BatchAPIRequest:
    """Individual API request within a batch operation"""

    request_id: str
    request_type: str  # 'search_by_apn', 'search_by_owner', 'search_by_address'
    identifier: str  # APN, owner name, address
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10, lower is higher priority
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def __hash__(self):
        return hash((self.request_type, self.identifier))

    def __eq__(self, other):
        if not isinstance(other, BatchAPIRequest):
            return False
        return (
            self.request_type == other.request_type
            and self.identifier == other.identifier
        )


class AdaptiveRateLimiter:
    """Intelligent rate limiter that adapts based on server responses"""

    def __init__(
        self,
        initial_rate: float = 2.0,
        min_rate: float = 0.5,
        max_rate: float = 5.0,
        burst_capacity: int = 10,
    ):

        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.burst_capacity = burst_capacity

        self.tokens = burst_capacity
        self.last_refill = time.time()
        self.lock = Lock()

        # Adaptive parameters
        self.success_count = 0
        self.error_count = 0
        self.rate_limit_count = 0
        self.last_rate_adjustment = time.time()

        logger.info(
            f"Adaptive rate limiter initialized - "
            f"Initial rate: {initial_rate} req/s, "
            f"Burst capacity: {burst_capacity}"
        )

    def acquire(self, timeout: float = 10.0) -> bool:
        """Acquire token with adaptive rate limiting"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                now = time.time()

                # Refill tokens
                time_passed = now - self.last_refill
                tokens_to_add = time_passed * self.current_rate
                self.tokens = min(self.burst_capacity, self.tokens + tokens_to_add)
                self.last_refill = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

            time.sleep(0.1)  # Short pause before retry

        return False

    def record_success(self):
        """Record successful request for rate adaptation"""
        with self.lock:
            self.success_count += 1
            self._maybe_adjust_rate()

    def record_error(self):
        """Record failed request for rate adaptation"""
        with self.lock:
            self.error_count += 1
            self._maybe_adjust_rate()

    def record_rate_limit(self):
        """Record rate limit hit - decrease rate immediately"""
        with self.lock:
            self.rate_limit_count += 1
            self._decrease_rate()

    def _maybe_adjust_rate(self):
        """Adjust rate based on success/error ratio"""
        now = time.time()

        # Only adjust every 30 seconds
        if now - self.last_rate_adjustment < 30:
            return

        total_requests = self.success_count + self.error_count
        if total_requests < 10:  # Need sufficient data
            return

        success_rate = self.success_count / total_requests

        if success_rate > 0.95 and self.rate_limit_count == 0:
            # High success rate, try to increase rate
            self.current_rate = min(self.max_rate, self.current_rate * 1.1)
            logger.debug(f"Increased rate to {self.current_rate:.2f} req/s")
        elif success_rate < 0.85 or self.rate_limit_count > 0:
            # Low success rate or rate limits, decrease rate
            self._decrease_rate()

        # Reset counters
        self.success_count = 0
        self.error_count = 0
        self.rate_limit_count = 0
        self.last_rate_adjustment = now

    def _decrease_rate(self):
        """Decrease the current rate"""
        self.current_rate = max(self.min_rate, self.current_rate * 0.8)
        logger.debug(f"Decreased rate to {self.current_rate:.2f} req/s")

    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics"""
        with self.lock:
            return {
                "current_rate": self.current_rate,
                "min_rate": self.min_rate,
                "max_rate": self.max_rate,
                "current_tokens": self.tokens,
                "burst_capacity": self.burst_capacity,
                "success_count": self.success_count,
                "error_count": self.error_count,
                "rate_limit_count": self.rate_limit_count,
            }


class ConnectionPoolManager:
    """Manages HTTP connection pools for optimized API requests"""

    def __init__(
        self,
        max_connections: int = 20,
        max_connections_per_host: int = 10,
        timeout: int = 30,
    ):

        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout = timeout

        # Initialize connector lazily when needed
        self.connector = None
        self.session = None
        self.lock = Lock()

        logger.info(
            f"Connection pool manager initialized - "
            f"Max connections: {max_connections}, "
            f"Max per host: {max_connections_per_host}"
        )

    def _ensure_connector(self):
        """Ensure connector is initialized (called in async context)"""
        if self.connector is None:
            self.connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections_per_host,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )

    async def get_session(self, token: str = None) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if not self.session or self.session.closed:
            self._ensure_connector()  # Ensure connector is initialized
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            headers = {
                "Accept": "application/json",
                "User-Agent": None,  # API requires null user-agent
            }
            if token:
                headers["AUTHORIZATION"] = token

            self.session = aiohttp.ClientSession(
                connector=self.connector, timeout=timeout, headers=headers
            )
        return self.session

    async def close(self):
        """Close connection pool"""
        if self.session and not self.session.closed:
            await self.session.close()
        if self.connector:
            await self.connector.close()


class UnifiedMaricopaAPIClient:
    """
    Unified Maricopa County API Client

    Combines all features from 8 different API client variants:
    - Comprehensive logging and error handling
    - Parallel/async processing capabilities
    - Batch operations with queue management
    - Adaptive rate limiting
    - Connection pooling
    - Smart caching with TTL
    - Thread safety
    - Performance optimizations
    """

    def __init__(self, config_manager=None):
        logger.info("Initializing Unified Maricopa API Client")

        # Configuration
        if config_manager:
            self.config = config_manager.get_api_config()
            self.base_url = self.config["base_url"]
            self.token = self.config.get("token", API_TOKEN)
            self.timeout = self.config["timeout"]
            self.max_retries = self.config["max_retries"]
        else:
            # Default configuration
            self.base_url = "https://mcassessor.maricopa.gov/api"
            self.token = API_TOKEN
            self.timeout = 30
            self.max_retries = 3

        logger.debug(
            f"API Configuration - Base URL: {self.base_url}, Timeout: {self.timeout}s, Max Retries: {self.max_retries}"
        )

        # Synchronous session for backward compatibility
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": None,  # API docs specify null user-agent
                "Accept": "application/json",
                "AUTHORIZATION": self.token if self.token else None,
            }
        )

        # Async components for high-performance operations
        self.connection_pool = ConnectionPoolManager(
            max_connections=20, max_connections_per_host=10, timeout=self.timeout
        )

        # Rate limiting
        self.rate_limiter = AdaptiveRateLimiter(
            initial_rate=2.0, max_rate=5.0, burst_capacity=10
        )

        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(
            max_workers=10, thread_name_prefix="MaricopaAPI"
        )

        # Caching system
        self._cache = {}
        self._cache_lock = threading.Lock()

        # Batch processing
        self.request_queue = queue.PriorityQueue()
        self.active_requests = {}
        self.completed_requests = {}
        self.requests_lock = RLock()

        # Performance tracking
        self.request_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        self.total_successful = 0
        self.total_failed = 0
        self.stats_lock = Lock()

        # Rate limiting for sync requests
        self.last_request_time = 0
        self.min_request_interval = 0.02  # 20ms between requests (optimized)

        logger.info("Unified Maricopa API Client initialized successfully")

    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _get_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache key for request"""
        params_str = json.dumps(params or {}, sort_keys=True)
        return f"{endpoint}:{hash(params_str)}"

    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if not expired"""
        with self._cache_lock:
            if cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                if not cache_entry.is_expired():
                    self.cache_hits += 1
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cache_entry.data
                else:
                    # Remove expired entry
                    del self._cache[cache_key]

        self.cache_misses += 1
        return None

    def _cache_data(self, cache_key: str, data: Dict, ttl: float = 300.0):
        """Cache response data"""
        with self._cache_lock:
            self._cache[cache_key] = PropertyDataCache(
                data=data, timestamp=time.time(), ttl=ttl
            )

    def test_connection(self) -> bool:
        """Test if API connection is working"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"API connection test failed: {e}")
            return False

    def _make_request(
        self, endpoint: str, params: Dict = None, retry_count: int = 0
    ) -> Optional[Dict]:
        """Make HTTP request with retry logic and caching"""
        cache_key = self._get_cache_key(endpoint, params)

        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        self._rate_limit()

        url = urljoin(self.base_url, endpoint)
        logger.debug(f"Making API request to: {url}")

        start_time = time.time()

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)

            response_time = time.time() - start_time
            self.request_times.append(response_time)

            logger.debug(
                f"API response status: {response.status_code} in {response_time:.3f}s"
            )

            if response.status_code == 200:
                data = response.json()
                # Cache successful responses for 5 minutes
                self._cache_data(cache_key, data, ttl=300.0)

                if self.rate_limiter:
                    self.rate_limiter.record_success()

                with self.stats_lock:
                    self.total_requests += 1
                    self.total_successful += 1

                return data
            elif response.status_code == 429:  # Rate limited
                if self.rate_limiter:
                    self.rate_limiter.record_rate_limit()

                if retry_count < self.max_retries:
                    wait_time = 2**retry_count  # Exponential backoff
                    logger.warning(
                        f"Rate limited, waiting {wait_time}s before retry (attempt {retry_count + 1})"
                    )
                    time.sleep(wait_time)
                    return self._make_request(endpoint, params, retry_count + 1)
                else:
                    logger.error(f"Max retries exceeded for {url}")
                    return None
            elif response.status_code == 404:
                # Cache 404s for 1 minute to avoid repeated failed requests
                self._cache_data(cache_key, {}, ttl=60.0)
                return None
            else:
                logger.error(
                    f"API request failed: {response.status_code} - {response.text}"
                )
                if self.rate_limiter:
                    self.rate_limiter.record_error()
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            if retry_count < self.max_retries:
                logger.info(f"Retrying after timeout (attempt {retry_count + 1})")
                return self._make_request(endpoint, params, retry_count + 1)

            with self.stats_lock:
                self.total_requests += 1
                self.total_failed += 1
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {url}: {e}")
            if retry_count < self.max_retries:
                logger.info(f"Retrying after exception (attempt {retry_count + 1})")
                return self._make_request(endpoint, params, retry_count + 1)

            with self.stats_lock:
                self.total_requests += 1
                self.total_failed += 1
            return None

    # ========================================================================
    # CORE API METHODS (Backward Compatible)
    # ========================================================================

    def search_by_owner(self, owner_name: str, limit: int = 50) -> List[Dict]:
        """Search properties by owner name using real Maricopa API with web scraping fallback"""
        logger.info(f"Searching properties by owner: {owner_name} (limit: {limit})")

        # Try API first
        params = {"q": owner_name}

        try:
            response = self._make_request("/search/property/", params)

            if response and "Results" in response:
                results = response["Results"][:limit]  # Limit results
                normalized_results = [
                    self._normalize_api_data(result) for result in results
                ]
                result_count = len(normalized_results)
                logger.info(
                    f"Found {result_count} properties for owner: {owner_name} (via API)"
                )

                # Log search analytics
                logger.info(
                    f"SEARCH_ANALYTICS: owner_search, results={result_count}, limit={limit}, source=api"
                )

                return normalized_results
            else:
                logger.warning(f"No properties found via API for owner: {owner_name}")

        except Exception as e:
            logger.warning(
                f"API search failed for owner {owner_name}: {e}, returning empty results"
            )

        # Web scraping fallback is not practical for owner searches
        # as it would require searching through many possible APNs
        logger.info(
            f"SEARCH_ANALYTICS: owner_search, results=0, limit={limit}, source=api_only"
        )
        return []

    def search_by_address(self, address: str, limit: int = 50) -> List[Dict]:
        """Search properties by address using real Maricopa API with web scraping fallback"""
        logger.info(f"Searching properties by address: {address} (limit: {limit})")

        # Try API first
        params = {"q": address}

        try:
            response = self._make_request("/search/property/", params)

            if response and "Results" in response:
                results = response["Results"][:limit]  # Limit results
                normalized_results = [
                    self._normalize_api_data(result) for result in results
                ]
                result_count = len(normalized_results)
                logger.info(
                    f"Found {result_count} properties for address: {address} (via API)"
                )

                # Log search analytics
                logger.info(
                    f"SEARCH_ANALYTICS: address_search, results={result_count}, limit={limit}, source=api"
                )

                return normalized_results
            else:
                logger.warning(f"No properties found via API for address: {address}")

        except Exception as e:
            logger.warning(
                f"API search failed for address {address}: {e}, returning empty results"
            )

        # Web scraping fallback is not practical for address searches
        # as it would require searching through many possible APNs
        logger.info(
            f"SEARCH_ANALYTICS: address_search, results=0, limit={limit}, source=api_only"
        )
        return []

    def search_by_apn(self, apn: str) -> Optional[Dict]:
        """Search property by APN using real Maricopa API with web scraping fallback"""
        logger.info(f"Searching property by APN: {apn}")

        # Try API first
        try:
            params = {"q": apn}
            response = self._make_request("/search/property/", params)

            if response and "Results" in response and len(response["Results"]) > 0:
                # Find exact APN match in results
                for result in response["Results"]:
                    if result.get("APN", "").replace("-", "").replace(
                        ".", ""
                    ) == apn.replace("-", "").replace(".", ""):
                        normalized_result = self._normalize_api_data(result)
                        logger.info(f"Found property for APN: {apn} (via API)")
                        logger.info(
                            f"SEARCH_ANALYTICS: apn_search, results=1, apn={apn}, source=api"
                        )
                        return normalized_result

                # If no exact match, return first result
                if response["Results"]:
                    normalized_result = self._normalize_api_data(response["Results"][0])
                    logger.info(f"Found similar property for APN: {apn} (via API)")
                    logger.info(
                        f"SEARCH_ANALYTICS: apn_search, results=1, apn={apn}, source=api"
                    )
                    return normalized_result

            logger.warning(
                f"No property found via API for APN: {apn}, trying web scraping fallback"
            )

        except Exception as e:
            logger.warning(
                f"API search failed for APN {apn}: {e}, trying web scraping fallback"
            )

        # Web scraping fallback - attempt to get basic property data
        try:
            # Try to get tax data which often contains property info
            tax_data = self._scrape_tax_data_sync(apn)
            if tax_data and tax_data.get("owner_info"):
                owner_info = tax_data["owner_info"]

                # Create basic property record from tax data
                property_data = {
                    "apn": apn,
                    "owner_name": owner_info.get("owner_name", ""),
                    "property_address": owner_info.get("property_address", ""),
                    "mailing_address": owner_info.get("mailing_address", ""),
                    "search_source": "web_scraping_tax",
                    "data_quality": "basic",
                }

                logger.info(
                    f"Found basic property data for APN: {apn} (via web scraping)"
                )
                logger.info(
                    f"SEARCH_ANALYTICS: apn_search, results=1, apn={apn}, source=webscrape"
                )
                return property_data

        except Exception as e:
            logger.error(f"Web scraping fallback failed for APN {apn}: {e}")

        logger.warning(f"No property found for APN: {apn} (tried API and web scraping)")
        logger.info(f"SEARCH_ANALYTICS: apn_search, results=0, apn={apn}, source=none")
        return None

    def get_property_details(self, apn: str) -> Optional[Dict]:
        """Get detailed property information using comprehensive API endpoints"""
        logger.info(f"Getting property details for APN: {apn}")

        try:
            # Use the comprehensive property data method
            detailed_info = self.get_comprehensive_property_info(apn)

            if detailed_info:
                logger.info(f"Retrieved property details for APN: {apn}")
                return detailed_info
            else:
                logger.warning(f"No property details found for APN: {apn}")
                return None

        except Exception as e:
            logger.error(f"Error getting property details for APN {apn}: {e}")
            raise

    def get_tax_history(self, apn: str, years: int = 5) -> List[Dict]:
        """
        Get tax history with automatic fallback to web scraping

        This method tries multiple approaches:
        1. API valuation endpoint (primary)
        2. Web scraping from Treasurer's office (fallback)
        3. Return empty list if no data found

        Args:
            apn: Property APN to lookup
            years: Number of years of history to retrieve (default: 5)

        Returns:
            List of tax records, empty if none found
        """
        logger.info(f"Getting tax history for APN: {apn} (years: {years})")

        try:
            # Primary method: API valuation endpoint
            response = self._make_request(f"/parcel/{apn}/valuations/")

            if response and isinstance(response, list):
                # Filter by years if requested
                current_year = 2024
                min_year = current_year - years + 1

                filtered_records = [
                    record
                    for record in response
                    if record.get("TaxYear")
                    and int(record.get("TaxYear", 0)) >= min_year
                ]

                result_count = len(filtered_records)
                logger.info(
                    f"Retrieved {result_count} tax records from API for APN: {apn}"
                )

                if result_count > 0:
                    return filtered_records

            # Fallback method: Web scraping from Treasurer's office
            logger.info(
                f"API returned limited tax data, attempting web scraping fallback for APN: {apn}"
            )
            try:
                tax_scrape_data = self.get_tax_information_web(apn)
                if tax_scrape_data and tax_scrape_data.get("tax_history"):
                    logger.info(
                        f"Retrieved tax history via web scraping fallback for APN: {apn}"
                    )
                    return tax_scrape_data["tax_history"]
            except Exception as scrape_error:
                logger.warning(
                    f"Web scraping fallback failed for tax history - APN {apn}: {scrape_error}"
                )

            logger.warning(f"No tax history found from any source for APN: {apn}")
            return []

        except Exception as e:
            logger.error(f"Error getting tax history for APN {apn}: {e}")

            # Try web scraping as last resort
            try:
                logger.info(
                    f"API failed, attempting web scraping as last resort for APN: {apn}"
                )
                tax_scrape_data = self.get_tax_information_web(apn)
                if tax_scrape_data and tax_scrape_data.get("tax_history"):
                    logger.info(
                        f"Retrieved tax history via web scraping last resort for APN: {apn}"
                    )
                    return tax_scrape_data["tax_history"]
            except Exception as scrape_error:
                logger.warning(
                    f"Web scraping last resort failed for tax history - APN {apn}: {scrape_error}"
                )

            # Return empty list rather than raising exception to maintain compatibility
            return []

    def get_sales_history(self, apn: str, years: int = 10) -> List[Dict]:
        """
        Get sales history with automatic fallback to web scraping

        This method tries multiple approaches:
        1. Check for API-based sales data (future enhancement)
        2. Fall back to web scraping from Recorder's office
        3. Return empty list if no data found

        Args:
            apn: Property APN to lookup
            years: Number of years of history to retrieve (default: 10)

        Returns:
            List of sales records, empty if none found
        """
        logger.info(f"Getting sales history for APN: {apn} (years: {years})")

        try:
            # Primary method: API-based sales history (not available yet in Maricopa API)
            # This placeholder allows for future API integration
            api_sales_data = None

            if api_sales_data:
                logger.info(f"Retrieved sales history from API for APN: {apn}")
                return api_sales_data

            # Fallback method: Web scraping from Recorder's office
            logger.info(f"Falling back to web scraping for sales history - APN: {apn}")
            sales_data = self._scrape_sales_data_sync(apn, years)

            if sales_data and "sales_history" in sales_data:
                sales_records = sales_data["sales_history"]
                result_count = len(sales_records)
                logger.info(
                    f"Retrieved {result_count} sales records via web scraping for APN: {apn}"
                )
                return sales_records
            else:
                logger.warning(
                    f"No sales history found via web scraping for APN: {apn}"
                )
                return []

        except Exception as e:
            logger.error(f"Error getting sales history for APN {apn}: {e}")
            # Return empty list rather than raising exception to maintain compatibility
            return []

    def bulk_property_search(self, apns: List[str]) -> Dict[str, Dict]:
        """Bulk search for multiple properties using individual API calls"""
        logger.info(f"Starting bulk search for {len(apns)} properties")

        results = {}

        try:
            for i, apn in enumerate(apns):
                logger.debug(f"Processing APN {i+1}/{len(apns)}: {apn}")

                try:
                    property_data = self.search_by_apn(apn)
                    if property_data:
                        results[apn] = property_data
                        logger.debug(f"Found property for APN: {apn}")
                    else:
                        logger.debug(f"No property found for APN: {apn}")
                except Exception as e:
                    logger.warning(f"Error searching APN {apn}: {e}")
                    continue

                # Rate limiting - small delay between requests
                if i < len(apns) - 1:
                    time.sleep(0.02)  # Optimized delay

            success_rate = (len(results) / len(apns)) * 100 if apns else 0
            logger.info(
                f"Bulk search completed: {len(results)}/{len(apns)} properties retrieved ({success_rate:.1f}% success rate)"
            )
            logger.info(
                f"SEARCH_ANALYTICS: bulk_search, requested={len(apns)}, returned={len(results)}, success_rate={success_rate:.1f}%"
            )

            return results

        except Exception as e:
            logger.error(f"Error in bulk property search for {len(apns)} APNs: {e}")
            raise

    def validate_apn(self, apn: str) -> bool:
        """Validate if APN exists by searching for it"""
        logger.debug(f"Validating APN: {apn}")

        try:
            property_data = self.search_by_apn(apn)
            is_valid = property_data is not None
            logger.debug(f"APN {apn} validation result: {is_valid}")
            return is_valid

        except Exception as e:
            logger.error(f"Error validating APN {apn}: {e}")
            return False

    def get_api_status(self) -> Dict[str, Any]:
        """Get API service status and limits"""
        logger.debug("Getting API status - real Maricopa County API active")

        # Return real API status with performance stats
        stats = self.get_performance_stats()

        return {
            "status": "Unified Real API",
            "version": "3.0",
            "rate_limit": {"requests_per_minute": 60, "remaining": 60},
            "endpoints": ["property", "tax", "sales"],
            "message": "Using unified Maricopa County Assessor API with performance optimizations",
            "performance_stats": stats,
        }

    # ========================================================================
    # HIGH-PERFORMANCE ASYNC METHODS
    # ========================================================================

    async def _make_async_request(
        self, endpoint: str, params: Dict = None
    ) -> Optional[Dict]:
        """Make async HTTP request with caching and error handling"""
        cache_key = self._get_cache_key(endpoint, params)

        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        start_time = time.time()
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        try:
            session = await self.connection_pool.get_session(self.token)
            async with session.get(url, params=params) as response:
                response_time = time.time() - start_time
                self.request_times.append(response_time)

                api_logger.debug(
                    f"API Request: {endpoint} - {response.status} - {response_time:.3f}s"
                )

                if response.status == 200:
                    data = await response.json()
                    # Cache successful responses for 5 minutes
                    self._cache_data(cache_key, data, ttl=300.0)

                    if self.rate_limiter:
                        self.rate_limiter.record_success()

                    return data
                elif response.status == 404:
                    # Cache 404s for 1 minute to avoid repeated failed requests
                    self._cache_data(cache_key, {}, ttl=60.0)
                    return None
                else:
                    logger.warning(
                        f"API request failed: {endpoint} - Status: {response.status}"
                    )
                    if self.rate_limiter:
                        self.rate_limiter.record_error()
                    return None

        except asyncio.TimeoutError:
            logger.warning(f"Request timeout for endpoint: {endpoint}")
            if self.rate_limiter:
                self.rate_limiter.record_error()
            return None
        except Exception as e:
            logger.error(f"Request error for endpoint {endpoint}: {e}")
            if self.rate_limiter:
                self.rate_limiter.record_error()
            return None

    async def _get_detailed_property_data_parallel(self, apn: str) -> Dict[str, Any]:
        """Get comprehensive property data using parallel requests"""
        logger.info(f"Getting detailed property data (parallel) for APN: {apn}")

        # Define all endpoints to fetch in parallel
        endpoints = {
            "valuations": f"/parcel/{apn}/valuations/",
            "residential_details": f"/parcel/{apn}/residential-details/",
            "improvements": f"/parcel/{apn}/improvements/",
            "sketches": f"/parcel/{apn}/sketches/",
            "mapids": f"/parcel/{apn}/mapids/",
        }

        # Try to get owner name for rental details (if needed)
        try:
            basic_search = await self._make_async_request(
                f"/search/property/", {"q": apn}
            )
            if basic_search and "Results" in basic_search and basic_search["Results"]:
                for result in basic_search["Results"]:
                    if "Ownership" in result:
                        owner_name = result["Ownership"]
                        endpoints["rental_details"] = (
                            f"/parcel/{apn}/rental-details/{owner_name}/"
                        )
                        break
        except Exception as e:
            logger.debug(f"Could not determine owner name for rental details: {e}")

        # Execute all requests in parallel
        start_time = time.time()
        tasks = []

        for endpoint_name, endpoint_path in endpoints.items():
            task = asyncio.create_task(
                self._make_async_request(endpoint_path), name=endpoint_name
            )
            tasks.append((endpoint_name, task))

        # Wait for all requests to complete
        detailed_data = {}
        for endpoint_name, task in tasks:
            try:
                response = await task
                if response:
                    detailed_data[endpoint_name] = response
                    logger.debug(f"Retrieved {endpoint_name} data")
                else:
                    logger.debug(f"No data from {endpoint_name}")
            except Exception as e:
                logger.error(f"Error retrieving {endpoint_name}: {e}")

        total_time = time.time() - start_time
        logger.info(
            f"Parallel data collection completed in {total_time:.3f}s for APN: {apn}"
        )

        return detailed_data

    def get_detailed_property_data_fast(self, apn: str) -> Dict[str, Any]:
        """Synchronous wrapper for parallel detailed property data retrieval"""
        return asyncio.run(self._get_detailed_property_data_parallel(apn))

    async def _get_comprehensive_property_info_parallel(
        self, apn: str
    ) -> Optional[Dict]:
        """Get complete property information using parallel requests"""
        logger.info(f"Getting comprehensive property info (parallel) for APN: {apn}")

        start_time = time.time()

        # Execute basic search and detailed data collection in parallel
        basic_search_task = asyncio.create_task(
            self._make_async_request("/search/property/", {"q": apn}),
            name="basic_search",
        )
        detailed_data_task = asyncio.create_task(
            self._get_detailed_property_data_parallel(apn), name="detailed_data"
        )

        # Wait for both to complete
        try:
            basic_search, detailed_data = await asyncio.gather(
                basic_search_task, detailed_data_task, return_exceptions=True
            )

            # Handle exceptions
            if isinstance(basic_search, Exception):
                logger.warning(f"Basic search failed: {basic_search}")
                basic_search = None

            if isinstance(detailed_data, Exception):
                logger.error(f"Detailed data collection failed: {detailed_data}")
                return None

            if not detailed_data or not any(detailed_data.values()):
                logger.warning(f"No detailed data found for APN: {apn}")
                return None

            # Start with basic info if available
            comprehensive_info = {}
            if basic_search and "Results" in basic_search and basic_search["Results"]:
                # Find exact APN match
                for result in basic_search["Results"]:
                    if result.get("APN", "").replace("-", "").replace(
                        ".", ""
                    ) == apn.replace("-", "").replace(".", ""):
                        comprehensive_info = self._normalize_api_data(result)
                        break

                # If no exact match, use first result
                if not comprehensive_info and basic_search["Results"]:
                    comprehensive_info = self._normalize_api_data(
                        basic_search["Results"][0]
                    )

            if not comprehensive_info:
                comprehensive_info = {
                    "apn": apn,
                    "search_source": "detailed_endpoints_only",
                }

            # Add valuation data
            if "valuations" in detailed_data and detailed_data["valuations"]:
                self._add_valuation_data(
                    comprehensive_info, detailed_data["valuations"]
                )

            # Add residential details
            if (
                "residential_details" in detailed_data
                and detailed_data["residential_details"]
            ):
                self._add_residential_data(
                    comprehensive_info, detailed_data["residential_details"]
                )

            # Add improvements data
            if "improvements" in detailed_data and detailed_data["improvements"]:
                self._add_improvements_data(
                    comprehensive_info, detailed_data["improvements"]
                )

            # Store all detailed data
            comprehensive_info["detailed_data"] = detailed_data

            total_time = time.time() - start_time
            logger.info(
                f"Comprehensive property info collected in {total_time:.3f}s for APN: {apn}"
            )

            return comprehensive_info

        except Exception as e:
            logger.error(
                f"Error in comprehensive property info collection for APN {apn}: {e}"
            )
            return None

    def get_comprehensive_property_info_fast(self, apn: str) -> Optional[Dict]:
        """Synchronous wrapper for parallel comprehensive property info retrieval"""
        return asyncio.run(self._get_comprehensive_property_info_parallel(apn))

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    def submit_batch_requests(self, requests: List[BatchAPIRequest]) -> List[str]:
        """Submit multiple API requests for batch processing"""
        request_ids = []

        with self.requests_lock:
            for request in requests:
                # Generate unique request ID if not provided
                if not request.request_id:
                    request.request_id = f"{request.request_type}_{request.identifier}_{int(time.time())}"

                # Add to priority queue
                priority_tuple = (request.priority, time.time())
                self.request_queue.put((priority_tuple, request))
                request_ids.append(request.request_id)

                logger.debug(f"Queued API request: {request.request_id}")

        # Start processing
        self._process_request_queue()

        logger.info(f"Submitted {len(requests)} batch API requests")
        return request_ids

    def batch_search_by_apns(
        self, apns: List[str], priority: int = 5, comprehensive: bool = True
    ) -> List[str]:
        """Batch search for multiple properties by APN"""
        requests = []

        for apn in apns:
            if comprehensive:
                request = BatchAPIRequest(
                    request_id=f"comprehensive_{apn}_{int(time.time())}",
                    request_type="get_comprehensive_property_info",
                    identifier=apn,
                    priority=priority,
                )
            else:
                request = BatchAPIRequest(
                    request_id=f"search_{apn}_{int(time.time())}",
                    request_type="search_by_apn",
                    identifier=apn,
                    priority=priority,
                )
            requests.append(request)

        return self.submit_batch_requests(requests)

    def _process_request_queue(self):
        """Process queued requests in thread pool"""
        self.executor.submit(self._queue_processor_worker)

    def _queue_processor_worker(self):
        """Background worker to process API request queue"""
        while True:
            try:
                # Get next request with timeout
                try:
                    priority_tuple, request = self.request_queue.get(timeout=5.0)
                except queue.Empty:
                    break  # No more requests to process

                # Submit request for execution
                future = self.executor.submit(self._execute_api_request, request)

                with self.requests_lock:
                    self.active_requests[request.request_id] = (request, future)

                # Brief pause to prevent overwhelming
                time.sleep(0.05)

            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                time.sleep(1.0)

    def _execute_api_request(self, request: BatchAPIRequest):
        """Execute a single API request with error handling and retries"""
        start_time = time.time()
        request.started_at = datetime.now()

        logger.debug(f"Executing API request: {request.request_id}")

        for attempt in range(request.max_retries + 1):
            try:
                # Rate limiting
                if self.rate_limiter and not self.rate_limiter.acquire(timeout=10.0):
                    raise TimeoutError("Rate limit timeout")

                # Execute based on request type
                if request.request_type == "search_by_apn":
                    result = self.search_by_apn(request.identifier)
                elif request.request_type == "search_by_owner":
                    limit = request.params.get("limit", 50)
                    result = self.search_by_owner(request.identifier, limit=limit)
                elif request.request_type == "search_by_address":
                    limit = request.params.get("limit", 50)
                    result = self.search_by_address(request.identifier, limit=limit)
                elif request.request_type == "get_property_details":
                    result = self.get_property_details(request.identifier)
                elif request.request_type == "get_comprehensive_property_info":
                    result = self.get_comprehensive_property_info(request.identifier)
                elif request.request_type == "get_tax_history":
                    years = request.params.get("years", 5)
                    result = self.get_tax_history(request.identifier, years=years)
                else:
                    raise ValueError(
                        f"Unsupported request type: {request.request_type}"
                    )

                # Success - record result
                request.result = result
                request.completed_at = datetime.now()

                # Update statistics
                response_time = time.time() - start_time
                with self.stats_lock:
                    self.total_requests += 1
                    self.total_successful += 1

                logger.info(
                    f"API request completed successfully: {request.request_id} in {response_time:.2f}s"
                )
                break

            except Exception as e:
                request.retry_count = attempt
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"

                if attempt < request.max_retries:
                    logger.warning(f"API request failed, retrying: {error_msg}")
                    # Exponential backoff with jitter
                    backoff_time = (2**attempt) + (time.time() % 1)  # Add jitter
                    time.sleep(backoff_time)
                else:
                    request.error = error_msg
                    request.completed_at = datetime.now()

                    # Update statistics
                    with self.stats_lock:
                        self.total_requests += 1
                        self.total_failed += 1

                    logger.error(
                        f"API request failed after {request.max_retries + 1} attempts: {error_msg}"
                    )

        # Move from active to completed
        with self.requests_lock:
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
            self.completed_requests[request.request_id] = request

    def wait_for_batch_completion(
        self, request_ids: List[str], timeout: float = 300.0
    ) -> Dict[str, Any]:
        """Wait for batch of requests to complete"""
        start_time = time.time()
        results = {}

        while time.time() - start_time < timeout:
            all_completed = True

            for request_id in request_ids:
                if request_id in results:
                    continue

                status = self.get_request_status(request_id)
                if status and status["status"] == "completed":
                    result = self.get_request_result(request_id)
                    results[request_id] = {"status": status, "result": result}
                else:
                    all_completed = False

            if all_completed:
                break

            time.sleep(1.0)  # Check every second

        # Return results for completed requests
        completion_stats = {
            "total_requested": len(request_ids),
            "completed": len(results),
            "successful": sum(1 for r in results.values() if r["status"]["success"]),
            "failed": sum(1 for r in results.values() if not r["status"]["success"]),
            "timeout": time.time() - start_time >= timeout,
            "results": results,
        }

        logger.info(
            f"Batch completion: {completion_stats['completed']}/{completion_stats['total_requested']} "
            f"requests completed, {completion_stats['successful']} successful"
        )

        return completion_stats

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an API request"""
        with self.requests_lock:
            # Check completed requests first
            if request_id in self.completed_requests:
                request = self.completed_requests[request_id]
                return {
                    "request_id": request_id,
                    "status": "completed",
                    "request_type": request.request_type,
                    "identifier": request.identifier,
                    "started_at": (
                        request.started_at.isoformat() if request.started_at else None
                    ),
                    "completed_at": (
                        request.completed_at.isoformat()
                        if request.completed_at
                        else None
                    ),
                    "success": request.result is not None,
                    "error": request.error,
                    "retry_count": request.retry_count,
                }

            # Check active requests
            if request_id in self.active_requests:
                request, future = self.active_requests[request_id]
                return {
                    "request_id": request_id,
                    "status": "running",
                    "request_type": request.request_type,
                    "identifier": request.identifier,
                    "started_at": (
                        request.started_at.isoformat() if request.started_at else None
                    ),
                    "success": False,
                    "error": None,
                }

            return None

    def get_request_result(self, request_id: str) -> Optional[Any]:
        """Get result from completed API request"""
        with self.requests_lock:
            if request_id in self.completed_requests:
                request = self.completed_requests[request_id]
                return request.result
            return None

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def get_comprehensive_property_info(self, apn: str) -> Optional[Dict]:
        """
        Get complete property information combining basic search + detailed data.
        This is the main method that should be used for most property lookups.
        Uses optimized parallel processing when available.
        """
        logger.info(f"Getting comprehensive property info for APN: {apn}")

        try:
            # Try fast parallel version first if event loop is available
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Already in async context, use the fast version
                    return self.get_comprehensive_property_info_fast(apn)
            except RuntimeError:
                pass  # No event loop, use sync version

            # Fallback to synchronous version
            return self._get_comprehensive_property_info_sync(apn)

        except Exception as e:
            logger.error(
                f"Error getting comprehensive property info for APN {apn}: {e}"
            )
            return None

    def _get_comprehensive_property_info_sync(self, apn: str) -> Optional[Dict]:
        """Synchronous version of comprehensive property info retrieval with web scraping fallback"""
        try:
            # Try to get basic property info first (optional)
            basic_info = None
            try:
                basic_info = self.search_by_apn(apn)
            except Exception as e:
                logger.warning(
                    f"Basic search failed for APN {apn}, continuing with detailed data only: {e}"
                )

            # Get detailed data using parallel thread execution
            detailed_data = self._get_detailed_property_data_threaded(apn)

            # Check if we have sufficient data from API
            api_data_sufficient = detailed_data and any(detailed_data.values())

            # If API data is insufficient, try web scraping fallback
            if not api_data_sufficient:
                logger.warning(
                    f"Insufficient API data for APN: {apn}, trying web scraping fallback"
                )

                try:
                    # Use the new comprehensive web scraping method
                    web_scraped_data = (
                        self.get_complete_property_with_automatic_data_collection(apn)
                    )

                    if web_scraped_data:
                        logger.info(
                            f"Successfully retrieved data via web scraping fallback for APN: {apn}"
                        )
                        return web_scraped_data

                except Exception as e:
                    logger.error(f"Web scraping fallback failed for APN {apn}: {e}")

                logger.warning(
                    f"No data found for APN: {apn} (tried API and web scraping)"
                )
                return None

            # Start with basic info if available, otherwise create minimal structure
            if basic_info:
                comprehensive_info = basic_info.copy()
            else:
                comprehensive_info = {
                    "apn": apn,
                    "search_source": "detailed_endpoints_only",
                }

            # Add valuation data
            if "valuations" in detailed_data and detailed_data["valuations"]:
                self._add_valuation_data(
                    comprehensive_info, detailed_data["valuations"]
                )

            # Add residential details
            if (
                "residential_details" in detailed_data
                and detailed_data["residential_details"]
            ):
                self._add_residential_data(
                    comprehensive_info, detailed_data["residential_details"]
                )

            # Add improvements data
            if "improvements" in detailed_data and detailed_data["improvements"]:
                self._add_improvements_data(
                    comprehensive_info, detailed_data["improvements"]
                )

            # Store all detailed data
            comprehensive_info["detailed_data"] = detailed_data

            # Add required database fields if not present from basic search
            self._ensure_required_fields(comprehensive_info)

            # Try to enhance with web scraping data if API data seems limited
            if self._is_api_data_limited(comprehensive_info):
                logger.info(
                    f"Enhancing limited API data with web scraping for APN: {apn}"
                )
                try:
                    # Get additional data via web scraping
                    tax_data = self._scrape_tax_data_sync(apn)
                    sales_data = self._scrape_sales_data_sync(apn)

                    # Enhance with tax data
                    if tax_data:
                        comprehensive_info["enhanced_tax_data"] = tax_data
                        if "owner_info" in tax_data and not comprehensive_info.get(
                            "owner_name"
                        ):
                            comprehensive_info["owner_name"] = tax_data[
                                "owner_info"
                            ].get("owner_name", "")

                    # Enhance with sales data
                    if sales_data:
                        comprehensive_info["enhanced_sales_data"] = sales_data

                    comprehensive_info["data_enhancement"] = "api_plus_webscraping"

                except Exception as e:
                    logger.warning(
                        f"Could not enhance API data with web scraping for APN {apn}: {e}"
                    )

            logger.info(f"Successfully compiled comprehensive info for APN: {apn}")
            return comprehensive_info

        except Exception as e:
            logger.error(
                f"Error getting comprehensive property info for APN {apn}: {e}"
            )
            return None

    def _get_detailed_property_data_threaded(self, apn: str) -> Dict[str, Any]:
        """Get detailed property data using threaded parallel execution"""
        logger.info(f"Getting detailed property data (threaded) for APN: {apn}")

        # Define endpoints for parallel execution
        endpoints = {
            "valuations": f"/parcel/{apn}/valuations/",
            "residential_details": f"/parcel/{apn}/residential-details/",
            "improvements": f"/parcel/{apn}/improvements/",
            "sketches": f"/parcel/{apn}/sketches/",
            "mapids": f"/parcel/{apn}/mapids/",
        }

        # Try to get owner name for rental details
        try:
            basic_search = self.search_by_apn(apn)
            if basic_search and basic_search.get("owner_name"):
                owner_name = basic_search["owner_name"]
                endpoints["rental_details"] = (
                    f"/parcel/{apn}/rental-details/{owner_name}/"
                )
        except Exception as e:
            logger.debug(f"Could not determine owner name for rental details: {e}")

        # Execute requests in parallel using thread pool
        start_time = time.time()
        detailed_data = {}

        # Submit all requests to thread pool
        future_to_endpoint = {}
        for endpoint_name, endpoint_path in endpoints.items():
            future = self.executor.submit(self._make_request, endpoint_path)
            future_to_endpoint[future] = endpoint_name

        # Collect results as they complete
        for future in as_completed(future_to_endpoint, timeout=30):
            endpoint_name = future_to_endpoint[future]
            try:
                response = future.result()
                if response:
                    detailed_data[endpoint_name] = response
                    logger.debug(f"Retrieved {endpoint_name} data")
                else:
                    logger.debug(f"No data from {endpoint_name}")
            except Exception as e:
                logger.error(f"Error retrieving {endpoint_name}: {e}")

        total_time = time.time() - start_time
        logger.info(
            f"Threaded data collection completed in {total_time:.3f}s for APN: {apn}"
        )

        return detailed_data

    def _is_api_data_limited(self, property_data: Dict[str, Any]) -> bool:
        """Determine if API data is limited and would benefit from web scraping enhancement"""
        if not property_data:
            return True

        # Check for missing critical fields
        critical_fields = ["owner_name", "property_address", "assessed_value"]
        missing_critical = sum(
            1 for field in critical_fields if not property_data.get(field)
        )

        # If more than half of critical fields are missing, enhance with web scraping
        if missing_critical >= len(critical_fields) // 2:
            logger.debug(
                f"API data missing {missing_critical}/{len(critical_fields)} critical fields"
            )
            return True

        # Check if detailed_data is sparse
        detailed_data = property_data.get("detailed_data", {})
        if not detailed_data or len([k for k, v in detailed_data.items() if v]) < 2:
            logger.debug("Detailed API data is sparse, would benefit from web scraping")
            return True

        return False

    def _add_valuation_data(self, comprehensive_info: Dict, valuations: List[Dict]):
        """Add valuation data to comprehensive info"""
        if valuations and len(valuations) > 0:
            latest_val = valuations[0]  # Most recent year
            comprehensive_info.update(
                {
                    "latest_tax_year": latest_val.get("TaxYear"),
                    "latest_assessed_value": self._safe_int(
                        latest_val.get("FullCashValue")
                    ),
                    "latest_limited_value": self._safe_int(
                        latest_val.get("LimitedPropertyValue", "").strip()
                    ),
                    "assessment_ratio": self._safe_float(
                        latest_val.get("AssessmentRatioPercentage")
                    ),
                    "tax_area_code": latest_val.get("TaxAreaCode"),
                    "property_use_description": latest_val.get("PEPropUseDesc"),
                    "valuation_history": valuations,
                }
            )

    def _add_residential_data(self, comprehensive_info: Dict, res_details: Dict):
        """Add residential details to comprehensive info"""
        comprehensive_info.update(
            {
                "year_built": self._safe_int(res_details.get("ConstructionYear")),
                "lot_size_sqft": self._safe_int(res_details.get("LotSize")),
                "living_area_sqft": self._safe_int(res_details.get("LivableSpace")),
                "pool": res_details.get("Pool", False),
                "quality_grade": res_details.get("ImprovementQualityGrade"),
                "exterior_walls": res_details.get("ExteriorWalls"),
                "roof_type": res_details.get("RoofType"),
                "bathrooms": self._safe_int(res_details.get("BathFixtures")),
                "garage_spaces": self._safe_int(res_details.get("NumberOfGarages")),
                "parking_details": res_details.get("ParkingDetails"),
                "residential_details": res_details,
            }
        )

        # Derive land use code from property use description
        if "property_use_description" in comprehensive_info:
            use_desc = comprehensive_info["property_use_description"]
            if "Multiple Family" in use_desc:
                comprehensive_info["land_use_code"] = "MFR"  # Multi-Family Residential
            elif "Single Family" in use_desc:
                comprehensive_info["land_use_code"] = "SFR"  # Single Family Residential
            elif "Commercial" in use_desc:
                comprehensive_info["land_use_code"] = "COM"  # Commercial

    def _add_improvements_data(
        self, comprehensive_info: Dict, improvements: List[Dict]
    ):
        """Add improvements data to comprehensive info"""
        if improvements:
            comprehensive_info["improvements_count"] = len(improvements)
            comprehensive_info["total_improvement_sqft"] = sum(
                self._safe_int(imp.get("ImprovementSquareFootage", 0)) or 0
                for imp in improvements
            )
            comprehensive_info["improvements_details"] = improvements

            # Calculate living area from residential improvements
            residential_sqft = sum(
                self._safe_int(imp.get("ImprovementSquareFootage", 0)) or 0
                for imp in improvements
                if "Apartment" in imp.get("ImprovementDescription", "")
                or "Town House" in imp.get("ImprovementDescription", "")
                or "Single Family" in imp.get("ImprovementDescription", "")
            )
            if residential_sqft > 0 and not comprehensive_info.get("living_area_sqft"):
                comprehensive_info["living_area_sqft"] = residential_sqft

            # Count apartment units for bedroom estimation
            apartment_units = sum(
                1
                for imp in improvements
                if "Apartment" in imp.get("ImprovementDescription", "")
                or "Town House" in imp.get("ImprovementDescription", "")
                or "Single Family" in imp.get("ImprovementDescription", "")
            )
            if apartment_units > 0 and not comprehensive_info.get("bedrooms"):
                # Estimate 1-2 bedrooms per unit for multi-family properties
                estimated_bedrooms = apartment_units * 2  # Conservative estimate
                comprehensive_info["bedrooms"] = estimated_bedrooms

    def _ensure_required_fields(self, comprehensive_info: Dict):
        """Ensure all required database fields are present"""
        required_fields = {
            "owner_name": None,
            "property_address": None,
            "mailing_address": None,
            "legal_description": None,
            "land_use_code": None,
            "bedrooms": None,
            "city": None,
            "zip_code": None,
            "property_type": None,
        }

        for field, default_value in required_fields.items():
            if field not in comprehensive_info:
                comprehensive_info[field] = default_value

        # Store raw detailed data if not already present
        if "raw_data" not in comprehensive_info:
            comprehensive_info["raw_data"] = json.dumps(
                comprehensive_info.get("detailed_data", {})
            )

    def _normalize_api_data(self, api_data: Dict) -> Dict:
        """Convert API field names to database field names"""
        field_mapping = {
            # API field -> Database field
            "APN": "apn",
            "MCR": "mcr",
            "Ownership": "owner_name",
            "SitusAddress": "property_address",
            "SitusCity": "city",
            "SitusZip": "zip_code",
            "PropertyType": "property_type",
            "RentalID": "rental_id",
            "SubdivisonName": "subdivision_name",
            "SectionTownshipRange": "section_township_range",
            # Business Personal Property fields
            "AccountNo": "account_number",
            "Name1": "business_name",
            "Name2": "business_name_2",
            # Additional common fields
            "Address": "property_address",
            "City": "city",
            "Zip": "zip_code",
            "Owner": "owner_name",
        }

        normalized = {}

        # Map known fields
        for api_field, db_field in field_mapping.items():
            if api_field in api_data:
                normalized[db_field] = api_data[api_field]

        # Keep unmapped fields as-is (lowercased)
        for key, value in api_data.items():
            if key not in field_mapping:
                normalized[key.lower()] = value

        # Ensure required fields exist with defaults
        if "apn" not in normalized and "APN" in api_data:
            normalized["apn"] = api_data["APN"]

        # Provide defaults for missing database fields
        default_fields = {
            "mailing_address": None,
            "legal_description": None,
            "land_use_code": None,
            "year_built": None,
            "living_area_sqft": None,
            "lot_size_sqft": None,
            "bedrooms": None,
            "bathrooms": None,
            "pool": None,
            "garage_spaces": None,
            "raw_data": json.dumps(api_data),  # Store original API response
        }

        for field, default_value in default_fields.items():
            if field not in normalized:
                normalized[field] = default_value

        logger.debug(f"Normalized API data: {list(normalized.keys())}")

        return normalized

    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if not value or value == "":
            return None
        try:
            return int(str(value).replace(",", "").strip())
        except (ValueError, AttributeError):
            return None

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if not value or value == "":
            return None
        try:
            return float(str(value).replace(",", "").strip())
        except (ValueError, AttributeError):
            return None

    def _scrape_tax_data_sync(self, apn: str) -> Optional[Dict]:
        """Synchronous wrapper for tax data scraping"""
        try:
            from tax_scraper import MaricopaTaxScraper
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--no-sandbox",
                    ],
                )
                page = browser.new_page()

                # Set longer timeouts for tax scraping
                page.set_default_timeout(90000)  # 90 seconds
                page.set_default_navigation_timeout(90000)

                scraper = MaricopaTaxScraper()
                tax_data = scraper.scrape_tax_data_for_apn(apn, page)

                browser.close()
                return tax_data

        except ImportError as e:
            logger.warning(f"Playwright not available for tax scraping: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in tax data scraping for {apn}: {e}")
            return None

    def _scrape_sales_data_sync(self, apn: str, years: int = 10) -> Optional[Dict]:
        """Synchronous wrapper for sales data scraping"""
        try:
            from recorder_scraper import MaricopaRecorderScraper
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--no-sandbox",
                    ],
                )
                page = browser.new_page()

                # Set longer timeouts for recorder scraping
                page.set_default_timeout(120000)  # 120 seconds
                page.set_default_navigation_timeout(120000)

                scraper = MaricopaRecorderScraper()
                recorder_data = scraper.scrape_document_data_for_apn(apn, page)

                browser.close()
                return recorder_data

        except ImportError as e:
            logger.warning(f"Playwright not available for sales scraping: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in sales data scraping for {apn}: {e}")
            return None

    # ========================================================================
    # WEB SCRAPING METHODS (Phase 1 Integration)
    # ========================================================================

    def get_tax_information_web(self, apn: str) -> Optional[Dict]:
        """
        Get tax information via web scraping from Maricopa County Treasurer's office

        Args:
            apn: Property APN to lookup

        Returns:
            Dictionary containing tax information scraped from treasurer.maricopa.gov
        """
        logger.info(f"Getting tax information via web scraping for APN: {apn}")

        try:
            # Use the existing tax scraping method
            tax_data = self._scrape_tax_data_sync(apn)

            if tax_data:
                logger.info(
                    f"Successfully retrieved tax information via web scraping for APN: {apn}"
                )
                return tax_data
            else:
                logger.warning(
                    f"No tax information found via web scraping for APN: {apn}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Error getting tax information via web scraping for APN {apn}: {e}"
            )
            return None

    def get_sales_history_web(self, apn: str, years: int = 10) -> Optional[Dict]:
        """
        Get sales history via web scraping from Maricopa County Recorder's office

        Args:
            apn: Property APN to lookup
            years: Number of years of history to retrieve (default: 10)

        Returns:
            Dictionary containing sales history scraped from recorder.maricopa.gov
        """
        logger.info(
            f"Getting sales history via web scraping for APN: {apn} (years: {years})"
        )

        try:
            # Use the existing recorder scraping method
            sales_data = self._scrape_sales_data_sync(apn, years)

            if sales_data:
                logger.info(
                    f"Successfully retrieved sales history via web scraping for APN: {apn}"
                )
                return sales_data
            else:
                logger.warning(
                    f"No sales history found via web scraping for APN: {apn}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Error getting sales history via web scraping for APN {apn}: {e}"
            )
            return None

    def get_complete_property_with_automatic_data_collection(
        self, apn: str
    ) -> Optional[Dict]:
        """
        Get complete property information with automatic fallback to web scraping

        This method combines API data with web scraping to provide the most comprehensive
        property information available. It follows the priority:
        1. API endpoints (fastest, most reliable)
        2. Web scraping for missing data (tax, sales history)
        3. Fallback data sources

        Args:
            apn: Property APN to lookup

        Returns:
            Dictionary containing comprehensive property information from all available sources
        """
        logger.info(
            f"Getting complete property with automatic data collection for APN: {apn}"
        )

        try:
            # Start with comprehensive API data
            property_info = self.get_comprehensive_property_info(apn)

            if not property_info:
                logger.warning(f"No basic property info found for APN: {apn}")
                return None

            # Check what additional data we can collect via web scraping
            needs_tax_data = not property_info.get("current_tax_amount")
            needs_sales_data = (
                not property_info.get("sales_history")
                or len(property_info.get("sales_history", [])) == 0
            )

            logger.info(
                f"Data collection needs for APN {apn} - Tax: {needs_tax_data}, Sales: {needs_sales_data}"
            )

            # Collect tax data via web scraping if needed
            if needs_tax_data:
                try:
                    logger.info(
                        f"Attempting to collect tax data via web scraping for APN: {apn}"
                    )
                    tax_data = self.get_tax_information_web(apn)

                    if tax_data:
                        # Integrate tax data with property info
                        owner_info = tax_data.get("owner_info", {})
                        current_tax = tax_data.get("current_tax", {})

                        # Update fields from tax scraping if not already present
                        if owner_info.get("owner_name") and not property_info.get(
                            "owner_name"
                        ):
                            property_info["owner_name"] = owner_info["owner_name"]
                        if owner_info.get("property_address") and not property_info.get(
                            "property_address"
                        ):
                            property_info["property_address"] = owner_info[
                                "property_address"
                            ]
                        if owner_info.get("mailing_address") and not property_info.get(
                            "mailing_address"
                        ):
                            property_info["mailing_address"] = owner_info[
                                "mailing_address"
                            ]

                        # Add current tax information
                        property_info.update(
                            {
                                "current_tax_amount": current_tax.get("assessed_tax"),
                                "current_payment_status": current_tax.get(
                                    "payment_status"
                                ),
                                "current_amount_due": current_tax.get("total_due"),
                                "tax_scrape_data": tax_data,
                            }
                        )

                        logger.info(f"Successfully integrated tax data for APN: {apn}")
                    else:
                        logger.warning(
                            f"Could not collect tax data via web scraping for APN: {apn}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error collecting tax data via web scraping for APN {apn}: {e}"
                    )

            # Collect sales data via web scraping if needed
            if needs_sales_data:
                try:
                    logger.info(
                        f"Attempting to collect sales data via web scraping for APN: {apn}"
                    )
                    sales_data = self.get_sales_history_web(apn)

                    if sales_data and sales_data.get("sales_history"):
                        property_info["sales_history"] = sales_data["sales_history"]
                        property_info["sales_scrape_data"] = sales_data
                        logger.info(
                            f"Successfully integrated sales data for APN: {apn} - {len(sales_data['sales_history'])} records"
                        )
                    else:
                        logger.warning(
                            f"Could not collect sales data via web scraping for APN: {apn}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error collecting sales data via web scraping for APN {apn}: {e}"
                    )

            # Add data completeness information
            property_info["data_completeness"] = {
                "has_api_data": True,
                "has_tax_scraping": bool(property_info.get("tax_scrape_data")),
                "has_sales_scraping": bool(property_info.get("sales_scrape_data")),
                "collection_method": "api_with_web_scraping_fallback",
                "last_updated": time.time(),
            }

            logger.info(f"Complete property data collection finished for APN {apn}")
            return property_info

        except Exception as e:
            logger.error(
                f"Error in complete property data collection for APN {apn}: {e}"
            )
            return None

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self.stats_lock:
            success_rate = (self.total_successful / max(1, self.total_requests)) * 100
            avg_response_time = sum(self.request_times) / max(
                len(self.request_times), 1
            )

        with self.requests_lock:
            active_count = len(self.active_requests)
            completed_count = len(self.completed_requests)
            pending_count = self.request_queue.qsize()

        stats = {
            "total_requests": self.total_requests,
            "total_successful": self.total_successful,
            "total_failed": self.total_failed,
            "success_rate_percent": success_rate,
            "average_response_time": avg_response_time,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (
                self.cache_hits / max(self.cache_hits + self.cache_misses, 1)
            )
            * 100,
            "cached_entries": len(self._cache),
            "active_requests": active_count,
            "completed_requests": completed_count,
            "pending_requests": pending_count,
        }

        # Add rate limiter stats if enabled
        if self.rate_limiter:
            stats["rate_limiter"] = self.rate_limiter.get_stats()

        return stats

    def cleanup_completed_requests(self, max_age_hours: int = 6):
        """Clean up old completed requests"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        removed_count = 0

        with self.requests_lock:
            requests_to_remove = [
                request_id
                for request_id, request in self.completed_requests.items()
                if request.completed_at and request.completed_at < cutoff_time
            ]

            for request_id in requests_to_remove:
                del self.completed_requests[request_id]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old API requests")

        return removed_count

    def close(self):
        """Close the HTTP sessions and cleanup resources"""
        try:
            if self.session:
                self.session.close()
                logger.info("Synchronous API client session closed successfully")

            # Close async components
            asyncio.run(self.connection_pool.close())

            # Shutdown executor
            self.executor.shutdown(wait=True)

            logger.info("Unified API client closed successfully")
        except Exception as e:
            logger.error(f"Error closing unified API client: {e}")

    async def async_close(self):
        """Async version of close for use in async contexts"""
        try:
            if self.session:
                self.session.close()

            await self.connection_pool.close()
            self.executor.shutdown(wait=True)

            logger.info("Unified API client closed successfully (async)")
        except Exception as e:
            logger.error(f"Error closing unified API client (async): {e}")


# Create aliases for backward compatibility
MaricopaAPIClient = UnifiedMaricopaAPIClient
MaricopaAssessorAPI = UnifiedMaricopaAPIClient
HighPerformanceMaricopaAPIClient = UnifiedMaricopaAPIClient
BatchAPIClient = UnifiedMaricopaAPIClient  # Unified client includes batch capabilities


class MockMaricopaAPIClient(UnifiedMaricopaAPIClient):
    """Mock API client for testing and development"""

    def __init__(self, config_manager=None):
        # Initialize parent but don't actually make HTTP requests
        if config_manager:
            self.config = config_manager.get_api_config()
            self.base_url = self.config["base_url"]
            self.token = self.config.get("token", API_TOKEN)
        else:
            self.base_url = "https://mcassessor.maricopa.gov/api"
            self.token = API_TOKEN

        logger.info("Initializing Mock API Client")
        logger.warning("Using Mock API Client - no actual API calls will be made")
        logger.debug(f"Mock API Configuration - Base URL: {self.base_url}")

    def test_connection(self) -> bool:
        """Mock test connection - always returns True"""
        logger.debug("Mock: Testing API connection (always returns True)")
        return True

    def _generate_mock_property(self, apn: str) -> Dict:
        """Generate mock property data"""
        import random

        logger.debug(f"Generating mock property data for APN: {apn}")

        return {
            "apn": apn,
            "owner_name": f"Mock Owner {apn[-4:]}",
            "property_address": f"{random.randint(100, 9999)} Mock Street, Phoenix, AZ 8510{random.randint(1, 9)}",
            "mailing_address": f"PO Box {random.randint(1000, 9999)}, Phoenix, AZ 8510{random.randint(1, 9)}",
            "legal_description": f"Mock Legal Description for {apn}",
            "land_use_code": random.choice(["R1", "R2", "C1", "I1"]),
            "year_built": random.randint(1950, 2023),
            "living_area_sqft": random.randint(800, 5000),
            "lot_size_sqft": random.randint(5000, 20000),
            "bedrooms": random.randint(2, 6),
            "bathrooms": random.randint(1, 4),
            "pool": random.choice([True, False]),
            "garage_spaces": random.randint(0, 3),
        }

    def search_by_apn(self, apn: str) -> Optional[Dict]:
        """Mock search by APN"""
        logger.info(f"Mock: Searching property by APN: {apn}")

        result = self._generate_mock_property(apn)
        logger.info(f"SEARCH_ANALYTICS: mock_apn_search, results=1, apn={apn}")

        return result

    def search_by_owner(self, owner_name: str, limit: int = 50) -> List[Dict]:
        """Mock search by owner"""
        logger.info(
            f"Mock: Searching properties by owner: {owner_name} (limit: {limit})"
        )

        result_count = min(3, limit)
        results = [
            self._generate_mock_property(f"12345{i:03d}") for i in range(result_count)
        ]

        logger.info(
            f"Mock: Generated {result_count} properties for owner: {owner_name}"
        )
        logger.info(
            f"SEARCH_ANALYTICS: mock_owner_search, results={result_count}, limit={limit}"
        )

        return results

    def search_by_address(self, address: str, limit: int = 50) -> List[Dict]:
        """Mock search by address"""
        logger.info(
            f"Mock: Searching properties by address: {address} (limit: {limit})"
        )

        result_count = min(2, limit)
        results = [
            self._generate_mock_property(f"67890{i:03d}") for i in range(result_count)
        ]

        logger.info(f"Mock: Generated {result_count} properties for address: {address}")
        logger.info(
            f"SEARCH_ANALYTICS: mock_address_search, results={result_count}, limit={limit}"
        )

        return results

    def get_api_status(self) -> Dict[str, Any]:
        """Mock API status"""
        logger.debug("Mock: Getting API status")

        return {
            "status": "mock",
            "version": "3.0.0-mock",
            "rate_limit": {"requests_per_minute": 60},
            "endpoints": ["mock_endpoints"],
            "message": "Using Mock Unified API Client",
        }
