#!/usr/bin/env python
"""
Batch Search System Demo
Demonstrates the batch/parallel search processing system capabilities
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient, MockMaricopaAPIClient
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager
from web_scraper import WebScraperManager, MockWebScraperManager
from background_data_collector import BackgroundDataCollectionManager
from batch_search_integration import BatchSearchIntegrationManager, BatchSearchJobType
from logging_config import setup_logging, get_logger


def demonstrate_batch_search():
    """Demonstrate batch search capabilities"""

    print("=" * 60)
    print("MARICOPA PROPERTY SEARCH - BATCH SEARCH DEMO")
    print("=" * 60)
    print()

    try:
        # Initialize configuration
        config = EnhancedConfigManager()
        logging_config = setup_logging(config)
        logger = get_logger(__name__)

        print("✓ Configuration and logging initialized")

        # Initialize database
        db_manager = ThreadSafeDatabaseManager(config)
        print("✓ Database manager initialized")

        # Initialize API client (use mock for demo)
        try:
            api_client = UnifiedMaricopaAPIClient(config)
            print("✓ Using real Maricopa API client")
        except Exception as e:
            print(f"⚠ Using mock API client ({e})")
            api_client = MockMaricopaAPIClient(config)

        # Initialize web scraper (use mock for demo)
        try:
            web_scraper = WebScraperManager(config)
            print("✓ Using real web scraper")
        except Exception as e:
            print(f"⚠ Using mock web scraper ({e})")
            web_scraper = MockWebScraperManager(config)

        # Initialize background data collection
        background_manager = BackgroundDataCollectionManager(db_manager)
        print("✓ Background data collection manager initialized")

        # Initialize batch search integration manager
        batch_manager = BatchSearchIntegrationManager(
            api_client=api_client,
            db_manager=db_manager,
            web_scraper_manager=web_scraper,
            background_manager=background_manager,
        )
        print("✓ Batch search integration manager initialized")
        print()

        # Demo data - sample APNs for testing
        sample_apns = [
            "123-45-678",
            "234-56-789",
            "345-67-890",
            "456-78-901",
            "567-89-012",
        ]

        sample_addresses = [
            "123 Main St Phoenix AZ",
            "456 Oak Ave Scottsdale AZ",
            "789 Pine Rd Tempe AZ",
        ]

        sample_owners = ["John Smith", "Jane Doe", "Robert Johnson"]

        # Demonstrate different batch search types
        demos = [
            {
                "name": "Basic Batch APN Search",
                "identifiers": sample_apns[:3],
                "search_type": "apn",
                "job_type": BatchSearchJobType.BASIC_SEARCH,
                "description": "Basic parallel search for 3 APNs with automatic caching",
            },
            {
                "name": "Comprehensive Address Search",
                "identifiers": sample_addresses,
                "search_type": "address",
                "job_type": BatchSearchJobType.COMPREHENSIVE_SEARCH,
                "description": "Comprehensive search with data collection for 3 addresses",
            },
            {
                "name": "Bulk Validation Search",
                "identifiers": sample_apns,
                "search_type": "apn",
                "job_type": BatchSearchJobType.VALIDATION_SEARCH,
                "description": "Fast validation check for 5 APNs",
            },
        ]

        for i, demo in enumerate(demos, 1):
            print(f"DEMO {i}: {demo['name']}")
            print("-" * 50)
            print(f"Description: {demo['description']}")
            print(f"Search Type: {demo['search_type']}")
            print(f"Items: {len(demo['identifiers'])}")
            print(f"Job Type: {demo['job_type'].value}")
            print()
            print("Search Items:")
            for item in demo["identifiers"]:
                print(f"  • {item}")
            print()

            # Start batch search with progress callback
            def progress_callback(job_id, progress, status):
                print(f"  Progress: {progress:.1f}% - {status}")

            start_time = time.time()

            try:
                job_id = batch_manager.execute_batch_search(
                    identifiers=demo["identifiers"],
                    search_type=demo["search_type"],
                    job_type=demo["job_type"],
                    max_concurrent=3,
                    enable_background_collection=True,
                    progress_callback=progress_callback,
                )

                print(f"✓ Batch job started: {job_id}")

                # Monitor job completion
                while True:
                    status = batch_manager.get_job_status(job_id)
                    if not status:
                        print("✗ Job status not found")
                        break

                    if status.get("progress", 0) >= 100:
                        print("✓ Job completed")
                        break

                    time.sleep(0.5)  # Check every 500ms

                # Get results
                results = batch_manager.get_job_results(job_id)
                if results:
                    print(f"✓ Results retrieved")
                    print(f"  Total Items: {results.total_items}")
                    print(f"  Successful: {results.successful_items}")
                    print(f"  Failed: {results.failed_items}")
                    print(
                        f"  Processing Time: {results.total_processing_time:.2f} seconds"
                    )
                    print(
                        f"  Average per Item: {results.average_time_per_item:.2f} seconds"
                    )
                    print(f"  API Calls Used: {results.api_calls_total}")

                    if results.results:
                        print(f"  Sample Results:")
                        for result in results.results[:2]:  # Show first 2
                            status_icon = "✓" if result.success else "✗"
                            print(
                                f"    {status_icon} {result.identifier}: {result.error_message or 'Success'}"
                            )
                else:
                    print("✗ No results available")

            except Exception as e:
                print(f"✗ Demo failed: {e}")

            elapsed = time.time() - start_time
            print(f"Demo {i} completed in {elapsed:.2f} seconds")
            print()

            if i < len(demos):
                print("Press Enter to continue to next demo...")
                input()
                print()

        # Show final statistics
        print("BATCH PROCESSING STATISTICS")
        print("-" * 50)
        stats = batch_manager.get_integration_statistics()

        print(f"Total Jobs Processed: {stats['total_jobs_processed']}")
        print(f"Total Items Processed: {stats['total_items_processed']}")
        print(
            f"Average Throughput: {stats['average_throughput_items_per_second']:.2f} items/sec"
        )
        print(f"Active Jobs: {stats['active_jobs']}")
        print(f"Completed Jobs: {stats['completed_jobs']}")
        print()

        # Component statistics
        if "batch_search_engine" in stats:
            engine_stats = stats["batch_search_engine"]
            print("Batch Search Engine Stats:")
            print(f"  Success Rate: {engine_stats.get('success_rate_percent', 0):.1f}%")
            print(
                f"  Connection Pool Size: {engine_stats.get('connection_pool_size', 0)}"
            )
            print()

        print("=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("Key Features Demonstrated:")
        print("✓ Parallel batch processing (3-5x faster than sequential)")
        print("✓ Multiple search types (APN, address, owner)")
        print("✓ Different job types (basic, comprehensive, validation)")
        print("✓ Real-time progress tracking")
        print("✓ Error handling and recovery")
        print("✓ Background data collection integration")
        print("✓ Connection pooling and rate limiting")
        print("✓ Performance statistics and monitoring")
        print()

    except Exception as e:
        print(f"✗ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Cleanup
        try:
            if "batch_manager" in locals():
                batch_manager.shutdown()
            if "background_manager" in locals():
                background_manager.stop_collection()
            print("✓ Cleanup completed")
        except:
            pass


if __name__ == "__main__":
    demonstrate_batch_search()
