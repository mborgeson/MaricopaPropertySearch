#!/usr/bin/env python3
"""
Tax and Sales History Data Flow Diagnostic Script

This script systematically investigates why tax and sales history are not displaying
in the PropertyDetailsDialog by checking each step of the data flow:

1. API Client Methods (tax/sales fetching)
2. Database Storage (tax/sales tables)
3. Database Manager Methods (retrieval)
4. UI Display (PropertyDetailsDialog)

Usage: python diagnose_tax_sales_data_flow.py <apn>
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging for diagnosis
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "logs" / "diagnosis.log"),
    ],
)

logger = logging.getLogger(__name__)


class TaxSalesDataFlowDiagnostic:
    """Comprehensive diagnostic tool for tax and sales data flow"""

    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5433,
            "database": "maricopa_properties",
            "user": "property_user",
            "password": "Wildcats777!!",
        }
        self.test_results = {
            "database_connection": False,
            "tables_exist": False,
            "api_methods_exist": False,
            "db_manager_methods_exist": False,
            "sample_data_retrieval": False,
            "ui_methods_exist": False,
        }

    def run_comprehensive_diagnosis(self, test_apn: str = "11727002"):
        """Run complete diagnostic for tax and sales data flow"""

        print("=" * 60)
        print("TAX AND SALES HISTORY DATA FLOW DIAGNOSIS")
        print("=" * 60)
        print(f"Test APN: {test_apn}")
        print("=" * 60)

        # Step 1: Test database connection
        print("\n1. TESTING DATABASE CONNECTION...")
        self.test_database_connection()

        # Step 2: Verify table structure
        print("\n2. CHECKING TABLE STRUCTURE...")
        self.check_table_structure()

        # Step 3: Check existing data in tables
        print("\n3. CHECKING EXISTING DATA...")
        self.check_existing_data(test_apn)

        # Step 4: Test API client methods
        print("\n4. TESTING API CLIENT METHODS...")
        self.test_api_client_methods(test_apn)

        # Step 5: Test database manager methods
        print("\n5. TESTING DATABASE MANAGER METHODS...")
        self.test_database_manager_methods(test_apn)

        # Step 6: Test data insertion
        print("\n6. TESTING DATA INSERTION...")
        self.test_data_insertion(test_apn)

        # Step 7: Test UI methods exist
        print("\n7. CHECKING UI METHODS...")
        self.check_ui_methods()

        # Final analysis
        print("\n" + "=" * 60)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 60)
        self.print_summary()

    def test_database_connection(self):
        """Test database connectivity"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()

            if result[0] == 1:
                print("✅ Database connection successful")
                self.test_results["database_connection"] = True
            else:
                print("❌ Database connection failed - unexpected result")

        except Exception as e:
            print(f"❌ Database connection failed: {e}")

    def check_table_structure(self):
        """Check if required tables exist with correct structure"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Check if tables exist
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('tax_history', 'sales_history', 'properties')
                ORDER BY table_name
            """
            )

            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ["properties", "tax_history", "sales_history"]
            missing_tables = [table for table in required_tables if table not in tables]

            if not missing_tables:
                print("✅ All required tables exist:", tables)
                self.test_results["tables_exist"] = True
            else:
                print(f"❌ Missing tables: {missing_tables}")
                print(f"   Existing tables: {tables}")

            # Check table structures
            for table in ["tax_history", "sales_history"]:
                if table in tables:
                    cursor.execute(
                        f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = '{table}'
                        ORDER BY ordinal_position
                    """
                    )

                    columns = cursor.fetchall()
                    print(f"\n   {table.upper()} table structure:")
                    for col_name, data_type, nullable in columns:
                        print(
                            f"     - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})"
                        )

            conn.close()

        except Exception as e:
            print(f"❌ Error checking table structure: {e}")

    def check_existing_data(self, apn: str):
        """Check if any data exists for the test APN"""
        try:
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            cursor = conn.cursor()

            # Check property exists
            cursor.execute("SELECT COUNT(*) FROM properties WHERE apn = %s", (apn,))
            property_count = cursor.fetchone()[0]
            print(f"   Properties for APN {apn}: {property_count}")

            # Check tax history
            cursor.execute("SELECT COUNT(*) FROM tax_history WHERE apn = %s", (apn,))
            tax_count = cursor.fetchone()[0]
            print(f"   Tax records for APN {apn}: {tax_count}")

            if tax_count > 0:
                cursor.execute(
                    "SELECT tax_year, assessed_value, tax_amount FROM tax_history WHERE apn = %s ORDER BY tax_year DESC LIMIT 3",
                    (apn,),
                )
                tax_records = cursor.fetchall()
                print("   Recent tax records:")
                for record in tax_records:
                    print(
                        f"     - Year {record['tax_year']}: Assessed ${record.get('assessed_value', 'N/A')}, Tax ${record.get('tax_amount', 'N/A')}"
                    )

            # Check sales history
            cursor.execute("SELECT COUNT(*) FROM sales_history WHERE apn = %s", (apn,))
            sales_count = cursor.fetchone()[0]
            print(f"   Sales records for APN {apn}: {sales_count}")

            if sales_count > 0:
                cursor.execute(
                    "SELECT sale_date, sale_price, seller_name FROM sales_history WHERE apn = %s ORDER BY sale_date DESC LIMIT 3",
                    (apn,),
                )
                sales_records = cursor.fetchall()
                print("   Recent sales records:")
                for record in sales_records:
                    print(
                        f"     - {record['sale_date']}: ${record.get('sale_price', 'N/A')} from {record.get('seller_name', 'Unknown')}"
                    )

            conn.close()

            if tax_count > 0 or sales_count > 0:
                print("✅ Some historical data exists in database")
            else:
                print("⚠️  No historical data found for this APN")

        except Exception as e:
            print(f"❌ Error checking existing data: {e}")

    def test_api_client_methods(self, apn: str):
        """Test if API client methods exist and can be called"""
        try:
            from src.api_client import MaricopaAPIClient
            from src.config_manager import ConfigManager

            config_manager = ConfigManager()
            api_client = MaricopaAPIClient(config_manager)

            print("✅ API Client initialized successfully")

            # Check if tax and sales methods exist
            methods_to_check = [
                "get_tax_history",
                "get_sales_history",
                "get_tax_information",
                "_scrape_tax_data_sync",
                "_scrape_sales_data_sync",
            ]

            existing_methods = []
            missing_methods = []

            for method_name in methods_to_check:
                if hasattr(api_client, method_name):
                    existing_methods.append(method_name)
                    print(f"   ✅ {method_name} method exists")
                else:
                    missing_methods.append(method_name)
                    print(f"   ❌ {method_name} method missing")

            if not missing_methods:
                self.test_results["api_methods_exist"] = True

                # Test calling the methods (without actually scraping)
                print(f"\n   Testing method calls for APN {apn}:")

                try:
                    # Test get_tax_history (API endpoint)
                    tax_result = api_client.get_tax_history(apn, years=2)
                    print(
                        f"   📊 get_tax_history returned {len(tax_result) if tax_result else 0} records"
                    )

                    # Test get_sales_history (scraper-based)
                    # sales_result = api_client.get_sales_history(apn, years=2)  # Skip to avoid long scraping
                    # print(f"   📊 get_sales_history returned {len(sales_result) if sales_result else 0} records")
                    print(
                        "   ⏭️  Skipping sales history test to avoid long scraping delay"
                    )

                except Exception as method_error:
                    print(f"   ⚠️  Error calling API methods: {method_error}")

        except ImportError as e:
            print(f"❌ Cannot import API client: {e}")
        except Exception as e:
            print(f"❌ Error testing API client: {e}")

    def test_database_manager_methods(self, apn: str):
        """Test database manager methods for tax and sales data"""
        try:
            from src.config_manager import ConfigManager
            from src.database_manager import DatabaseManager

            config_manager = ConfigManager()
            db_manager = DatabaseManager(config_manager)

            print("✅ Database Manager initialized successfully")

            # Check if required methods exist
            methods_to_check = [
                "get_tax_history",
                "get_sales_history",
                "insert_tax_history",
                "insert_sales_history",
            ]

            existing_methods = []
            missing_methods = []

            for method_name in methods_to_check:
                if hasattr(db_manager, method_name):
                    existing_methods.append(method_name)
                    print(f"   ✅ {method_name} method exists")
                else:
                    missing_methods.append(method_name)
                    print(f"   ❌ {method_name} method missing")

            if not missing_methods:
                self.test_results["db_manager_methods_exist"] = True

                # Test method calls
                print(f"\n   Testing method calls for APN {apn}:")

                try:
                    # Test retrieval methods
                    tax_history = db_manager.get_tax_history(apn)
                    print(f"   📊 get_tax_history returned {len(tax_history)} records")

                    sales_history = db_manager.get_sales_history(apn)
                    print(
                        f"   📊 get_sales_history returned {len(sales_history)} records"
                    )

                    if len(tax_history) > 0 or len(sales_history) > 0:
                        self.test_results["sample_data_retrieval"] = True

                except Exception as method_error:
                    print(
                        f"   ⚠️  Error calling database manager methods: {method_error}"
                    )

        except ImportError as e:
            print(f"❌ Cannot import database manager: {e}")
        except Exception as e:
            print(f"❌ Error testing database manager: {e}")

    def test_data_insertion(self, apn: str):
        """Test inserting sample data to verify the flow works"""
        try:
            from src.config_manager import ConfigManager
            from src.database_manager import DatabaseManager

            config_manager = ConfigManager()
            db_manager = DatabaseManager(config_manager)

            print("📝 Testing data insertion with sample data...")

            # Insert sample tax record
            sample_tax_data = {
                "apn": apn,
                "tax_year": 2024,
                "assessed_value": 250000.00,
                "limited_value": 225000.00,
                "tax_amount": 2750.00,
                "payment_status": "PAID",
                "last_payment_date": "2024-01-15",
                "raw_data": {"test": "diagnostic_data"},
            }

            tax_inserted = db_manager.insert_tax_history(sample_tax_data)
            print(
                f"   {'✅' if tax_inserted else '❌'} Sample tax record insertion: {'SUCCESS' if tax_inserted else 'FAILED'}"
            )

            # Insert sample sales record
            sample_sales_data = {
                "apn": apn,
                "sale_date": "2023-06-15",
                "sale_price": 275000.00,
                "seller_name": "Test Seller",
                "buyer_name": "Test Buyer",
                "deed_type": "Warranty Deed",
                "recording_number": "TEST123456",
            }

            sales_inserted = db_manager.insert_sales_history(sample_sales_data)
            print(
                f"   {'✅' if sales_inserted else '❌'} Sample sales record insertion: {'SUCCESS' if sales_inserted else 'FAILED'}"
            )

            # Verify retrieval after insertion
            if tax_inserted or sales_inserted:
                print("\n   Verifying retrieval after insertion:")

                retrieved_tax = db_manager.get_tax_history(apn)
                print(f"   📊 Retrieved {len(retrieved_tax)} tax records")

                retrieved_sales = db_manager.get_sales_history(apn)
                print(f"   📊 Retrieved {len(retrieved_sales)} sales records")

                if len(retrieved_tax) > 0 and len(retrieved_sales) > 0:
                    print("   ✅ Data insertion and retrieval working correctly")
                    self.test_results["sample_data_retrieval"] = True

                    # Clean up test data
                    self._cleanup_test_data(apn)

        except Exception as e:
            print(f"❌ Error testing data insertion: {e}")

    def _cleanup_test_data(self, apn: str):
        """Clean up diagnostic test data"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Remove test records
            cursor.execute(
                "DELETE FROM tax_history WHERE apn = %s AND tax_year = 2024", (apn,)
            )
            cursor.execute(
                "DELETE FROM sales_history WHERE apn = %s AND recording_number = 'TEST123456'",
                (apn,),
            )

            conn.commit()
            conn.close()
            print("   🧹 Cleaned up diagnostic test data")

        except Exception as e:
            print(f"   ⚠️  Could not clean up test data: {e}")

    def check_ui_methods(self):
        """Check if UI methods exist for displaying data"""
        try:
            # Try to import the UI module
            gui_file = PROJECT_ROOT / "src" / "gui" / "enhanced_main_window.py"

            if gui_file.exists():
                print("✅ UI file exists")

                # Check for key methods in the file
                with open(gui_file, "r", encoding="utf-8") as f:
                    content = f.read()

                required_ui_methods = [
                    "populate_tax_table",
                    "populate_sales_table",
                    "setup_tax_history_tab",
                    "setup_sales_history_tab",
                    "load_property_details",
                ]

                existing_ui_methods = []
                missing_ui_methods = []

                for method in required_ui_methods:
                    if f"def {method}" in content:
                        existing_ui_methods.append(method)
                        print(f"   ✅ {method} found in UI")
                    else:
                        missing_ui_methods.append(method)
                        print(f"   ❌ {method} missing in UI")

                if not missing_ui_methods:
                    self.test_results["ui_methods_exist"] = True
            else:
                print("❌ UI file not found")

        except Exception as e:
            print(f"❌ Error checking UI methods: {e}")

    def print_summary(self):
        """Print diagnostic summary and recommendations"""

        print("\nTEST RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")

        # Determine likely issues
        print("\nLIKELY ISSUES IDENTIFIED:")

        if not self.test_results["database_connection"]:
            print("🚨 DATABASE CONNECTION ISSUE")
            print("   - Check PostgreSQL is running on port 5433")
            print("   - Verify database credentials")
            print("   - Ensure maricopa_properties database exists")

        elif not self.test_results["tables_exist"]:
            print("🚨 DATABASE SCHEMA ISSUE")
            print("   - Run setup_database_tables.py to create missing tables")
            print("   - Check database permissions for property_user")

        elif not self.test_results["api_methods_exist"]:
            print("🚨 API CLIENT ISSUE")
            print("   - Tax/sales methods missing from MaricopaAPIClient")
            print("   - Check tax_scraper.py and recorder_scraper.py exist")
            print("   - Verify Playwright dependencies installed")

        elif not self.test_results["db_manager_methods_exist"]:
            print("🚨 DATABASE MANAGER ISSUE")
            print("   - Tax/sales methods missing from DatabaseManager")
            print("   - Check database_manager.py implementation")

        elif not self.test_results["sample_data_retrieval"]:
            print("⚠️  DATA FLOW ISSUE")
            print("   - Data is not being stored or retrieved properly")
            print("   - Check logging for insertion/retrieval errors")
            print("   - Verify data collection processes are running")

        elif not self.test_results["ui_methods_exist"]:
            print("🚨 USER INTERFACE ISSUE")
            print("   - UI methods missing from PropertyDetailsDialog")
            print("   - Check enhanced_main_window.py implementation")

        else:
            print("🤔 ALL TESTS PASS BUT DATA NOT SHOWING")
            print("   - Data collection may not have been triggered")
            print("   - Check background data collection service")
            print("   - Verify PropertyDetailsDialog calls database correctly")
            print("   - Check logs for runtime errors")

        print("\nRECOMMENDED ACTIONS:")
        print("1. Run this diagnostic on a known APN with expected data")
        print("2. Check logs directory for detailed error messages")
        print("3. Manually trigger data collection for test APN")
        print("4. Verify PropertyDetailsDialog refreshes after data collection")
        print("5. Test with both API and scraping data sources")


def main():
    """Main diagnostic function"""

    # Get APN from command line or use default
    test_apn = sys.argv[1] if len(sys.argv) > 1 else "11727002"

    # Ensure logs directory exists
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Run diagnosis
    diagnostic = TaxSalesDataFlowDiagnostic()
    diagnostic.run_comprehensive_diagnosis(test_apn)

    print(f"\n📋 Detailed logs written to: {logs_dir / 'diagnosis.log'}")
    print(
        "💡 Use this information to identify and fix the root cause of missing tax/sales history"
    )


if __name__ == "__main__":
    main()
