#!/usr/bin/env python
"""
Test Background Data Collection System
"""
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(Path(__file__).parent.parent))
    def test_background_collection():
    """Test the background data collection system"""
        print("TESTING BACKGROUND DATA COLLECTION SYSTEM")
        print("=" * 50)
    
    try:
        # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        config = EnhancedConfigManager()
        api_client = UnifiedMaricopaAPIClient(config)
        db_manager = ThreadSafeDatabaseManager(config)
        
        # Test 1: Try to create the improved data collector
        print("1. TESTING IMPROVED DATA COLLECTOR")
        try:
import inspect

from src.improved_automatic_data_collector import ImprovedMaricopaDataCollector

            # Check the constructor signature

            sig = inspect.signature(ImprovedMaricopaDataCollector.__init__)
        print(f"Constructor signature: {sig}")
            
            # Try creating with the API client
            collector = ImprovedMaricopaDataCollector(db_manager, api_client)
        print("SUCCESS: ImprovedMaricopaDataCollector created successfully")
            
            # Test data collection for our Missouri Ave property
            apn = "10215009"  # The APN we found earlier
        print(f"\n2. TESTING DATA COLLECTION FOR APN: {apn}")
            
            result = collector.collect_data_for_apn_sync(apn)
        print(f"Collection result: {result}")
            
        except ImportError as e:
        print(f"FAILED to import ImprovedMaricopaDataCollector: {e}")
        except Exception as e:
        print(f"FAILED to create/use collector: {e}")
        
        # Test 2: Try the regular automatic data collector
        print("\n3. TESTING REGULAR DATA COLLECTOR")
        try:
from src.automatic_data_collector import MaricopaDataCollector

            # Check constructor signature
            sig = inspect.signature(MaricopaDataCollector.__init__)
        print(f"Constructor signature: {sig}")
            
            collector2 = MaricopaDataCollector(db_manager)
        print("SUCCESS: MaricopaDataCollector created")
            
        except ImportError as e:
        print(f"FAILED to import MaricopaDataCollector: {e}")
        except Exception as e:
        print(f"FAILED to create regular collector: {e}")
        
        # Test 3: Background Data Worker
        print("\n4. TESTING BACKGROUND DATA WORKER (NO QT)")
        try:
            # Check if we can import without Qt dependencies
from src.background_data_collector import DataCollectionJob, JobPriority

        print("SUCCESS: Can import background collection classes")
            
            # Try creating a job
            job = DataCollectionJob("10215009", JobPriority.HIGH)
        print(f"Job created: APN={job.apn}, Priority={job.priority.name}")
            
        except ImportError as e:
        print(f"FAILED to import background collector: {e}")
        except Exception as e:
        print(f"FAILED to test background worker: {e}")
        
        api_client.close()
        db_manager.close()
        print("\nBACKGROUND COLLECTION TEST COMPLETED")
        return True
        
    except Exception as e:
        print(f"Background collection test failed: {e}")
import traceback

from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

        traceback.print_exc()

    return False

if __name__ == "__main__":
    success = test_background_collection()
        print(f"RESULT: {'PASS' if success else 'FAIL'}")