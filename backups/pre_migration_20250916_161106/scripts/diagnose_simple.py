#!/usr/bin/env python3
"""
Simple Tax and Sales History Data Flow Diagnostic

Tests the basic components of the tax and sales data flow.
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2
from psycopg2.extras import RealDictCursor

def test_database_connection():
    """Test basic database connection"""
    print("1. TESTING DATABASE CONNECTION...")

    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'maricopa_properties',
        'user': 'property_user',
        'password': 'Wildcats777!!'
    }

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()

        if result[0] == 1:
            print("   [PASS] Database connection successful")
            return True
        else:
            print("   [FAIL] Database connection failed - unexpected result")
            return False

    except Exception as e:
        print(f"   [FAIL] Database connection failed: {e}")
        return False

def check_tables_and_data(test_apn="11727002"):
    """Check if tables exist and contain data"""
    print(f"\n2. CHECKING TABLES AND DATA (APN: {test_apn})...")

    db_config = {
        'host': 'localhost',
        'port': 5433,
        'database': 'maricopa_properties',
        'user': 'property_user',
        'password': 'Wildcats777!!'
    }

    try:
        conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('tax_history', 'sales_history', 'properties')
            ORDER BY table_name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        print(f"   Tables found: {tables}")

        if 'properties' not in tables:
            print("   [FAIL] Properties table missing")
            return False
        if 'tax_history' not in tables:
            print("   [FAIL] Tax_history table missing")
            return False
        if 'sales_history' not in tables:
            print("   [FAIL] Sales_history table missing")
            return False

        print("   [PASS] All required tables exist")

        # Check data for test APN
        cursor.execute("SELECT COUNT(*) FROM properties WHERE apn = %s", (test_apn,))
        property_count = cursor.fetchone()[0]
        print(f"   Property records for APN {test_apn}: {property_count}")

        cursor.execute("SELECT COUNT(*) FROM tax_history WHERE apn = %s", (test_apn,))
        tax_count = cursor.fetchone()[0]
        print(f"   Tax records for APN {test_apn}: {tax_count}")

        cursor.execute("SELECT COUNT(*) FROM sales_history WHERE apn = %s", (test_apn,))
        sales_count = cursor.fetchone()[0]
        print(f"   Sales records for APN {test_apn}: {sales_count}")

        # Show sample data if exists
        if tax_count > 0:
            cursor.execute("SELECT tax_year, assessed_value, tax_amount FROM tax_history WHERE apn = %s ORDER BY tax_year DESC LIMIT 3", (test_apn,))
            tax_records = cursor.fetchall()
            print("   Sample tax records:")
            for record in tax_records:
                print(f"     - Year {record['tax_year']}: Assessed ${record.get('assessed_value', 'N/A')}, Tax ${record.get('tax_amount', 'N/A')}")

        if sales_count > 0:
            cursor.execute("SELECT sale_date, sale_price FROM sales_history WHERE apn = %s ORDER BY sale_date DESC LIMIT 3", (test_apn,))
            sales_records = cursor.fetchall()
            print("   Sample sales records:")
            for record in sales_records:
                print(f"     - {record['sale_date']}: ${record.get('sale_price', 'N/A')}")

        conn.close()
        return True

    except Exception as e:
        print(f"   [FAIL] Error checking tables: {e}")
        return False

def test_api_client():
    """Test if API client can be imported and has required methods"""
    print("\n3. TESTING API CLIENT...")

    try:
        from src.config_manager import ConfigManager
        from src.api_client import MaricopaAPIClient

        config_manager = ConfigManager()
        api_client = MaricopaAPIClient(config_manager)

        print("   [PASS] API Client imported successfully")

        # Check for required methods
        methods = ['get_tax_history', 'get_sales_history', 'get_tax_information']
        missing_methods = []

        for method in methods:
            if hasattr(api_client, method):
                print(f"   [PASS] Method {method} exists")
            else:
                print(f"   [FAIL] Method {method} missing")
                missing_methods.append(method)

        return len(missing_methods) == 0

    except ImportError as e:
        print(f"   [FAIL] Cannot import API client: {e}")
        return False
    except Exception as e:
        print(f"   [FAIL] Error testing API client: {e}")
        return False

def test_database_manager():
    """Test if database manager can be imported and has required methods"""
    print("\n4. TESTING DATABASE MANAGER...")

    try:
        from src.config_manager import ConfigManager
        from src.database_manager import DatabaseManager

        config_manager = ConfigManager()
        db_manager = DatabaseManager(config_manager)

        print("   [PASS] Database Manager imported successfully")

        # Check for required methods
        methods = ['get_tax_history', 'get_sales_history', 'insert_tax_history', 'insert_sales_history']
        missing_methods = []

        for method in methods:
            if hasattr(db_manager, method):
                print(f"   [PASS] Method {method} exists")
            else:
                print(f"   [FAIL] Method {method} missing")
                missing_methods.append(method)

        return len(missing_methods) == 0

    except ImportError as e:
        print(f"   [FAIL] Cannot import database manager: {e}")
        return False
    except Exception as e:
        print(f"   [FAIL] Error testing database manager: {e}")
        return False

def test_data_retrieval(test_apn="11727002"):
    """Test data retrieval through database manager"""
    print(f"\n5. TESTING DATA RETRIEVAL (APN: {test_apn})...")

    try:
        from src.config_manager import ConfigManager
        from src.database_manager import DatabaseManager

        config_manager = ConfigManager()
        db_manager = DatabaseManager(config_manager)

        # Test tax history retrieval
        tax_history = db_manager.get_tax_history(test_apn)
        print(f"   Tax history retrieval: {len(tax_history)} records")

        if tax_history:
            print("   Sample tax data:")
            for record in tax_history[:2]:
                print(f"     - Year {record.get('tax_year')}: ${record.get('assessed_value', 'N/A')}")

        # Test sales history retrieval
        sales_history = db_manager.get_sales_history(test_apn)
        print(f"   Sales history retrieval: {len(sales_history)} records")

        if sales_history:
            print("   Sample sales data:")
            for record in sales_history[:2]:
                print(f"     - {record.get('sale_date')}: ${record.get('sale_price', 'N/A')}")

        return len(tax_history) > 0 or len(sales_history) > 0

    except Exception as e:
        print(f"   [FAIL] Error testing data retrieval: {e}")
        return False

def test_insert_sample_data(test_apn="11727002"):
    """Test inserting and retrieving sample data"""
    print(f"\n6. TESTING SAMPLE DATA INSERTION (APN: {test_apn})...")

    try:
        from src.config_manager import ConfigManager
        from src.database_manager import DatabaseManager

        config_manager = ConfigManager()
        db_manager = DatabaseManager(config_manager)

        # Insert sample tax data
        sample_tax = {
            'apn': test_apn,
            'tax_year': 2024,
            'assessed_value': 999999.99,
            'limited_value': 888888.88,
            'tax_amount': 9999.99,
            'payment_status': 'TEST_DATA',
            'last_payment_date': '2024-01-01',
            'raw_data': {'test': True}
        }

        tax_inserted = db_manager.insert_tax_history(sample_tax)
        print(f"   Tax data insertion: {'SUCCESS' if tax_inserted else 'FAILED'}")

        # Insert sample sales data
        sample_sales = {
            'apn': test_apn,
            'sale_date': '2024-01-01',
            'sale_price': 999999.99,
            'seller_name': 'TEST SELLER',
            'buyer_name': 'TEST BUYER',
            'deed_type': 'TEST DEED',
            'recording_number': 'TEST123'
        }

        sales_inserted = db_manager.insert_sales_history(sample_sales)
        print(f"   Sales data insertion: {'SUCCESS' if sales_inserted else 'FAILED'}")

        # Test retrieval
        if tax_inserted or sales_inserted:
            tax_history = db_manager.get_tax_history(test_apn)
            sales_history = db_manager.get_sales_history(test_apn)

            print(f"   After insertion - Tax: {len(tax_history)}, Sales: {len(sales_history)}")

            # Clean up test data
            cleanup_test_data(test_apn)

            return tax_inserted and sales_inserted

        return False

    except Exception as e:
        print(f"   [FAIL] Error testing data insertion: {e}")
        return False

def cleanup_test_data(test_apn):
    """Clean up test data"""
    try:
        db_config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'maricopa_properties',
            'user': 'property_user',
            'password': 'Wildcats777!!'
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tax_history WHERE apn = %s AND payment_status = 'TEST_DATA'", (test_apn,))
        cursor.execute("DELETE FROM sales_history WHERE apn = %s AND recording_number = 'TEST123'", (test_apn,))

        conn.commit()
        conn.close()
        print("   [CLEANUP] Test data removed")

    except Exception as e:
        print(f"   [CLEANUP FAIL] {e}")

def main():
    print("=" * 50)
    print("TAX AND SALES DATA FLOW DIAGNOSTIC")
    print("=" * 50)

    test_apn = sys.argv[1] if len(sys.argv) > 1 else "11727002"

    results = []
    results.append(test_database_connection())
    results.append(check_tables_and_data(test_apn))
    results.append(test_api_client())
    results.append(test_database_manager())
    results.append(test_data_retrieval(test_apn))
    results.append(test_insert_sample_data(test_apn))

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All components working correctly!")
        print("Issue may be:")
        print("- Data collection not triggered for specific APNs")
        print("- UI not refreshing after data collection")
        print("- PropertyDetailsDialog not calling database methods")
    else:
        print(f"\n[ISSUE] {total - passed} component(s) failing")
        print("Check the failed components above")

if __name__ == "__main__":
    main()