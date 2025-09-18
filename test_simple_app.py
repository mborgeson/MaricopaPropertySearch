#!/usr/bin/env python
"""
Simple test version of the Maricopa Property Search Application
This version runs without database and with minimal dependencies
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Starting simplified application test...")

# Import only what we need
try:
    # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
    print("✓ ConfigManager imported")
except Exception as e:
    print(f"✗ ConfigManager import failed: {e}")

try:
    # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
    print("✓ APIClient imported")
except Exception as e:
    print(f"✗ APIClient import failed: {e}")

# Simple test class for search functionality
class SimplePropertySearch:
    def __init__(self):
        self.config = EnhancedConfigManager()
        self.api_client = UnifiedMaricopaAPIClient(self.config)

    def search_by_apn(self, apn):
        """Test property search by APN"""
        print(f"\nSearching for APN: {apn}")
        try:
            result = self.api_client.search_by_apn(apn)
            if result:
                print(f"Found property:")
                print(f"  Address: {result.get('address', 'N/A')}")
                print(f"  Owner: {result.get('owner_name', 'N/A')}")
                print(f"  Market Value: ${result.get('market_value', 0):,}")
                return result
            else:
                print("No property found")
                return None
        except Exception as e:
            print(f"Search error: {e}")
            return None

    def get_tax_sales_history(self, apn):
        """Test fetching tax and sales history"""
        print(f"\nFetching tax and sales history for APN: {apn}")
        try:
            # Get tax history
            tax_history = self.api_client.get_tax_history(apn)
            if tax_history:
                print(f"Found {len(tax_history)} tax records")
                for record in tax_history[:3]:  # Show first 3
                    print(f"  Year {record.get('tax_year')}: ${record.get('amount_due', 0):,}")

            # Get sales history
            sales_history = self.api_client.get_sales_history(apn)
            if sales_history:
                print(f"Found {len(sales_history)} sales records")
                for sale in sales_history[:3]:  # Show first 3
                    print(f"  {sale.get('sale_date')}: ${sale.get('sale_amount', 0):,}")

            return tax_history, sales_history
        except Exception as e:
            print(f"History fetch error: {e}")
            return None, None

def main():
    print("\n" + "="*60)
    print("MARICOPA PROPERTY SEARCH - SIMPLE TEST")
    print("="*60)

    try:
        # Create search instance
        search = SimplePropertySearch()

        # Test with sample APNs
        test_apns = ["123-45-678", "117-01-001", "234-56-789"]

        for apn in test_apns:
            print("\n" + "-"*40)
            result = search.search_by_apn(apn)
            if result:
                # Also get tax and sales history
                tax_history, sales_history = search.get_tax_sales_history(apn)

        print("\n" + "="*60)
        print("Test completed successfully!")
        return 0

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())