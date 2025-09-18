#!/usr/bin/env python3
"""
Comprehensive DatabaseManager Test Suite
Tests all database functionality and ConfigManager integration
"""

import sys
import os
import traceback
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
    # MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
    from logging_config import get_logger, setup_logging
    import time
    import json
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager

    # Initialize logging
    setup_logging()
    logger = get_logger(__name__)

except ImportError as e:
    print(f"Import error: {e}")
    print("Current Python path:", sys.path)
    sys.exit(1)

class DatabaseManagerTester:
    """Comprehensive test suite for DatabaseManager"""

    def __init__(self):
        self.config_manager = None
        self.db_manager = None
        self.test_results = {
            'initialization': False,
            'connectivity': False,
            'property_operations': {},
            'tax_operations': {},
            'sales_operations': {},
            'performance': {},
            'errors': []
        }
        self.test_apn = "12345678"

    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 80)
        print("DATABASE MANAGER COMPREHENSIVE TEST SUITE")
        print("=" * 80)

        try:
            # Test 1: Initialization
            self.test_initialization()

            if self.test_results['initialization']:
                # Test 2: Connectivity
                self.test_connectivity()

                if self.test_results['connectivity']:
                    # Test 3: Property Operations
                    self.test_property_operations()

                    # Test 4: Tax Operations
                    self.test_tax_operations()

                    # Test 5: Sales Operations
                    self.test_sales_operations()

                    # Test 6: Performance Tests
                    self.test_performance()

                    # Test 7: CRUD Operations
                    self.test_crud_operations()

                else:
                    print("⚠️ Skipping database-dependent tests due to connectivity issues")
            else:
                print("❌ Skipping all tests due to initialization failure")

        except Exception as e:
            self.test_results['errors'].append(f"Test suite error: {str(e)}")
            print(f"❌ Test suite failed with error: {e}")
            traceback.print_exc()

        finally:
            self.cleanup()
            self.generate_report()

    def test_initialization(self):
        """Test 1ThreadSafeDatabaseManager initialization with ConfigManager"""
        print("\n[TEST 1] DatabaseManager Initialization")
        print("-" * 50)

        try:
            # Test ConfigManager creation
            print("Creating EnhancedConfigManager...")
            self.config_manager = EnhancedConfigManager()
            print(f"[PASS] ConfigManager created successfully")

            # Test database config retrieval
            db_config = self.config_manager.get_db_config()
            print(f"[PASS] Database config retrieved: {db_config.get('host')}:{db_config.get('port')}")

            # Test DatabaseManager creation with ConfigManager
            print("Creating DatabaseManager with EnhancedConfigManager...")
            self.db_manager = ThreadSafeDatabaseManager(self.config_manager)
            print("[PASS] DatabaseManager created successfully with ConfigManager integration")

            self.test_results['initialization'] = True

        except Exception as e:
            error_msg = f"Initialization failed: {str(e)}"
            self.test_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            traceback.print_exc()

    def test_connectivity(self):
        """Test 2: Database connectivity"""
        print("\n🔌 TEST 2: Database Connectivity")
        print("-" * 50)

        try:
            start_time = time.time()
            is_connected = self.db_manager.test_connection()
            connection_time = time.time() - start_time

            if is_connected:
                print(f"✅ Database connection successful ({connection_time:.3f}s)")
                self.test_results['connectivity'] = True
                self.test_results['performance']['connection_time'] = connection_time
            else:
                print("❌ Database connection failed")
                self.test_results['errors'].append("Database connection test failed")

        except Exception as e:
            error_msg = f"Connectivity test failed: {str(e)}"
            self.test_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")

    def test_property_operations(self):
        """Test 3: Property CRUD operations"""
        print("\n🏠 TEST 3: Property Operations")
        print("-" * 50)

        # Test data for property
        test_property = {
            'apn': self.test_apn,
            'owner_name': 'Test Owner',
            'property_address': '123 Test Street, Phoenix, AZ 85001',
            'mailing_address': '123 Test Street, Phoenix, AZ 85001',
            'legal_description': 'Test Legal Description',
            'land_use_code': 'R1',
            'year_built': 2000,
            'living_area_sqft': 1500,
            'lot_size_sqft': 7200,
            'bedrooms': 3,
            'bathrooms': 2,
            'pool': False,
            'garage_spaces': 2,
            'raw_data': {'test': 'data'}
        }

        try:
            # Test property insertion
            print(f"Inserting test property (APN: {self.test_apn})...")
            insert_result = self.db_manager.insert_property(test_property)
            print(f"✅ Property insertion: {'Success' if insert_result else 'Failed'}")
            self.test_results['property_operations']['insert'] = insert_result

            if insert_result:
                # Test property retrieval by APN (new method)
                print("Testing get_property_by_apn...")
                property_data = self.db_manager.get_property_by_apn(self.test_apn)
                if property_data and property_data.get('apn') == self.test_apn:
                    print(f"✅ get_property_by_apn successful")
                    self.test_results['property_operations']['get_by_apn'] = True
                else:
                    print(f"❌ get_property_by_apn failed")
                    self.test_results['property_operations']['get_by_apn'] = False

                # Test property details retrieval (alias method)
                print("Testing get_property_details (alias)...")
                property_details = self.db_manager.get_property_details(self.test_apn)
                if property_details and property_details.get('apn') == self.test_apn:
                    print(f"✅ get_property_details successful")
                    self.test_results['property_operations']['get_details'] = True
                else:
                    print(f"❌ get_property_details failed")
                    self.test_results['property_operations']['get_details'] = False

                # Test search operations
                print("Testing search by owner...")
                owner_search = self.db_manager.search_properties_by_owner('Test Owner')
                print(f"✅ Owner search returned {len(owner_search)} results")
                self.test_results['property_operations']['search_owner'] = len(owner_search) > 0

                print("Testing search by address...")
                address_search = self.db_manager.search_properties_by_address('Test Street')
                print(f"✅ Address search returned {len(address_search)} results")
                self.test_results['property_operations']['search_address'] = len(address_search) > 0

        except Exception as e:
            error_msg = f"Property operations test failed: {str(e)}"
            self.test_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")

    def test_tax_operations(self):
        """Test 4: Tax history operations"""
        print("\n💰 TEST 4: Tax History Operations")
        print("-" * 50)

        test_tax_data = {
            'apn': self.test_apn,
            'tax_year': 2023,
            'assessed_value': 250000,
            'limited_value': 240000,
            'tax_amount': 3500.00,
            'payment_status': 'Paid',
            'last_payment_date': '2023-12-15',
            'raw_data': {'test': 'tax_data'}
        }

        try:
            # Test tax history insertion
            print(f"Inserting tax history for APN {self.test_apn}...")
            tax_insert = self.db_manager.insert_tax_history(test_tax_data)
            print(f"✅ Tax history insertion: {'Success' if tax_insert else 'Failed'}")
            self.test_results['tax_operations']['insert'] = tax_insert

            if tax_insert:
                # Test tax history retrieval
                print("Retrieving tax history...")
                tax_history = self.db_manager.get_tax_history(self.test_apn)
                print(f"✅ Tax history retrieval: {len(tax_history)} records found")
                self.test_results['tax_operations']['retrieve'] = len(tax_history) > 0

                if tax_history:
                    latest_tax = tax_history[0]
                    print(f"   Latest tax year: {latest_tax.get('tax_year')}")
                    print(f"   Assessed value: ${latest_tax.get('assessed_value'):,}")

        except Exception as e:
            error_msg = f"Tax operations test failed: {str(e)}"
            self.test_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")

    def test_sales_operations(self):
        """Test 5: Sales history operations"""
        print("\n🏷️ TEST 5: Sales History Operations")
        print("-" * 50)

        test_sales_data = {
            'apn': self.test_apn,
            'sale_date': '2023-06-15',
            'sale_price': 275000,
            'seller_name': 'Previous Owner',
            'buyer_name': 'Test Owner',
            'deed_type': 'Warranty Deed',
            'recording_number': 'REC2023001234'
        }

        try:
            # Test sales history insertion
            print(f"Inserting sales history for APN {self.test_apn}...")
            sales_insert = self.db_manager.insert_sales_history(test_sales_data)
            print(f"✅ Sales history insertion: {'Success' if sales_insert else 'Failed'}")
            self.test_results['sales_operations']['insert'] = sales_insert

            if sales_insert:
                # Test sales history retrieval
                print("Retrieving sales history...")
                sales_history = self.db_manager.get_sales_history(self.test_apn)
                print(f"✅ Sales history retrieval: {len(sales_history)} records found")
                self.test_results['sales_operations']['retrieve'] = len(sales_history) > 0

                if sales_history:
                    latest_sale = sales_history[0]
                    print(f"   Sale date: {latest_sale.get('sale_date')}")
                    print(f"   Sale price: ${latest_sale.get('sale_price'):,}")

        except Exception as e:
            error_msg = f"Sales operations test failed: {str(e)}"
            self.test_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")

    def test_performance(self):
        """Test 6: Database performance metrics"""
        print("\n⚡ TEST 6: Performance Testing")
        print("-" * 50)

        try:
            # Test database statistics
            start_time = time.time()
            stats = self.db_manager.get_database_stats()
            stats_time = time.time() - start_time

            print(f"✅ Database statistics retrieved ({stats_time:.3f}s):")
            for key, value in stats.items():
                print(f"   {key}: {value:,}")

            self.test_results['performance']['stats_time'] = stats_time
            self.test_results['performance']['database_stats'] = stats

            # Test connection pool stability
            print("Testing connection pool stability...")
            connection_tests = []
            for i in range(5):
                start = time.time()
                result = self.db_manager.test_connection()
                duration = time.time() - start
                connection_tests.append(duration)

            avg_connection_time = sum(connection_tests) / len(connection_tests)
            print(f"✅ Average connection time over 5 tests: {avg_connection_time:.3f}s")
            self.test_results['performance']['avg_connection_time'] = avg_connection_time

        except Exception as e:
            error_msg = f"Performance test failed: {str(e)}"
            self.test_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")

    def test_crud_operations(self):
        """Test 7: Complete CRUD operations"""
        print("\n🔄 TEST 7: CRUD Operations Verification")
        print("-" * 50)

        try:
            # CREATE (already tested in property operations)
            create_success = self.test_results['property_operations'].get('insert', False)
            print(f"✅ CREATE operation: {'Success' if create_success else 'Failed'}")

            # READ (already tested)
            read_success = self.test_results['property_operations'].get('get_by_apn', False)
            print(f"✅ READ operation: {'Success' if read_success else 'Failed'}")

            # UPDATE (test updating existing property)
            if create_success:
                updated_property = {
                    'apn': self.test_apn,
                    'owner_name': 'Updated Test Owner',
                    'property_address': '123 Test Street, Phoenix, AZ 85001',
                    'year_built': 2001  # Updated year
                }

                update_result = self.db_manager.insert_property(updated_property)  # Uses upsert
                if update_result:
                    # Verify update
                    updated_data = self.db_manager.get_property_by_apn(self.test_apn)
                    if updated_data and updated_data.get('owner_name') == 'Updated Test Owner':
                        print(f"✅ UPDATE operation: Success")
                        self.test_results['property_operations']['update'] = True
                    else:
                        print(f"❌ UPDATE operation: Failed to verify update")
                        self.test_results['property_operations']['update'] = False
                else:
                    print(f"❌ UPDATE operation: Failed")
                    self.test_results['property_operations']['update'] = False

            # DELETE is not implemented in current schema, but we can test search analytics
            print("Testing search analytics logging...")
            self.db_manager.log_search('apn', self.test_apn, 1, '127.0.0.1')
            print(f"✅ Analytics logging: Success")

        except Exception as e:
            error_msg = f"CRUD operations test failed: {str(e)}"
            self.test_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")

    def cleanup(self):
        """Clean up test resources"""
        try:
            if self.db_manager:
                self.db_manager.close()
                print("\n🧹 Database connections closed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 80)

        # Summary statistics
        total_tests = 0
        passed_tests = 0

        print("\n📊 TEST RESULTS SUMMARY:")
        print("-" * 30)

        if self.test_results['initialization']:
            print("✅ DatabaseManager Initialization: PASSED")
            passed_tests += 1
        else:
            print("❌ DatabaseManager Initialization: FAILED")
        total_tests += 1

        if self.test_results['connectivity']:
            print("✅ Database Connectivity: PASSED")
            passed_tests += 1
        else:
            print("❌ Database Connectivity: FAILED")
        total_tests += 1

        # Property operations
        prop_ops = self.test_results['property_operations']
        prop_passed = sum(1 for v in prop_ops.values() if v is True)
        prop_total = len(prop_ops)
        if prop_total > 0:
            print(f"🏠 Property Operations: {prop_passed}/{prop_total} PASSED")
            total_tests += prop_total
            passed_tests += prop_passed

        # Tax operations
        tax_ops = self.test_results['tax_operations']
        tax_passed = sum(1 for v in tax_ops.values() if v is True)
        tax_total = len(tax_ops)
        if tax_total > 0:
            print(f"💰 Tax Operations: {tax_passed}/{tax_total} PASSED")
            total_tests += tax_total
            passed_tests += tax_passed

        # Sales operations
        sales_ops = self.test_results['sales_operations']
        sales_passed = sum(1 for v in sales_ops.values() if v is True)
        sales_total = len(sales_ops)
        if sales_total > 0:
            print(f"🏷️ Sales Operations: {sales_passed}/{sales_total} PASSED")
            total_tests += sales_total
            passed_tests += sales_passed

        print(f"\n📈 OVERALL SCORE: {passed_tests}/{total_tests} ({(passed_tests/total_tests*100):.1f}%)")

        # Performance metrics
        perf = self.test_results['performance']
        if perf:
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"   Connection Time: {perf.get('connection_time', 0):.3f}s")
            print(f"   Stats Query Time: {perf.get('stats_time', 0):.3f}s")
            print(f"   Avg Connection Time (5 tests): {perf.get('avg_connection_time', 0):.3f}s")

        # Key fixes verification
        print(f"\n🔧 KEY FIXES VERIFICATION:")
        print("-" * 30)

        config_integration = self.test_results['initialization']
        print(f"✅ ConfigManager Integration: {'WORKING' if config_integration else 'FAILED'}")

        apn_method_fix = self.test_results['property_operations'].get('get_by_apn', False)
        print(f"✅ get_property_by_apn Method: {'WORKING' if apn_method_fix else 'FAILED'}")

        alias_method = self.test_results['property_operations'].get('get_details', False)
        print(f"✅ get_property_details Alias: {'WORKING' if alias_method else 'FAILED'}")

        # Error summary
        if self.test_results['errors']:
            print(f"\n❌ ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"   {i}. {error}")
        else:
            print(f"\n✅ NO ERRORS ENCOUNTERED")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 20)

        if not self.test_results['initialization']:
            print("   • Fix ConfigManager integration issues")

        if not self.test_results['connectivity']:
            print("   • Check database connection settings in config.ini")
            print("   • Verify PostgreSQL service is running")

        if len(self.test_results['errors']) > 0:
            print("   • Review error logs for detailed troubleshooting")

        if passed_tests == total_tests:
            print("   • 🎉 All tests passed! DatabaseManager is working correctly.")

        print("\n" + "=" * 80)

def main():
    """Main test execution function"""
    tester = DatabaseManagerTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()