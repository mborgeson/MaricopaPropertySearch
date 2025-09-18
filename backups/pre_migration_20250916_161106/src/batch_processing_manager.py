#!/usr/bin/env python
"""
Batch Processing Manager
Central coordinator for all batch/parallel processing operations
Integrates batch search, parallel scraping, and optimized data collection
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Callable, Union
from threading import Lock, RLock, Event
import threading
import json
import uuid

from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer

from batch_search_engine import BatchSearchEngine, SearchMode, BatchPriority
from batch_api_client import BatchAPIClient
from parallel_web_scraper import ParallelWebScraperManager, ScrapingTask, ScrapingRequest
from background_data_collector import BackgroundDataCollectionManager
from logging_config import get_logger

logger = get_logger(__name__)


class ProcessingMode(Enum):
    """Processing execution modes"""
    API_ONLY = "api_only"                    # API calls only
    SCRAPING_ONLY = "scraping_only"          # Web scraping only
    API_THEN_SCRAPING = "api_then_scraping"  # API first, scrape if needed
    PARALLEL_ALL = "parallel_all"            # Everything in parallel
    INTELLIGENT = "intelligent"              # Smart selection based on data availability


class BatchProcessingJobType(Enum):
    """Types of batch processing jobs"""
    PROPERTY_SEARCH = "property_search"
    DATA_ENHANCEMENT = "data_enhancement"
    COMPREHENSIVE_COLLECTION = "comprehensive_collection"
    TAX_DATA_COLLECTION = "tax_data_collection"
    SALES_DATA_COLLECTION = "sales_data_collection"
    BULK_VALIDATION = "bulk_validation"


@dataclass
class BatchProcessingJob:
    """Complete batch processing job specification"""
    job_id: str
    job_type: BatchProcessingJobType
    identifiers: List[str]  # APNs, addresses, owner names
    search_type: str  # 'apn', 'address', 'owner'
    processing_mode: ProcessingMode = ProcessingMode.INTELLIGENT
    priority: BatchPriority = BatchPriority.NORMAL
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Job tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    progress: float = 0.0
    
    # Results tracking
    total_items: int = 0
    completed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class BatchProcessingManager:
    """Central manager for all batch processing operations"""
    
    def __init__(self, 
                 api_client,
                 db_manager,
                 config_manager,
                 web_scraper_manager=None,
                 max_concurrent_jobs: int = 3,
                 enable_background_collection: bool = True):
        
        logger.info("Initializing Batch Processing Manager")
        
        self.api_client = api_client
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.web_scraper_manager = web_scraper_manager
        self.max_concurrent_jobs = max_concurrent_jobs
        self.enable_background_collection = enable_background_collection
        
        # Initialize component managers
        self.batch_search_engine = BatchSearchEngine(
            api_client=api_client,
            db_manager=db_manager,
            web_scraper=web_scraper_manager,
            max_concurrent_jobs=max_concurrent_jobs,
            max_concurrent_per_job=5
        )
        
        self.batch_api_client = BatchAPIClient(
            base_api_client=api_client,
            max_concurrent_requests=10,
            enable_connection_pooling=True,
            enable_adaptive_rate_limiting=True
        )
        
        if web_scraper_manager:
            self.parallel_scraper = ParallelWebScraperManager(
                config_manager=config_manager,
                max_concurrent_scrapers=4,
                enable_tax_scraping=True,
                enable_recorder_scraping=True
            )
        else:
            self.parallel_scraper = None
        
        if enable_background_collection:
            self.background_collector = BackgroundDataCollectionManager(
                db_manager=db_manager,
                max_concurrent_jobs=3
            )
        else:
            self.background_collector = None
        
        # Job management
        self.active_jobs: Dict[str, BatchProcessingJob] = {}
        self.completed_jobs: Dict[str, BatchProcessingJob] = {}
        self.jobs_lock = RLock()
        
        # Thread pool for job coordination
        self.executor = ThreadPoolExecutor(
            max_workers=max_concurrent_jobs,
            thread_name_prefix="BatchProcessing"
        )
        
        # Performance tracking
        self.total_jobs_processed = 0
        self.total_items_processed = 0
        self.total_successful_items = 0
        self.average_job_time = 0.0
        self.stats_lock = Lock()
        
        # Shutdown event
        self.shutdown_event = Event()
        
        logger.info(f"Batch processing manager initialized - "
                   f"Max concurrent jobs: {max_concurrent_jobs}, "
                   f"Background collection: {enable_background_collection}")
    
    def submit_batch_job(self, 
                        identifiers: List[str],
                        job_type: BatchProcessingJobType,
                        search_type: str,
                        processing_mode: ProcessingMode = ProcessingMode.INTELLIGENT,
                        priority: BatchPriority = BatchPriority.NORMAL,
                        parameters: Dict[str, Any] = None,
                        callback: Callable = None) -> str:
        """
        Submit a comprehensive batch processing job
        
        Args:
            identifiers: List of APNs, addresses, or owner names
            job_type: Type of processing job
            search_type: 'apn', 'address', or 'owner'
            processing_mode: How to execute the job
            priority: Job priority level
            parameters: Additional job parameters
            callback: Optional callback for progress updates
        
        Returns:
            job_id for tracking the job
        """
        job_id = str(uuid.uuid4())
        
        # Create job specification
        job = BatchProcessingJob(
            job_id=job_id,
            job_type=job_type,
            identifiers=identifiers,
            search_type=search_type,
            processing_mode=processing_mode,
            priority=priority,
            parameters=parameters or {},
            total_items=len(identifiers)
        )
        
        # Store job
        with self.jobs_lock:
            self.active_jobs[job_id] = job
        
        # Submit for execution
        future = self.executor.submit(self._execute_batch_job, job, callback)
        
        logger.info(f"Submitted batch processing job {job_id}: "
                   f"{job_type.value}, {len(identifiers)} items, "
                   f"{processing_mode.value} mode, {priority.value} priority")
        
        return job_id
    
    def _execute_batch_job(self, job: BatchProcessingJob, callback: Callable = None):
        """Execute a complete batch processing job"""
        job.started_at = datetime.now()
        job.status = "running"
        start_time = time.time()
        
        try:
            logger.info(f"Executing batch job {job.job_id}: {job.job_type.value}")
            
            # Execute based on job type
            if job.job_type == BatchProcessingJobType.PROPERTY_SEARCH:
                self._execute_property_search_job(job, callback)
            elif job.job_type == BatchProcessingJobType.DATA_ENHANCEMENT:
                self._execute_data_enhancement_job(job, callback)
            elif job.job_type == BatchProcessingJobType.COMPREHENSIVE_COLLECTION:
                self._execute_comprehensive_collection_job(job, callback)
            elif job.job_type == BatchProcessingJobType.TAX_DATA_COLLECTION:
                self._execute_tax_collection_job(job, callback)
            elif job.job_type == BatchProcessingJobType.SALES_DATA_COLLECTION:
                self._execute_sales_collection_job(job, callback)
            elif job.job_type == BatchProcessingJobType.BULK_VALIDATION:
                self._execute_bulk_validation_job(job, callback)
            else:
                raise ValueError(f"Unsupported job type: {job.job_type}")
            
            # Complete job
            job.completed_at = datetime.now()
            job.status = "completed"
            job.progress = 100.0
            
            execution_time = time.time() - start_time
            
            # Update statistics
            with self.stats_lock:
                self.total_jobs_processed += 1
                self.total_items_processed += job.total_items
                self.total_successful_items += job.successful_items
                
                total_time = self.average_job_time * (self.total_jobs_processed - 1) + execution_time
                self.average_job_time = total_time / self.total_jobs_processed
            
            logger.info(f"Batch job {job.job_id} completed in {execution_time:.2f}s - "
                       f"Success: {job.successful_items}/{job.total_items}")
            
            # Final callback
            if callback:
                try:
                    callback(job)
                except Exception as e:
                    logger.error(f"Error in job callback: {e}")
        
        except Exception as e:
            job.status = "failed"
            job.errors.append(str(e))
            logger.error(f"Batch job {job.job_id} failed: {e}")
        
        finally:
            # Move to completed jobs
            with self.jobs_lock:
                if job.job_id in self.active_jobs:
                    del self.active_jobs[job.job_id]
                self.completed_jobs[job.job_id] = job
    
    def _execute_property_search_job(self, job: BatchProcessingJob, callback: Callable = None):
        """Execute property search job"""
        logger.info(f"Executing property search for {len(job.identifiers)} items")
        
        if job.processing_mode == ProcessingMode.API_ONLY:
            # Use batch API client
            request_ids = self.batch_api_client.batch_search_by_apns(
                job.identifiers, 
                priority=job.priority.value,
                comprehensive=job.parameters.get('comprehensive', True)
            )
            
            # Wait for completion
            completion_stats = self.batch_api_client.wait_for_batch_completion(
                request_ids, 
                timeout=job.parameters.get('timeout', 300.0)
            )
            
            # Process results
            for request_id, result_data in completion_stats['results'].items():
                if result_data['status']['success']:
                    job.successful_items += 1
                    job.results[request_id] = result_data['result']
                else:
                    job.failed_items += 1
                    job.errors.append(f"API request {request_id}: {result_data['status'].get('error')}")
                
                job.completed_items += 1
                job.progress = (job.completed_items / job.total_items) * 100
                
                if callback:
                    callback(job)
        
        elif job.processing_mode in [ProcessingMode.API_THEN_SCRAPING, ProcessingMode.INTELLIGENT]:
            # Use batch search engine for smart processing
            search_mode = SearchMode.HYBRID if job.processing_mode == ProcessingMode.INTELLIGENT else SearchMode.SEQUENTIAL
            
            batch_job_id = self.batch_search_engine.submit_batch_search(
                identifiers=job.identifiers,
                search_type=job.search_type,
                mode=search_mode,
                priority=job.priority,
                callback=lambda batch_job: self._update_job_progress(job, batch_job, callback)
            )
            
            # Wait for completion
            while True:
                status = self.batch_search_engine.get_job_status(batch_job_id)
                if not status or status['status'] in ['completed', 'failed']:
                    break
                time.sleep(1.0)
            
            # Get results
            if status and status['status'] == 'completed':
                results = self.batch_search_engine.get_job_results(batch_job_id)
                if results:
                    for result in results:
                        if result['success']:
                            job.successful_items += 1
                            job.results[result['identifier']] = result['result']
                        else:
                            job.failed_items += 1
                            job.errors.append(f"Search {result['identifier']}: {result['error']}")
                        
                        job.completed_items += 1
                        job.progress = (job.completed_items / job.total_items) * 100
        
        else:
            raise ValueError(f"Unsupported processing mode for property search: {job.processing_mode}")
    
    def _execute_data_enhancement_job(self, job: BatchProcessingJob, callback: Callable = None):
        """Execute data enhancement job using background collection"""
        logger.info(f"Executing data enhancement for {len(job.identifiers)} properties")
        
        if not self.background_collector:
            raise ValueError("Background collection is disabled")
        
        # Start background collection if not already running
        if not self.background_collector.is_running():
            self.background_collector.start_collection()
        
        # Submit properties for enhancement
        enhancement_result = self.background_collector.collect_batch_data(
            job.identifiers,
            priority=job.priority
        )
        
        if not enhancement_result['success']:
            raise ValueError(f"Failed to start batch enhancement: {enhancement_result['error']}")
        
        # Monitor progress
        while True:
            status = self.background_collector.get_collection_status()
            
            # Update job progress
            if status.get('total_jobs', 0) > 0:
                job.progress = (status.get('completed_jobs', 0) / status['total_jobs']) * 100
                job.completed_items = status.get('completed_jobs', 0)
                job.successful_items = status.get('completed_jobs', 0)  # Simplified for now
            
            if callback:
                callback(job)
            
            # Check if done
            if (status.get('pending_jobs', 1) == 0 and 
                status.get('active_jobs', 1) == 0):
                break
            
            time.sleep(2.0)
    
    def _execute_comprehensive_collection_job(self, job: BatchProcessingJob, callback: Callable = None):
        """Execute comprehensive data collection using all available methods"""
        logger.info(f"Executing comprehensive collection for {len(job.identifiers)} properties")
        
        # Phase 1: API Collection
        logger.info("Phase 1: API data collection")
        api_request_ids = self.batch_api_client.batch_search_by_apns(
            job.identifiers,
            priority=job.priority.value,
            comprehensive=True
        )
        
        api_stats = self.batch_api_client.wait_for_batch_completion(
            api_request_ids,
            timeout=job.parameters.get('api_timeout', 180.0)
        )
        
        # Phase 2: Parallel Scraping (if enabled)
        if self.parallel_scraper and job.parameters.get('enable_scraping', True):
            logger.info("Phase 2: Parallel web scraping")
            
            scraping_requests = []
            
            # Tax data scraping
            if job.parameters.get('collect_tax_data', True):
                tax_requests = [
                    ScrapingRequest(
                        task_type=ScrapingTask.TAX_INFORMATION,
                        identifier=apn,
                        priority=job.priority.value
                    )
                    for apn in job.identifiers
                ]
                scraping_requests.extend(tax_requests)
            
            # Sales data scraping
            if job.parameters.get('collect_sales_data', True):
                sales_requests = [
                    ScrapingRequest(
                        task_type=ScrapingTask.SALES_HISTORY,
                        identifier=apn,
                        priority=job.priority.value
                    )
                    for apn in job.identifiers
                ]
                scraping_requests.extend(sales_requests)
            
            if scraping_requests:
                scraping_request_ids = self.parallel_scraper.submit_scraping_requests(scraping_requests)
                
                # Monitor scraping progress
                completed_scraping = set()
                while len(completed_scraping) < len(scraping_request_ids):
                    for request_id in scraping_request_ids:
                        if request_id in completed_scraping:
                            continue
                        
                        status = self.parallel_scraper.get_request_status(request_id)
                        if status and status['status'] == 'completed':
                            completed_scraping.add(request_id)
                            
                            if status['success']:
                                result = self.parallel_scraper.get_request_result(request_id)
                                job.results[request_id] = result
                            else:
                                job.errors.append(f"Scraping {request_id}: {status['error']}")
                    
                    # Update progress
                    total_operations = len(api_request_ids) + len(scraping_request_ids)
                    completed_operations = len(api_stats['results']) + len(completed_scraping)
                    job.progress = (completed_operations / total_operations) * 100
                    
                    if callback:
                        callback(job)
                    
                    time.sleep(2.0)
        
        # Combine results
        job.successful_items = api_stats['successful'] + len([
            r for r in job.results.values() if r is not None
        ])
        job.failed_items = api_stats['failed']
        job.completed_items = job.total_items
        
        # Store API results
        for request_id, result_data in api_stats['results'].items():
            if result_data['status']['success']:
                job.results[f"api_{request_id}"] = result_data['result']
    
    def _execute_tax_collection_job(self, job: BatchProcessingJob, callback: Callable = None):
        """Execute tax data collection job"""
        logger.info(f"Executing tax data collection for {len(job.identifiers)} properties")
        
        if not self.parallel_scraper:
            raise ValueError("Web scraping is disabled")
        
        # Submit tax scraping requests
        request_ids = self.parallel_scraper.batch_scrape_tax_data(
            job.identifiers,
            priority=job.priority.value
        )
        
        # Monitor progress
        completed_requests = set()
        while len(completed_requests) < len(request_ids):
            for request_id in request_ids:
                if request_id in completed_requests:
                    continue
                
                status = self.parallel_scraper.get_request_status(request_id)
                if status and status['status'] == 'completed':
                    completed_requests.add(request_id)
                    
                    if status['success']:
                        result = self.parallel_scraper.get_request_result(request_id)
                        job.results[request_id] = result
                        job.successful_items += 1
                    else:
                        job.errors.append(f"Tax scraping {request_id}: {status['error']}")
                        job.failed_items += 1
                    
                    job.completed_items += 1
                    job.progress = (job.completed_items / job.total_items) * 100
                    
                    if callback:
                        callback(job)
            
            time.sleep(2.0)
    
    def _execute_sales_collection_job(self, job: BatchProcessingJob, callback: Callable = None):
        """Execute sales data collection job"""
        logger.info(f"Executing sales data collection for {len(job.identifiers)} properties")
        
        if not self.parallel_scraper:
            raise ValueError("Web scraping is disabled")
        
        # Submit sales scraping requests
        request_ids = self.parallel_scraper.batch_scrape_sales_data(
            job.identifiers,
            priority=job.priority.value
        )
        
        # Monitor progress (similar to tax collection)
        completed_requests = set()
        while len(completed_requests) < len(request_ids):
            for request_id in request_ids:
                if request_id in completed_requests:
                    continue
                
                status = self.parallel_scraper.get_request_status(request_id)
                if status and status['status'] == 'completed':
                    completed_requests.add(request_id)
                    
                    if status['success']:
                        result = self.parallel_scraper.get_request_result(request_id)
                        job.results[request_id] = result
                        job.successful_items += 1
                    else:
                        job.errors.append(f"Sales scraping {request_id}: {status['error']}")
                        job.failed_items += 1
                    
                    job.completed_items += 1
                    job.progress = (job.completed_items / job.total_items) * 100
                    
                    if callback:
                        callback(job)
            
            time.sleep(2.0)
    
    def _execute_bulk_validation_job(self, job: BatchProcessingJob, callback: Callable = None):
        """Execute bulk validation job"""
        logger.info(f"Executing bulk validation for {len(job.identifiers)} items")
        
        # Use API client to validate all identifiers
        validation_requests = []
        
        for identifier in job.identifiers:
            if job.search_type == 'apn':
                # For APNs, use search_by_apn to validate
                from batch_api_client import BatchAPIRequest
                request = BatchAPIRequest(
                    request_id=f"validate_{identifier}",
                    request_type='search_by_apn',
                    identifier=identifier,
                    priority=job.priority.value
                )
                validation_requests.append(request)
        
        if validation_requests:
            request_ids = self.batch_api_client.submit_batch_requests(validation_requests)
            
            completion_stats = self.batch_api_client.wait_for_batch_completion(
                request_ids,
                timeout=job.parameters.get('timeout', 120.0)
            )
            
            # Process validation results
            for request_id, result_data in completion_stats['results'].items():
                if result_data['status']['success'] and result_data['result']:
                    job.successful_items += 1
                    job.results[request_id] = {'valid': True, 'data': result_data['result']}
                else:
                    job.failed_items += 1
                    job.results[request_id] = {'valid': False, 'error': result_data['status'].get('error')}
                
                job.completed_items += 1
                job.progress = (job.completed_items / job.total_items) * 100
                
                if callback:
                    callback(job)
    
    def _update_job_progress(self, job: BatchProcessingJob, batch_job, callback: Callable = None):
        """Update job progress from batch search engine"""
        job.progress = batch_job.progress
        
        if callback:
            callback(job)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch processing job"""
        with self.jobs_lock:
            # Check active jobs first
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
            elif job_id in self.completed_jobs:
                job = self.completed_jobs[job_id]
            else:
                return None
            
            return {
                'job_id': job.job_id,
                'job_type': job.job_type.value,
                'status': job.status,
                'progress': job.progress,
                'total_items': job.total_items,
                'completed_items': job.completed_items,
                'successful_items': job.successful_items,
                'failed_items': job.failed_items,
                'search_type': job.search_type,
                'processing_mode': job.processing_mode.value,
                'priority': job.priority.value,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_count': len(job.errors)
            }
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get results from a completed job"""
        with self.jobs_lock:
            if job_id in self.completed_jobs:
                job = self.completed_jobs[job_id]
                return {
                    'job_id': job.job_id,
                    'status': job.status,
                    'results': job.results,
                    'errors': job.errors,
                    'statistics': {
                        'total_items': job.total_items,
                        'successful_items': job.successful_items,
                        'failed_items': job.failed_items,
                        'success_rate': (job.successful_items / max(1, job.total_items)) * 100
                    }
                }
            elif job_id in self.active_jobs:
                return {'status': 'Job still running', 'partial_results': self.active_jobs[job_id].results}
            else:
                return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running batch processing job"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = "cancelled"
                
                # Attempt to cancel underlying operations
                # This would require additional implementation in component managers
                
                logger.info(f"Cancelled batch processing job {job_id}")
                return True
            return False
    
    def get_manager_statistics(self) -> Dict[str, Any]:
        """Get comprehensive manager statistics"""
        with self.stats_lock:
            success_rate = (self.total_successful_items / max(1, self.total_items_processed)) * 100
        
        with self.jobs_lock:
            active_jobs_count = len(self.active_jobs)
            completed_jobs_count = len(self.completed_jobs)
        
        stats = {
            'total_jobs_processed': self.total_jobs_processed,
            'total_items_processed': self.total_items_processed,
            'total_successful_items': self.total_successful_items,
            'success_rate_percent': success_rate,
            'average_job_time': self.average_job_time,
            'active_jobs': active_jobs_count,
            'completed_jobs': completed_jobs_count,
            'max_concurrent_jobs': self.max_concurrent_jobs,
            'components': {
                'batch_search_engine': self.batch_search_engine.get_engine_statistics(),
                'batch_api_client': self.batch_api_client.get_batch_statistics(),
                'parallel_scraper': self.parallel_scraper.get_scraper_statistics() if self.parallel_scraper else None,
                'background_collector': self.background_collector.get_collection_status() if self.background_collector else None
            }
        }
        
        return stats
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        removed_count = 0
        
        with self.jobs_lock:
            jobs_to_remove = [
                job_id for job_id, job in self.completed_jobs.items()
                if job.completed_at and job.completed_at < cutoff_time
            ]
            
            for job_id in jobs_to_remove:
                del self.completed_jobs[job_id]
                removed_count += 1
        
        # Also cleanup component managers
        self.batch_search_engine.cleanup_completed_jobs(max_age_hours)
        self.batch_api_client.cleanup_completed_requests(max_age_hours // 4)  # More frequent for API requests
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old batch processing jobs")
        
        return removed_count
    
    def shutdown(self):
        """Gracefully shutdown the batch processing manager"""
        logger.info("Shutting down batch processing manager...")
        
        self.shutdown_event.set()
        
        # Shutdown component managers
        self.batch_search_engine.shutdown()
        # Note: batch_api_client.shutdown() is async, would need proper handling
        
        if self.parallel_scraper:
            self.parallel_scraper.shutdown()
        
        if self.background_collector:
            self.background_collector.stop_collection()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Batch processing manager shutdown completed")


class BatchProcessingWorker(QThread):
    """Qt-based worker for batch processing operations"""
    
    job_started = pyqtSignal(str)  # job_id
    job_progress = pyqtSignal(str, float)  # job_id, progress
    job_completed = pyqtSignal(str, dict)  # job_id, results
    job_failed = pyqtSignal(str, str)  # job_id, error
    
    def __init__(self, processing_manager: BatchProcessingManager):
        super().__init__()
        self.processing_manager = processing_manager
        self.current_job_id = None
    
    def start_batch_processing(self,
                              identifiers: List[str],
                              job_type: BatchProcessingJobType,
                              search_type: str,
                              processing_mode: ProcessingMode = ProcessingMode.INTELLIGENT,
                              priority: BatchPriority = BatchPriority.NORMAL,
                              parameters: Dict[str, Any] = None):
        """Start batch processing job"""
        self.identifiers = identifiers
        self.job_type = job_type
        self.search_type = search_type
        self.processing_mode = processing_mode
        self.priority = priority
        self.parameters = parameters or {}
        self.start()
    
    def run(self):
        """Execute batch processing in background thread"""
        try:
            # Submit job
            self.current_job_id = self.processing_manager.submit_batch_job(
                identifiers=self.identifiers,
                job_type=self.job_type,
                search_type=self.search_type,
                processing_mode=self.processing_mode,
                priority=self.priority,
                parameters=self.parameters,
                callback=self._progress_callback
            )
            
            self.job_started.emit(self.current_job_id)
            
            # Monitor job progress
            while True:
                status = self.processing_manager.get_job_status(self.current_job_id)
                if not status:
                    break
                
                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break
                
                self.msleep(2000)  # Check every 2 seconds
            
            # Get final results
            if status:
                if status['status'] == 'completed':
                    results = self.processing_manager.get_job_results(self.current_job_id)
                    self.job_completed.emit(self.current_job_id, results or {})
                else:
                    error_msg = f"Job {status['status']}"
                    if status.get('error_count', 0) > 0:
                        error_msg += f" with {status['error_count']} errors"
                    self.job_failed.emit(self.current_job_id, error_msg)
            else:
                self.job_failed.emit(self.current_job_id, "Job status not found")
        
        except Exception as e:
            logger.error(f"Batch processing worker error: {e}")
            self.job_failed.emit(self.current_job_id or "unknown", f"Worker error: {str(e)}")
    
    def _progress_callback(self, job: BatchProcessingJob):
        """Handle progress updates"""
        if self.current_job_id:
            self.job_progress.emit(self.current_job_id, job.progress)