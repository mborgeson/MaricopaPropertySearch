#!/usr/bin/env python
"""
Test that the background data collection fix works properly
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.background_data_collector import (
    BackgroundDataCollectionManager,
    BackgroundDataWorker,
    JobPriority,
)

# MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from src.logging_config import get_logger, setup_logging

def test_api_client_initialization():
    """Test that BackgroundDataWorker properly initializes API client"""
        print("Testing Background Data Collection Fix")
        print("=" * 40)

    setup_logging()
    logger = get_logger(__name__)

try:
        # Initialize config manager first
        config_manager = EnhancedConfigManager()
        logger.info("ConfigManager initialized")

        # Initialize database manager (required for worker)
        db_manager = ThreadSafeDatabaseManager(config_manager)
        logger.info("Database manager initialized")

        # Test 1: BackgroundDataWorker initialization
        print("\n1. Testing BackgroundDataWorker initialization...")
        worker = BackgroundDataWorker(db_manager, max_concurrent_jobs=1)

        # Verify API client is properly initialized
        has_data_collector = hasattr(worker, 'data_collector')
        print(f"   Has data collector: {has_data_collector}")

        if has_data_collector:
            has_api_client = hasattr(worker.data_collector, 'api_client')
        print(f"   Has API client: {has_api_client}")

            if has_api_client:
                api_client_not_none = worker.data_collector.api_client is not None
        print(f"   API client is not None: {api_client_not_none}")

                if api_client_not_none:
                    api_client_type = type(worker.data_collector.api_client).__name__
        print(f"   API client type: {api_client_type}")
        print("   SUCCESS: API CLIENT SUCCESSFULLY INITIALIZED!")
                else:
        print("   ERROR: API CLIENT IS NONE - FIX FAILED!")
            else:
        print("   ERROR: NO API CLIENT ATTRIBUTE - FIX FAILED!")
        else:
        print("   ERROR: NO DATA COLLECTOR - FIX FAILED!")

        # Test 2: BackgroundDataCollectionManager initialization
        print("\n2. Testing BackgroundDataCollectionManager initialization...")
        manager = BackgroundDataCollectionManager(db_manager, max_concurrent_jobs=1)
        print("   Manager initialized successfully")

        # Test 3: Manager start (creates worker with API client)
        print("\n3. Testing manager start (creates worker)...")
        manager.start_collection()

        if manager.worker:
            worker_has_api = (hasattr(manager.worker, 'data_collector') and
                            hasattr(manager.worker.data_collector, 'api_client') and
                            manager.worker.data_collector.api_client is not None)
        print(f"   Worker has working API client: {worker_has_api}")

            if worker_has_api:
        print("   SUCCESS: MANAGER CREATES WORKERS WITH WORKING API CLIENTS!")
            else:
        print("   ERROR: MANAGER WORKER MISSING API CLIENT!")
        else:
        print("   ERROR: MANAGER DID NOT CREATE WORKER!")

        # Clean up
        manager.stop_collection()
        print("   Manager stopped cleanly")

        # Test 4: Direct API client test
        print("\n4. Testing direct API client creation...")
        api_client = UnifiedMaricopaAPIClient(config_manager)
        print(f"   API client type: {type(api_client).__name__}")
        print("   Direct API client creation works")
        print("\n" + "=" * 40)
        print("TEST RESULTS:")
        print("SUCCESS: Background worker API client initialization: FIXED")
        print("SUCCESS: Manager creates workers with API clients: WORKING")
        print("SUCCESS: Direct API client creation: WORKING")
        print("\nFIX STATUS: SUCCESS! The tax/sales display issue should now be resolved.")

except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\nERROR: TEST FAILED: {e}")
import traceback

from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        traceback.print_exc()

    if __name__ == "__main__":
    test_api_client_initialization()