#!/usr/bin/env python
"""
Batch Search Engine
Advanced batch/parallel processing system for property searches with optimized performance
"""
import asyncio
import json
import logging
import queue
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Event, Lock, RLock
from typing import Any, Callable, Dict, List, Optional, Set, Union

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from logging_config import get_logger, get_performance_logger

# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
# MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


class SearchMode(Enum):
    """Batch search execution modes"""

    PARALLEL = "parallel"  # Full parallel execution
    SEQUENTIAL = "sequential"  # One at a time
    HYBRID = "hybrid"  # Mixed approach based on load


class BatchPriority(Enum):
    """Batch job priority levels"""

    URGENT = 1  # User-initiated immediate requests
    HIGH = 2  # Top search results, critical operations
    NORMAL = 3  # Standard batch operations
    LOW = 4  # Background bulk processing


@dataclass
class BatchSearchRequest:
    """Individual search request within a batch"""

    identifier: str  # APN, address, or owner name
    search_type: str  # 'apn', 'address', 'owner'
    priority: BatchPriority = BatchPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    def __hash__(self):
        return hash((self.identifier, self.search_type))
    def __eq__(self, other):
        if not isinstance(other, BatchSearchRequest):
            return False
        return (
            self.identifier == other.identifier
            and self.search_type == other.search_type
        )


@dataclass
class BatchSearchJob:
    """Complete batch search job containing multiple requests"""

    job_id: str
    requests: List[BatchSearchRequest]
    mode: SearchMode = SearchMode.HYBRID
    max_concurrent: int = 5
    timeout_per_request: float = 30.0
    total_timeout: float = 600.0  # 10 minutes max per batch
    callback: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    status: str = "pending"


class RateLimiter:
    """Advanced rate limiter for API calls and web scraping"""
    def __init__(
        self,
        api_calls_per_second: float = 2.0,
        scraper_calls_per_second: float = 1.0,
        burst_size: int = 5,
    ):
        self.api_calls_per_second = api_calls_per_second
        self.scraper_calls_per_second = scraper_calls_per_second
        self.burst_size = burst_size

        # Token buckets for different rate limits
        self.api_bucket = burst_size
        self.scraper_bucket = burst_size
        self.last_api_refill = time.time()
        self.last_scraper_refill = time.time()
        self.lock = Lock()
    def acquire_api_token(self, timeout: float = 5.0) -> bool:
        """Acquire token for API call with timeout"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                now = time.time()

                # Refill API bucket
                time_passed = now - self.last_api_refill
                tokens_to_add = time_passed * self.api_calls_per_second
                self.api_bucket = min(self.burst_size, self.api_bucket + tokens_to_add)
                self.last_api_refill = now

                if self.api_bucket >= 1.0:
                    self.api_bucket -= 1.0
                    return True

            time.sleep(0.1)  # Short pause before retry

        return False
    def acquire_scraper_token(self, timeout: float = 10.0) -> bool:
        """Acquire token for web scraper call with timeout"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                now = time.time()

                # Refill scraper bucket
                time_passed = now - self.last_scraper_refill
                tokens_to_add = time_passed * self.scraper_calls_per_second
                self.scraper_bucket = min(
                    self.burst_size, self.scraper_bucket + tokens_to_add
                )
                self.last_scraper_refill = now

                if self.scraper_bucket >= 1.0:
                    self.scraper_bucket -= 1.0
                    return True

            time.sleep(0.2)  # Longer pause for scraper

        return False


class ConnectionPoolManager:
    """Database connection pooling for batch operations"""
    def __init__(self, db_managerThreadSafeDatabaseManager, pool_size: int = 10):
        self.db_manager = db_manager
        self.pool_size = pool_size
        self.connections = queue.Queue(maxsize=pool_size)
        self.lock = RLock()
        self.total_connections = 0

        # Pre-populate some connections
        self._initialize_pool()
    def _initialize_pool(self):
        """Initialize connection pool with a few connections"""
        initial_size = min(3, self.pool_size)
        for _ in range(initial_size):
    try:
                conn = self.db_manager.get_connection()
                self.connections.put(conn, block=False)
                self.total_connections += 1
    except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")
                break
    def acquire_connection(self, timeout: float = 5.0):
        """Get connection from pool or create new one"""
    try:
            # Try to get existing connection first
            return self.connections.get(timeout=timeout)
    except queue.Empty:
            # Create new connection if pool is empty and we haven't hit limit
            with self.lock:
                if self.total_connections < self.pool_size:
    try:
                        conn = self.db_manager.get_connection()
                        self.total_connections += 1
                        return conn
    except Exception as e:
                        logger.error(f"Failed to create new connection: {e}")
                        raise

            # If we hit the limit, wait for a connection to be returned
            return self.connections.get(timeout=timeout)
    def release_connection(self, connection):
        """Return connection to pool"""
    try:
            self.connections.put(connection, block=False)
    except queue.Full:
            # Pool is full, close this connection
    try:
                connection.close()
                with self.lock:
                    self.total_connections -= 1
    except Exception as e:
                logger.warning(f"Error closing excess connection: {e}")


class BatchSearchEngine:
    """Advanced batch search engine with parallel processing and optimization"""
    def __init__(
        self,
        api_clientUnifiedMaricopaAPIClient,
        db_managerThreadSafeDatabaseManager,
        web_scraper=None,
        max_concurrent_jobs: int = 3,
        max_concurrent_per_job: int = 5,
    ):

        logger.info("Initializing Batch Search Engine")

        self.api_client = api_client
        self.db_manager = db_manager
        self.web_scraper = web_scraper
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_concurrent_per_job = max_concurrent_per_job

        # Thread pool for batch operations
        self.executor = ThreadPoolExecutor(
            max_workers=max_concurrent_jobs * max_concurrent_per_job,
            thread_name_prefix="BatchSearch",
        )

        # Rate limiting and connection management
        self.rate_limiter = RateLimiter(
            api_calls_per_second=2.0, scraper_calls_per_second=0.8
        )
        self.connection_pool = ConnectionPoolManager(db_manager, pool_size=15)

        # Job management
        self.active_jobs: Dict[str, BatchSearchJob] = {}
        self.job_futures: Dict[str, List[Future]] = {}
        self.jobs_lock = RLock()
        self.shutdown_event = Event()

        # Performance tracking
        self.total_requests_processed = 0
        self.total_successful_requests = 0
        self.total_processing_time = 0.0
        self.stats_lock = Lock()

        # Fresh data configuration - never use cached data as fallback
        self.fresh_data_only = True  # Always fetch fresh data
        self.use_cache = False  # Disable cache fallback completely

        logger.info(
            f"Batch search engine initialized - "
            f"Max concurrent jobs: {max_concurrent_jobs}, "
            f"Max concurrent per job: {max_concurrent_per_job}"
        )
    def submit_batch_search(
        self,
        identifiers: List[str],
        search_type: str,
        mode: SearchMode = SearchMode.HYBRID,
        priority: BatchPriority = BatchPriority.NORMAL,
        max_concurrent: int = None,
        timeout_per_request: float = 30.0,
        callback: Callable = None,
    ) -> str:
        """
        Submit a batch search job

        Args:
            identifiers: List of APNs, addresses, or owner names to search
            search_type: 'apn', 'address', or 'owner'
            mode: Search execution mode
            priority: Job priority level
            max_concurrent: Override default concurrency
            timeout_per_request: Timeout per individual request
            callback: Callback function for progress updates

        Returns:
            job_id for tracking the batch job
        """
        job_id = f"batch_{search_type}_{int(time.time())}_{id(identifiers)}"

        # Create individual requests
        requests = []
        seen = set()  # Deduplicate identifiers

        for identifier in identifiers:
            if identifier and identifier not in seen:
                request = BatchSearchRequest(
                    identifier=identifier, search_type=search_type, priority=priority
                )
                requests.append(request)
                seen.add(identifier)

        if not requests:
            raise ValueError("No valid identifiers provided")

        # Create batch job
        batch_job = BatchSearchJob(
            job_id=job_id,
            requests=requests,
            mode=mode,
            max_concurrent=max_concurrent or self.max_concurrent_per_job,
            timeout_per_request=timeout_per_request,
            callback=callback,
        )

        # Store and start job
        with self.jobs_lock:
            self.active_jobs[job_id] = batch_job
            self.job_futures[job_id] = []

        # Submit job for execution
        future = self.executor.submit(self._execute_batch_job, batch_job)
        self.job_futures[job_id].append(future)

        logger.info(
            f"Submitted batch job {job_id}: {len(requests)} requests "
            f"({search_type} search, {mode.value} mode, {priority.value} priority)"
        )

        return job_id
    def _execute_batch_job(self, batch_job: BatchSearchJob):
        """Execute a complete batch job"""
        job_id = batch_job.job_id
        start_time = time.time()

    try:
            batch_job.started_at = datetime.now()
            batch_job.status = "running"

            logger.info(
                f"Executing batch job {job_id} with {len(batch_job.requests)} requests"
            )

            if batch_job.mode == SearchMode.SEQUENTIAL:
                self._execute_sequential(batch_job)
            elif batch_job.mode == SearchMode.PARALLEL:
                self._execute_parallel(batch_job)
            else:  # HYBRID
                self._execute_hybrid(batch_job)

            # Calculate final statistics
            completed_count = sum(
                1 for req in batch_job.requests if req.completed_at is not None
            )
            successful_count = sum(
                1 for req in batch_job.requests if req.result is not None
            )
            error_count = sum(1 for req in batch_job.requests if req.error is not None)

            batch_job.completed_at = datetime.now()
            batch_job.status = "completed"
            batch_job.progress = 100.0

            execution_time = time.time() - start_time

            # Update global statistics
            with self.stats_lock:
                self.total_requests_processed += len(batch_job.requests)
                self.total_successful_requests += successful_count
                self.total_processing_time += execution_time

            logger.info(
                f"Batch job {job_id} completed in {execution_time:.2f}s - "
                f"Processed: {completed_count}/{len(batch_job.requests)}, "
                f"Successful: {successful_count}, "
                f"Errors: {error_count}"
            )

            # Final callback
            if batch_job.callback:
    try:
                    batch_job.callback(batch_job)
    except Exception as e:
                    logger.error(f"Error in batch job callback: {e}")

    except Exception as e:
            batch_job.status = "failed"
            logger.error(f"Batch job {job_id} failed: {e}")
            raise

    finally:
            # Cleanup
            with self.jobs_lock:
                if job_id in self.job_futures:
                    del self.job_futures[job_id]
    def _execute_sequential(self, batch_job: BatchSearchJob):
        """Execute batch job sequentially"""
        logger.debug(f"Executing batch job {batch_job.job_id} in SEQUENTIAL mode")

        for i, request in enumerate(batch_job.requests):
            if self.shutdown_event.is_set():
                break

            self._execute_single_request(request)

            # Update progress
            batch_job.progress = (i + 1) / len(batch_job.requests) * 100

            if batch_job.callback:
                batch_job.callback(batch_job)
    def _execute_parallel(self, batch_job: BatchSearchJob):
        """Execute batch job in full parallel mode"""
        logger.debug(f"Executing batch job {batch_job.job_id} in PARALLEL mode")

        with ThreadPoolExecutor(max_workers=batch_job.max_concurrent) as executor:
            # Submit all requests
            future_to_request = {}
            for request in batch_job.requests:
                future = executor.submit(self._execute_single_request, request)
                future_to_request[future] = request

            # Process completed requests
            completed = 0
            for future in as_completed(
                future_to_request, timeout=batch_job.total_timeout
            ):
                completed += 1
                batch_job.progress = completed / len(batch_job.requests) * 100

                if batch_job.callback:
                    batch_job.callback(batch_job)

                if self.shutdown_event.is_set():
                    break
    def _execute_hybrid(self, batch_job: BatchSearchJob):
        """Execute batch job using hybrid approach"""
        logger.debug(f"Executing batch job {batch_job.job_id} in HYBRID mode")

        # Sort requests by priority
        sorted_requests = sorted(batch_job.requests, key=lambda x: x.priority.value)

        # Process high priority items first with higher concurrency
        high_priority = [
            r
            for r in sorted_requests
            if r.priority in [BatchPriority.URGENT, BatchPriority.HIGH]
        ]
        normal_priority = [
            r for r in sorted_requests if r.priority == BatchPriority.NORMAL
        ]
        low_priority = [r for r in sorted_requests if r.priority == BatchPriority.LOW]

        total_requests = len(batch_job.requests)
        completed = 0

        # Execute high priority with max concurrency
        if high_priority:
            logger.debug(f"Processing {len(high_priority)} high priority requests")
            completed += self._execute_batch_subset(
                high_priority, batch_job.max_concurrent
            )
            batch_job.progress = completed / total_requests * 100
            if batch_job.callback:
                batch_job.callback(batch_job)

        # Execute normal priority with reduced concurrency
        if normal_priority and not self.shutdown_event.is_set():
            logger.debug(f"Processing {len(normal_priority)} normal priority requests")
            concurrency = max(1, batch_job.max_concurrent // 2)
            completed += self._execute_batch_subset(normal_priority, concurrency)
            batch_job.progress = completed / total_requests * 100
            if batch_job.callback:
                batch_job.callback(batch_job)

        # Execute low priority with minimal concurrency
        if low_priority and not self.shutdown_event.is_set():
            logger.debug(f"Processing {len(low_priority)} low priority requests")
            completed += self._execute_batch_subset(low_priority, 1)
            batch_job.progress = completed / total_requests * 100
            if batch_job.callback:
                batch_job.callback(batch_job)
    def _execute_batch_subset(
        self, requests: List[BatchSearchRequest], max_workers: int
    ) -> int:
        """Execute a subset of requests with specified concurrency"""
        completed_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_request = {}
            for request in requests:
                future = executor.submit(self._execute_single_request, request)
                future_to_request[future] = request

            for future in as_completed(
                future_to_request, timeout=300
            ):  # 5 min timeout for subset
                completed_count += 1
                if self.shutdown_event.is_set():
                    break

        return completed_count
    def _execute_single_request(self, request: BatchSearchRequest):
        """Execute a single search request with error handling and retries"""
        request.started_at = datetime.now()
        logger.debug(
            f"Executing {request.search_type} search for: {request.identifier}"
        )

        for attempt in range(request.max_retries + 1):
    try:
                if self.shutdown_event.is_set():
                    request.error = "Shutdown requested"
                    return

                # Execute based on search type
                if request.search_type == "apn":
                    result = self._search_by_apn(request.identifier)
                elif request.search_type == "address":
                    result = self._search_by_address(request.identifier)
                elif request.search_type == "owner":
                    result = self._search_by_owner(request.identifier)
                else:
                    raise ValueError(f"Unsupported search type: {request.search_type}")

                # Store result
                request.result = result
                request.completed_at = datetime.now()

                logger.debug(
                    f"Successfully completed {request.search_type} search for: {request.identifier}"
                )
                return

    except Exception as e:
                request.retry_count = attempt
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"

                if attempt < request.max_retries:
                    logger.warning(f"Request failed, retrying: {error_msg}")
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    request.error = error_msg
                    request.completed_at = datetime.now()
                    logger.error(
                        f"Request failed after {request.max_retries + 1} attempts: {error_msg}"
                    )
    def _search_by_apn(self, apn: str) -> Optional[Dict]:
        """Search for property by APN using fresh data collection"""
        # Always collect fresh data - no cache fallback
        if not self.rate_limiter.acquire_api_token():
            raise TimeoutError("Rate limit timeout for API call")

    try:
            # Get comprehensive property info with fresh data
            result = self.api_client.get_comprehensive_property_info(apn)

            if result:
                # Save to database
                connection = self.connection_pool.acquire_connection()
    try:
                    success = self.db_manager.save_comprehensive_property_data(result)
                    if not success:
                        logger.warning(f"Failed to save property data for APN: {apn}")
    finally:
                    self.connection_pool.release_connection(connection)

            return result

    except Exception as e:
            logger.error(f"API search failed for APN {apn}: {e}")
            raise
    def _search_by_address(self, address: str) -> List[Dict]:
        """Search for properties by address using fresh data"""
        if not self.rate_limiter.acquire_api_token():
            raise TimeoutError("Rate limit timeout for API call")

    try:
            results = self.api_client.search_by_address(address, limit=50)

            # Save all results to database
            connection = self.connection_pool.acquire_connection()
    try:
                for result in results:
                    self.db_manager.insert_property(result)
    finally:
                self.connection_pool.release_connection(connection)

            return results

    except Exception as e:
            logger.error(f"API search failed for address {address}: {e}")
            raise
    def _search_by_owner(self, owner_name: str) -> List[Dict]:
        """Search for properties by owner name using fresh data"""
        if not self.rate_limiter.acquire_api_token():
            raise TimeoutError("Rate limit timeout for API call")

    try:
            results = self.api_client.search_by_owner(owner_name, limit=50)

            # Save all results to database
            connection = self.connection_pool.acquire_connection()
    try:
                for result in results:
                    self.db_manager.insert_property(result)
    finally:
                self.connection_pool.release_connection(connection)

            return results

    except Exception as e:
            logger.error(f"API search failed for owner {owner_name}: {e}")
            raise
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch job"""
        with self.jobs_lock:
            if job_id not in self.active_jobs:
                return None

            job = self.active_jobs[job_id]

            completed_count = sum(
                1 for req in job.requests if req.completed_at is not None
            )
            successful_count = sum(1 for req in job.requests if req.result is not None)
            error_count = sum(1 for req in job.requests if req.error is not None)

            return {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "total_requests": len(job.requests),
                "completed_requests": completed_count,
                "successful_requests": successful_count,
                "failed_requests": error_count,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": (
                    job.completed_at.isoformat() if job.completed_at else None
                ),
                "mode": job.mode.value,
                "max_concurrent": job.max_concurrent,
            }
    def get_job_results(self, job_id: str) -> Optional[List[Dict]]:
        """Get results from completed batch job"""
        with self.jobs_lock:
            if job_id not in self.active_jobs:
                return None

            job = self.active_jobs[job_id]
            results = []

            for request in job.requests:
                result_entry = {
                    "identifier": request.identifier,
                    "search_type": request.search_type,
                    "priority": request.priority.value,
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
                    "result": request.result,
                }
                results.append(result_entry)

            return results
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running batch job"""
        with self.jobs_lock:
            if job_id not in self.active_jobs:
                return False

            job = self.active_jobs[job_id]
            job.status = "cancelled"

            # Cancel associated futures
            if job_id in self.job_futures:
                for future in self.job_futures[job_id]:
                    future.cancel()

            logger.info(f"Cancelled batch job {job_id}")
            return True
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        with self.stats_lock:
            active_jobs_count = len(self.active_jobs)
            avg_processing_time = self.total_processing_time / max(
                1, self.total_requests_processed
            )
            success_rate = (
                self.total_successful_requests / max(1, self.total_requests_processed)
            ) * 100

        return {
            "total_requests_processed": self.total_requests_processed,
            "total_successful_requests": self.total_successful_requests,
            "success_rate_percent": success_rate,
            "average_processing_time": avg_processing_time,
            "active_jobs_count": active_jobs_count,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "max_concurrent_per_job": self.max_concurrent_per_job,
            "connection_pool_size": self.connection_pool.pool_size,
            "rate_limits": {
                "api_calls_per_second": self.rate_limiter.api_calls_per_second,
                "scraper_calls_per_second": self.rate_limiter.scraper_calls_per_second,
            },
        }
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        removed_count = 0

        with self.jobs_lock:
            jobs_to_remove = [
                job_id
                for job_id, job in self.active_jobs.items()
                if job.completed_at and job.completed_at < cutoff_time
            ]

            for job_id in jobs_to_remove:
                del self.active_jobs[job_id]
                if job_id in self.job_futures:
                    del self.job_futures[job_id]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old batch jobs")

        return removed_count
    def shutdown(self):
        """Gracefully shutdown the batch search engine"""
        logger.info("Shutting down batch search engine...")

        self.shutdown_event.set()

        # Cancel all active jobs
        with self.jobs_lock:
            for job_id in list(self.active_jobs.keys()):
                self.cancel_job(job_id)

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        logger.info("Batch search engine shutdown completed")


class BatchSearchWorker(QThread):
    """Qt-based worker for batch search operations"""

    job_started = pyqtSignal(str)  # job_id
    job_progress = pyqtSignal(str, float)  # job_id, progress
    job_completed = pyqtSignal(str, dict)  # job_id, results
    job_failed = pyqtSignal(str, str)  # job_id, error
    def __init__(self, batch_engine: BatchSearchEngine):
        super().__init__()
        self.batch_engine = batch_engine
        self.current_job_id = None
    def start_batch_search(
        self,
        identifiers: List[str],
        search_type: str,
        mode: SearchMode = SearchMode.HYBRID,
        priority: BatchPriority = BatchPriority.NORMAL,
    ):
        """Start batch search in Qt thread"""
        self.identifiers = identifiers
        self.search_type = search_type
        self.mode = mode
        self.priority = priority
        self.start()
    def run(self):
        """Execute batch search in background thread"""
    try:
            # Submit batch job
            self.current_job_id = self.batch_engine.submit_batch_search(
                identifiers=self.identifiers,
                search_type=self.search_type,
                mode=self.mode,
                priority=self.priority,
                callback=self._progress_callback,
            )

            self.job_started.emit(self.current_job_id)

            # Wait for completion
            while True:
                status = self.batch_engine.get_job_status(self.current_job_id)
                if not status:
                    break

                if status["status"] in ["completed", "failed", "cancelled"]:
                    break

                self.msleep(1000)  # Check every second

            # Get final results
            if status and status["status"] == "completed":
                results = self.batch_engine.get_job_results(self.current_job_id)
                self.job_completed.emit(
                    self.current_job_id, {"results": results, "status": status}
                )
            else:
                error_msg = f"Job failed with status: {status.get('status', 'unknown') if status else 'not found'}"
                self.job_failed.emit(self.current_job_id, error_msg)

    except Exception as e:
            error_msg = f"Batch search worker error: {str(e)}"
            logger.error(error_msg)
            self.job_failed.emit(self.current_job_id or "unknown", error_msg)
    def _progress_callback(self, batch_job: BatchSearchJob):
        """Handle progress updates from batch job"""
        if self.current_job_id:
            self.job_progress.emit(self.current_job_id, batch_job.progress)
