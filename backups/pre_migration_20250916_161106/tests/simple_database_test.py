#!/usr/bin/env python3
"""
Simple Database Manager Test
Tests DatabaseManager fixes and ConfigManager integration
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_database_manager():
    print("=" * 60)
    print("DATABASE MANAGER FIXES TEST")
    print("=" * 60)

    results = {}

    try:
        # Test 1: Import and Configuration
        print("\n1. Testing imports and configuration...")
        from config_manager import ConfigManager
        from database_manager import DatabaseManager
        from logging_config import setup_logging

        setup_logging()
        print("[PASS] All imports successful")

        # Test 2: ConfigManager initialization
        print("\n2. Testing ConfigManager initialization...")
        config_manager = ConfigManager()
        db_config = config_manager.get_db_config()
        print(f"[PASS] ConfigManager created, DB config: {db_config['host']}:{db_config['port']}")
        results['config_manager'] = True

        # Test 3: DatabaseManager initialization with ConfigManager
        print("\n3. Testing DatabaseManager initialization...")
        db_manager = DatabaseManager(config_manager)
        print("[PASS] DatabaseManager initialized with ConfigManager")
        results['db_manager_init'] = True

        # Test 4: Database connectivity
        print("\n4. Testing database connectivity...")
        is_connected = db_manager.test_connection()
        if is_connected:
            print("[PASS] Database connection successful")
            results['connectivity'] = True

            # Test 5: Property operations
            print("\n5. Testing property operations...")

            # Test get_property_by_apn method (the key fix)
            test_apn = "12345678"

            # Insert test property first
            test_property = {
                'apn': test_apn,
                'owner_name': 'Test Owner',
                'property_address': '123 Test Street, Phoenix, AZ 85001'
            }

            insert_result = db_manager.insert_property(test_property)
            if insert_result:
                print("[PASS] Property insertion successful")
                results['property_insert'] = True

                # Test the fixed get_property_by_apn method
                property_data = db_manager.get_property_by_apn(test_apn)
                if property_data and property_data.get('apn') == test_apn:
                    print("[PASS] get_property_by_apn method working correctly")
                    results['get_by_apn'] = True
                else:
                    print("[FAIL] get_property_by_apn method failed")
                    results['get_by_apn'] = False

                # Test the alias method get_property_details
                property_details = db_manager.get_property_details(test_apn)
                if property_details and property_details.get('apn') == test_apn:
                    print("[PASS] get_property_details alias method working")
                    results['get_details_alias'] = True
                else:
                    print("[FAIL] get_property_details alias method failed")
                    results['get_details_alias'] = False

                # Test search operations
                search_results = db_manager.search_properties_by_owner('Test Owner')
                if len(search_results) > 0:
                    print(f"[PASS] Owner search returned {len(search_results)} results")
                    results['owner_search'] = True
                else:
                    print("[FAIL] Owner search returned no results")
                    results['owner_search'] = False

            else:
                print("[FAIL] Property insertion failed")
                results['property_insert'] = False

            # Test 6: Tax history operations
            print("\n6. Testing tax history operations...")
            test_tax = {
                'apn': test_apn,
                'tax_year': 2023,
                'assessed_value': 250000,
                'limited_value': 240000,
                'tax_amount': 3500.00,
                'payment_status': 'Paid',
                'last_payment_date': '2023-12-15',
                'raw_data': {'test': 'tax_data'}
            }

            tax_insert = db_manager.insert_tax_history(test_tax)
            if tax_insert:
                print("[PASS] Tax history insertion successful")
                results['tax_insert'] = True

                tax_history = db_manager.get_tax_history(test_apn)
                if len(tax_history) > 0:
                    print(f"[PASS] Tax history retrieval successful ({len(tax_history)} records)")
                    results['tax_retrieve'] = True
                else:
                    print("[FAIL] Tax history retrieval failed")
                    results['tax_retrieve'] = False
            else:
                print("[FAIL] Tax history insertion failed")
                results['tax_insert'] = False

            # Test 7: Sales history operations
            print("\n7. Testing sales history operations...")
            test_sales = {
                'apn': test_apn,
                'sale_date': '2023-06-15',
                'sale_price': 275000,
                'seller_name': 'Previous Owner',
                'buyer_name': 'Test Owner',
                'deed_type': 'Warranty Deed',
                'recording_number': 'REC2023001234'
            }

            sales_insert = db_manager.insert_sales_history(test_sales)
            if sales_insert:
                print("[PASS] Sales history insertion successful")
                results['sales_insert'] = True

                sales_history = db_manager.get_sales_history(test_apn)
                if len(sales_history) > 0:
                    print(f"[PASS] Sales history retrieval successful ({len(sales_history)} records)")
                    results['sales_retrieve'] = True
                else:
                    print("[FAIL] Sales history retrieval failed")
                    results['sales_retrieve'] = False
            else:
                print("[FAIL] Sales history insertion failed")
                results['sales_insert'] = False

            # Test 8: Database statistics
            print("\n8. Testing database statistics...")
            stats = db_manager.get_database_stats()
            if stats:
                print("[PASS] Database statistics retrieved successfully")
                print(f"  Properties: {stats.get('properties', 0)}")
                print(f"  Tax records: {stats.get('tax_records', 0)}")
                print(f"  Sales records: {stats.get('sales_records', 0)}")
                results['statistics'] = True
            else:
                print("[FAIL] Database statistics retrieval failed")
                results['statistics'] = False

        else:
            print("[FAIL] Database connection failed")
            results['connectivity'] = False

        # Cleanup
        if 'db_manager' in locals():
            db_manager.close()
            print("\n[INFO] Database connections closed")

    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        results['error'] = str(e)

    # Generate report
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed_tests = 0
    total_tests = 0

    test_categories = [
        ('Configuration Management', results.get('config_manager', False)),
        ('DatabaseManager Initialization', results.get('db_manager_init', False)),
        ('Database Connectivity', results.get('connectivity', False)),
        ('Property Operations', results.get('property_insert', False)),
        ('get_property_by_apn Fix', results.get('get_by_apn', False)),
        ('get_property_details Alias', results.get('get_details_alias', False)),
        ('Owner Search', results.get('owner_search', False)),
        ('Tax History Operations', results.get('tax_insert', False) and results.get('tax_retrieve', False)),
        ('Sales History Operations', results.get('sales_insert', False) and results.get('sales_retrieve', False)),
        ('Database Statistics', results.get('statistics', False)),
    ]

    for test_name, passed in test_categories:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
        if passed:
            passed_tests += 1
        total_tests += 1

    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\nOVERALL RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

    # Key fixes verification
    print(f"\nKEY FIXES VERIFICATION:")
    print("-" * 25)
    config_fix = results.get('config_manager', False) and results.get('db_manager_init', False)
    apn_method_fix = results.get('get_by_apn', False)
    alias_fix = results.get('get_details_alias', False)

    print(f"[{'PASS' if config_fix else 'FAIL'}] ConfigManager integration working")
    print(f"[{'PASS' if apn_method_fix else 'FAIL'}] get_property_by_apn method working")
    print(f"[{'PASS' if alias_fix else 'FAIL'}] get_property_details alias working")

    if config_fix and apn_method_fix and alias_fix:
        print(f"\n[SUCCESS] All critical DatabaseManager fixes are working correctly!")
    else:
        print(f"\n[WARNING] Some fixes may need attention")

    if 'error' in results:
        print(f"\nERROR DETAILS: {results['error']}")

    print("=" * 60)

if __name__ == "__main__":
    test_database_manager()