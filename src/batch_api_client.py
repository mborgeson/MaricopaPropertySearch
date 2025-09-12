#!/usr/bin/env python
"""
Batch API Client
Enhanced API client with optimized batch operations and parallel processing
"""

import asyncio
import aiohttp
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from threading import Lock, RLock, Semaphore
import threading
import json
import queue

from PyQt5.QtCore import QThread, pyqtSignal

from src.api_client import MaricopaAPIClient
from src.logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


@dataclass
class BatchAPIRequest:
    """Individual API request within a batch"""
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
        return (self.request_type == other.request_type and 
                self.identifier == other.identifier)


class ConnectionPoolManager:
    """Manages HTTP connection pools for optimized API requests"""
    
    def __init__(self, 
                 max_connections: int = 20,
                 max_connections_per_host: int = 10,
                 timeout: int = 30):
        
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout = timeout
        
        # Initialize connector lazily when needed
        self.connector = None
        self.session = None
        self.lock = Lock()
        
        logger.info(f"Connection pool manager initialized - "
                   f"Max connections: {max_connections}, "
                   f"Max per host: {max_connections_per_host}")
    
    def _ensure_connector(self):
        """Ensure connector is initialized (called in async context)"""
        if self.connector is None:
            self.connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections_per_host,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if not self.session or self.session.closed:
            self._ensure_connector()  # Ensure connector is initialized
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def close(self):
        """Close connection pool"""
        if self.session and not self.session.closed:
            await self.session.close()
        if self.connector:
            await self.connector.close()


class AdaptiveRateLimiter:
    """Smart rate limiter that adapts based on server responses"""
    
    def __init__(self, 
                 initial_rate: float = 2.0,
                 min_rate: float = 0.5,
                 max_rate: float = 5.0,
                 burst_capacity: int = 10):
        
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
        
        logger.info(f"Adaptive rate limiter initialized - "
                   f"Initial rate: {initial_rate} req/s, "
                   f"Burst capacity: {burst_capacity}")
    
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
                'current_rate': self.current_rate,
                'min_rate': self.min_rate,
                'max_rate': self.max_rate,
                'current_tokens': self.tokens,
                'burst_capacity': self.burst_capacity,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'rate_limit_count': self.rate_limit_count
            }


class BatchAPIClient:
    """Enhanced API client with batch operations and parallel processing"""
    
    def __init__(self, 
                 base_api_client: MaricopaAPIClient,
                 max_concurrent_requests: int = 10,
                 enable_connection_pooling: bool = True,
                 enable_adaptive_rate_limiting: bool = True):
        
        logger.info("Initializing Batch API Client")
        
        self.base_client = base_api_client
        self.max_concurrent_requests = max_concurrent_requests
        self.enable_connection_pooling = enable_connection_pooling
        self.enable_adaptive_rate_limiting = enable_adaptive_rate_limiting
        
        # Connection management
        if enable_connection_pooling:
            self.connection_pool = ConnectionPoolManager(
                max_connections=max_concurrent_requests + 5,
                max_connections_per_host=max_concurrent_requests
            )
        else:
            self.connection_pool = None
        
        # Rate limiting
        if enable_adaptive_rate_limiting:
            self.rate_limiter = AdaptiveRateLimiter(
                initial_rate=2.0,
                max_rate=5.0,
                burst_capacity=max_concurrent_requests
            )
        else:
            self.rate_limiter = None
        
        # Request management
        self.request_queue = queue.PriorityQueue()
        self.active_requests = {}
        self.completed_requests = {}
        self.requests_lock = RLock()
        
        # Thread pool for batch operations
        self.executor = ThreadPoolExecutor(
            max_workers=max_concurrent_requests,
            thread_name_prefix="BatchAPI"
        )
        
        # Performance tracking
        self.total_requests = 0
        self.total_successful = 0
        self.total_failed = 0
        self.average_response_time = 0.0
        self.stats_lock = Lock()
        
        # Caching (disabled for fresh data collection)
        self.enable_caching = False
        
        logger.info(f"Batch API client initialized - "
                   f"Max concurrent: {max_concurrent_requests}, "
                   f"Connection pooling: {enable_connection_pooling}, "
                   f"Adaptive rate limiting: {enable_adaptive_rate_limiting}")
    
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
    
    def _process_request_queue(self):
        """Process queued requests in thread pool"""
        # Submit queue processing to executor
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
                if request.request_type == 'search_by_apn':
                    result = self.base_client.search_by_apn(request.identifier)
                elif request.request_type == 'search_by_owner':
                    limit = request.params.get('limit', 50)
                    result = self.base_client.search_by_owner(request.identifier, limit=limit)
                elif request.request_type == 'search_by_address':
                    limit = request.params.get('limit', 50)
                    result = self.base_client.search_by_address(request.identifier, limit=limit)
                elif request.request_type == 'get_property_details':
                    result = self.base_client.get_property_details(request.identifier)
                elif request.request_type == 'get_comprehensive_property_info':
                    result = self.base_client.get_comprehensive_property_info(request.identifier)
                elif request.request_type == 'get_tax_history':
                    years = request.params.get('years', 5)
                    result = self.base_client.get_tax_history(request.identifier, years=years)
                elif request.request_type == 'bulk_property_search':
                    # Special handling for bulk search
                    apns = request.params.get('apns', [])
                    result = self.base_client.bulk_property_search(apns)
                else:
                    raise ValueError(f"Unsupported request type: {request.request_type}")
                
                # Success - record result
                request.result = result
                request.completed_at = datetime.now()
                
                if self.rate_limiter:
                    self.rate_limiter.record_success()
                
                # Update statistics
                response_time = time.time() - start_time
                with self.stats_lock:
                    self.total_requests += 1
                    self.total_successful += 1
                    total_time = self.average_response_time * (self.total_requests - 1) + response_time
                    self.average_response_time = total_time / self.total_requests
                
                logger.info(f"API request completed successfully: {request.request_id} in {response_time:.2f}s")
                break
                
            except Exception as e:
                request.retry_count = attempt
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                
                # Check if this is a rate limit error
                if "429" in str(e) or "rate limit" in str(e).lower():
                    if self.rate_limiter:
                        self.rate_limiter.record_rate_limit()
                elif self.rate_limiter:
                    self.rate_limiter.record_error()
                
                if attempt < request.max_retries:
                    logger.warning(f"API request failed, retrying: {error_msg}")
                    # Exponential backoff with jitter
                    backoff_time = (2 ** attempt) + (time.time() % 1)  # Add jitter
                    time.sleep(backoff_time)
                else:
                    request.error = error_msg
                    request.completed_at = datetime.now()
                    
                    # Update statistics
                    response_time = time.time() - start_time
                    with self.stats_lock:
                        self.total_requests += 1
                        self.total_failed += 1
                    
                    logger.error(f"API request failed after {request.max_retries + 1} attempts: {error_msg}")
        
        # Move from active to completed
        with self.requests_lock:
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
            self.completed_requests[request.request_id] = request
    
    def batch_search_by_apns(self, 
                            apns: List[str], 
                            priority: int = 5,
                            comprehensive: bool = True) -> List[str]:
        """Batch search for multiple properties by APN"""
        requests = []
        
        for apn in apns:
            if comprehensive:
                request = BatchAPIRequest(
                    request_id=f"comprehensive_{apn}_{int(time.time())}",
                    request_type='get_comprehensive_property_info',
                    identifier=apn,
                    priority=priority
                )
            else:
                request = BatchAPIRequest(
                    request_id=f"search_{apn}_{int(time.time())}",
                    request_type='search_by_apn',
                    identifier=apn,
                    priority=priority
                )
            requests.append(request)
        
        return self.submit_batch_requests(requests)
    
    def batch_search_by_owners(self, 
                              owner_names: List[str], 
                              priority: int = 5,
                              limit: int = 50) -> List[str]:
        """Batch search for properties by multiple owner names"""
        requests = []
        
        for owner_name in owner_names:
            request = BatchAPIRequest(
                request_id=f"owner_{owner_name}_{int(time.time())}",
                request_type='search_by_owner',
                identifier=owner_name,
                params={'limit': limit},
                priority=priority
            )
            requests.append(request)
        
        return self.submit_batch_requests(requests)
    
    def batch_search_by_addresses(self, 
                                 addresses: List[str], 
                                 priority: int = 5,
                                 limit: int = 50) -> List[str]:
        """Batch search for properties by multiple addresses"""
        requests = []
        
        for address in addresses:
            request = BatchAPIRequest(
                request_id=f"address_{address}_{int(time.time())}",
                request_type='search_by_address',
                identifier=address,
                params={'limit': limit},
                priority=priority
            )
            requests.append(request)
        
        return self.submit_batch_requests(requests)
    
    def batch_get_tax_history(self, 
                             apns: List[str], 
                             priority: int = 6,
                             years: int = 5) -> List[str]:
        """Batch get tax history for multiple APNs"""
        requests = []
        
        for apn in apns:
            request = BatchAPIRequest(
                request_id=f"tax_{apn}_{int(time.time())}",
                request_type='get_tax_history',
                identifier=apn,
                params={'years': years},
                priority=priority
            )
            requests.append(request)
        
        return self.submit_batch_requests(requests)
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an API request"""
        with self.requests_lock:
            # Check completed requests first
            if request_id in self.completed_requests:
                request = self.completed_requests[request_id]
                return {
                    'request_id': request_id,
                    'status': 'completed',
                    'request_type': request.request_type,
                    'identifier': request.identifier,
                    'started_at': request.started_at.isoformat() if request.started_at else None,
                    'completed_at': request.completed_at.isoformat() if request.completed_at else None,
                    'success': request.result is not None,
                    'error': request.error,
                    'retry_count': request.retry_count
                }
            
            # Check active requests
            if request_id in self.active_requests:
                request, future = self.active_requests[request_id]
                return {
                    'request_id': request_id,
                    'status': 'running',
                    'request_type': request.request_type,
                    'identifier': request.identifier,
                    'started_at': request.started_at.isoformat() if request.started_at else None,
                    'success': False,
                    'error': None
                }
            
            return None
    
    def get_request_result(self, request_id: str) -> Optional[Any]:
        """Get result from completed API request"""
        with self.requests_lock:
            if request_id in self.completed_requests:
                request = self.completed_requests[request_id]
                return request.result
            return None
    
    def wait_for_batch_completion(self, 
                                 request_ids: List[str], 
                                 timeout: float = 300.0) -> Dict[str, Any]:
        """Wait for batch of requests to complete"""
        start_time = time.time()
        results = {}
        
        while time.time() - start_time < timeout:
            all_completed = True
            
            for request_id in request_ids:
                if request_id in results:
                    continue
                
                status = self.get_request_status(request_id)
                if status and status['status'] == 'completed':
                    result = self.get_request_result(request_id)
                    results[request_id] = {
                        'status': status,
                        'result': result
                    }
                else:
                    all_completed = False
            
            if all_completed:
                break
            
            time.sleep(1.0)  # Check every second
        
        # Return results for completed requests
        completion_stats = {
            'total_requested': len(request_ids),
            'completed': len(results),
            'successful': sum(1 for r in results.values() if r['status']['success']),
            'failed': sum(1 for r in results.values() if not r['status']['success']),
            'timeout': time.time() - start_time >= timeout,
            'results': results
        }
        
        logger.info(f"Batch completion: {completion_stats['completed']}/{completion_stats['total_requested']} "
                   f"requests completed, {completion_stats['successful']} successful")
        
        return completion_stats
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get comprehensive batch API statistics"""
        with self.stats_lock:
            success_rate = (self.total_successful / max(1, self.total_requests)) * 100
        
        with self.requests_lock:
            active_count = len(self.active_requests)
            completed_count = len(self.completed_requests)
            pending_count = self.request_queue.qsize()
        
        stats = {
            'total_requests': self.total_requests,
            'total_successful': self.total_successful,
            'total_failed': self.total_failed,
            'success_rate_percent': success_rate,
            'average_response_time': self.average_response_time,
            'active_requests': active_count,
            'completed_requests': completed_count,
            'pending_requests': pending_count,
            'max_concurrent_requests': self.max_concurrent_requests
        }
        
        # Add rate limiter stats if enabled
        if self.rate_limiter:
            stats['rate_limiter'] = self.rate_limiter.get_stats()
        
        return stats
    
    def cleanup_completed_requests(self, max_age_hours: int = 6):
        """Clean up old completed requests"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        removed_count = 0
        
        with self.requests_lock:
            requests_to_remove = [
                request_id for request_id, request in self.completed_requests.items()
                if request.completed_at and request.completed_at < cutoff_time
            ]
            
            for request_id in requests_to_remove:
                del self.completed_requests[request_id]
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old API requests")
        
        return removed_count
    
    async def shutdown(self):
        """Gracefully shutdown the batch API client"""
        logger.info("Shutting down batch API client...")
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Close connection pool
        if self.connection_pool:
            await self.connection_pool.close()
        
        logger.info("Batch API client shutdown completed")


class BatchAPIWorker(QThread):
    """Qt-based worker for batch API operations"""
    
    batch_started = pyqtSignal(list)  # request_ids
    request_completed = pyqtSignal(str, dict)  # request_id, result
    request_failed = pyqtSignal(str, str)  # request_id, error
    batch_progress = pyqtSignal(int, int)  # completed, total
    batch_completed = pyqtSignal(dict)  # completion_stats
    
    def __init__(self, batch_client: BatchAPIClient):
        super().__init__()
        self.batch_client = batch_client
        self.current_request_ids = []
    
    def start_batch_search(self, 
                          identifiers: List[str],
                          search_type: str,
                          priority: int = 5,
                          params: Dict[str, Any] = None):
        """Start batch search operation"""
        self.identifiers = identifiers
        self.search_type = search_type
        self.priority = priority
        self.params = params or {}
        self.start()
    
    def run(self):
        """Execute batch API operations in background thread"""
        try:
            # Submit requests based on type
            if self.search_type == 'apn':
                comprehensive = self.params.get('comprehensive', True)
                self.current_request_ids = self.batch_client.batch_search_by_apns(
                    self.identifiers, self.priority, comprehensive
                )
            elif self.search_type == 'owner':
                limit = self.params.get('limit', 50)
                self.current_request_ids = self.batch_client.batch_search_by_owners(
                    self.identifiers, self.priority, limit
                )
            elif self.search_type == 'address':
                limit = self.params.get('limit', 50)
                self.current_request_ids = self.batch_client.batch_search_by_addresses(
                    self.identifiers, self.priority, limit
                )
            elif self.search_type == 'tax_history':
                years = self.params.get('years', 5)
                self.current_request_ids = self.batch_client.batch_get_tax_history(
                    self.identifiers, self.priority, years
                )
            else:
                self.request_failed.emit("batch", f"Unsupported search type: {self.search_type}")
                return
            
            self.batch_started.emit(self.current_request_ids)
            
            # Monitor progress
            timeout = self.params.get('timeout', 300.0)
            completion_stats = self.batch_client.wait_for_batch_completion(
                self.current_request_ids, timeout
            )
            
            # Emit individual results
            for request_id, result_data in completion_stats['results'].items():
                if result_data['status']['success']:
                    self.request_completed.emit(request_id, result_data['result'])
                else:
                    self.request_failed.emit(request_id, result_data['status'].get('error', 'Unknown error'))
            
            # Emit final statistics
            self.batch_completed.emit(completion_stats)
        
        except Exception as e:
            logger.error(f"Batch API worker error: {e}")
            self.request_failed.emit("batch", f"Worker error: {str(e)}")