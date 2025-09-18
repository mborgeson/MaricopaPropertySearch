#!/usr/bin/env python3
"""
Test GUI Database Integration
Tests that the GUI properly initializes and uses DatabaseManager
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_gui_database_integration():
    print("=" * 60)
    print("GUI DATABASE INTEGRATION TEST")
    print("=" * 60)

    results = {}

    try:
        # Test 1: Import GUI components
        print("\n1. Testing GUI imports...")

        # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
        from logging_config import setup_logging

        setup_logging()
        print("[PASS] Core imports successful")

        # Test 2: Manual DatabaseManager initialization (simulating GUI)
        print("\n2. Testing manual DatabaseManager setup...")
        config_manager = EnhancedConfigManager()
        db_manager = ThreadSafeDatabaseManager(config_manager)

        # Test connectivity
        if db_manager.test_connection():
            print("[PASS] DatabaseManager initialized and connected successfully")
            results['db_init'] = True

            # Test key method that the GUI uses
            print("\n3. Testing GUI-required methods...")

            # Test get_property_details (method used by GUI)
            test_apn = "12345678"  # APN from our previous test
            property_data = db_manager.get_property_details(test_apn)

            if property_data:
                print(f"[PASS] get_property_details returned data for APN {test_apn}")
                print(f"        Owner: {property_data.get('owner_name', 'N/A')}")
                print(f"        Address: {property_data.get('property_address', 'N/A')}")
                results['gui_method'] = True
            else:
                print(f"[FAIL] get_property_details returned no data for APN {test_apn}")
                results['gui_method'] = False

            # Test search methods used by GUI
            print("\n4. Testing search methods...")

            owner_results = db_manager.search_properties_by_owner("Test Owner")
            if len(owner_results) > 0:
                print(f"[PASS] Owner search working ({len(owner_results)} results)")
                results['search_owner'] = True
            else:
                print(f"[FAIL] Owner search failed")
                results['search_owner'] = False

            address_results = db_manager.search_properties_by_address("Test Street")
            if len(address_results) > 0:
                print(f"[PASS] Address search working ({len(address_results)} results)")
                results['search_address'] = True
            else:
                print(f"[FAIL] Address search failed")
                results['search_address'] = False

            # Test database stats (used by GUI status indicators)
            print("\n5. Testing database statistics for GUI...")
            stats = db_manager.get_database_stats()
            if stats and 'properties' in stats:
                print(f"[PASS] Database stats available for GUI")
                print(f"        Total properties: {stats['properties']:,}")
                print(f"        Tax records: {stats['tax_records']:,}")
                print(f"        Sales records: {stats['sales_records']:,}")
                results['stats'] = True
            else:
                print(f"[FAIL] Database stats not available")
                results['stats'] = False

        else:
            print("[FAIL] DatabaseManager connection failed")
            results['db_init'] = False

        # Cleanup
        db_manager.close()
        print("\n[INFO] Database connections closed")

    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        import traceback
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager
        traceback.print_exc()
        results['error'] = str(e)

    # Generate report
    print("\n" + "=" * 60)
    print("GUI INTEGRATION TEST RESULTS")
    print("=" * 60)

    test_results = [
        ('DatabaseManager Initialization', results.get('db_init', False)),
        ('GUI Property Details Method', results.get('gui_method', False)),
        ('GUI Owner Search', results.get('search_owner', False)),
        ('GUI Address Search', results.get('search_address', False)),
        ('GUI Database Statistics', results.get('stats', False)),
    ]

    passed_tests = 0
    for test_name, passed in test_results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
        if passed:
            passed_tests += 1

    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    print(f"\nOVERALL RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

    if passed_tests == total_tests:
        print(f"\n[SUCCESS] GUI-DatabaseManager integration is working correctly!")
        print(f"The GUI should be able to:")
        print(f"  - Initialize DatabaseManager with ConfigManager")
        print(f"  - Connect to the database")
        print(f"  - Retrieve property details")
        print(f"  - Perform owner and address searches")
        print(f"  - Display database statistics")
    else:
        print(f"\n[WARNING] Some GUI integration issues detected")

    if 'error' in results:
        print(f"\nERROR DETAILS: {results['error']}")

    print("=" * 60)

if __name__ == "__main__":
    test_gui_database_integration()