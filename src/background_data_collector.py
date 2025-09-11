#!/usr/bin/env python
"""
Background Data Collection System
Automatically collects property data in the background without blocking the UI
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from queue import Queue, Empty, PriorityQueue
from threading import Lock, Event
from typing import Dict, List, Optional, Any, Callable
import json

from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtWidgets import QApplication

from automatic_data_collector import MaricopaDataCollector
from logging_config import get_logger

logger = get_logger(__name__)


class JobPriority(Enum):
    """Job priority levels"""
    CRITICAL = 1    # User-initiated immediate requests
    HIGH = 2        # Top search results
    NORMAL = 3      # Background enhancement
    LOW = 4         # Bulk operations


class JobStatus(Enum):
    """Job status tracking"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"  
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class DataCollectionJob:
    """Individual data collection job"""
    apn: str
    priority: JobPriority
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Dict] = None
    
    def __lt__(self, other):
        """Enable priority queue sorting"""
        return self.priority.value < other.priority.value


class DataCollectionStats:
    """Statistics tracking for data collection"""
    
    def __init__(self):
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.total_processing_time = 0.0
        self.average_processing_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.start_time = datetime.now()
        self._lock = Lock()
    
    def record_job_completion(self, processing_time: float, success: bool):
        """Record job completion statistics"""
        with self._lock:
            if success:
                self.jobs_completed += 1
            else:
                self.jobs_failed += 1
                
            self.total_processing_time += processing_time
            total_jobs = self.jobs_completed + self.jobs_failed
            if total_jobs > 0:
                self.average_processing_time = self.total_processing_time / total_jobs
    
    def record_cache_hit(self):
        """Record cache hit"""
        with self._lock:
            self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        with self._lock:
            self.cache_misses += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        with self._lock:
            uptime = datetime.now() - self.start_time
            total_jobs = self.jobs_completed + self.jobs_failed
            success_rate = (self.jobs_completed / total_jobs * 100) if total_jobs > 0 else 0
            cache_total = self.cache_hits + self.cache_misses
            cache_hit_rate = (self.cache_hits / cache_total * 100) if cache_total > 0 else 0
            
            return {
                'uptime_seconds': uptime.total_seconds(),
                'jobs_completed': self.jobs_completed,
                'jobs_failed': self.jobs_failed,
                'total_jobs': total_jobs,
                'success_rate_percent': success_rate,
                'average_processing_time': self.average_processing_time,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate_percent': cache_hit_rate
            }


class DataCollectionCache:
    """Smart caching system to avoid duplicate collection"""
    
    def __init__(self, max_age_hours: int = 24):
        self.max_age_hours = max_age_hours
        self.cache = {}  # apn -> {'timestamp': datetime, 'data': dict}
        self._lock = Lock()
    
    def is_cached(self, apn: str) -> bool:
        """Check if APN data is cached and still valid"""
        with self._lock:
            if apn not in self.cache:
                return False
                
            entry = self.cache[apn]
            age = datetime.now() - entry['timestamp']
            return age.total_seconds() < (self.max_age_hours * 3600)
    
    def get_cached(self, apn: str) -> Optional[Dict]:
        """Get cached data for APN"""
        with self._lock:
            if self.is_cached(apn):
                return self.cache[apn]['data']
            return None
    
    def cache_data(self, apn: str, data: Dict):
        """Cache data for APN"""
        with self._lock:
            self.cache[apn] = {
                'timestamp': datetime.now(),
                'data': data
            }
    
    def clear_expired(self):
        """Clear expired cache entries"""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                apn for apn, entry in self.cache.items()
                if (now - entry['timestamp']).total_seconds() >= (self.max_age_hours * 3600)
            ]
            for apn in expired_keys:
                del self.cache[apn]
                
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._lock:
            return {
                'total_entries': len(self.cache),
                'max_age_hours': self.max_age_hours
            }


class BackgroundDataWorker(QThread):
    """Background worker thread for data collection"""
    
    # Signals for progress reporting
    job_started = pyqtSignal(str)  # APN
    job_completed = pyqtSignal(str, dict)  # APN, result
    job_failed = pyqtSignal(str, str)  # APN, error
    progress_updated = pyqtSignal(int, int)  # completed, total
    status_updated = pyqtSignal(str)  # status message
    
    def __init__(self, db_manager, max_concurrent_jobs: int = 3):
        super().__init__()
        self.db_manager = db_manager
        self.max_concurrent_jobs = max_concurrent_jobs
        self.job_queue = PriorityQueue()
        self.active_jobs = {}  # apn -> job
        self.should_stop = Event()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)
        self.data_collector = MaricopaDataCollector(db_manager)
        
        # Statistics and caching
        self.stats = DataCollectionStats()
        self.cache = DataCollectionCache()
        
        # Performance tracking
        self.jobs_completed_count = 0
        self.total_jobs_count = 0
        
        logger.info(f"Background data worker initialized with {max_concurrent_jobs} concurrent jobs")
    
    def add_job(self, apn: str, priority: JobPriority = JobPriority.NORMAL) -> bool:
        """Add a data collection job to the queue"""
        # Check if already in queue or actively being processed
        if apn in self.active_jobs:
            logger.debug(f"Job for APN {apn} already active, skipping")
            return False
        
        # Check if recently cached
        if self.cache.is_cached(apn):
            logger.debug(f"Data for APN {apn} is cached, skipping")
            self.stats.record_cache_hit()
            return False
            
        job = DataCollectionJob(apn=apn, priority=priority)
        self.job_queue.put(job)
        self.total_jobs_count += 1
        
        logger.info(f"Added data collection job for APN {apn} with priority {priority.name}")
        return True
    
    def add_bulk_jobs(self, apns: List[str], priority: JobPriority = JobPriority.NORMAL) -> int:
        """Add multiple jobs efficiently"""
        added_count = 0
        for apn in apns:
            if self.add_job(apn, priority):
                added_count += 1
        
        logger.info(f"Added {added_count} bulk jobs out of {len(apns)} APNs")
        return added_count
    
    def run(self):
        """Main worker thread loop"""
        logger.info("Background data worker started")
        
        # Set up periodic cache cleanup
        cache_cleanup_timer = time.time()
        
        while not self.should_stop.is_set():
            try:
                # Get next job with timeout
                try:
                    job = self.job_queue.get(timeout=1.0)
                except Empty:
                    # No jobs available, do maintenance
                    self._perform_maintenance(cache_cleanup_timer)
                    continue
                
                # Process job if we have capacity
                if len(self.active_jobs) < self.max_concurrent_jobs:
                    self._process_job(job)
                else:
                    # Re-queue job if at capacity
                    self.job_queue.put(job)
                    time.sleep(0.1)  # Brief pause when at capacity
                
            except Exception as e:
                logger.error(f"Error in worker thread main loop: {e}")
                time.sleep(1.0)  # Prevent tight error loop
        
        # Cleanup when stopping
        logger.info("Background data worker stopping...")
        self.executor.shutdown(wait=True)
        logger.info("Background data worker stopped")
    
    def _process_job(self, job: DataCollectionJob):
        """Process a single job"""
        self.active_jobs[job.apn] = job
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.now()
        
        self.job_started.emit(job.apn)
        self.status_updated.emit(f"Collecting data for APN {job.apn}...")
        
        logger.info(f"Processing data collection job for APN {job.apn} (priority: {job.priority.name})")
        
        # Submit job to thread pool
        future = self.executor.submit(self._collect_data_for_job, job)
        
        # Use a callback to handle completion
        future.add_done_callback(lambda f: self._handle_job_completion(job, f))
    
    def _collect_data_for_job(self, job: DataCollectionJob) -> Dict[str, Any]:
        """Collect data for a specific job"""
        start_time = time.time()
        
        try:
            # Check database first for existing data
            existing_tax = self.db_manager.get_tax_history(job.apn)
            existing_sales = self.db_manager.get_sales_history(job.apn)
            
            # Determine if we need to collect data
            needs_collection = (
                len(existing_tax) == 0 or 
                len(existing_sales) == 0 or
                self._is_data_stale(existing_tax, existing_sales)
            )
            
            if not needs_collection:
                logger.info(f"APN {job.apn} has current data, skipping collection")
                return {
                    'apn': job.apn,
                    'skipped': True,
                    'reason': 'Data already current',
                    'tax_records_count': len(existing_tax),
                    'sales_records_count': len(existing_sales)
                }
            
            # Perform actual data collection
            self.stats.record_cache_miss()
            result = self.data_collector.collect_data_for_apn_sync(job.apn)
            
            # Cache the result
            self.cache.cache_data(job.apn, result)
            
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            logger.info(f"Data collection completed for APN {job.apn} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Data collection failed for APN {job.apn}: {str(e)}"
            logger.error(error_msg)
            
            return {
                'apn': job.apn,
                'error': error_msg,
                'processing_time': processing_time
            }
    
    def _handle_job_completion(self, job: DataCollectionJob, future):
        """Handle job completion in main thread"""
        try:
            result = future.result()
            job.result = result
            job.completed_at = datetime.now()
            
            if 'error' in result:
                # Job failed
                job.status = JobStatus.FAILED
                job.error_message = result['error']
                
                # Retry logic
                if job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = JobStatus.RETRYING
                    job.started_at = None
                    
                    # Re-queue with exponential backoff
                    retry_delay = 2 ** job.retry_count  # 2, 4, 8 seconds
                    QTimer.singleShot(retry_delay * 1000, lambda: self.job_queue.put(job))
                    
                    logger.warning(f"Retrying job for APN {job.apn} (attempt {job.retry_count}/{job.max_retries})")
                else:
                    logger.error(f"Job for APN {job.apn} failed after {job.max_retries} retries")
                    self.job_failed.emit(job.apn, job.error_message)
                    self.stats.record_job_completion(result.get('processing_time', 0), False)
            else:
                # Job succeeded
                job.status = JobStatus.COMPLETED
                self.job_completed.emit(job.apn, result)
                self.stats.record_job_completion(result.get('processing_time', 0), True)
                logger.info(f"Job completed successfully for APN {job.apn}")
            
            # Update progress
            self.jobs_completed_count += 1
            self.progress_updated.emit(self.jobs_completed_count, self.total_jobs_count)
            
        except Exception as e:
            logger.error(f"Error handling job completion for APN {job.apn}: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self.job_failed.emit(job.apn, str(e))
        
        finally:
            # Remove from active jobs
            self.active_jobs.pop(job.apn, None)
    
    def _is_data_stale(self, tax_records: List, sales_records: List, max_age_days: int = 7) -> bool:
        """Check if existing data is stale and needs refresh"""
        if not tax_records and not sales_records:
            return True
            
        # Check if we have recent tax data (current year)
        current_year = datetime.now().year
        has_current_tax = any(
            record.get('tax_year') == current_year 
            for record in tax_records
        )
        
        if not has_current_tax:
            return True
            
        # For now, consider data current if we have this year's tax data
        return False
    
    def _perform_maintenance(self, last_cleanup_time: float):
        """Perform periodic maintenance tasks"""
        current_time = time.time()
        
        # Clean up cache every hour
        if current_time - last_cleanup_time > 3600:  # 1 hour
            self.cache.clear_expired()
            last_cleanup_time = current_time
            
            # Log statistics
            stats = self.stats.get_stats()
            cache_stats = self.cache.get_cache_stats()
            
            logger.info(f"Worker stats: {stats['jobs_completed']} completed, "
                       f"{stats['jobs_failed']} failed, "
                       f"{stats['success_rate_percent']:.1f}% success rate, "
                       f"cache: {cache_stats['total_entries']} entries")
    
    def stop_worker(self):
        """Stop the worker thread gracefully"""
        logger.info("Stopping background data worker...")
        self.should_stop.set()
        self.wait(5000)  # Wait up to 5 seconds
        
        if self.isRunning():
            logger.warning("Worker thread did not stop gracefully, terminating...")
            self.terminate()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'pending_jobs': self.job_queue.qsize(),
            'active_jobs': len(self.active_jobs),
            'completed_jobs': self.jobs_completed_count,
            'total_jobs': self.total_jobs_count,
            'worker_running': self.isRunning(),
            'statistics': self.stats.get_stats(),
            'cache_stats': self.cache.get_cache_stats()
        }


class BackgroundDataCollectionManager(QObject):
    """Main manager for background data collection system"""
    
    # Signals for UI updates
    collection_started = pyqtSignal()
    collection_stopped = pyqtSignal() 
    progress_updated = pyqtSignal(dict)  # status dict
    job_completed = pyqtSignal(str, dict)  # APN, result
    
    def __init__(self, db_manager, max_concurrent_jobs: int = 3):
        super().__init__()
        self.db_manager = db_manager
        self.worker = None
        self.max_concurrent_jobs = max_concurrent_jobs
        
        # Progress tracking
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._emit_progress_update)
        self.status_timer.setInterval(5000)  # Update every 5 seconds
        
        logger.info("Background data collection manager initialized")
    
    def start_collection(self):
        """Start background data collection"""
        if self.worker and self.worker.isRunning():
            logger.warning("Data collection already running")
            return
        
        logger.info("Starting background data collection")
        
        self.worker = BackgroundDataWorker(self.db_manager, self.max_concurrent_jobs)
        
        # Connect signals
        self.worker.job_completed.connect(self.job_completed.emit)
        self.worker.progress_updated.connect(self._on_progress_updated)
        
        self.worker.start()
        self.status_timer.start()
        self.collection_started.emit()
    
    def stop_collection(self):
        """Stop background data collection"""
        if not self.worker or not self.worker.isRunning():
            logger.warning("Data collection not running")
            return
        
        logger.info("Stopping background data collection")
        
        self.status_timer.stop()
        self.worker.stop_worker()
        self.worker = None
        self.collection_stopped.emit()
    
    def enhance_search_results(self, search_results: List[Dict], max_properties: int = 20):
        """Automatically enhance search results with smart prioritized background data collection"""
        if not self.worker or not self.worker.isRunning():
            logger.warning("Background worker not running, cannot enhance results")
            return 0
        
        # Smart prioritization based on data completeness
        apns_to_enhance = []
        for i, result in enumerate(search_results[:max_properties]):
            apn = result.get('apn')
            if not apn:
                continue
                
            # Check existing data to determine priority
            try:
                existing_tax = self.db_manager.get_tax_history(apn)
                existing_sales = self.db_manager.get_sales_history(apn)
                
                # Determine priority based on data completeness and position
                if len(existing_tax) == 0 and len(existing_sales) == 0:
                    # No data at all - high priority
                    priority = JobPriority.HIGH if i < 3 else JobPriority.NORMAL
                elif len(existing_tax) == 0 or len(existing_sales) == 0:
                    # Partial data - medium priority
                    priority = JobPriority.NORMAL
                else:
                    # Has data but might be stale - low priority for top results only
                    priority = JobPriority.LOW if i < 10 else None
                
                if priority and self.worker.add_job(apn, priority):
                    apns_to_enhance.append(apn)
                    logger.debug(f"Queued APN {apn} with priority {priority.name} (position {i})")
                    
            except Exception as e:
                logger.warning(f"Error checking data for APN {apn}: {e}")
                # Default to normal priority if we can't check
                priority = JobPriority.NORMAL if i < 10 else JobPriority.LOW
                if self.worker.add_job(apn, priority):
                    apns_to_enhance.append(apn)
        
        logger.info(f"Smart enhancement: queued {len(apns_to_enhance)} of {len(search_results)} properties")
        return len(apns_to_enhance)
    
    def collect_data_for_apn(self, apn: str, priority: JobPriority = JobPriority.CRITICAL) -> bool:
        """Request immediate data collection for a specific APN"""
        if not self.worker or not self.worker.isRunning():
            logger.warning("Background worker not running")
            return False
        
        return self.worker.add_job(apn, priority)
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status"""
        if not self.worker:
            return {
                'status': 'stopped',
                'pending_jobs': 0,
                'active_jobs': 0,
                'completed_jobs': 0
            }
        
        status = self.worker.get_queue_status()
        status['status'] = 'running' if self.worker.isRunning() else 'stopped'
        return status
    
    def _on_progress_updated(self, completed: int, total: int):
        """Handle progress updates from worker"""
        # Could add specific progress logic here if needed
        pass
    
    def _emit_progress_update(self):
        """Emit periodic progress updates"""
        status = self.get_collection_status()
        self.progress_updated.emit(status)
    
    def is_running(self) -> bool:
        """Check if background collection is running"""
        return self.worker is not None and self.worker.isRunning()