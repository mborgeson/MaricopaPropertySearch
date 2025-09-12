#!/usr/bin/env python
"""
Batch Processing Examples
Practical examples showing how to use the batch/parallel processing system
"""

import asyncio
import time
import logging
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.config_manager import ConfigManager
from src.database_manager import DatabaseManager
from src.api_client import MaricopaAPIClient
from src.batch_processing_manager import (
    BatchProcessingManager, 
    BatchProcessingJobType, 
    ProcessingMode,
    BatchPriority
)
from src.batch_search_engine import BatchSearchEngine, SearchMode
from src.batch_api_client import BatchAPIClient
from src.parallel_web_scraper import ParallelWebScraperManager, ScrapingTask, ScrapingRequest
from src.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


class BatchProcessingExamples:
    """Examples of batch processing operations"""
    
    def __init__(self):
        """Initialize with configuration and components"""
        # Load configuration
        self.config = ConfigManager()
        setup_logging(self.config)
        
        # Initialize core components
        self.db_manager = DatabaseManager(self.config)
        self.api_client = MaricopaAPIClient(self.config)
        
        # Initialize batch processing manager
        self.batch_manager = BatchProcessingManager(
            api_client=self.api_client,
            db_manager=self.db_manager,
            max_concurrent_jobs=3,
            enable_background_collection=True
        )
        
        logger.info("Batch processing examples initialized")
    
    def example_1_simple_batch_search(self, apns: List[str]):
        """
        Example 1: Simple batch search for multiple APNs
        Uses intelligent processing mode to automatically choose best approach
        """
        logger.info(f"Example 1: Simple batch search for {len(apns)} APNs")
        
        # Submit batch job
        job_id = self.batch_manager.submit_batch_job(
            identifiers=apns,
            job_type=BatchProcessingJobType.PROPERTY_SEARCH,
            search_type='apn',
            processing_mode=ProcessingMode.INTELLIGENT,
            priority=BatchPriority.HIGH,
            parameters={
                'comprehensive': True,
                'timeout': 300.0
            }
        )
        
        # Monitor progress
        print(f"Submitted job: {job_id}")
        
        while True:
            status = self.batch_manager.get_job_status(job_id)
            if not status:
                print("Job not found")
                break
            
            print(f"Progress: {status['progress']:.1f}% - "
                  f"Completed: {status['completed_items']}/{status['total_items']} - "
                  f"Successful: {status['successful_items']}")
            
            if status['status'] in ['completed', 'failed']:
                break
            
            time.sleep(2.0)
        
        # Get results
        results = self.batch_manager.get_job_results(job_id)
        if results:
            print(f"Job completed with {results['statistics']['success_rate']:.1f}% success rate")
            print(f"Retrieved data for {len(results['results'])} properties")
            
            # Sample some results
            for i, (key, result) in enumerate(results['results'].items()):
                if i >= 3:  # Show first 3 results
                    break
                if result:
                    print(f"  {key}: Found property data")
                else:
                    print(f"  {key}: No data found")
        
        return results
    
    def example_2_comprehensive_data_collection(self, apns: List[str]):
        """
        Example 2: Comprehensive data collection using API + web scraping
        Collects property data, tax history, and sales records
        """
        logger.info(f"Example 2: Comprehensive data collection for {len(apns)} APNs")
        
        job_id = self.batch_manager.submit_batch_job(
            identifiers=apns,
            job_type=BatchProcessingJobType.COMPREHENSIVE_COLLECTION,
            search_type='apn',
            processing_mode=ProcessingMode.PARALLEL_ALL,
            priority=BatchPriority.NORMAL,
            parameters={
                'enable_scraping': True,
                'collect_tax_data': True,
                'collect_sales_data': True,
                'api_timeout': 180.0,
                'scraping_timeout': 300.0
            }
        )
        
        print(f"Started comprehensive collection job: {job_id}")
        
        # Monitor with more detailed progress
        last_progress = -1
        while True:
            status = self.batch_manager.get_job_status(job_id)
            if not status:
                break
            
            # Only print when progress changes significantly
            if abs(status['progress'] - last_progress) >= 5.0:
                print(f"Progress: {status['progress']:.1f}% - "
                      f"Items: {status['completed_items']}/{status['total_items']} - "
                      f"Success: {status['successful_items']} - "
                      f"Status: {status['status']}")
                last_progress = status['progress']
            
            if status['status'] in ['completed', 'failed']:
                break
            
            time.sleep(3.0)
        
        # Get comprehensive results
        results = self.batch_manager.get_job_results(job_id)
        if results:
            print(f"Comprehensive collection completed:")
            print(f"  Success rate: {results['statistics']['success_rate']:.1f}%")
            print(f"  Total results: {len(results['results'])}")
            print(f"  Errors: {len(results['errors'])}")
            
            # Analyze result types
            api_results = sum(1 for k in results['results'].keys() if k.startswith('api_'))
            scraping_results = len(results['results']) - api_results
            
            print(f"  API results: {api_results}")
            print(f"  Scraping results: {scraping_results}")
        
        return results
    
    def example_3_tax_data_collection(self, apns: List[str]):
        """
        Example 3: Focused tax data collection using parallel web scraping
        """
        logger.info(f"Example 3: Tax data collection for {len(apns)} APNs")
        
        job_id = self.batch_manager.submit_batch_job(
            identifiers=apns,
            job_type=BatchProcessingJobType.TAX_DATA_COLLECTION,
            search_type='apn',
            processing_mode=ProcessingMode.SCRAPING_ONLY,
            priority=BatchPriority.NORMAL,
            parameters={
                'timeout': 240.0,
                'max_retries': 2
            }
        )
        
        print(f"Started tax data collection job: {job_id}")
        
        # Monitor progress
        while True:
            status = self.batch_manager.get_job_status(job_id)
            if not status:
                break
            
            print(f"Tax Collection Progress: {status['progress']:.1f}% - "
                  f"{status['successful_items']} successful, "
                  f"{status['failed_items']} failed")
            
            if status['status'] in ['completed', 'failed']:
                break
            
            time.sleep(2.0)
        
        # Get tax data results
        results = self.batch_manager.get_job_results(job_id)
        if results:
            print(f"Tax collection completed with {results['statistics']['success_rate']:.1f}% success rate")
            
            # Sample tax data
            for i, (key, tax_data) in enumerate(results['results'].items()):
                if i >= 2:  # Show first 2 tax results
                    break
                if tax_data and isinstance(tax_data, dict):
                    print(f"  {key}: Tax data collected")
                    if 'current_tax' in tax_data:
                        print(f"    Current tax: ${tax_data['current_tax'].get('assessed_tax', 'N/A')}")
        
        return results
    
    def example_4_bulk_validation(self, apns: List[str]):
        """
        Example 4: Bulk validation of APNs to check which exist in the system
        """
        logger.info(f"Example 4: Bulk validation for {len(apns)} APNs")
        
        job_id = self.batch_manager.submit_batch_job(
            identifiers=apns,
            job_type=BatchProcessingJobType.BULK_VALIDATION,
            search_type='apn',
            processing_mode=ProcessingMode.API_ONLY,
            priority=BatchPriority.HIGH,
            parameters={
                'timeout': 120.0
            }
        )
        
        print(f"Started bulk validation job: {job_id}")
        
        # Monitor validation
        while True:
            status = self.batch_manager.get_job_status(job_id)
            if not status:
                break
            
            print(f"Validation Progress: {status['progress']:.1f}% - "
                  f"{status['completed_items']}/{status['total_items']} checked")
            
            if status['status'] in ['completed', 'failed']:
                break
            
            time.sleep(1.0)
        
        # Get validation results
        results = self.batch_manager.get_job_results(job_id)
        if results:
            valid_apns = []
            invalid_apns = []
            
            for key, validation_result in results['results'].items():
                if isinstance(validation_result, dict):
                    if validation_result.get('valid'):
                        valid_apns.append(key)
                    else:
                        invalid_apns.append(key)
            
            print(f"Validation completed:")
            print(f"  Valid APNs: {len(valid_apns)}")
            print(f"  Invalid APNs: {len(invalid_apns)}")
            print(f"  Success rate: {results['statistics']['success_rate']:.1f}%")
            
            # Show some invalid APNs
            if invalid_apns:
                print(f"  Sample invalid APNs: {invalid_apns[:3]}")
        
        return results
    
    def example_5_batch_api_only(self, owner_names: List[str]):
        """
        Example 5: Direct batch API usage for owner searches
        """
        logger.info(f"Example 5: Batch API search for {len(owner_names)} owners")
        
        # Get batch API client
        batch_api = self.batch_manager.batch_api_client
        
        # Submit batch owner searches
        request_ids = batch_api.batch_search_by_owners(
            owner_names=owner_names,
            priority=5,
            limit=10
        )
        
        print(f"Submitted {len(request_ids)} API requests")
        
        # Wait for completion with timeout
        completion_stats = batch_api.wait_for_batch_completion(
            request_ids=request_ids,
            timeout=180.0
        )
        
        print(f"Batch API completed:")
        print(f"  Total requested: {completion_stats['total_requested']}")
        print(f"  Completed: {completion_stats['completed']}")
        print(f"  Successful: {completion_stats['successful']}")
        print(f"  Failed: {completion_stats['failed']}")
        
        # Process results
        all_properties = []
        for request_id, result_data in completion_stats['results'].items():
            if result_data['status']['success'] and result_data['result']:
                properties = result_data['result']
                if isinstance(properties, list):
                    all_properties.extend(properties)
                    print(f"  {request_id}: Found {len(properties)} properties")
                else:
                    print(f"  {request_id}: Found 1 property")
        
        print(f"Total properties found: {len(all_properties)}")
        return all_properties
    
    def example_6_monitoring_and_statistics(self):
        """
        Example 6: Monitoring system performance and statistics
        """
        logger.info("Example 6: System monitoring and statistics")
        
        # Get comprehensive statistics
        stats = self.batch_manager.get_manager_statistics()
        
        print("Batch Processing Manager Statistics:")
        print(f"  Total jobs processed: {stats['total_jobs_processed']}")
        print(f"  Total items processed: {stats['total_items_processed']}")
        print(f"  Success rate: {stats['success_rate_percent']:.1f}%")
        print(f"  Average job time: {stats['average_job_time']:.2f}s")
        print(f"  Active jobs: {stats['active_jobs']}")
        print(f"  Completed jobs: {stats['completed_jobs']}")
        
        # Component statistics
        print("\nComponent Statistics:")
        
        # Batch search engine stats
        if 'batch_search_engine' in stats['components']:
            engine_stats = stats['components']['batch_search_engine']
            print(f"  Search Engine - Processed: {engine_stats['total_requests_processed']}, "
                  f"Success: {engine_stats['success_rate_percent']:.1f}%")
        
        # Batch API client stats
        if 'batch_api_client' in stats['components']:
            api_stats = stats['components']['batch_api_client']
            print(f"  API Client - Requests: {api_stats['total_requests']}, "
                  f"Success: {api_stats['success_rate_percent']:.1f}%, "
                  f"Avg time: {api_stats['average_response_time']:.2f}s")
        
        # Parallel scraper stats
        if stats['components']['parallel_scraper']:
            scraper_stats = stats['components']['parallel_scraper']
            print(f"  Web Scraper - Scraped: {scraper_stats['total_scraped']}, "
                  f"Success: {scraper_stats['success_rate_percent']:.1f}%, "
                  f"Active: {scraper_stats['active_requests']}")
        
        # Background collector stats
        if stats['components']['background_collector']:
            collector_stats = stats['components']['background_collector']
            print(f"  Background Collector - Status: {collector_stats['status']}, "
                  f"Queue: {collector_stats.get('pending_jobs', 0)} pending")
        
        return stats
    
    def cleanup_example(self):
        """Clean up old jobs and resources"""
        logger.info("Cleaning up old jobs and resources")
        
        # Cleanup completed jobs older than 6 hours
        removed_jobs = self.batch_manager.cleanup_completed_jobs(max_age_hours=6)
        print(f"Cleaned up {removed_jobs} old jobs")
        
        # Get final statistics
        final_stats = self.batch_manager.get_manager_statistics()
        print(f"Final state: {final_stats['active_jobs']} active jobs, "
              f"{final_stats['completed_jobs']} completed jobs")


def run_examples():
    """Run all batch processing examples"""
    examples = BatchProcessingExamples()
    
    # Sample data for examples
    sample_apns = [
        "123-45-678",
        "987-65-432", 
        "456-78-901",
        "234-56-789",
        "345-67-890"
    ]
    
    sample_owners = [
        "SMITH JOHN",
        "JOHNSON MARY",
        "WILLIAMS ROBERT"
    ]
    
    print("=" * 60)
    print("BATCH PROCESSING EXAMPLES")
    print("=" * 60)
    
    try:
        # Example 1: Simple batch search
        print("\n" + "=" * 40)
        print("EXAMPLE 1: Simple Batch Search")
        print("=" * 40)
        results1 = examples.example_1_simple_batch_search(sample_apns[:3])
        
        # Example 2: Comprehensive collection (commented out for demo)
        # print("\n" + "=" * 40)
        # print("EXAMPLE 2: Comprehensive Collection") 
        # print("=" * 40)
        # results2 = examples.example_2_comprehensive_data_collection(sample_apns[:2])
        
        # Example 4: Bulk validation
        print("\n" + "=" * 40)
        print("EXAMPLE 4: Bulk Validation")
        print("=" * 40)
        results4 = examples.example_4_bulk_validation(sample_apns)
        
        # Example 5: Batch API only
        print("\n" + "=" * 40)
        print("EXAMPLE 5: Batch API Search")
        print("=" * 40)
        results5 = examples.example_5_batch_api_only(sample_owners)
        
        # Example 6: Monitoring
        print("\n" + "=" * 40)
        print("EXAMPLE 6: System Monitoring")
        print("=" * 40)
        examples.example_6_monitoring_and_statistics()
        
        # Cleanup
        print("\n" + "=" * 40)
        print("CLEANUP")
        print("=" * 40)
        examples.cleanup_example()
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        print(f"Error: {e}")
    
    finally:
        # Shutdown
        print("\nShutting down batch processing manager...")
        examples.batch_manager.shutdown()
        print("Examples completed!")


if __name__ == "__main__":
    run_examples()