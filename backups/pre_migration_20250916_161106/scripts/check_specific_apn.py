#!/usr/bin/env python3
"""
Check specific APN data flow
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2
from psycopg2.extras import RealDictCursor

def check_apn_comprehensive(test_apn):
    """Check comprehensive data for specific APN"""

    print(f"COMPREHENSIVE CHECK FOR APN: {test_apn}")
    print("=" * 50)

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

        # Check if property exists
        cursor.execute("SELECT * FROM properties WHERE apn = %s", (test_apn,))
        property_record = cursor.fetchone()

        if property_record:
            print(f"✅ Property exists in database")
            print(f"   Owner: {property_record.get('owner_name', 'Unknown')}")
            print(f"   Address: {property_record.get('property_address', 'Unknown')}")
            print(f"   Last Updated: {property_record.get('last_updated', 'Unknown')}")
        else:
            print(f"❌ Property NOT found in database")
            conn.close()
            return

        # Check tax history
        cursor.execute("SELECT * FROM tax_history WHERE apn = %s ORDER BY tax_year DESC", (test_apn,))
        tax_records = cursor.fetchall()
        print(f"\n📊 Tax History: {len(tax_records)} records")

        for record in tax_records[:3]:
            print(f"   - {record['tax_year']}: ${record.get('assessed_value', 'N/A')} assessed, ${record.get('tax_amount', 'N/A')} tax")

        # Check sales history
        cursor.execute("SELECT * FROM sales_history WHERE apn = %s ORDER BY sale_date DESC", (test_apn,))
        sales_records = cursor.fetchall()
        print(f"\n🏠 Sales History: {len(sales_records)} records")

        for record in sales_records[:3]:
            print(f"   - {record['sale_date']}: ${record.get('sale_price', 'N/A')} ({record.get('deed_type', 'Unknown')})")

        conn.close()

        # Now test API data collection
        print(f"\n🔍 Testing API data collection for APN: {test_apn}")

        from src.config_manager import ConfigManager
        from src.api_client import MaricopaAPIClient

        config_manager = ConfigManager()
        api_client = MaricopaAPIClient(config_manager)

        print("Getting tax history from API...")
        try:
            api_tax_history = api_client.get_tax_history(test_apn, years=3)
            print(f"   API returned {len(api_tax_history) if api_tax_history else 0} tax records")

            if api_tax_history:
                for record in api_tax_history[:2]:
                    print(f"   - Year {record.get('TaxYear', 'Unknown')}: ${record.get('FullCashValue', 'N/A')}")
        except Exception as e:
            print(f"   ❌ API tax collection failed: {e}")

        print("\nGetting sales history from API...")
        try:
            # Note: This might take time as it does web scraping
            print("   (Skipping sales API call to avoid delay - uses web scraping)")
            # api_sales_history = api_client.get_sales_history(test_apn, years=3)
            # print(f"   API returned {len(api_sales_history) if api_sales_history else 0} sales records")
        except Exception as e:
            print(f"   ❌ API sales collection failed: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_apn = sys.argv[1] if len(sys.argv) > 1 else "13304019"
    check_apn_comprehensive(test_apn)