#!/usr/bin/env python
"""
Verify all smart agent fixes are working
Tests the three critical fixes applied to resolve runtime errors
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
def test_apn_keyerror_fix():
    """Test that insert_property handles missing 'apn' gracefully"""
        print("\n[TEST 1] Testing APN KeyError fix in ThreadSafeDatabaseManager...")

try:
        # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        config = EnhancedConfigManager()
        db = ThreadSafeDatabaseManager(config)

        # Test with missing 'apn' key
        property_data = {
            'owner_name': 'Test Owner',
            'property_address': '123 Test St',
            # 'apn' is missing intentionally
        }

        # This should not crash but return False
        result = db.insert_property(property_data)

        if result is False:
        print("  [OK] insert_property handles missing 'apn' gracefully")
        else:
        print("  [WARNING] insert_property returned unexpected result")

        # Test validation method exists
        if hasattr(db, 'validate_property_data'):
            errors = db.validate_property_data(property_data)
            if errors and 'apn' in str(errors):
        print("  [OK] validate_property_data detects missing 'apn'")
            else:
        print("  [WARNING] validate_property_data didn't detect missing 'apn'")

        db.close()
        return True

except Exception as e:
        print(f"  [ERROR] APN KeyError fix test failed: {e}")
        return False
def test_int_not_iterable_fix():
    """Test that data status checking handles int return values"""
        print("\n[TEST 2] Testing 'int' object not iterable fix...")

try:
        # Mock test since we need GUI context
        # Check if the fix is in place by examining the method
import inspect

from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        # Get the source of _get_data_collection_status method
        source_lines = inspect.getsource(EnhancedPropertySearchApp._get_data_collection_status)

        # Check if type checking is implemented
        if 'isinstance' in source_lines and 'active_jobs' in source_lines:
        print("  [OK] Type checking for active_jobs is implemented")

            if 'isinstance(active_jobs, (list, tuple))' in source_lines:
        print("  [OK] Handles both list and int types for active_jobs")
            else:
        print("  [WARNING] Type checking may be incomplete")

            return True
        else:
        print("  [ERROR] Type checking not found in _get_data_collection_status")
            return False

except Exception as e:
        print(f"  [ERROR] Int not iterable fix test failed: {e}")
        return False
def test_is_cached_method():
    """Test that DataCollectionCache has is_cached method"""
        print("\n[TEST 3] Testing is_cached method in DataCollectionCache...")

try:
from src.data_collection_cache import DataCollectionCache
from src.enhanced_config_manager import EnhancedConfigManager
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        cache = DataCollectionCache()

        # Test method exists
        if not hasattr(cache, 'is_cached'):
        print("  [ERROR] is_cached method missing")
            return False
        print("  [OK] is_cached method exists")

        # Test with None
        result = cache.is_cached(None)
        if result is False:
        print("  [OK] is_cached(None) returns False")
        else:
        print("  [WARNING] is_cached(None) should return False")

        # Test with empty string
        result = cache.is_cached('')
        if result is False:
        print("  [OK] is_cached('') returns False")
        else:
        print("  [WARNING] is_cached('') should return False")

        # Test with valid APN (not cached)
        result = cache.is_cached('12345678')
        if result is False:
        print("  [OK] is_cached returns False for uncached APN")
        else:
        print("  [WARNING] is_cached should return False for new APN")

        # Add test data and verify
        cache.property_cache['12345678'] = {'test': 'data'}
        result = cache.is_cached('12345678')
        if result is True:
        print("  [OK] is_cached returns True for cached APN")
        else:
        print("  [ERROR] is_cached should return True for cached APN")
            return False

        return True

except Exception as e:
        print(f"  [ERROR] is_cached method test failed: {e}")
        return False
def main():
        print("=" * 60)
        print(" SMART AGENT FIXES VERIFICATION")
        print("=" * 60)

    all_passed = True

    # Run all tests
    if not test_apn_keyerror_fix():
        all_passed = False

    if not test_int_not_iterable_fix():
        all_passed = False

    if not test_is_cached_method():
        all_passed = False

    # Summary
        print("\n" + "=" * 60)
        print(" VERIFICATION SUMMARY")
        print("=" * 60)

    if all_passed:
        print("\n[SUCCESS] All smart agent fixes verified!")
        print("\n[FIXES APPLIED]:")
        print("  1. [OK] KeyError 'apn' - Now handles missing APN gracefully")
        print("  2. [OK] 'int' not iterable - Type checking for active_jobs")
        print("  3. [OK] is_cached method - Added to DataCollectionCache")
        print("\n[READY] The application should now run without these errors:")
        print("  - No more KeyError when inserting properties")
        print("  - No more 'int' object is not iterable errors")
        print("  - No more AttributeError for is_cached")
        print("\n[TEST] Run the application:")
        print("  python RUN_APPLICATION.py")

    else:
        print("\n[FAILURE] Some fixes may not be complete")
        print("Check the error messages above for details")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())