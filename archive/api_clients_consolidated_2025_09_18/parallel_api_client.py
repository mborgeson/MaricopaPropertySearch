"""
High-Performance Parallel Maricopa API Client
Optimized for sub-3 second property data collection using:
- Concurrent API calls
- Connection pooling
- Smart caching
- Optimized timeouts
- Progressive loading
"""

import asyncio
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp

from logging_config import get_api_logger

logger = logging.getLogger(__name__)
api_logger = get_api_logger(__name__)


@dataclass
class PropertyDataCache:
    """Cache entry for property data"""

    data: Dict[str, Any]
    timestamp: float
    ttl: float = 300.0  # 5 minutes default TTL

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl


class HighPerformanceMaricopaAPIClient:
    """High-performance API client with parallel request capabilities"""

    def __init__(self, config_manager):
        logger.info("Initializing High-Performance Maricopa API Client")

        self.config = config_manager.get_api_config()
        self.base_url = self.config["base_url"]
        self.token = self.config["token"]
        # Optimized timeouts for fast failure recovery
        self.timeout = min(self.config["timeout"], 5)  # Max 5 seconds per request
        self.max_retries = 2  # Reduced retries for faster failure recovery

        # Connection pooling configuration
        self.session = None
        self.session_lock = threading.Lock()
        self.connector_limit = 20  # Concurrent connections

        # Cache for repeated lookups
        self._cache = {}
        self._cache_lock = threading.Lock()

        # Performance tracking
        self.request_times = []
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(
            "High-Performance API Client initialized with parallel capabilities"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.connector_limit,
                limit_per_host=10,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )

            headers = {"Accept": "application/json", "User-Agent": None}
            if self.token:
                headers["AUTHORIZATION"] = self.token

            timeout = aiohttp.ClientTimeout(total=self.timeout)

            self.session = aiohttp.ClientSession(
                connector=connector, headers=headers, timeout=timeout
            )

        return self.session

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
            session = await self._get_session()
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
                    return data
                elif response.status == 404:
                    # Cache 404s for 1 minute to avoid repeated failed requests
                    self._cache_data(cache_key, {}, ttl=60.0)
                    return None
                else:
                    logger.warning(
                        f"API request failed: {endpoint} - Status: {response.status}"
                    )
                    return None

        except asyncio.TimeoutError:
            logger.warning(f"Request timeout for endpoint: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Request error for endpoint {endpoint}: {e}")
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
            basic_search = await self._make_async_request(f"/parcel/{apn}/")
            if basic_search and "owner_name" in basic_search:
                owner_name = basic_search["owner_name"]
                endpoints["rental_details"] = (
                    f"/parcel/{apn}/rental-details/{owner_name}/"
                )
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
            self._make_async_request(f"/parcel/{apn}/"), name="basic_search"
        )
        detailed_data_task = asyncio.create_task(
            self._get_detailed_property_data_parallel(apn), name="detailed_data"
        )

        # Wait for both to complete
        try:
            basic_info, detailed_data = await asyncio.gather(
                basic_search_task, detailed_data_task, return_exceptions=True
            )

            # Handle exceptions
            if isinstance(basic_info, Exception):
                logger.warning(f"Basic search failed: {basic_info}")
                basic_info = None

            if isinstance(detailed_data, Exception):
                logger.error(f"Detailed data collection failed: {detailed_data}")
                return None

            if not detailed_data or not any(detailed_data.values()):
                logger.warning(f"No detailed data found for APN: {apn}")
                return None

            # Combine results
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
                comprehensive_info["improvements"] = detailed_data["improvements"]

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
                "residential_details": res_details,
            }
        )

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

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (
                self.cache_hits / max(self.cache_hits + self.cache_misses, 1)
            )
            * 100,
            "avg_request_time": sum(self.request_times)
            / max(len(self.request_times), 1),
            "total_requests": len(self.request_times),
            "cached_entries": len(self._cache),
        }

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, "session") and self.session and not self.session.closed:
            asyncio.run(self.close())
