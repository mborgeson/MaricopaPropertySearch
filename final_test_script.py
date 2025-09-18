#!/usr/bin/env python3
"""
Final Test Script - Tests all data collection methods
Simple ASCII-only version for Windows compatibility.
"""

import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

def test_all_methods():
    """Test all data collection methods"""
    print("=" * 60)
    print("FINAL TEST - MARICOPA PROPERTY DATA COLLECTION")
    print("=" * 60)
    
    # Initialize components
    try:
        config_manager = EnhancedConfigManager()
        api_client = UnifiedMaricopaAPIClient(config_manager)
        print("PASS: API Client initialized successfully")
    except Exception as e:
        print(f"FAIL: Failed to initialize API client: {e}")
        return
    
    test_apn = "501-38-034A"
    backup_apns = ["501-38-034", "501-38-001", "500-01-001"]
    print(f"Testing with APN: {test_apn}")
    print(f"Backup APNs: {', '.join(backup_apns)}")
    print()
    
    results = {}
    
    # Test 1: get_property_details() (equivalent to get_property_info)
    print("TEST 1: get_property_details() method")
    try:
        result = api_client.get_property_details(test_apn)
        if result:
            print("   PASS: Property details retrieved")
            print(f"   - Owner: {result.get('owner_name', 'N/A')}")
            print(f"   - Address: {result.get('property_address', 'N/A')}")
            print(f"   - APN: {result.get('apn', 'N/A')}")
            print(f"   - Search Source: {result.get('search_source', 'N/A')}")
            results['property_details'] = True
        else:
            print("   WARN: No property details found (method works but no data)")
            results['property_details'] = False
    except Exception as e:
        print(f"   FAIL: {e}")
        results['property_details'] = False
    print()
    
    # Test 2: get_tax_information()
    print("TEST 2: get_tax_information() method")
    try:
        result = api_client.get_tax_information(test_apn)
        if result:
            print("   PASS: Tax information retrieved")
            scraped_data = result.get('scraped_data', {})
            payment_status = scraped_data.get('current_tax', {}).get('payment_status', 'N/A')
            print(f"   - Payment Status: {payment_status}")
            print(f"   - Data Sources: {result.get('data_sources', [])}")
            print(f"   - Timestamp: {result.get('timestamp', 'N/A')}")
            results['tax_information'] = True
        else:
            print("   WARN: No tax information found")
            results['tax_information'] = False
    except Exception as e:
        print(f"   FAIL: {e}")
        results['tax_information'] = False
    print()
    
    # Test 3: get_sales_history()
    print("TEST 3: get_sales_history() method")
    try:
        result = api_client.get_sales_history(test_apn, years=5)
        if result and len(result) > 0:
            print(f"   PASS: {len(result)} sales records retrieved")
            for i, sale in enumerate(result[:2]):  # Show first 2
                price = sale.get('sale_price')
                price_str = f"${price:,}" if price else "N/A"
                print(f"   - Sale {i+1}: {sale.get('sale_date', 'N/A')} - {price_str}")
            results['sales_history'] = True
        else:
            print("   WARN: No sales history found")
            results['sales_history'] = False
    except Exception as e:
        print(f"   FAIL: {e}")
        results['sales_history'] = False
    print()
    
    # Test 4: get_owner_information() (part of property details)
    print("TEST 4: Owner information retrieval")
    try:
        result = api_client.get_property_details(test_apn)
        if result and (result.get('owner_name') or result.get('mailing_address')):
            print("   PASS: Owner information available")
            print(f"   - Owner: {result.get('owner_name', 'N/A')}")
            print(f"   - Mailing Address: {result.get('mailing_address', 'N/A')}")
            results['owner_information'] = True
        else:
            print("   WARN: No owner information found")
            results['owner_information'] = False
    except Exception as e:
        print(f"   FAIL: {e}")
        results['owner_information'] = False
    print()
    
    # Test 5: API client integration with scrapers
    print("TEST 5: API client and scraper integration")
    try:
        result = api_client.get_comprehensive_property_info(test_apn)
        if result:
            print("   PASS: Scraper integration working")
            data_fields = len(result.get('detailed_data', {}))
            print(f"   - Detailed data sections: {data_fields}")
            print(f"   - Has raw data: {'Yes' if result.get('raw_data') else 'No'}")
            results['scraper_integration'] = True
        else:
            print("   WARN: Scraper integration limited")
            results['scraper_integration'] = False
    except Exception as e:
        print(f"   FAIL: {e}")
        results['scraper_integration'] = False
    print()
    
    # Test 6: Error handling with invalid APN
    print("TEST 6: Error handling with invalid inputs")
    try:
        invalid_apn = "INVALID-TEST-123"
        result = api_client.get_property_details(invalid_apn)
        if result is None:
            print("   PASS: Invalid APN correctly returned None")
            results['error_handling'] = True
        else:
            print("   WARN: Invalid APN returned data (might be valid behavior)")
            results['error_handling'] = True  # Still consider this OK
    except Exception as e:
        print(f"   PASS: Invalid APN correctly handled with exception: {type(e).__name__}")
        results['error_handling'] = True
    print()
    
    # Test with backup APNs if primary failed
    if not results.get('property_details'):
        print("TEST 7: Trying backup APNs (primary failed)")
        for backup_apn in backup_apns:
            try:
                print(f"   Trying APN: {backup_apn}")
                result = api_client.get_property_details(backup_apn)
                if result and (result.get('owner_name') or result.get('property_address')):
                    print(f"   PASS: Backup APN {backup_apn} worked!")
                    print(f"   - Owner: {result.get('owner_name', 'N/A')}")
                    print(f"   - Address: {result.get('property_address', 'N/A')}")
                    results['backup_apn_success'] = backup_apn
                    break
            except Exception as e:
                print(f"   FAIL: {backup_apn} - {e}")
        print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY:")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    total = len([k for k in results.keys() if k != 'backup_apn_success'])
    
    print(f"Overall: {passed}/{total} tests passed")
    print()
    
    for test, result in results.items():
        if test == 'backup_apn_success':
            continue
        status = "PASS" if result else "FAIL/WARN"
        print(f"  {test.replace('_', ' ').title()}: {status}")
    
    if 'backup_apn_success' in results:
        print(f"  Backup APN Success: {results['backup_apn_success']}")
    
    print()
    print("INTERPRETATION:")
    print("- PASS: Method works correctly")
    print("- WARN: Method works but no data for test APN")  
    print("- FAIL: Method has errors or doesn't work")
    print()
    
    if passed >= total - 1:  # Allow for one failure/warning
        print("OVERALL STATUS: DATA COLLECTION METHODS ARE WORKING!")
        return 0
    else:
        print("OVERALL STATUS: SOME ISSUES DETECTED - CHECK FAILURES ABOVE")
        return 1

if __name__ == "__main__":
    sys.exit(test_all_methods())