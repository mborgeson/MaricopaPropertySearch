#!/usr/bin/env python
"""
Background Data Collection System
Automatically collects property data in the background without blocking the UI
"""

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from queue import Empty, PriorityQueue, Queue
from threading import Event, Lock
from typing import Any, Callable, Dict, List, Optional

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication

from improved_automatic_data_collector import ImprovedMaricopaDataCollector

# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from logging_config import get_logger
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

logger = get_logger(__name__)


class JobPriority(Enum):
    """Job priority levels"""

    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class DataCollectionJob:
    """Data collection job definition"""

    apn: str
    priority: JobPriority
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    force_fresh: bool = False

    def __lt__(self, other):
        """Enable priority queue sorting"""
        return self.priority.value < other.priority.value


class DataCollectionStats:
    """Statistics tracking for data collection"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all statistics"""
        self.jobs_submitted = 0
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.total_processing_time = 0.0
        self.avg_processing_time = 0.0

    def record_job_completion(self, processing_time: float):
        """Record successful job completion"""
        self.jobs_completed += 1
        self.total_processing_time += processing_time
        self.avg_processing_time = self.total_processing_time / max(
            1, self.jobs_completed
        )

    def record_job_failure(self):
        """Record job failure"""
        self.jobs_failed += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        total_jobs = self.jobs_completed + self.jobs_failed
        success_rate = (self.jobs_completed / max(1, total_jobs)) * 100

        return {
            "jobs_submitted": self.jobs_submitted,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "success_rate_percent": success_rate,
            "avg_processing_time": self.avg_processing_time,
            "total_processing_time": self.total_processing_time,
        }


class DataCollectionCache:
    """Simple in-memory cache for data collection results"""

    def __init__(self, ttl_hours: int = 24):
        self.cache = {}
        self.ttl_seconds = ttl_hours * 3600
        self.lock = Lock()

    def get_cached_data(self, apn: str) -> Optional[Dict]:
        """Get cached data if available and fresh"""
        with self.lock:
            if apn in self.cache:
                cached_item = self.cache[apn]
                age = time.time() - cached_item["timestamp"]

                if age < self.ttl_seconds:
                    logger.debug(f"Cache hit for APN {apn} (age: {age:.0f}s)")
                    return cached_item["data"]
                else:
                    # Expired, remove from cache
                    del self.cache[apn]
                    logger.debug(f"Cache expired for APN {apn} (age: {age:.0f}s)")

            return None

    def cache_data(self, apn: str, data: Dict):
        """Cache data for future use"""
        with self.lock:
            self.cache[apn] = {"data": data, "timestamp": time.time()}
            logger.debug(f"Cached data for APN {apn}")

    def clear_expired(self):
        """Remove expired cache entries"""
        with self.lock:
            current_time = time.time()
            expired_apns = [
                apn
                for apn, item in self.cache.items()
                if current_time - item["timestamp"] > self.ttl_seconds
            ]

            for apn in expired_apns:
                del self.cache[apn]

            if expired_apns:
                logger.info(f"Cleared {len(expired_apns)} expired cache entries")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                "total_entries": len(self.cache),
                "cache_size_mb": len(json.dumps(self.cache)) / (1024 * 1024),
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

        # FIXED: Properly initialize API client instead of None
        try:
            config_manager = EnhancedConfigManager()
            api_client = UnifiedMaricopaAPIClient(config_manager)
            self.data_collector = ImprovedMaricopaDataCollector(db_manager, api_client)
            logger.info(
                "BackgroundDataWorker: Successfully initialized with working API client"
            )
        except Exception as e:
            logger.error(f"BackgroundDataWorker: Failed to initialize API client: {e}")
            # Fallback to None but log the issue
            self.data_collector = ImprovedMaricopaDataCollector(
                db_manager, api_client=None
            )

        # Statistics and caching
        self.stats = DataCollectionStats()
        self.cache = DataCollectionCache()

        # Performance tracking
        self.jobs_completed_count = 0
        self.total_jobs_count = 0

        logger.info(
            f"Background data worker initialized with {max_concurrent_jobs} concurrent jobs"
        )

    def add_job(
        self,
        apn: str,
        priority: JobPriority = JobPriority.NORMAL,
        force_fresh: bool = False,
    ) -> bool:
        """Add a job to the queue"""
        try:
            # Check if job already exists for this APN (avoid duplicates)
            if apn in self.active_jobs:
                logger.debug(f"Job already active for APN {apn}")
                return False

            # Check cache if not forcing fresh data
            if not force_fresh:
                cached_data = self.cache.get_cached_data(apn)
                if cached_data:
                    logger.info(f"Using cached data for APN {apn}")
                    # Emit completion with cached data
                    self.job_completed.emit(apn, cached_data)
                    return True

            job = DataCollectionJob(apn=apn, priority=priority, force_fresh=force_fresh)
            self.job_queue.put(job)
            self.total_jobs_count += 1
            self.stats.jobs_submitted += 1

            logger.info(
                f"Added collection job for APN {apn} with priority {priority.name}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to add job for APN {apn}: {e}")
            return False

    def run(self):
        """Main worker thread loop"""
        logger.info("Background data worker started")
        last_maintenance = time.time()

        try:
            while not self.should_stop.is_set():
                try:
                    # Get next job with timeout
                    job = self.job_queue.get(timeout=1.0)

                    # Process job
                    self._process_job(job)

                    # Periodic maintenance
                    if time.time() - last_maintenance > 300:  # Every 5 minutes
                        self._perform_maintenance(last_maintenance)
                        last_maintenance = time.time()

                except Empty:
                    # Timeout - continue loop (allows checking should_stop)
                    continue

        except Exception as e:
            logger.error(f"Worker thread error: {e}")
        finally:
            logger.info("Background data worker stopped")
            self.executor.shutdown(wait=True)

    def _process_job(self, job: DataCollectionJob):
        """Process a single data collection job"""
        apn = job.apn

        try:
            self.active_jobs[apn] = job
            job.started_at = datetime.now()

            logger.info(f"Processing data collection job for APN {apn}")
            self.job_started.emit(apn)

            # Check if we need to collect data
            if not job.force_fresh and not self._needs_data_collection(apn):
                logger.info(f"APN {apn} has recent data, skipping collection")
                result = {
                    "apn": apn,
                    "skipped": True,
                    "reason": "Recent data available",
                }
                self._handle_job_success(job, result)
                return

            # Submit to thread pool for actual collection
            future = self.executor.submit(self._collect_data, job)
            future.add_done_callback(lambda f: self._handle_job_completion(job, f))

        except Exception as e:
            error_msg = f"Failed to process job for APN {apn}: {str(e)}"
            logger.error(error_msg)
            self._handle_job_failure(job, error_msg)

    def _collect_data(self, job: DataCollectionJob) -> Dict[str, Any]:
        """Collect data for a specific APN"""
        apn = job.apn
        start_time = time.time()

        try:
            logger.info(f"Starting data collection for APN {apn}")

            # Validate that data collector has API client
            if (
                not hasattr(self.data_collector, "api_client")
                or self.data_collector.api_client is None
            ):
                raise Exception("Data collector API client is not initialized")

            # Use the comprehensive data collection method
            result = self.data_collector.collect_data_for_apn_sync(job.apn)

            # Cache the result
            self.cache.cache_data(job.apn, result)

            processing_time = time.time() - start_time
            result["processing_time"] = processing_time

            logger.info(
                f"Data collection completed for APN {job.apn} in {processing_time:.2f}s"
            )
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Data collection failed for APN {job.apn}: {str(e)}"
            logger.error(error_msg)

            return {
                "apn": job.apn,
                "error": error_msg,
                "processing_time": processing_time,
            }

    def _handle_job_completion(self, job: DataCollectionJob, future):
        """Handle job completion in main thread"""
        try:
            result = future.result()
            job.result = result
            job.completed_at = datetime.now()

            if "error" in result:
                # Job failed
                self._handle_job_failure(job, result["error"])
            else:
                # Job succeeded
                self._handle_job_success(job, result)

        except Exception as e:
            error_msg = f"Exception in job completion handler: {str(e)}"
            logger.error(error_msg)
            self._handle_job_failure(job, error_msg)

    def _handle_job_success(self, job: DataCollectionJob, result: Dict):
        """Handle successful job completion"""
        apn = job.apn

        # Remove from active jobs
        if apn in self.active_jobs:
            del self.active_jobs[apn]

        # Update statistics
        if "processing_time" in result:
            self.stats.record_job_completion(result["processing_time"])

        self.jobs_completed_count += 1

        logger.info(f"Data collection successful for APN {apn}")
        self.job_completed.emit(apn, result)
        self._emit_progress_update()

    def _handle_job_failure(self, job: DataCollectionJob, error_msg: str):
        """Handle failed job completion"""
        apn = job.apn

        # Remove from active jobs
        if apn in self.active_jobs:
            del self.active_jobs[apn]

        # Update statistics
        self.stats.record_job_failure()

        logger.error(f"Data collection failed for APN {apn}: {error_msg}")
        self.job_failed.emit(apn, error_msg)
        self._emit_progress_update()

    def _emit_progress_update(self):
        """Emit progress update signal"""
        self.progress_updated.emit(self.jobs_completed_count, self.total_jobs_count)

    def _needs_data_collection(self, apn: str) -> bool:
        """Check if data collection is needed for this APN"""
        try:
            # Check if we have any tax records
            tax_records = self.db_manager.get_tax_history(apn)
            if not tax_records or len(tax_records) == 0:
                return True

            # Check if we have any sales records
            sales_records = self.db_manager.get_sales_history(apn)
            if not sales_records or len(sales_records) == 0:
                return True

        except Exception as e:
            logger.warning(f"Error checking data freshness for APN {apn}: {e}")
            # If we can't check, assume we need data
            return True

        # Check if we have recent tax data (current year)
        current_year = datetime.now().year
        has_current_tax = any(
            record.get("tax_year") == current_year for record in tax_records
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

            logger.info(
                f"Worker stats: {stats['jobs_completed']} completed, "
                f"{stats['jobs_failed']} failed, "
                f"{stats['success_rate_percent']:.1f}% success rate, "
                f"cache: {cache_stats['total_entries']} entries"
            )

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
            "pending_jobs": self.job_queue.qsize(),
            "active_jobs": len(self.active_jobs),
            "completed_jobs": self.jobs_completed_count,
            "total_jobs": self.total_jobs_count,
            "worker_running": self.isRunning(),
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

    def is_running(self) -> bool:
        """Check if collection is currently running"""
        return self.worker and self.worker.isRunning()

    def collect_data_for_apn(
        self,
        apn: str,
        priority: JobPriority = JobPriority.CRITICAL,
        force_fresh: bool = False,
    ) -> bool:
        """Request immediate data collection for a specific APN"""
        if not self.worker or not self.worker.isRunning():
            logger.warning("Background worker not running")
            return False

        return self.worker.add_job(apn, priority, force_fresh)

    def collect_batch_data(
        self,
        apns: List[str],
        priority: JobPriority = JobPriority.HIGH,
        force_fresh: bool = False,
    ) -> Dict[str, Any]:
        """Request batch data collection for multiple APNs with comprehensive feedback"""
        if not self.worker or not self.worker.isRunning():
            logger.warning("Background worker not running for batch collection")
            return {
                "success": False,
                "error": "Background worker not running",
                "jobs_added": 0,
                "total_requested": len(apns),
            }

        if not apns:
            return {
                "success": True,
                "jobs_added": 0,
                "total_requested": 0,
                "message": "No APNs provided",
            }

        jobs_added = 0
        failed_apns = []

        for apn in apns:
            success = self.worker.add_job(apn.strip(), priority, force_fresh)
            if success:
                jobs_added += 1
            else:
                failed_apns.append(apn.strip())

        result = {
            "success": jobs_added > 0,
            "jobs_added": jobs_added,
            "total_requested": len(apns),
            "failed_apns": failed_apns,
        }

        if failed_apns:
            result["warning"] = f"{len(failed_apns)} APNs failed to queue"

        logger.info(
            f"Batch collection: {jobs_added}/{len(apns)} jobs added successfully"
        )
        return result

    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status"""
        if not self.worker:
            return {
                "status": "stopped",
                "pending_jobs": 0,
                "active_jobs": 0,
                "completed_jobs": 0,
                "total_jobs": 0,
            }

        queue_status = self.worker.get_queue_status()
        stats = self.worker.stats.get_stats()

        return {
            "status": "running" if self.worker.isRunning() else "stopped",
            "pending_jobs": queue_status["pending_jobs"],
            "active_jobs": queue_status["active_jobs"],
            "completed_jobs": queue_status["completed_jobs"],
            "total_jobs": queue_status["total_jobs"],
            "success_rate": f"{stats['success_rate_percent']:.1f}%",
            "avg_processing_time": f"{stats['avg_processing_time']:.2f}s",
        }

    def _emit_progress_update(self):
        """Emit progress update signal"""
        status = self.get_collection_status()
        self.progress_updated.emit(status)

    def _on_progress_updated(self, completed: int, total: int):
        """Handle progress update from worker"""
        self._emit_progress_update()


# Convenience functions for standalone usage
def create_background_manager(
    db_manager, max_concurrent_jobs: int = 3
) -> BackgroundDataCollectionManager:
    """Create a background data collection manager"""
    return BackgroundDataCollectionManager(db_manager, max_concurrent_jobs)


def start_background_collection(
    db_manager, max_concurrent_jobs: int = 3
) -> BackgroundDataCollectionManager:
    """Start background collection and return the manager"""
    manager = create_background_manager(db_manager, max_concurrent_jobs)
    manager.start_collection()
    return manager
