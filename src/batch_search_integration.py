#!/usr/bin/env python
"""
Batch Search Integration
Connects the BatchSearchDialog GUI with the parallel batch processing backend
Implements complete batch/parallel search processing system
"""

import asyncio
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set, Union
from threading import Lock, RLock, Event, Thread
import queue
import json
import uuid
import csv
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtWidgets import QMessageBox, QFileDialog

from src.batch_search_engine import BatchSearchEngine, SearchMode, BatchPriority
from src.batch_processing_manager import BatchProcessingManager, ProcessingMode, BatchProcessingJobType
from src.logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


class BatchSearchJobType(Enum):
    """Enhanced batch search job types"""
    BASIC_SEARCH = "basic_search"              # Simple property search
    COMPREHENSIVE_SEARCH = "comprehensive_search"  # Search + data collection
    VALIDATION_SEARCH = "validation_search"    # Validate property data exists
    BULK_ENHANCEMENT = "bulk_enhancement"      # Enhance existing properties
    

@dataclass
class BatchSearchResult:
    """Individual search result within a batch"""
    identifier: str
    search_type: str
    success: bool = False
    result_data: Optional[Dict] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    api_calls_used: int = 0
    data_sources_used: List[str] = field(default_factory=list)
    

@dataclass 
class BatchSearchSummary:
    """Summary of complete batch search operation"""
    job_id: str
    job_type: BatchSearchJobType
    total_items: int
    successful_items: int
    failed_items: int
    total_processing_time: float
    average_time_per_item: float
    api_calls_total: int
    results: List[BatchSearchResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class BatchSearchIntegrationManager:
    """Central integration manager for batch search operations"""
    
    def __init__(self, 
                 api_client,
                 db_manager,
                 config_manager,
                 web_scraper_manager=None,
                 background_manager=None):
        
        logger.info("Initializing Batch Search Integration Manager")
        
        self.api_client = api_client
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.web_scraper_manager = web_scraper_manager
        self.background_manager = background_manager
        
        # Initialize batch processing components
        self.batch_search_engine = BatchSearchEngine(
            api_client=api_client,
            db_manager=db_manager,
            web_scraper=web_scraper_manager,
            max_concurrent_jobs=3,
            max_concurrent_per_job=5
        )
        
        self.batch_processing_manager = BatchProcessingManager(
            api_client=api_client,
            db_manager=db_manager,
            config_manager=config_manager,
            web_scraper_manager=web_scraper_manager,
            max_concurrent_jobs=3,
            enable_background_collection=True
        )
        
        # Job tracking
        self.active_jobs: Dict[str, Any] = {}
        self.completed_jobs: Dict[str, BatchSearchSummary] = {}
        self.jobs_lock = RLock()
        
        # Performance metrics
        self.total_jobs_processed = 0
        self.total_items_processed = 0
        self.average_throughput = 0.0  # items per second
        self.stats_lock = Lock()
        
        logger.info("Batch Search Integration Manager initialized")
    
    def execute_batch_search(self,
                           identifiers: List[str],
                           search_type: str,
                           job_type: BatchSearchJobType = BatchSearchJobType.BASIC_SEARCH,
                           max_concurrent: int = 3,
                           enable_background_collection: bool = True,
                           progress_callback: Callable = None) -> str:
        """
        Execute comprehensive batch search operation
        
        Args:
            identifiers: List of APNs, addresses, or owner names
            search_type: 'apn', 'address', or 'owner'  
            job_type: Type of batch search operation
            max_concurrent: Max parallel searches (1-10)
            enable_background_collection: Enable data collection after search
            progress_callback: Function to call for progress updates
            
        Returns:
            job_id for tracking the operation
        """
        job_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting batch search job {job_id}: "
                   f"{len(identifiers)} {search_type} items, "
                   f"job type: {job_type.value}, "
                   f"max concurrent: {max_concurrent}")
        
        # Create job tracking
        job_info = {
            'job_id': job_id,
            'job_type': job_type,
            'identifiers': identifiers,
            'search_type': search_type,
            'max_concurrent': max_concurrent,
            'enable_background_collection': enable_background_collection,
            'start_time': start_time,
            'status': 'running',
            'progress': 0.0,
            'results': []
        }
        
        with self.jobs_lock:
            self.active_jobs[job_id] = job_info
        
        # Execute based on job type
        if job_type == BatchSearchJobType.BASIC_SEARCH:
            self._execute_basic_search(job_id, job_info, progress_callback)
        elif job_type == BatchSearchJobType.COMPREHENSIVE_SEARCH:
            self._execute_comprehensive_search(job_id, job_info, progress_callback)
        elif job_type == BatchSearchJobType.VALIDATION_SEARCH:
            self._execute_validation_search(job_id, job_info, progress_callback)
        elif job_type == BatchSearchJobType.BULK_ENHANCEMENT:
            self._execute_bulk_enhancement(job_id, job_info, progress_callback)
        else:
            raise ValueError(f"Unsupported job type: {job_type}")
            
        return job_id
    
    def _execute_basic_search(self, job_id: str, job_info: Dict, progress_callback: Callable = None):
        """Execute basic batch search using batch search engine"""
        
        # Configure search mode based on concurrency
        if job_info['max_concurrent'] <= 1:
            search_mode = SearchMode.SEQUENTIAL
        elif job_info['max_concurrent'] >= 5:
            search_mode = SearchMode.PARALLEL
        else:
            search_mode = SearchMode.HYBRID
        
        # Submit to batch search engine
        engine_job_id = self.batch_search_engine.submit_batch_search(
            identifiers=job_info['identifiers'],
            search_type=job_info['search_type'],
            mode=search_mode,
            priority=BatchPriority.NORMAL,
            max_concurrent=job_info['max_concurrent'],
            timeout_per_request=30.0,
            callback=lambda batch_job: self._update_job_progress(job_id, batch_job, progress_callback)
        )
        
        job_info['engine_job_id'] = engine_job_id
        
        # Monitor completion in background thread
        Thread(target=self._monitor_basic_search_completion, 
               args=(job_id, engine_job_id, job_info, progress_callback),
               daemon=True).start()
    
    def _execute_comprehensive_search(self, job_id: str, job_info: Dict, progress_callback: Callable = None):
        """Execute comprehensive search with data collection"""
        
        # Use batch processing manager for comprehensive operations
        processing_job_id = self.batch_processing_manager.submit_batch_job(
            identifiers=job_info['identifiers'],
            job_type=BatchProcessingJobType.COMPREHENSIVE_COLLECTION,
            search_type=job_info['search_type'],
            processing_mode=ProcessingMode.INTELLIGENT,
            priority=BatchPriority.NORMAL,
            parameters={
                'comprehensive': True,
                'enable_scraping': True,
                'collect_tax_data': True,
                'collect_sales_data': True,
                'timeout': 300.0
            },
            callback=lambda batch_job: self._update_job_progress(job_id, batch_job, progress_callback)
        )
        
        job_info['processing_job_id'] = processing_job_id
        
        # Monitor completion
        Thread(target=self._monitor_comprehensive_search_completion,
               args=(job_id, processing_job_id, job_info, progress_callback),
               daemon=True).start()
    
    def _execute_validation_search(self, job_id: str, job_info: Dict, progress_callback: Callable = None):
        """Execute validation search to check data availability"""
        
        processing_job_id = self.batch_processing_manager.submit_batch_job(
            identifiers=job_info['identifiers'],
            job_type=BatchProcessingJobType.BULK_VALIDATION,
            search_type=job_info['search_type'],
            processing_mode=ProcessingMode.API_ONLY,
            priority=BatchPriority.HIGH,
            parameters={'timeout': 120.0},
            callback=lambda batch_job: self._update_job_progress(job_id, batch_job, progress_callback)
        )
        
        job_info['processing_job_id'] = processing_job_id
        
        Thread(target=self._monitor_validation_completion,
               args=(job_id, processing_job_id, job_info, progress_callback),
               daemon=True).start()
    
    def _execute_bulk_enhancement(self, job_id: str, job_info: Dict, progress_callback: Callable = None):
        """Execute bulk data enhancement using background collection"""
        
        if not self.background_manager:
            raise ValueError("Background collection manager is not available")
        
        processing_job_id = self.batch_processing_manager.submit_batch_job(
            identifiers=job_info['identifiers'],
            job_type=BatchProcessingJobType.DATA_ENHANCEMENT,
            search_type=job_info['search_type'],
            processing_mode=ProcessingMode.INTELLIGENT,
            priority=BatchPriority.NORMAL,
            parameters={
                'comprehensive': True,
                'background_priority': 'high'
            },
            callback=lambda batch_job: self._update_job_progress(job_id, batch_job, progress_callback)
        )
        
        job_info['processing_job_id'] = processing_job_id
        
        Thread(target=self._monitor_enhancement_completion,
               args=(job_id, processing_job_id, job_info, progress_callback),
               daemon=True).start()
    
    def _monitor_basic_search_completion(self, job_id: str, engine_job_id: str, job_info: Dict, progress_callback: Callable):
        """Monitor basic search completion"""
        try:
            while True:
                status = self.batch_search_engine.get_job_status(engine_job_id)
                if not status or status['status'] in ['completed', 'failed', 'cancelled']:
                    break
                time.sleep(1.0)
            
            if status and status['status'] == 'completed':
                # Get results
                raw_results = self.batch_search_engine.get_job_results(engine_job_id)
                results = self._process_engine_results(raw_results, job_info['search_type'])
                
                # Trigger background collection if enabled
                if job_info['enable_background_collection'] and results:
                    self._trigger_background_collection(results)
                
                self._complete_job(job_id, results, progress_callback)
            else:
                error_msg = f"Search job failed with status: {status.get('status', 'unknown') if status else 'not found'}"
                self._fail_job(job_id, error_msg, progress_callback)
                
        except Exception as e:
            logger.error(f"Error monitoring basic search completion for job {job_id}: {e}")
            self._fail_job(job_id, str(e), progress_callback)
    
    def _monitor_comprehensive_search_completion(self, job_id: str, processing_job_id: str, job_info: Dict, progress_callback: Callable):
        """Monitor comprehensive search completion"""
        try:
            while True:
                status = self.batch_processing_manager.get_job_status(processing_job_id)
                if not status or status['status'] in ['completed', 'failed', 'cancelled']:
                    break
                time.sleep(2.0)
            
            if status and status['status'] == 'completed':
                # Get comprehensive results
                raw_results = self.batch_processing_manager.get_job_results(processing_job_id)
                results = self._process_comprehensive_results(raw_results, job_info['search_type'])
                
                self._complete_job(job_id, results, progress_callback)
            else:
                error_msg = f"Comprehensive search failed with status: {status.get('status', 'unknown') if status else 'not found'}"
                self._fail_job(job_id, error_msg, progress_callback)
                
        except Exception as e:
            logger.error(f"Error monitoring comprehensive search for job {job_id}: {e}")
            self._fail_job(job_id, str(e), progress_callback)
    
    def _monitor_validation_completion(self, job_id: str, processing_job_id: str, job_info: Dict, progress_callback: Callable):
        """Monitor validation completion"""
        try:
            while True:
                status = self.batch_processing_manager.get_job_status(processing_job_id)
                if not status or status['status'] in ['completed', 'failed', 'cancelled']:
                    break
                time.sleep(1.0)
            
            if status and status['status'] == 'completed':
                raw_results = self.batch_processing_manager.get_job_results(processing_job_id)
                results = self._process_validation_results(raw_results, job_info['search_type'])
                
                self._complete_job(job_id, results, progress_callback)
            else:
                error_msg = f"Validation failed with status: {status.get('status', 'unknown') if status else 'not found'}"
                self._fail_job(job_id, error_msg, progress_callback)
                
        except Exception as e:
            logger.error(f"Error monitoring validation for job {job_id}: {e}")
            self._fail_job(job_id, str(e), progress_callback)
    
    def _monitor_enhancement_completion(self, job_id: str, processing_job_id: str, job_info: Dict, progress_callback: Callable):
        """Monitor enhancement completion"""
        try:
            while True:
                status = self.batch_processing_manager.get_job_status(processing_job_id)
                if not status or status['status'] in ['completed', 'failed', 'cancelled']:
                    break
                time.sleep(3.0)
            
            if status and status['status'] == 'completed':
                raw_results = self.batch_processing_manager.get_job_results(processing_job_id)
                results = self._process_enhancement_results(raw_results, job_info['search_type'])
                
                self._complete_job(job_id, results, progress_callback)
            else:
                error_msg = f"Enhancement failed with status: {status.get('status', 'unknown') if status else 'not found'}"
                self._fail_job(job_id, error_msg, progress_callback)
                
        except Exception as e:
            logger.error(f"Error monitoring enhancement for job {job_id}: {e}")
            self._fail_job(job_id, str(e), progress_callback)
    
    def _process_engine_results(self, raw_results: List[Dict], search_type: str) -> List[BatchSearchResult]:
        """Process results from batch search engine"""
        results = []
        
        if not raw_results:
            return results
        
        for raw_result in raw_results:
            result = BatchSearchResult(
                identifier=raw_result.get('identifier', ''),
                search_type=search_type,
                success=raw_result.get('success', False),
                result_data=raw_result.get('result'),
                error_message=raw_result.get('error'),
                processing_time=0.0,  # Would need to calculate from timing data
                api_calls_used=1 if raw_result.get('success') else 0,
                data_sources_used=['api'] if raw_result.get('success') else []
            )
            results.append(result)
        
        return results
    
    def _process_comprehensive_results(self, raw_results: Dict, search_type: str) -> List[BatchSearchResult]:
        """Process results from comprehensive search"""
        results = []
        
        if not raw_results or 'results' not in raw_results:
            return results
        
        comprehensive_results = raw_results['results']
        
        for identifier, result_data in comprehensive_results.items():
            if isinstance(result_data, dict):
                result = BatchSearchResult(
                    identifier=identifier,
                    search_type=search_type,
                    success=result_data is not None,
                    result_data=result_data,
                    processing_time=0.0,
                    api_calls_used=1,
                    data_sources_used=['api', 'scraping', 'background']
                )
                results.append(result)
        
        return results
    
    def _process_validation_results(self, raw_results: Dict, search_type: str) -> List[BatchSearchResult]:
        """Process validation results"""
        results = []
        
        if not raw_results or 'results' not in raw_results:
            return results
        
        validation_results = raw_results['results']
        
        for identifier, validation_data in validation_results.items():
            valid = validation_data.get('valid', False) if isinstance(validation_data, dict) else False
            
            result = BatchSearchResult(
                identifier=identifier,
                search_type=search_type,
                success=valid,
                result_data={'validation': validation_data} if valid else None,
                error_message=validation_data.get('error') if isinstance(validation_data, dict) else 'Invalid',
                processing_time=0.0,
                api_calls_used=1,
                data_sources_used=['api']
            )
            results.append(result)
        
        return results
    
    def _process_enhancement_results(self, raw_results: Dict, search_type: str) -> List[BatchSearchResult]:
        """Process enhancement results"""
        results = []
        
        if not raw_results or 'results' not in raw_results:
            return results
        
        enhancement_results = raw_results['results']
        
        for identifier, enhancement_data in enhancement_results.items():
            result = BatchSearchResult(
                identifier=identifier,
                search_type=search_type,
                success=enhancement_data is not None,
                result_data=enhancement_data,
                processing_time=0.0,
                api_calls_used=0,  # Enhancement uses background processes
                data_sources_used=['background', 'scraping']
            )
            results.append(result)
        
        return results
    
    def _trigger_background_collection(self, results: List[BatchSearchResult]):
        """Trigger background data collection for search results"""
        if not self.background_manager:
            return
            
        # Extract APNs from successful results
        apns = []
        for result in results:
            if result.success and result.result_data:
                if isinstance(result.result_data, dict):
                    apn = result.result_data.get('apn')
                    if apn:
                        apns.append(apn)
                elif isinstance(result.result_data, list):
                    for item in result.result_data:
                        if isinstance(item, dict):
                            apn = item.get('apn')
                            if apn:
                                apns.append(apn)
        
        if apns:
            logger.info(f"Triggering background collection for {len(apns)} properties")
            try:
                self.background_manager.enhance_search_results(
                    [{'apn': apn} for apn in apns],
                    max_properties=50
                )
            except Exception as e:
                logger.warning(f"Failed to trigger background collection: {e}")
    
    def _update_job_progress(self, job_id: str, batch_job, progress_callback: Callable = None):
        """Update job progress from underlying batch operations"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                job_info = self.active_jobs[job_id]
                job_info['progress'] = getattr(batch_job, 'progress', 0.0)
                
                if progress_callback:
                    try:
                        progress_callback(job_id, job_info['progress'], f"Processing... {job_info['progress']:.1f}% complete")
                    except Exception as e:
                        logger.warning(f"Progress callback error for job {job_id}: {e}")
    
    def _complete_job(self, job_id: str, results: List[BatchSearchResult], progress_callback: Callable = None):
        """Complete a batch search job"""
        with self.jobs_lock:
            if job_id not in self.active_jobs:
                return
            
            job_info = self.active_jobs[job_id]
            end_time = time.time()
            total_time = end_time - job_info['start_time']
            
            # Create summary
            successful_count = sum(1 for r in results if r.success)
            failed_count = len(results) - successful_count
            
            summary = BatchSearchSummary(
                job_id=job_id,
                job_type=job_info['job_type'],
                total_items=len(job_info['identifiers']),
                successful_items=successful_count,
                failed_items=failed_count,
                total_processing_time=total_time,
                average_time_per_item=total_time / max(1, len(results)),
                api_calls_total=sum(r.api_calls_used for r in results),
                results=results
            )
            
            # Update statistics
            with self.stats_lock:
                self.total_jobs_processed += 1
                self.total_items_processed += len(results)
                if total_time > 0:
                    current_throughput = len(results) / total_time
                    self.average_throughput = (
                        (self.average_throughput * (self.total_jobs_processed - 1) + current_throughput)
                        / self.total_jobs_processed
                    )
            
            # Store completed job
            del self.active_jobs[job_id]
            self.completed_jobs[job_id] = summary
            
            # Final progress callback
            if progress_callback:
                try:
                    progress_callback(job_id, 100.0, f"Completed: {successful_count}/{len(results)} successful")
                except Exception as e:
                    logger.warning(f"Final progress callback error for job {job_id}: {e}")
            
            logger.info(f"Batch search job {job_id} completed: "
                       f"{successful_count}/{len(results)} successful, "
                       f"total time: {total_time:.2f}s")
    
    def _fail_job(self, job_id: str, error_message: str, progress_callback: Callable = None):
        """Mark a job as failed"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                job_info = self.active_jobs[job_id]
                job_info['status'] = 'failed'
                job_info['error'] = error_message
                
                if progress_callback:
                    try:
                        progress_callback(job_id, 0.0, f"Failed: {error_message}")
                    except Exception as e:
                        logger.warning(f"Failure callback error for job {job_id}: {e}")
                
                logger.error(f"Batch search job {job_id} failed: {error_message}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a batch search job"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                job_info = self.active_jobs[job_id]
                return {
                    'job_id': job_id,
                    'job_type': job_info['job_type'].value,
                    'status': job_info['status'],
                    'progress': job_info.get('progress', 0.0),
                    'total_items': len(job_info['identifiers']),
                    'search_type': job_info['search_type'],
                    'start_time': job_info['start_time']
                }
            elif job_id in self.completed_jobs:
                summary = self.completed_jobs[job_id]
                return {
                    'job_id': job_id,
                    'job_type': summary.job_type.value,
                    'status': 'completed',
                    'progress': 100.0,
                    'total_items': summary.total_items,
                    'successful_items': summary.successful_items,
                    'failed_items': summary.failed_items,
                    'total_time': summary.total_processing_time
                }
            else:
                return None
    
    def get_job_results(self, job_id: str) -> Optional[BatchSearchSummary]:
        """Get results from completed job"""
        with self.jobs_lock:
            return self.completed_jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running batch search job"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                job_info = self.active_jobs[job_id]
                job_info['status'] = 'cancelled'
                
                # Cancel underlying operations
                if 'engine_job_id' in job_info:
                    self.batch_search_engine.cancel_job(job_info['engine_job_id'])
                if 'processing_job_id' in job_info:
                    self.batch_processing_manager.cancel_job(job_info['processing_job_id'])
                
                logger.info(f"Cancelled batch search job {job_id}")
                return True
            return False
    
    def export_results_to_csv(self, job_id: str, file_path: str) -> bool:
        """Export batch search results to CSV file"""
        try:
            summary = self.get_job_results(job_id)
            if not summary:
                return False
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Identifier', 'Search Type', 'Success', 'Processing Time (s)',
                    'API Calls Used', 'Data Sources', 'Error Message'
                ])
                
                # Write results
                for result in summary.results:
                    writer.writerow([
                        result.identifier,
                        result.search_type,
                        'Yes' if result.success else 'No',
                        f"{result.processing_time:.2f}",
                        result.api_calls_used,
                        ', '.join(result.data_sources_used),
                        result.error_message or ''
                    ])
                
                # Write summary
                writer.writerow([])
                writer.writerow(['=== SUMMARY ==='])
                writer.writerow(['Total Items', summary.total_items])
                writer.writerow(['Successful', summary.successful_items])
                writer.writerow(['Failed', summary.failed_items])
                writer.writerow(['Total Time (s)', f"{summary.total_processing_time:.2f}"])
                writer.writerow(['Average Time per Item (s)', f"{summary.average_time_per_item:.2f}"])
                writer.writerow(['Total API Calls', summary.api_calls_total])
            
            logger.info(f"Exported batch search results for job {job_id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export results for job {job_id}: {e}")
            return False
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics"""
        with self.stats_lock:
            stats = {
                'total_jobs_processed': self.total_jobs_processed,
                'total_items_processed': self.total_items_processed,
                'average_throughput_items_per_second': self.average_throughput,
                'active_jobs': len(self.active_jobs),
                'completed_jobs': len(self.completed_jobs)
            }
        
        # Add component statistics
        stats['batch_search_engine'] = self.batch_search_engine.get_engine_statistics()
        stats['batch_processing_manager'] = self.batch_processing_manager.get_manager_statistics()
        
        return stats
    
    def shutdown(self):
        """Gracefully shutdown the integration manager"""
        logger.info("Shutting down Batch Search Integration Manager...")
        
        # Cancel all active jobs
        with self.jobs_lock:
            for job_id in list(self.active_jobs.keys()):
                self.cancel_job(job_id)
        
        # Shutdown components
        self.batch_search_engine.shutdown()
        self.batch_processing_manager.shutdown()
        
        logger.info("Batch Search Integration Manager shutdown completed")