#!/usr/bin/env python
"""
Check tax history records in database
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database_manager import DatabaseManager

from config_manager import ConfigManager


def check_tax_history_records():
    """Check what tax history records exist in database"""
    print("Tax History Records Check")
    print("=" * 40)

    config = ConfigManager()
    db_manager = DatabaseManager(config)

    test_apn = "13304014A"

    try:
        # Get tax history records
        tax_records = db_manager.get_tax_history(test_apn)

        print(f"Tax history records for APN: {test_apn}")
        print(f"Total records found: {len(tax_records)}")
        print("-" * 30)

        if tax_records:
            for record in tax_records:
                print(f"Year: {record.get('tax_year')}")

                assessed_value = record.get("assessed_value")
                assessed_text = (
                    f"${assessed_value:,.2f}" if assessed_value is not None else "None"
                )
                print(f"  Assessed Value: {assessed_text}")

                limited_value = record.get("limited_value")
                limited_text = (
                    f"${limited_value:,.2f}" if limited_value is not None else "None"
                )
                print(f"  Limited Value: {limited_text}")

                tax_amount = record.get("tax_amount")
                tax_text = f"${tax_amount:,.2f}" if tax_amount is not None else "None"
                print(f"  Tax Amount: {tax_text}")

                print(f"  Payment Status: {record.get('payment_status') or 'None'}")
                print(
                    f"  Last Payment Date: {record.get('last_payment_date') or 'None'}"
                )
                print()
        else:
            print("No tax history records found!")

        # Also check what's in the properties table for tax info
        property_record = db_manager.get_property_by_apn(test_apn)
        if property_record:
            print("Properties table tax fields:")
            print(f"  latest_tax_year: {property_record.get('latest_tax_year')}")
            print(
                f"  latest_assessed_value: {property_record.get('latest_assessed_value')}"
            )
            print(f"  latest_tax_amount: {property_record.get('latest_tax_amount')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        db_manager.close()


if __name__ == "__main__":
    check_tax_history_records()
