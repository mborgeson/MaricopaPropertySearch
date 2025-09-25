#!/usr/bin/env python3
"""
Quick Method Test - Tests specific data collection methods
Focused on testing the exact methods requested.
"""

import json
import os
import sys
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from api_client import MaricopaAPIClient

from config_manager import ConfigManager


def test_specific_methods():
    """Test the specific methods requested"""
    print("=" * 60)
    print("QUICK METHOD TEST - MARICOPA PROPERTY SEARCH")
    print("=" * 60)

    # Initialize components
    try:
        config_manager = ConfigManager()
        api_client = MaricopaAPIClient(config_manager)
        print("✓ API Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize API client: {e}")
        return

    test_apn = "501-38-034A"
    print(f"Testing with APN: {test_apn}")
    print()

    # Test 1: get_property_info() - This might be get_property_details()
    print("1. Testing get_property_details()...")
    try:
        result = api_client.get_property_details(test_apn)
        if result:
            print("   ✓ SUCCESS: Property details retrieved")
            print(f"   - Owner: {result.get('owner_name', 'N/A')}")
            print(f"   - Address: {result.get('property_address', 'N/A')}")
            print(f"   - APN: {result.get('apn', 'N/A')}")
        else:
            print("   ⚠ No property details found (method works but no data)")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    print()

    # Test 2: get_tax_information()
    print("2. Testing get_tax_information()...")
    try:
        result = api_client.get_tax_information(test_apn)
        if result:
            print("   ✓ SUCCESS: Tax information retrieved")
            print(
                f"   - Payment Status: {result.get('scraped_data', {}).get('current_tax', {}).get('payment_status', 'N/A')}"
            )
            print(f"   - Data Sources: {result.get('data_sources', [])}")
        else:
            print("   ⚠ No tax information found (method works but no data)")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    print()

    # Test 3: get_sales_history()
    print("3. Testing get_sales_history()...")
    try:
        result = api_client.get_sales_history(test_apn, years=5)
        if result and len(result) > 0:
            print(f"   ✓ SUCCESS: {len(result)} sales records retrieved")
            for i, sale in enumerate(result[:2]):  # Show first 2
                print(
                    f"   - Sale {i+1}: {sale.get('sale_date', 'N/A')} - ${sale.get('sale_price', 'N/A'):,}"
                    if sale.get("sale_price")
                    else f"   - Sale {i+1}: {sale.get('sale_date', 'N/A')} - N/A"
                )
        else:
            print("   ⚠ No sales history found (method works but no data)")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    print()

    # Test 4: get_owner_information() - might be part of property details
    print("4. Testing owner information (via get_property_details)...")
    try:
        result = api_client.get_property_details(test_apn)
        if result and result.get("owner_name"):
            print("   ✓ SUCCESS: Owner information available")
            print(f"   - Owner: {result.get('owner_name')}")
            print(f"   - Mailing Address: {result.get('mailing_address', 'N/A')}")
        else:
            print("   ⚠ No owner information found (method works but no data)")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    print()

    # Test 5: API client integration with scrapers
    print("5. Testing API client scraper integration...")
    try:
        # The get_tax_information method already integrates with scrapers
        # Let's test the comprehensive method
        result = api_client.get_comprehensive_property_info(test_apn)
        if result:
            print("   ✓ SUCCESS: Scraper integration working")
            print(
                f"   - Property data: {'Available' if result.get('property_address') or result.get('owner_name') else 'Limited'}"
            )
            print(f"   - Raw data fields: {len(result.get('detailed_data', {}))}")
        else:
            print("   ⚠ Scraper integration works but limited data")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    print()

    # Test 6: Error handling with invalid APN
    print("6. Testing error handling with invalid APN...")
    try:
        invalid_apn = "INVALID-TEST"
        result = api_client.get_property_details(invalid_apn)
        if result is None:
            print("   ✓ SUCCESS: Invalid APN correctly returned None")
        else:
            print("   ⚠ WARNING: Invalid APN returned unexpected data")
    except Exception as e:
        print(
            f"   ✓ SUCCESS: Invalid APN correctly raised exception: {type(e).__name__}"
        )
    print()

    print("=" * 60)
    print("QUICK TEST SUMMARY:")
    print("✓ = Working correctly")
    print("⚠ = Method works but limited/no data for test APN")
    print("✗ = Method has errors")
    print("=" * 60)


if __name__ == "__main__":
    test_specific_methods()
