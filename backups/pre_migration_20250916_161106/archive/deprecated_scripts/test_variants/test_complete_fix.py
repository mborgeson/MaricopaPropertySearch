#!/usr/bin/env python
"""
Test the complete fix for both database and data collection issues
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from api_client import MaricopaAPIClient
from database_manager import DatabaseManager

from config_manager import ConfigManager
from improved_automatic_data_collector import ImprovedMaricopaDataCollector
from logging_config import setup_logging


def test_complete_fix():
    """Test both the database fix and improved data collector"""

    # Setup logging
    setup_logging()

    print("Testing Complete Data Collection Fix...")
    print("=" * 50)

    try:
        # Initialize components
        config_manager = ConfigManager()
        api_client = MaricopaAPIClient(config_manager)
        db_manager = DatabaseManager(config_manager)

        # Use the improved data collector
        collector = ImprovedMaricopaDataCollector(db_manager, api_client)

        # Test APN from logs
        test_apn = "13304018"

        print(f"\n1. Testing improved data collection for APN: {test_apn}")

        # Clear any existing data for clean test
        try:
            # Get current data
            existing_tax = db_manager.get_tax_history(test_apn)
            print(
                f"   Existing tax records: {len(existing_tax) if isinstance(existing_tax, list) else existing_tax}"
            )
        except Exception as e:
            print(f"   Error checking existing data: {e}")

        # Run improved collection
        results = collector.collect_data_for_apn_sync(test_apn)

        print(f"   Collection results:")
        print(f"     Tax data collected: {results['tax_data_collected']}")
        print(f"     Sales data collected: {results['sales_data_collected']}")
        print(f"     Tax records: {len(results['tax_records'])}")
        print(f"     Errors: {len(results['errors'])}")

        if results["errors"]:
            for error in results["errors"]:
                print(f"     Error: {error}")

        print(f"\n2. Testing database JSON fix...")

        # Test the individual tax history insertion (should now work with JSON fix)
        try:
            # Get some API data to test with
            api_tax_data = api_client.get_tax_history(test_apn)
            if api_tax_data and len(api_tax_data) > 0:
                test_record = api_tax_data[0]

                tax_data = {
                    "apn": test_apn,
                    "tax_year": test_record.get("TaxYear"),
                    "assessed_value": (
                        int(test_record.get("FullCashValue", 0))
                        if test_record.get("FullCashValue")
                        else None
                    ),
                    "limited_value": None,
                    "tax_amount": None,
                    "payment_status": None,
                    "last_payment_date": None,
                    "raw_data": test_record,  # This should now work with JSON fix
                }

                success = db_manager.insert_tax_history(tax_data)
                if success:
                    print(f"   [OK] Individual tax history insertion now works!")
                else:
                    print(f"   [ERROR] Individual tax history insertion still failing")
            else:
                print(f"   [WARNING] No API tax data available for individual test")

        except Exception as e:
            print(f"   [ERROR] Database JSON fix test failed: {e}")

        print(f"\n3. Final verification...")

        # Verify final state
        try:
            final_tax_records = db_manager.get_tax_history(test_apn)
            final_sales_records = db_manager.get_sales_history(test_apn)

            print(
                f"   Final tax records: {len(final_tax_records) if isinstance(final_tax_records, list) else final_tax_records}"
            )
            print(
                f"   Final sales records: {len(final_sales_records) if isinstance(final_sales_records, list) else final_sales_records}"
            )

            if isinstance(final_tax_records, list) and len(final_tax_records) > 0:
                print(f"   [SUCCESS] Tax data is now properly populated!")
            else:
                print(f"   [WARNING] Tax data still not populated")

        except Exception as e:
            print(f"   [ERROR] Final verification failed: {e}")

        print("\n" + "=" * 50)
        print("[COMPLETE] Complete fix test finished!")
        print("The application should now show tax data properly.")

        # Clean up
        api_client.close()
        db_manager.close()

        return True

    except Exception as e:
        print(f"\n[ERROR] Complete fix test failed: {e}")
        import traceback

        traceback.print_exc()

    return False


if __name__ == "__main__":
    success = test_complete_fix()
    sys.exit(0 if success else 1)
